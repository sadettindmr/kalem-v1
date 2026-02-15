import random
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from loguru import logger
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from athena.core.config import get_settings
from athena.models.library import DownloadStatus, LibraryEntry

# User-Agent rotasyonu için liste
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Indirme timeout suresi (saniye)
DOWNLOAD_TIMEOUT = 120.0


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
    # Yıl
    year = paper.year or "unknown"

    # İlk yazarın slug'ı
    author_slug = "unknown"
    if paper.authors:
        author_slug = slugify(paper.authors[0].name)

    # Başlık slug'ı
    title_slug = slugify(paper.title)

    # Dosya adı
    filename = f"{year}_{author_slug}_{title_slug}.pdf"

    # Tam yol
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

    Args:
        entry_id: LibraryEntry ID

    Returns:
        İşlem sonucu dict
    """
    settings = get_settings()
    db: Session = get_sync_db_session()

    retry_info = f"(attempt {self.request.retries + 1}/{self.max_retries + 1})" if self.request.retries > 0 else ""
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
        logger.info(f"[Download] Paper: id={paper.id}, title='{paper.title[:80]}', doi={paper.doi}")

        # 2. Status güncelle: downloading
        entry.download_status = DownloadStatus.DOWNLOADING
        db.commit()

        # 3. PDF URL kontrol
        pdf_url = _find_pdf_url(paper)

        if not pdf_url:
            entry.download_status = DownloadStatus.FAILED
            db.commit()
            logger.warning(f"[Download] No PDF URL found: entry_id={entry_id}, paper_id={paper.id}")
            return {"status": "failed", "message": "No PDF URL"}

        logger.info(f"[Download] PDF URL found: {pdf_url[:120]}")

        # 4. Dosya yolu oluştur
        file_path = generate_file_path(paper, settings)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 5. PDF indir
        logger.info(f"[Download] Downloading: entry_id={entry_id} -> {file_path}")
        _download_file(pdf_url, file_path)

        # 6. Dosya boyutunu kontrol et
        file_size = file_path.stat().st_size
        if file_size < 1024:
            logger.warning(f"[Download] Suspiciously small file ({file_size} bytes): entry_id={entry_id}")

        # 7. Başarılı: Status ve file_path güncelle
        entry.download_status = DownloadStatus.COMPLETED
        entry.file_path = str(file_path)
        db.commit()

        logger.info(f"[Download] Completed: entry_id={entry_id}, size={file_size} bytes, path={file_path}")
        return {
            "status": "completed",
            "entry_id": entry_id,
            "file_path": str(file_path),
            "file_size": file_size,
        }

    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        error_type = type(e).__name__
        logger.warning(f"[Download] HTTP error: entry_id={entry_id}, type={error_type}, detail={e}")
        # Celery otomatik retry yapacak
        raise

    except MaxRetriesExceededError:
        # Maksimum retry aşıldı
        entry.download_status = DownloadStatus.FAILED
        db.commit()
        logger.error(f"[Download] Max retries exceeded: entry_id={entry_id}")
        return {"status": "failed", "message": "Max retries exceeded"}

    except Exception as e:
        # Beklenmeyen hata
        error_type = type(e).__name__
        logger.error(f"[Download] Unexpected error: entry_id={entry_id}, type={error_type}, detail={e}")
        try:
            entry.download_status = DownloadStatus.FAILED
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

    Bu task manuel olarak POST /api/v2/library/retry-downloads ile
    veya Celery Beat ile periyodik olarak çağrılabilir.
    """
    db: Session = get_sync_db_session()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    try:
        # Takılı kayıtları bul
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
            # Durumu pending'e çevir
            entry.download_status = DownloadStatus.PENDING
            retried_ids.append(entry.id)
            logger.info(f"[RetryStuck] Resetting entry_id={entry.id}, paper_id={entry.paper_id}")

        db.commit()

        # Tekrar kuyruğa ekle
        for entry_id in retried_ids:
            download_paper_task.delay(entry_id=entry_id)
            logger.info(f"[RetryStuck] Re-queued entry_id={entry_id}")

        logger.info(f"[RetryStuck] Retried {len(retried_ids)} stuck downloads")
        return {"status": "ok", "retried_count": len(retried_ids), "entry_ids": retried_ids}

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
    Manuel tetikleme icin (Settings sayfasi).
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
            logger.info(f"[RetryAll] Resetting entry_id={entry.id}, paper_id={entry.paper_id}")

        db.commit()

        for entry_id in retried_ids:
            download_paper_task.delay(entry_id=entry_id)
            logger.info(f"[RetryAll] Re-queued entry_id={entry_id}")

        logger.info(f"[RetryAll] Retried {len(retried_ids)} incomplete downloads")
        return {"status": "ok", "retried_count": len(retried_ids), "entry_ids": retried_ids}

    except Exception as e:
        logger.error(f"[RetryAll] Error: {type(e).__name__} - {e}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


def _find_pdf_url(paper) -> str | None:
    """PDF URL'ini bulmaya çalışır.

    Öncelik sırası:
    1. Paper modeline kaydedilmiş pdf_url
    2. DOI varsa Unpaywall'dan dene (Sprint 6.1'de implement edilecek)
    3. None
    """
    # 1. Paper'da kaydedilmiş pdf_url varsa kullan
    if paper.pdf_url:
        return paper.pdf_url

    # 2. DOI varsa Unpaywall denemesi yapılabilir
    if paper.doi:
        # Placeholder: Unpaywall adapter Sprint 6.1'de eklenecek
        pass

    return None


def _download_file(url: str, file_path: Path) -> None:
    """URL'den dosyayı indirir.

    Args:
        url: İndirilecek dosyanın URL'i
        file_path: Kaydedilecek dosya yolu
    """
    # Rastgele User-Agent seç
    user_agent = random.choice(USER_AGENTS)

    headers = {
        "User-Agent": user_agent,
        "Accept": "application/pdf,*/*",
    }

    with httpx.Client(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
        with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
