"""PDF indirme stratejileri — Fallback Chain mimarisi.

Her strateji, verilen makale metadata'sından PDF indirmeyi dener.
Başarısız olursa bir sonraki stratejiye geçilir.

Zincir sırası:
  1. PrimaryDownloadStrategy  — Kaydedilmiş pdf_url'den doğrudan indir
  2. UnpaywallStrategy        — DOI ile Unpaywall OA PDF ara ve indir
  3. CoreApiStrategy          — DOI ile CORE açık erişim deposundan ara ve indir
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import httpx
from loguru import logger

# Gerçekçi tarayıcı User-Agent rotasyonu
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

DOWNLOAD_TIMEOUT = 120.0
UNPAYWALL_EMAIL = "kalem-kasghar@academic-tool.org"

# İndirme sonucu minimum geçerli PDF boyutu (byte)
MIN_VALID_PDF_SIZE = 1024


@dataclass
class PaperMeta:
    """Stratejilerin ihtiyaç duyduğu minimal makale bilgisi."""

    pdf_url: str | None
    doi: str | None
    title: str
    entry_id: int | None = None


def is_valid_pdf(content: bytes) -> bool:
    """İndirilen verinin gerçek PDF olup olmadığını kontrol eder.

    PDF dosyaları ``%PDF`` magic byte'ı ile başlar.
    Cloudflare challenge, paywall HTML veya boş yanıtlar ``False`` döner.
    """
    if len(content) < MIN_VALID_PDF_SIZE:
        return False
    return content[:5].startswith(b"%PDF")


def _browser_headers() -> dict[str, str]:
    """Yayıncı bot engellerini aşmak için gerçekçi tarayıcı header seti."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/pdf,application/xhtml+xml,text/html,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }


def _download_url(url: str, proxy_url: str | None = None) -> bytes:
    """URL'den byte içerik indirir (streaming)."""
    client_kwargs: dict = {
        "timeout": DOWNLOAD_TIMEOUT,
        "follow_redirects": True,
    }
    if proxy_url:
        client_kwargs["proxy"] = proxy_url

    headers = _browser_headers()

    with httpx.Client(**client_kwargs) as client:
        with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            return response.read()


# ─────────────────────────────────────────────────────────────
# Strateji Arayüzü
# ─────────────────────────────────────────────────────────────

class BaseDownloadStrategy(ABC):
    """İndirme stratejisi arayüzü."""

    name: str = "base"

    @abstractmethod
    def execute(
        self,
        meta: PaperMeta,
        proxy_url: str | None = None,
    ) -> bytes | None:
        """PDF byte içeriği döndürür, başarısız olursa ``None``."""
        ...


# ─────────────────────────────────────────────────────────────
# Strateji 1 — Doğrudan URL İndirme (Mevcut Mantık)
# ─────────────────────────────────────────────────────────────

class PrimaryDownloadStrategy(BaseDownloadStrategy):
    """Kaydedilmiş pdf_url'den doğrudan indirme."""

    name = "PrimaryDownload"

    def execute(self, meta: PaperMeta, proxy_url: str | None = None) -> bytes | None:
        if not meta.pdf_url:
            logger.debug(f"[{self.name}] PDF URL yok, atlanıyor: entry_id={meta.entry_id}")
            return None

        logger.info(
            f"[{self.name}] İndirme deneniyor: entry_id={meta.entry_id}, "
            f"url={meta.pdf_url[:120]}"
        )
        content = _download_url(meta.pdf_url, proxy_url)
        return content


# ─────────────────────────────────────────────────────────────
# Strateji 2 — Unpaywall Open Access
# ─────────────────────────────────────────────────────────────

class UnpaywallStrategy(BaseDownloadStrategy):
    """DOI üzerinden Unpaywall API'den açık erişim PDF bulma ve indirme."""

    name = "Unpaywall"

    def _fetch_oa_pdf_url(self, doi: str) -> str | None:
        api_url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                resp = client.get(api_url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"[{self.name}] API hatası: DOI={doi}, {type(e).__name__}: {e}")
            return None

        if not data.get("is_oa"):
            logger.debug(f"[{self.name}] Makale açık erişim değil: DOI={doi}")
            return None

        best_oa = data.get("best_oa_location") or {}
        pdf_url = best_oa.get("url_for_pdf")
        if pdf_url:
            logger.info(f"[{self.name}] OA PDF bulundu: DOI={doi}, url={pdf_url[:120]}")
            return pdf_url

        # url_for_pdf yoksa landing page dene
        landing = best_oa.get("url")
        if landing:
            logger.info(f"[{self.name}] Landing page bulundu: DOI={doi}, url={landing[:120]}")
            return landing

        # Diğer OA konumlarına da bak
        oa_locations = data.get("oa_locations") or []
        for loc in oa_locations:
            loc_pdf = loc.get("url_for_pdf")
            if loc_pdf:
                logger.info(
                    f"[{self.name}] Alternatif OA konumu bulundu: DOI={doi}, url={loc_pdf[:120]}"
                )
                return loc_pdf

        logger.debug(f"[{self.name}] OA ama kullanılabilir URL bulunamadı: DOI={doi}")
        return None

    def execute(self, meta: PaperMeta, proxy_url: str | None = None) -> bytes | None:
        if not meta.doi:
            logger.debug(f"[{self.name}] DOI yok, atlanıyor: entry_id={meta.entry_id}")
            return None

        logger.info(
            f"[{self.name}] Unpaywall API kullanılarak alternatif link aranıyor... "
            f"entry_id={meta.entry_id}, DOI={meta.doi}"
        )
        oa_url = self._fetch_oa_pdf_url(meta.doi)
        if not oa_url:
            return None

        content = _download_url(oa_url, proxy_url)
        return content


# ─────────────────────────────────────────────────────────────
# Strateji 3 — CORE Açık Erişim Deposu
# ─────────────────────────────────────────────────────────────

class CoreApiStrategy(BaseDownloadStrategy):
    """DOI üzerinden CORE API'den açık erişim PDF bulma ve indirme."""

    name = "CoreAPI"
    CORE_API_BASE = "https://api.core.ac.uk/v3"

    def __init__(self, core_api_key: str | None = None) -> None:
        self.core_api_key = core_api_key

    def _fetch_core_pdf_url(self, doi: str) -> str | None:
        if not self.core_api_key:
            logger.debug(f"[{self.name}] CORE API key yok, atlanıyor")
            return None

        search_url = f"{self.CORE_API_BASE}/search/works"
        headers = {"Authorization": f"Bearer {self.core_api_key}"}
        params = {"q": f'doi:"{doi}"', "limit": 1}

        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                resp = client.get(search_url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"[{self.name}] API hatası: DOI={doi}, {type(e).__name__}: {e}")
            return None

        results = data.get("results") or []
        if not results:
            logger.debug(f"[{self.name}] CORE'da sonuç bulunamadı: DOI={doi}")
            return None

        work = results[0]

        # downloadUrl — doğrudan PDF linki
        download_url = work.get("downloadUrl")
        if download_url:
            logger.info(
                f"[{self.name}] CORE downloadUrl bulundu: DOI={doi}, url={download_url[:120]}"
            )
            return download_url

        # sourceFulltextUrls — alternatif tam metin linkleri
        fulltext_urls = work.get("sourceFulltextUrls") or []
        for url in fulltext_urls:
            if url:
                logger.info(
                    f"[{self.name}] CORE fulltext URL bulundu: DOI={doi}, url={url[:120]}"
                )
                return url

        logger.debug(f"[{self.name}] CORE'da PDF URL bulunamadı: DOI={doi}")
        return None

    def execute(self, meta: PaperMeta, proxy_url: str | None = None) -> bytes | None:
        if not meta.doi:
            logger.debug(f"[{self.name}] DOI yok, atlanıyor: entry_id={meta.entry_id}")
            return None

        logger.info(
            f"[{self.name}] CORE API'de açık erişim aranıyor... "
            f"entry_id={meta.entry_id}, DOI={meta.doi}"
        )
        core_url = self._fetch_core_pdf_url(meta.doi)
        if not core_url:
            return None

        content = _download_url(core_url, proxy_url)
        return content


# ─────────────────────────────────────────────────────────────
# Fallback Chain Yöneticisi
# ─────────────────────────────────────────────────────────────

def run_fallback_chain(
    meta: PaperMeta,
    file_path: Path,
    proxy_url: str | None = None,
    core_api_key: str | None = None,
) -> bool:
    """Stratejileri sırasıyla deneyerek PDF indirmeyi gerçekleştirir.

    Args:
        meta: Makale metadata'sı
        file_path: Kaydedilecek dosya yolu
        proxy_url: Opsiyonel proxy URL
        core_api_key: Opsiyonel CORE API anahtarı

    Returns:
        True ise geçerli PDF indirildi ve dosya kaydedildi.
        False ise tüm stratejiler başarısız oldu.
    """
    strategies: list[BaseDownloadStrategy] = [
        PrimaryDownloadStrategy(),
        UnpaywallStrategy(),
        CoreApiStrategy(core_api_key=core_api_key),
    ]

    for strategy in strategies:
        try:
            content = strategy.execute(meta, proxy_url)
            if content is None:
                continue

            if is_valid_pdf(content):
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(content)
                logger.info(
                    f"[FallbackChain] Başarılı — strateji={strategy.name}, "
                    f"entry_id={meta.entry_id}, boyut={len(content)} bytes"
                )
                return True
            else:
                logger.warning(
                    f"[FallbackChain] {strategy.name} geçersiz dosya (PDF değil) döndürdü. "
                    f"entry_id={meta.entry_id}. Bir sonraki stratejiye geçiliyor..."
                )
        except Exception as e:
            logger.warning(
                f"[FallbackChain] {strategy.name} başarısız oldu: "
                f"{type(e).__name__}: {e}. entry_id={meta.entry_id}. "
                f"Bir sonrakine geçiliyor..."
            )

    logger.warning(
        f"[FallbackChain] Tüm stratejiler başarısız — entry_id={meta.entry_id}, "
        f"doi={meta.doi}"
    )
    return False
