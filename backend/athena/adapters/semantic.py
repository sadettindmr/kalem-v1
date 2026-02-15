import asyncio

import httpx
from loguru import logger

from athena.adapters.base import BaseSearchProvider
from athena.core.config import get_settings
from athena.schemas.search import AuthorSchema, PaperResponse, PaperSource, SearchFilters


class SemanticScholarProvider(BaseSearchProvider):
    """Semantic Scholar Graph API adaptoru.

    Standart search endpoint kullanir:
    - URL: /graph/v1/paper/search
    - Keyword relevance siralamasi (API varsayilani)
    - offset + limit bazli pagination (100/sayfa, max 1000)
    - Server-side yil ve citation filtreleme

    API Docs: https://api.semanticscholar.org/api-docs/#tag/Paper-Data/operation/get_graph_paper_relevance_search
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    FIELDS = "title,abstract,year,citationCount,venue,authors,externalIds,openAccessPdf"
    RESULTS_PER_PAGE = 100
    MAX_RESULTS = 1000

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        """Semantic Scholar API ile makale aramasi yapar.

        offset + limit bazli pagination ile MAX_RESULTS'a kadar sonuc toplar.
        Yil ve citation filtreleri server-side uygulanir.
        Rate limit onlemek icin istekler arasi 0.5s bekleme yapilir.

        Args:
            filters: Arama kriterleri

        Returns:
            Bulunan makalelerin listesi (hata durumunda kismi veya bos liste)
        """
        params: dict[str, str | int] = {
            "query": filters.query,
            "fields": self.FIELDS,
            "limit": self.RESULTS_PER_PAGE,
            "offset": 0,
        }

        # Server-side yil filtresi
        if filters.year_start and filters.year_end:
            params["year"] = f"{filters.year_start}-{filters.year_end}"
        elif filters.year_start:
            params["year"] = f"{filters.year_start}-"
        elif filters.year_end:
            params["year"] = f"-{filters.year_end}"

        # Server-side minimum citation filtresi
        if filters.min_citations:
            params["minCitationCount"] = str(filters.min_citations)

        # API key varsa header'a ekle
        headers: dict[str, str] = {}
        if self.settings.semantic_scholar_api_key:
            headers["x-api-key"] = self.settings.semantic_scholar_api_key

        all_data: list[dict] = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                offset = 0
                while offset < self.MAX_RESULTS:
                    params["offset"] = offset

                    response = await client.get(
                        self.BASE_URL, params=params, headers=headers
                    )
                    response.raise_for_status()
                    json_data = response.json()

                    page_data = json_data.get("data", [])
                    if not page_data:
                        break

                    all_data.extend(page_data)

                    # API'nin toplam sonuc sayisini kontrol et
                    total_api = json_data.get("total", 0)
                    if offset + self.RESULTS_PER_PAGE >= total_api:
                        break

                    offset += self.RESULTS_PER_PAGE

                    # Rate limit onleme (0.5s bekleme)
                    await asyncio.sleep(0.5)

            logger.info(f"Semantic Scholar search: {len(all_data)} results fetched")
            return self._parse_results(all_data)

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Semantic Scholar API error: {e.response.status_code} - {e.response.text[:200]}"
            )
            # Kismi sonuclar varsa onlari don
            if all_data:
                logger.info(f"Returning {len(all_data)} partial results from Semantic Scholar")
                return self._parse_results(all_data)
            return []
        except httpx.RequestError as e:
            logger.warning(f"Semantic Scholar request error: {e}")
            if all_data:
                return self._parse_results(all_data)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Semantic Scholar search: {e}")
            if all_data:
                return self._parse_results(all_data)
            return []

    def _parse_results(self, data: list[dict]) -> list[PaperResponse]:
        """API yanitini PaperResponse listesine donusturur.

        Args:
            data: API'den donen ham veri

        Returns:
            PaperResponse listesi
        """
        results: list[PaperResponse] = []

        for item in data:
            year = item.get("year")
            citation_count = item.get("citationCount") or 0

            # Authors mapping
            authors = [
                AuthorSchema(name=author.get("name", "Unknown"))
                for author in item.get("authors", [])
                if author.get("name")
            ]

            # External ID mapping (DOI oncelikli, yoksa paperId)
            external_ids = item.get("externalIds") or {}
            external_id = external_ids.get("DOI") or item.get("paperId")

            # PDF URL mapping
            open_access_pdf = item.get("openAccessPdf") or {}
            pdf_url = open_access_pdf.get("url")

            paper = PaperResponse(
                title=item.get("title", "Untitled"),
                abstract=item.get("abstract"),
                year=year,
                citation_count=citation_count,
                venue=item.get("venue"),
                authors=authors,
                source=PaperSource.SEMANTIC,
                external_id=external_id,
                pdf_url=pdf_url,
            )
            results.append(paper)

        return results
