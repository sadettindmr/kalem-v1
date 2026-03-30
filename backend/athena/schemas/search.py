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

    name: str = Field(..., description="Yazar adı ve soyadı", examples=["Yann LeCun"])


class PaperResponse(BaseModel):
    """Arama sonuçlarında dönen makale DTO'su."""

    title: str = Field(
        ...,
        description="Makalenin başlığı",
        examples=["Deep Learning for Natural Language Processing"],
    )
    abstract: Optional[str] = Field(
        default=None,
        description="Makalenin özeti",
        examples=[
            "This paper presents a comprehensive survey of deep learning methods..."
        ],
    )
    year: Optional[int] = Field(
        default=None,
        description="Yayın yılı",
        examples=[2023],
    )
    citation_count: int = Field(
        default=0,
        description="Toplam atıf sayısı",
        examples=[142],
    )
    venue: Optional[str] = Field(
        default=None,
        description="Yayınlandığı dergi veya konferans",
        examples=["Nature Machine Intelligence"],
    )
    authors: list[AuthorSchema] = Field(
        default_factory=list,
        description="Yazar listesi",
    )
    source: PaperSource = Field(
        ...,
        description="Sonucun geldiği kaynak",
        examples=["semantic"],
    )
    external_id: Optional[str] = Field(
        default=None,
        description="DOI veya kaynak ID (Semantic Scholar ID, OpenAlex ID)",
        examples=["10.1038/s41586-021-03819-2"],
    )
    pdf_url: Optional[str] = Field(
        default=None,
        description="PDF indirme bağlantısı (varsa)",
        examples=["https://arxiv.org/pdf/2301.00001.pdf"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Attention Is All You Need",
                    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                    "year": 2017,
                    "citation_count": 95000,
                    "venue": "NeurIPS",
                    "authors": [{"name": "Ashish Vaswani"}, {"name": "Noam Shazeer"}],
                    "source": "semantic",
                    "external_id": "10.48550/arXiv.1706.03762",
                    "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
                }
            ]
        }
    }


class SearchFilters(BaseModel):
    """Arama filtreleri DTO'su."""

    query: str = Field(
        ...,
        min_length=1,
        description="Aranacak anahtar kelimeler",
        examples=["machine learning"],
    )
    year_start: Optional[int] = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Başlangıç yılı filtresi",
        examples=[2020],
    )
    year_end: Optional[int] = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Bitiş yılı filtresi",
        examples=[2024],
    )
    min_citations: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum atıf sayısı eşiği",
        examples=[50],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "machine learning",
                    "year_start": 2020,
                    "year_end": 2024,
                    "min_citations": 10,
                }
            ]
        }
    }


class SearchMeta(BaseModel):
    """Arama sonuç istatistikleri."""

    raw_semantic: int = Field(
        default=0, description="Semantic Scholar ham sonuç sayısı", examples=[50]
    )
    raw_openalex: int = Field(
        default=0, description="OpenAlex ham sonuç sayısı", examples=[50]
    )
    raw_arxiv: int = Field(
        default=0, description="arXiv ham sonuç sayısı", examples=[25]
    )
    raw_crossref: int = Field(
        default=0, description="Crossref ham sonuç sayısı", examples=[30]
    )
    raw_core: int = Field(default=0, description="CORE ham sonuç sayısı", examples=[20])
    relevance_removed: int = Field(
        default=0,
        description="Alaka dışı olduğu için elenen sonuç sayısı",
        examples=[15],
    )
    duplicates_removed: int = Field(
        default=0, description="Elenen mükerrer sonuç sayısı", examples=[40]
    )
    total: int = Field(
        default=0, description="Dedup sonrası toplam sonuç sayısı", examples=[120]
    )
    errors: list[str] = Field(
        default_factory=list, description="Hata veren kaynak bilgileri"
    )


class SearchResponse(BaseModel):
    """Arama yanıtı - sonuçlar + meta istatistikler."""

    results: list[PaperResponse] = Field(
        ...,
        description="Tekilleştirilmiş makale listesi",
    )
    meta: SearchMeta = Field(
        ...,
        description="Kaynak bazlı ham sayılar ve eleme istatistikleri",
    )
