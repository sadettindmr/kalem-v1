from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from athena.schemas.search import AuthorSchema, PaperSource


class TagSchema(BaseModel):
    """Tag DTO'su."""

    id: int
    name: str


class PaperDetailSchema(BaseModel):
    """Kütüphanedeki makale detay DTO'su."""

    id: int
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = 0
    venue: Optional[str] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    authors: list[AuthorSchema] = Field(default_factory=list)
    created_at: datetime


class LibraryEntrySchema(BaseModel):
    """Kütüphane girişi DTO'su - Paper detayları ile birlikte."""

    id: int
    source: PaperSource
    download_status: str
    file_path: Optional[str] = None
    is_favorite: bool = False
    tags: list[TagSchema] = Field(default_factory=list)
    paper: PaperDetailSchema

    model_config = {"from_attributes": True}


class LibraryListResponse(BaseModel):
    """Kütüphane listeleme yanıtı - Pagination destekli."""

    items: list[LibraryEntrySchema]
    total: int
    page: int
    limit: int
