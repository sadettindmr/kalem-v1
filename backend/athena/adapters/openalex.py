import httpx
from loguru import logger

from athena.adapters.base import BaseSearchProvider
from athena.core.config import get_settings
from athena.schemas.search import AuthorSchema, PaperResponse, PaperSource, SearchFilters


class OpenAlexProvider(BaseSearchProvider):
    """OpenAlex API adaptoru.

    Cursor pagination kullanir:
    - Ilk istekte cursor=* gonderilir
    - Sonraki isteklerde meta.next_cursor kullanilir
    - next_cursor null olunca sonuclarin sonu

    API Docs: https://docs.openalex.org/
    Rate: 100 req/s, search sorgusu 1000 kredi/istek (gunluk 100K kredi free)
    Polite Pool: User-Agent header'inda email adresi gonderilir.
    """

    BASE_URL = "https://api.openalex.org/works"
    RESULTS_PER_PAGE = 100
    MAX_RESULTS = 1000

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        """OpenAlex API'den cursor pagination ile makale aramasi yapar.

        Args:
            filters: Arama kriterleri

        Returns:
            Bulunan makalelerin listesi (hata durumunda bos liste)
        """
        params: dict[str, str | int] = {
            "search": filters.query,
            "per_page": self.RESULTS_PER_PAGE,
            "cursor": "*",
        }

        # Server-side yil filtresi
        if filters.year_start and filters.year_end:
            params["filter"] = f"publication_year:{filters.year_start}-{filters.year_end}"
        elif filters.year_start:
            params["filter"] = f"publication_year:{filters.year_start}-"
        elif filters.year_end:
            params["filter"] = f"publication_year:-{filters.year_end}"

        headers = {
            "User-Agent": f"Athena/2.0 (mailto:{self.settings.openalex_email})",
        }

        all_results: list[dict] = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                while len(all_results) < self.MAX_RESULTS:
                    response = await client.get(
                        self.BASE_URL, params=params, headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()

                    page_results = data.get("results", [])
                    if not page_results:
                        break

                    all_results.extend(page_results)

                    # Cursor pagination: next_cursor null ise sonuclarin sonu
                    meta = data.get("meta", {})
                    next_cursor = meta.get("next_cursor")
                    if not next_cursor:
                        break

                    # Sonraki sayfa icin cursor'u guncelle
                    params["cursor"] = next_cursor

            logger.info(f"OpenAlex cursor pagination: {len(all_results)} results fetched")
            return self._parse_results(all_results, filters)

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"OpenAlex API error: {e.response.status_code} - {e.response.text}"
            )
            if all_results:
                return self._parse_results(all_results, filters)
            return []
        except httpx.RequestError as e:
            logger.warning(f"OpenAlex request error: {e}")
            if all_results:
                return self._parse_results(all_results, filters)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in OpenAlex search: {e}")
            return []

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
        """OpenAlex abstract_inverted_index formatindan duz metin olusturur."""
        if not inverted_index:
            return None
        words: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                words.append((pos, word))
        words.sort(key=lambda x: x[0])
        return " ".join(word for _, word in words) if words else None

    def _parse_results(
        self, results: list[dict], filters: SearchFilters
    ) -> list[PaperResponse]:
        """API yanitini PaperResponse listesine donusturur.

        Args:
            results: API'den donen ham veri
            filters: Client-side filtreleme icin arama kriterleri

        Returns:
            PaperResponse listesi
        """
        papers: list[PaperResponse] = []

        for item in results:
            year = item.get("publication_year")

            # Client-side yil filtresi (server-side filter yoksa fallback)
            if filters.year_start and year and year < filters.year_start:
                continue
            if filters.year_end and year and year > filters.year_end:
                continue

            # Atif filtresi (client-side)
            citation_count = item.get("cited_by_count") or 0
            if filters.min_citations and citation_count < filters.min_citations:
                continue

            # Authors mapping (authorships -> author.display_name)
            authors = []
            for authorship in item.get("authorships", []):
                author_info = authorship.get("author", {})
                name = author_info.get("display_name")
                if name:
                    authors.append(AuthorSchema(name=name))

            # External ID mapping (DOI)
            doi = item.get("doi")
            if doi and doi.startswith("https://doi.org/"):
                doi = doi.replace("https://doi.org/", "")

            # PDF URL mapping (best_oa_location.pdf_url)
            best_oa_location = item.get("best_oa_location") or {}
            pdf_url = best_oa_location.get("pdf_url")

            # Venue mapping
            primary_location = item.get("primary_location") or {}
            source = primary_location.get("source") or {}
            venue = source.get("display_name")

            paper = PaperResponse(
                title=item.get("title") or "Untitled",
                abstract=self._reconstruct_abstract(item.get("abstract_inverted_index")),
                year=year,
                citation_count=citation_count,
                venue=venue,
                authors=authors,
                source=PaperSource.OPENALEX,
                external_id=doi,
                pdf_url=pdf_url,
            )
            papers.append(paper)

        return papers
