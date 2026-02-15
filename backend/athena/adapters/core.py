import asyncio

import httpx
from loguru import logger

from athena.adapters.base import BaseSearchProvider
from athena.core.config import get_settings
from athena.schemas.search import AuthorSchema, PaperResponse, PaperSource, SearchFilters


class CoreProvider(BaseSearchProvider):
    """CORE API v3 adaptoru.

    Acik erisimli akademik makalelerin tam metin aramasini yapar.
    - URL: https://api.core.ac.uk/v3/search/works
    - Auth: Bearer token (CORE_API_KEY)
    - Pagination: offset + limit parametreleri
    - CORE_API_KEY yoksa bos liste doner (Warning log)

    API Docs: https://api.core.ac.uk/docs/v3
    """

    BASE_URL = "https://api.core.ac.uk/v3/search/works"
    RESULTS_PER_PAGE = 100
    MAX_RESULTS = 1000

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        """CORE API'den makale aramasi yapar.

        CORE_API_KEY ayarlanmamissa bos liste doner.

        Args:
            filters: Arama kriterleri

        Returns:
            Bulunan makalelerin listesi (hata veya API key yoksa bos liste)
        """
        if not self.settings.core_api_key:
            logger.warning("CORE_API_KEY is not set, skipping CORE search")
            return []

        headers = {
            "Authorization": f"Bearer {self.settings.core_api_key}",
        }

        all_results: list[dict] = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                offset = 0
                while offset < self.MAX_RESULTS:
                    params: dict[str, str | int] = {
                        "q": filters.query,
                        "limit": self.RESULTS_PER_PAGE,
                        "offset": offset,
                    }

                    # Server-side yil filtresi
                    if filters.year_start and filters.year_end:
                        params["q"] = f"{filters.query} AND yearPublished>={filters.year_start} AND yearPublished<={filters.year_end}"
                    elif filters.year_start:
                        params["q"] = f"{filters.query} AND yearPublished>={filters.year_start}"
                    elif filters.year_end:
                        params["q"] = f"{filters.query} AND yearPublished<={filters.year_end}"

                    response = await client.get(
                        self.BASE_URL, params=params, headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()

                    results = data.get("results", [])
                    if not results:
                        break

                    all_results.extend(results)

                    # Toplam sonuc sayisi kontrolu
                    total_hits = data.get("totalHits", 0)
                    if offset + self.RESULTS_PER_PAGE >= total_hits:
                        break

                    offset += self.RESULTS_PER_PAGE

                    # Rate limit onleme
                    await asyncio.sleep(0.5)

            logger.info(f"CORE search: {len(all_results)} results fetched")
            return self._parse_results(all_results, filters)

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"CORE API error: {e.response.status_code} - {e.response.text[:200]}"
            )
            if all_results:
                return self._parse_results(all_results, filters)
            return []
        except httpx.RequestError as e:
            logger.warning(f"CORE request error: {e}")
            if all_results:
                return self._parse_results(all_results, filters)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in CORE search: {e}")
            return []

    def _parse_results(
        self, results: list[dict], filters: SearchFilters
    ) -> list[PaperResponse]:
        """CORE API yanitini PaperResponse listesine donusturur."""
        papers: list[PaperResponse] = []

        for item in results:
            title = item.get("title") or "Untitled"
            abstract = item.get("abstract")

            year = item.get("yearPublished")

            # Client-side yil filtresi (fallback)
            if filters.year_start and year and year < filters.year_start:
                continue
            if filters.year_end and year and year > filters.year_end:
                continue

            # Citation count (CORE bunu saglamayabilir)
            citation_count = item.get("citationCount", 0) or 0

            # Client-side citation filtresi
            if filters.min_citations and citation_count < filters.min_citations:
                continue

            # Authors
            authors = []
            for author in item.get("authors", []):
                name = author.get("name")
                if name:
                    authors.append(AuthorSchema(name=name))

            # DOI
            doi = None
            for ext_id in item.get("identifiers", []):
                if isinstance(ext_id, str) and ext_id.startswith("10."):
                    doi = ext_id
                    break
            if not doi:
                doi = item.get("doi")

            # External ID: DOI varsa DOI, yoksa CORE ID
            core_id = str(item.get("id", ""))
            external_id = doi if doi else core_id

            # PDF URL (downloadUrl alanini kullan)
            pdf_url = item.get("downloadUrl")

            # Venue
            venue = None
            journal = item.get("journal")
            if journal:
                venue = journal.get("title") if isinstance(journal, dict) else str(journal)

            paper = PaperResponse(
                title=title,
                abstract=abstract,
                year=year,
                citation_count=citation_count,
                venue=venue,
                authors=authors,
                source=PaperSource.CORE,
                external_id=external_id,
                pdf_url=pdf_url,
            )
            papers.append(paper)

        return papers
