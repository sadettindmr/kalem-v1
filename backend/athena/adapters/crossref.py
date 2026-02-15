import asyncio

import httpx
from loguru import logger

from athena.adapters.base import BaseSearchProvider
from athena.core.config import get_settings
from athena.schemas.search import AuthorSchema, PaperResponse, PaperSource, SearchFilters


class CrossrefProvider(BaseSearchProvider):
    """Crossref API adaptoru.

    REST API ile akademik makale metadata araması yapar.
    - URL: https://api.crossref.org/works
    - Pagination: offset + rows parametreleri
    - Polite Pool: User-Agent header'inda email gonderilir (rate limit arttirir)
    - Her sonucta DOI kesinlikle bulunur

    API Docs: https://api.crossref.org/swagger-ui/index.html
    Rate: Polite Pool ile ~50 req/s, yoksa ~1 req/s
    """

    BASE_URL = "https://api.crossref.org/works"
    RESULTS_PER_PAGE = 100
    MAX_RESULTS = 1000

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        """Crossref API'den makale aramasi yapar.

        Args:
            filters: Arama kriterleri

        Returns:
            Bulunan makalelerin listesi (hata durumunda bos liste)
        """
        headers = {
            "User-Agent": f"Athena/2.0 (mailto:{self.settings.openalex_email})",
        }

        all_items: list[dict] = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                offset = 0
                while offset < self.MAX_RESULTS:
                    params: dict[str, str | int] = {
                        "query": filters.query,
                        "rows": self.RESULTS_PER_PAGE,
                        "offset": offset,
                        "sort": "relevance",
                        "order": "desc",
                    }

                    # Server-side yil filtresi
                    filter_parts: list[str] = []
                    if filters.year_start:
                        filter_parts.append(f"from-pub-date:{filters.year_start}")
                    if filters.year_end:
                        filter_parts.append(f"until-pub-date:{filters.year_end}")
                    if filter_parts:
                        params["filter"] = ",".join(filter_parts)

                    response = await client.get(
                        self.BASE_URL, params=params, headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()

                    message = data.get("message", {})
                    items = message.get("items", [])
                    if not items:
                        break

                    all_items.extend(items)

                    # Toplam sonuc sayisi kontrolu
                    total_results = message.get("total-results", 0)
                    if offset + self.RESULTS_PER_PAGE >= total_results:
                        break

                    offset += self.RESULTS_PER_PAGE

                    # Crossref derin sayfalarda yavaslar, timeout onleme
                    await asyncio.sleep(0.5)

            logger.info(f"Crossref search: {len(all_items)} results fetched")
            return self._parse_results(all_items, filters)

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Crossref API error: {e.response.status_code} - {e.response.text[:200]}"
            )
            if all_items:
                return self._parse_results(all_items, filters)
            return []
        except httpx.RequestError as e:
            logger.warning(f"Crossref request error: {e}")
            if all_items:
                return self._parse_results(all_items, filters)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Crossref search: {e}")
            return []

    def _parse_results(
        self, items: list[dict], filters: SearchFilters
    ) -> list[PaperResponse]:
        """Crossref API yanitini PaperResponse listesine donusturur."""
        papers: list[PaperResponse] = []

        for item in items:
            # Title (genellikle list olarak gelir)
            title_list = item.get("title", [])
            title = title_list[0] if title_list else "Untitled"

            # Abstract (XML tag'leri icerebilir, basitce temizle)
            abstract = item.get("abstract")
            if abstract:
                # <jats:p> gibi XML tag'lerini temizle
                import re
                abstract = re.sub(r"<[^>]+>", "", abstract).strip()

            # Year
            date_parts = item.get("published", {}).get("date-parts", [[]])
            year = date_parts[0][0] if date_parts and date_parts[0] else None

            # Client-side yil filtresi (server-side yoksa fallback)
            if filters.year_start and year and year < filters.year_start:
                continue
            if filters.year_end and year and year > filters.year_end:
                continue

            # Citation count
            citation_count = item.get("is-referenced-by-count", 0) or 0

            # Client-side citation filtresi
            if filters.min_citations and citation_count < filters.min_citations:
                continue

            # Authors
            authors = []
            for author in item.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(AuthorSchema(name=name))

            # DOI (Crossref'te her zaman vardir)
            doi = item.get("DOI")

            # Venue
            container_title = item.get("container-title", [])
            venue = container_title[0] if container_title else None

            # PDF URL (link'lerden)
            pdf_url = None
            for link in item.get("link", []):
                if link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL")
                    break

            paper = PaperResponse(
                title=title,
                abstract=abstract,
                year=year,
                citation_count=citation_count,
                venue=venue,
                authors=authors,
                source=PaperSource.CROSSREF,
                external_id=doi,
                pdf_url=pdf_url,
            )
            papers.append(paper)

        return papers
