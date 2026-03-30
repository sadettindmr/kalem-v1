from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from athena.schemas.search import AuthorSchema, PaperSource


class TagSchema(BaseModel):
    """Tag DTO'su."""

    id: int = Field(..., description="Etiket ID", examples=[1])
    name: str = Field(..., description="Etiket adı", examples=["machine learning"])


class PaperDetailSchema(BaseModel):
    """Kütüphanedeki makale detay DTO'su."""

    id: int = Field(..., description="Paper veritabanı ID", examples=[42])
    title: str = Field(
        ...,
        description="Makalenin başlığı",
        examples=["Attention Is All You Need"],
    )
    abstract: Optional[str] = Field(
        default=None,
        description="Makalenin özeti",
    )
    year: Optional[int] = Field(
        default=None,
        description="Yayın yılı",
        examples=[2017],
    )
    citation_count: int = Field(
        default=0,
        description="Toplam atıf sayısı",
        examples=[95000],
    )
    venue: Optional[str] = Field(
        default=None,
        description="Yayınlandığı dergi veya konferans",
        examples=["NeurIPS"],
    )
    doi: Optional[str] = Field(
        default=None,
        description="Digital Object Identifier",
        examples=["10.48550/arXiv.1706.03762"],
    )
    pdf_url: Optional[str] = Field(
        default=None,
        description="PDF indirme bağlantısı",
        examples=["https://arxiv.org/pdf/1706.03762.pdf"],
    )
    authors: list[AuthorSchema] = Field(
        default_factory=list,
        description="Yazar listesi",
    )
    created_at: datetime = Field(
        ...,
        description="Veritabanına eklenme tarihi",
    )


class LibraryEntrySchema(BaseModel):
    """Kütüphane girişi DTO'su - Paper detayları ile birlikte."""

    id: int = Field(..., description="Library entry ID", examples=[1])
    source: PaperSource = Field(
        ...,
        description="Makalenin geldiği kaynak",
        examples=["semantic"],
    )
    download_status: str = Field(
        ...,
        description="PDF indirme durumu (pending, downloading, completed, failed)",
        examples=["completed"],
    )
    file_path: Optional[str] = Field(
        default=None,
        description="İndirilen PDF dosyasının yolu",
        examples=["library/42_attention_is_all_you_need.pdf"],
    )
    error_message: Optional[str] = Field(
        default=None,
        description="İndirme hatası mesajı (varsa)",
        examples=["HTTP 403: Forbidden"],
    )
    is_favorite: bool = Field(
        default=False,
        description="Favori olarak işaretlenmiş mi",
    )
    tags: list[TagSchema] = Field(
        default_factory=list,
        description="Makaleye atanan etiketler",
    )
    paper: PaperDetailSchema = Field(
        ...,
        description="Makale detayları",
    )

    model_config = {"from_attributes": True}


class LibraryListResponse(BaseModel):
    """Kütüphane listeleme yanıtı - Pagination destekli."""

    items: list[LibraryEntrySchema] = Field(
        ...,
        description="Makale listesi",
    )
    total: int = Field(
        ...,
        description="Toplam kayıt sayısı (filtrelenmiş)",
        examples=[156],
    )
    page: int = Field(
        ...,
        description="Mevcut sayfa numarası",
        examples=[1],
    )
    limit: int = Field(
        ...,
        description="Sayfa başına öğe sayısı",
        examples=[20],
    )
