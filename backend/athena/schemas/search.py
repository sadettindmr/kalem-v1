import enum
from typing import Optional

from pydantic import BaseModel, Field


class PaperSource(str, enum.Enum):
    """Kaynak türü enum'u - API'den dönen verilerin kaynağını belirtir."""

    SEMANTIC = "semantic"
    OPENALEX = "openalex"
    ARXIV = "arxiv"
    CROSSREF = "crossref"
    CORE = "core"
    MANUAL = "manual"


class AuthorSchema(BaseModel):
    """Yazar bilgisi DTO'su."""

    name: str


class PaperResponse(BaseModel):
    """Arama sonuçlarında dönen makale DTO'su."""

    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = Field(default=0)
    venue: Optional[str] = None
    authors: list[AuthorSchema] = Field(default_factory=list)
    source: PaperSource
    external_id: Optional[str] = Field(
        default=None, description="DOI veya kaynak ID (Semantic Scholar ID, OpenAlex ID)"
    )
    pdf_url: Optional[str] = None


class SearchFilters(BaseModel):
    """Arama filtreleri DTO'su."""

    query: str = Field(..., min_length=1, description="Arama sorgusu")
    year_start: Optional[int] = Field(default=None, ge=1900, le=2100)
    year_end: Optional[int] = Field(default=None, ge=1900, le=2100)
    min_citations: Optional[int] = Field(default=None, ge=0)


class SearchMeta(BaseModel):
    """Arama sonuc istatistikleri."""

    raw_semantic: int = Field(default=0, description="Semantic Scholar ham sonuc sayisi")
    raw_openalex: int = Field(default=0, description="OpenAlex ham sonuc sayisi")
    raw_arxiv: int = Field(default=0, description="arXiv ham sonuc sayisi")
    raw_crossref: int = Field(default=0, description="Crossref ham sonuc sayisi")
    raw_core: int = Field(default=0, description="CORE ham sonuc sayisi")
    relevance_removed: int = Field(default=0, description="Alaka disi oldugu icin elenen sonuc sayisi")
    duplicates_removed: int = Field(default=0, description="Elenen mukerrer sonuc sayisi")
    total: int = Field(default=0, description="Dedup sonrasi toplam sonuc sayisi")
    errors: list[str] = Field(default_factory=list, description="Hata veren kaynak bilgileri")


class SearchResponse(BaseModel):
    """Arama yaniti - sonuclar + meta istatistikler."""

    results: list[PaperResponse]
    meta: SearchMeta
