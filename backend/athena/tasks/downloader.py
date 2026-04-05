"""PDF indirme Celery task modülü.

Makale PDF'lerini indirip yerel dosya sistemine kaydeder.
Başarısız indirmeler için Fallback Chain (Yedekleme Zinciri) kullanır:

  1. PrimaryDownload — Kaydedilmiş pdf_url'den doğrudan indir
  2. Unpaywall       — DOI ile açık erişim PDF bul ve indir
  3. CoreAPI         — DOI ile CORE deposundan bul ve indir

Fallback chain başarısız olursa EZProxy fallback denenir (ayrı mekanizma).
"""

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from athena.core.config import get_settings
from athena.models.library import DownloadStatus, LibraryEntry
from athena.models.settings import UserSettings
from athena.tasks.download_strategies import PaperMeta, run_fallback_chain


def slugify(text: str) -> str:
    """Metni URL-friendly slug formatına dönüştürür."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:100]


def get_sync_db_session():
    """Senkron veritabanı bağlantısı oluşturur (Celery worker için)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    settings = get_settings()
    # asyncpg -> psycopg2 dönüşümü
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def generate_file_path(paper, settings) -> Path:
    """PDF dosya yolunu oluşturur.

    Format: {data_dir}/{paper_id}/{year}_{author_slug}_{title_slug}.pdf
    """
    year = paper.year or "unknown"

    author_slug = "unknown"
    if paper.authors:
        author_slug = slugify(paper.authors[0].name)

    title_slug = slugify(paper.title)
    filename = f"{year}_{author_slug}_{title_slug}.pdf"

    base_dir = Path(settings.data_dir)
    paper_dir = base_dir / str(paper.id)

    return paper_dir / filename


@shared_task(
    bind=True,
    autoretry_for=(httpx.HTTPStatusError, httpx.RequestError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def download_paper_task(self, entry_id: int) -> dict:
    """PDF indirme Celery task'i.

    Fallback Chain ile indirme dener, başarısız olursa EZProxy'ye düşer.
    """
    settings = get_settings()
    db: Session = get_sync_db_session()
    runtime_proxy_url = _resolve_runtime_proxy_url(db, settings.outbound_proxy)
    ezproxy_settings = _load_ezproxy_settings(db)
    core_api_key = _load_core_api_key(db, settings)

    retry_info = (
        f"(attempt {self.request.retries + 1}/{self.max_retries + 1})"
        if self.request.retries > 0
        else ""
    )
    logger.info(f"[Download] Starting entry_id={entry_id} {retry_info}")

    try:
        # 1. LibraryEntry'yi al
        stmt = select(LibraryEntry).where(LibraryEntry.id == entry_id)
        result = db.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            logger.error(f"[Download] LibraryEntry not found: entry_id={entry_id}")
            return {"status": "error", "message": "LibraryEntry not found"}

        paper = entry.paper
        logger.info(
            f"[Download] Paper: id={paper.id}, title='{paper.title[:80]}', doi={paper.doi}"
        )

        # 2. Status güncelle: downloading
        entry.download_status = DownloadStatus.DOWNLOADING
        db.commit()

        # 3. Dosya yolu oluştur
        file_path = generate_file_path(paper, settings)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 4. Fallback Chain ile indir
        meta = PaperMeta(
            pdf_url=paper.pdf_url,
            doi=paper.doi,
            title=paper.title,
            entry_id=entry_id,
        )
        success = run_fallback_chain(
            meta=meta,
            file_path=file_path,
            proxy_url=runtime_proxy_url,
            core_api_key=core_api_key,
        )

        if success:
            file_size = file_path.stat().st_size
            try:
                stored_path = str(file_path.relative_to(settings.data_dir))
            except ValueError:
                stored_path = str(file_path)

            entry.download_status = DownloadStatus.COMPLETED
            entry.file_path = stored_path
            entry.error_message = None
            db.commit()

            logger.info(
                f"[Download] Completed: entry_id={entry_id}, "
                f"size={file_size} bytes, path={stored_path}"
            )
            return {
                "status": "completed",
                "entry_id": entry_id,
                "file_path": stored_path,
                "file_size": file_size,
            }

        # 5. Fallback chain başarısız — PDF/DOI yoksa direkt fail
        if not paper.pdf_url and not paper.doi:
            entry.download_status = DownloadStatus.FAILED
            entry.error_message = (
                "PDF URL ve DOI bulunamadı. Makale muhtemelen açık erişim değil."
            )
            db.commit()
            logger.warning(
                f"[Download] No PDF URL or DOI: entry_id={entry_id}, paper_id={paper.id}"
            )
            return {"status": "failed", "message": "No PDF URL or DOI"}

        # 6. Fallback chain başarısız — HTTP üzerinden son deneme ve EZProxy fallback
        #    için orijinal hata zincirini tetikle (Celery retry mekanizması için)
        logger.warning(
            f"[Download] Fallback chain tükenmiş, EZProxy/retry denenecek: "
            f"entry_id={entry_id}"
        )
        _raise_for_retry(meta, runtime_proxy_url)

    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        error_type = type(e).__name__
        logger.warning(
            f"[Download] HTTP error: entry_id={entry_id}, type={error_type}, detail={e}"
        )
        # EZProxy fallback (mevcut mantık korunuyor, dokunulmadı)
        if _should_try_ezproxy(e, paper.pdf_url, paper, ezproxy_settings):
            try:
                _download_via_ezproxy(
                    ezproxy_settings,
                    file_path,
                    paper,
                    paper.pdf_url,
                    runtime_proxy_url,
                    entry_id,
                )
                entry.download_status = DownloadStatus.COMPLETED
                entry.error_message = None
                try:
                    stored_path = str(file_path.relative_to(settings.data_dir))
                except ValueError:
                    stored_path = str(file_path)
                entry.file_path = stored_path
                db.commit()
                logger.info(f"[Download] Completed via EZProxy: entry_id={entry_id}")
                return {
                    "status": "completed",
                    "entry_id": entry_id,
                    "file_path": stored_path,
                }
            except Exception as ez_err:
                logger.warning(
                    f"[Download] EZProxy fallback failed: entry_id={entry_id}, "
                    f"reason={ez_err}"
                )
        try:
            if self.request.retries >= self.max_retries:
                entry.download_status = DownloadStatus.FAILED
                entry.error_message = f"HTTP hatası ({error_type}): {str(e)[:200]}"
                db.commit()
                logger.error(
                    f"[Download] Max retries reached, marked FAILED: entry_id={entry_id}"
                )
                return {
                    "status": "failed",
                    "entry_id": entry_id,
                    "message": f"Max retries reached after HTTP error: {e}",
                }

            entry.download_status = DownloadStatus.PENDING
            db.commit()
            logger.info(
                f"[Download] Marked pending for retry: entry_id={entry_id}, "
                f"next_attempt={self.request.retries + 2}"
            )
        except Exception as mark_err:
            logger.error(
                f"[Download] Could not update status after HTTP error: {mark_err}"
            )

        # Celery otomatik retry yapacak
        raise

    except MaxRetriesExceededError:
        entry.download_status = DownloadStatus.FAILED
        entry.error_message = "Maksimum deneme sayısı aşıldı. PDF erişilemiyor."
        db.commit()
        logger.error(f"[Download] Max retries exceeded: entry_id={entry_id}")
        return {"status": "failed", "message": "Max retries exceeded"}

    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            f"[Download] Unexpected error: entry_id={entry_id}, "
            f"type={error_type}, detail={e}"
        )
        try:
            entry.download_status = DownloadStatus.FAILED
            entry.error_message = f"Beklenmeyen hata ({error_type}): {str(e)[:200]}"
            db.commit()
        except Exception:
            pass
        return {"status": "failed", "message": str(e)}

    finally:
        db.close()


@shared_task(bind=True)
def retry_stuck_downloads(self) -> dict:
    """Takılı kalan indirme görevlerini tespit edip tekrar kuyruğa ekler.

    Kriterler:
    - download_status = 'downloading' veya 'pending'
    - updated_at değeri 1 saatten eski
    """
    db: Session = get_sync_db_session()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    try:
        stmt = select(LibraryEntry).where(
            or_(
                LibraryEntry.download_status == DownloadStatus.PENDING,
                LibraryEntry.download_status == DownloadStatus.DOWNLOADING,
            ),
            LibraryEntry.updated_at < cutoff,
        )
        result = db.execute(stmt)
        stuck_entries = result.scalars().all()

        if not stuck_entries:
            logger.info("[RetryStuck] No stuck downloads found")
            return {"status": "ok", "retried_count": 0}

        logger.info(f"[RetryStuck] Found {len(stuck_entries)} stuck downloads")

        retried_ids = []
        for entry in stuck_entries:
            entry.download_status = DownloadStatus.PENDING
            retried_ids.append(entry.id)
            logger.info(
                f"[RetryStuck] Resetting entry_id={entry.id}, paper_id={entry.paper_id}"
            )

        db.commit()

        for entry_id in retried_ids:
            download_paper_task.delay(entry_id=entry_id)
            logger.info(f"[RetryStuck] Re-queued entry_id={entry_id}")

        logger.info(f"[RetryStuck] Retried {len(retried_ids)} stuck downloads")
        return {
            "status": "ok",
            "retried_count": len(retried_ids),
            "entry_ids": retried_ids,
        }

    except Exception as e:
        logger.error(f"[RetryStuck] Error: {type(e).__name__} - {e}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


@shared_task(bind=True)
def retry_all_incomplete_downloads(self) -> dict:
    """Tamamlanmamis tum indirmeleri tekrar kuyruga ekler.

    pending, downloading ve failed durumdaki TUM kayitlari bulur,
    durumlarini pending'e cevirip tekrar indirme kuyruguna ekler.
    """
    db: Session = get_sync_db_session()

    try:
        stmt = select(LibraryEntry).where(
            or_(
                LibraryEntry.download_status == DownloadStatus.PENDING,
                LibraryEntry.download_status == DownloadStatus.DOWNLOADING,
                LibraryEntry.download_status == DownloadStatus.FAILED,
            ),
        )
        result = db.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            logger.info("[RetryAll] No incomplete downloads found")
            return {"status": "ok", "retried_count": 0}

        logger.info(f"[RetryAll] Found {len(entries)} incomplete downloads")

        retried_ids = []
        for entry in entries:
            entry.download_status = DownloadStatus.PENDING
            retried_ids.append(entry.id)
            logger.info(
                f"[RetryAll] Resetting entry_id={entry.id}, paper_id={entry.paper_id}"
            )

        db.commit()

        for entry_id in retried_ids:
            download_paper_task.delay(entry_id=entry_id)
            logger.info(f"[RetryAll] Re-queued entry_id={entry_id}")

        logger.info(f"[RetryAll] Retried {len(retried_ids)} incomplete downloads")
        return {
            "status": "ok",
            "retried_count": len(retried_ids),
            "entry_ids": retried_ids,
        }

    except Exception as e:
        logger.error(f"[RetryAll] Error: {type(e).__name__} - {e}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# Yardımcı fonksiyonlar
# ─────────────────────────────────────────────────────────────


def _raise_for_retry(meta: PaperMeta, proxy_url: str | None) -> None:
    """Fallback chain başarısız olduktan sonra, Celery retry mekanizmasını
    tetiklemek için orijinal URL'ye bir kez daha istek atarak HTTPStatusError
    veya RequestError fırlatır."""
    from athena.tasks.download_strategies import _browser_headers, _download_url

    if meta.pdf_url:
        _download_url(meta.pdf_url, proxy_url)
    elif meta.doi:
        doi_url = f"https://doi.org/{meta.doi}"
        _download_url(doi_url, proxy_url)
    else:
        raise ValueError("PDF URL ve DOI bulunamadı")


def _resolve_runtime_proxy_url(db: Session, fallback_proxy: str | None) -> str | None:
    """DB'deki UserSettings'e gore guncel proxy URL'i belirler."""
    try:
        row = db.execute(
            select(UserSettings).order_by(UserSettings.id.asc())
        ).scalar_one_or_none()
    except Exception as exc:
        logger.warning(f"[Download] Could not read user_settings for proxy: {exc}")
        return fallback_proxy

    if not row:
        return fallback_proxy

    if row.proxy_enabled and row.proxy_url:
        return row.proxy_url

    return None


def _load_ezproxy_settings(db: Session) -> dict | None:
    """DB'den EZProxy ayarlarını çeker."""
    try:
        row = db.execute(
            select(UserSettings).order_by(UserSettings.id.asc())
        ).scalar_one_or_none()
    except Exception as exc:
        logger.warning(f"[Download] Could not read user_settings for ezproxy: {exc}")
        return None

    if not row or not row.ezproxy_prefix or not row.ezproxy_cookie:
        return None

    return {
        "prefix": row.ezproxy_prefix.strip(),
        "cookie": row.ezproxy_cookie.strip(),
    }


def _load_core_api_key(db: Session, settings) -> str | None:
    """DB veya .env'den CORE API anahtarını çeker."""
    try:
        row = db.execute(
            select(UserSettings).order_by(UserSettings.id.asc())
        ).scalar_one_or_none()
        if row and row.core_api_key:
            return row.core_api_key
    except Exception:
        pass
    return getattr(settings, "core_api_key", None)


def _should_try_ezproxy(
    error: Exception, pdf_url: str | None, paper, ezproxy_settings: dict | None
) -> bool:
    """EZProxy fallback şartlarını kontrol eder."""
    if not ezproxy_settings:
        return False
    if isinstance(error, httpx.HTTPStatusError) and error.response.status_code not in (
        401,
        402,
        403,
    ):
        return False
    if not pdf_url and not paper.doi:
        return False
    return True


def _build_ezproxy_target(prefix: str, pdf_url: str | None, paper) -> str:
    if pdf_url:
        return f"{prefix}{pdf_url}"
    if paper.doi:
        doi_url = paper.doi
        if not doi_url.startswith("http"):
            doi_url = f"https://doi.org/{doi_url}"
        return f"{prefix}{doi_url}"
    raise ValueError("EZProxy target could not be built")


def _download_via_ezproxy(
    ezproxy_settings: dict,
    file_path: Path,
    paper,
    original_pdf_url: str | None,
    proxy_url: str | None,
    entry_id: int | None,
) -> None:
    """EZProxy üzerinden indirme. Mevcut mantık aynen korunuyor."""
    from athena.tasks.download_strategies import _browser_headers, _download_url

    target = _build_ezproxy_target(ezproxy_settings["prefix"], original_pdf_url, paper)
    logger.info(
        f"[Download] EZProxy fallback attempted: entry_id={entry_id}, "
        f"target={target[:120]}"
    )
    headers = _browser_headers()
    headers["Cookie"] = ezproxy_settings["cookie"]

    client_kwargs: dict = {"timeout": 120.0, "follow_redirects": True}
    if proxy_url:
        client_kwargs["proxy"] = proxy_url

    with httpx.Client(**client_kwargs) as client:
        with client.stream("GET", target, headers=headers) as response:
            response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
