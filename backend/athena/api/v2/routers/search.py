from fastapi import APIRouter

from athena.schemas.search import SearchFilters, SearchResponse
from athena.services.search import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search_papers(filters: SearchFilters) -> SearchResponse:
    """Akademik makale aramasi yapar.

    Semantic Scholar ve OpenAlex API'lerinden paralel arama yapar,
    sonuclari birlestirir ve tekillestirir.

    Returns:
        SearchResponse: results (makale listesi) + meta (ham/dedup istatistikler)
    """
    service = SearchService()
    return await service.search_papers(filters)
