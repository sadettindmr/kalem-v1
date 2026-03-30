from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from athena.core.database import get_db
from athena.schemas.search import SearchFilters, SearchResponse
from athena.services.search import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post(
    "",
    response_model=SearchResponse,
    summary="Akademik Literatür Taraması Yap",
    response_description="Arama sonuçları ve kaynak istatistikleri",
)
async def search_papers(
    filters: SearchFilters,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Birden fazla akademik kaynaktan paralel makale araması yapar.

    **Desteklenen Kaynaklar:**
    - Semantic Scholar
    - OpenAlex
    - arXiv
    - Crossref
    - CORE

    Sonuçlar birleştirilir, DOI ve başlık bazında tekilleştirilir,
    alaka düzeyi düşük sonuçlar filtrelenir.
    `meta` alanında her kaynaktan gelen ham sayılar ve eleme istatistikleri döner.
    """
    service = SearchService(db)
    return await service.search_papers(filters)
