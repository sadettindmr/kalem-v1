from fastapi import APIRouter, Depends

from athena.core.database import get_db
from athena.schemas.search import SearchFilters, SearchResponse
from sqlalchemy.ext.asyncio import AsyncSession
from athena.services.search import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search_papers(
    filters: SearchFilters,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Akademik makale aramasi yapar.

    Semantic Scholar ve OpenAlex API'lerinden paralel arama yapar,
    sonuclari birlestirir ve tekillestirir.

    Returns:
        SearchResponse: results (makale listesi) + meta (ham/dedup istatistikler)
    """
    service = SearchService(db)
    return await service.search_papers(filters)
