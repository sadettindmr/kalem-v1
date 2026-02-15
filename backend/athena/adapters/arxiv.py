import asyncio

import httpx
import feedparser
from loguru import logger

from athena.adapters.base import BaseSearchProvider
from athena.schemas.search import AuthorSchema, PaperResponse, PaperSource, SearchFilters


class ArxivProvider(BaseSearchProvider):
    """arXiv API adaptoru.

    Atom/XML formatinda yanit dondurur, feedparser ile parse edilir.
    - URL: http://export.arxiv.org/api/query
    - Pagination: start + max_results parametreleri
    - Rate limit: ~3 req/s (resmi limit yok ama nazik kullanim beklenir)

    API Docs: https://info.arxiv.org/help/api/
    """

    BASE_URL = "http://export.arxiv.org/api/query"
    RESULTS_PER_PAGE = 100
    MAX_RESULTS = 1000

    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        """arXiv API'den makale aramasi yapar.

        start/max_results pagination ile MAX_RESULTS'a kadar sonuc toplar.

        Args:
            filters: Arama kriterleri

        Returns:
            Bulunan makalelerin listesi (hata durumunda bos liste)
        """
        all_entries: list[dict] = []

        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                start = 0
                while start < self.MAX_RESULTS:
                    params = {
                        "search_query": f"all:{filters.query}",
                        "start": start,
                        "max_results": self.RESULTS_PER_PAGE,
                        "sortBy": "relevance",
                        "sortOrder": "descending",
                    }

                    response = await client.get(self.BASE_URL, params=params)
                    response.raise_for_status()

                    feed = feedparser.parse(response.text)
                    entries = feed.get("entries", [])

                    if not entries:
                        break

                    all_entries.extend(entries)

                    # toplam sonuc sayisini kontrol et
                    total_results = int(
                        feed.get("feed", {}).get("opensearch_totalresults", "0")
                    )
                    if start + self.RESULTS_PER_PAGE >= total_results:
                        break

                    start += self.RESULTS_PER_PAGE

                    # Rate limit onleme (arXiv nazik kullanim bekler)
                    await asyncio.sleep(0.5)

            logger.info(f"arXiv search: {len(all_entries)} results fetched")
            return self._parse_results(all_entries, filters)

        except httpx.HTTPStatusError as e:
            logger.warning(f"arXiv API error: {e.response.status_code}")
            if all_entries:
                return self._parse_results(all_entries, filters)
            return []
        except httpx.RequestError as e:
            logger.warning(f"arXiv request error: {e}")
            if all_entries:
                return self._parse_results(all_entries, filters)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in arXiv search: {e}")
            return []

    @staticmethod
    def _extract_arxiv_id(entry_id: str) -> str:
        """arXiv entry ID'sinden arxiv numarasini cikarir.

        Ornek: 'http://arxiv.org/abs/2101.00001v1' -> '2101.00001'
        """
        # URL'den son kismi al ve versiyon bilgisini kaldir
        arxiv_id = entry_id.rstrip("/").split("/")[-1]
        # v1, v2 gibi versiyon suffix'ini kaldir
        if "v" in arxiv_id:
            arxiv_id = arxiv_id.rsplit("v", 1)[0]
        return arxiv_id

    @staticmethod
    def _extract_pdf_url(links: list[dict]) -> str | None:
        """Entry link'lerinden PDF URL'ini bulur."""
        for link in links:
            if link.get("type") == "application/pdf":
                return link.get("href")
            if link.get("rel") == "related" and link.get("title") == "pdf":
                return link.get("href")
        return None

    @staticmethod
    def _extract_year(published: str | None) -> int | None:
        """Yayinlanma tarihinden yili cikarir. Ornek: '2021-01-15T...' -> 2021"""
        if not published:
            return None
        try:
            return int(published[:4])
        except (ValueError, IndexError):
            return None

    def _parse_results(
        self, entries: list[dict], filters: SearchFilters
    ) -> list[PaperResponse]:
        """feedparser entry'lerini PaperResponse listesine donusturur."""
        papers: list[PaperResponse] = []

        for entry in entries:
            title = entry.get("title", "Untitled").replace("\n", " ").strip()
            abstract = entry.get("summary", "").replace("\n", " ").strip() or None

            year = self._extract_year(entry.get("published"))

            # Client-side yil filtresi
            if filters.year_start and year and year < filters.year_start:
                continue
            if filters.year_end and year and year > filters.year_end:
                continue

            # Authors
            authors = [
                AuthorSchema(name=a.get("name", "Unknown"))
                for a in entry.get("authors", [])
                if a.get("name")
            ]

            # External ID: DOI varsa DOI, yoksa arXiv ID
            doi = None
            arxiv_doi = entry.get("arxiv_doi")
            if arxiv_doi:
                doi = arxiv_doi

            entry_id = entry.get("id", "")
            arxiv_id = self._extract_arxiv_id(entry_id)

            external_id = doi if doi else arxiv_id

            # PDF URL
            pdf_url = self._extract_pdf_url(entry.get("links", []))

            # Venue: primary_category
            primary_category = entry.get("arxiv_primary_category", {})
            venue = primary_category.get("term")  # ornek: cs.LG, cs.AI

            paper = PaperResponse(
                title=title,
                abstract=abstract,
                year=year,
                citation_count=0,  # arXiv citation bilgisi saglamaz
                venue=venue,
                authors=authors,
                source=PaperSource.ARXIV,
                external_id=external_id,
                pdf_url=pdf_url,
            )
            papers.append(paper)

        return papers
