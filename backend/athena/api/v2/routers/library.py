from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from athena.core.database import get_db
from athena.models.author import Author
from athena.models.library import DownloadStatus, LibraryEntry
from athena.models.paper import Paper
from athena.models.tag import Tag
from athena.schemas.library import (
    LibraryEntrySchema,
    LibraryListResponse,
    PaperDetailSchema,
    TagSchema,
)
from athena.schemas.search import AuthorSchema, PaperResponse, PaperSource
from athena.services.export import ExportService
from athena.services.library import LibraryService
from athena.tasks.downloader import download_paper_task, retry_stuck_downloads, retry_all_incomplete_downloads

router = APIRouter(prefix="/library", tags=["Library"])


class IngestRequest(BaseModel):
    """Kütüphaneye makale ekleme isteği."""

    paper: PaperResponse
    search_query: str = Field(
        default="",
        description="Arama terimi (etiketleme için, virgülle ayrılmış)",
    )


class IngestResponse(BaseModel):
    """Kütüphaneye makale ekleme yanıtı."""

    status: str
    entry_id: int


@router.post("/ingest", response_model=IngestResponse)
async def ingest_paper(
    request: IngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Makaleyi kütüphaneye ekler ve PDF indirme görevini başlatır.

    Args:
        request: Makale verisi ve arama terimi
        db: Veritabanı oturumu

    Returns:
        İşlem durumu ve entry_id
    """
    # 1. LibraryService ile makaleyi kaydet
    service = LibraryService(db)
    entry = await service.add_paper_to_library(request.paper, request.search_query)

    logger.info(f"Paper added to library: entry_id={entry.id}, paper_id={entry.paper_id}")

    # 2. Download task'i kuyruğa ekle (broker bağlantı hatası olabilir)
    status = "queued"
    try:
        download_paper_task.delay(entry_id=entry.id)
        logger.info(f"Download task queued for entry_id={entry.id}")
    except Exception as e:
        # Broker bağlantı hatası olursa makale yine de kaydedilmiş olur
        logger.warning(f"Could not queue download task for entry_id={entry.id}: {e}")
        status = "saved"

    return IngestResponse(status=status, entry_id=entry.id)


class BulkIngestRequest(BaseModel):
    """Toplu kutuphanye ekleme istegi."""

    papers: list[PaperResponse] = Field(..., min_length=1, max_length=100)
    search_query: str = Field(default="")


class BulkIngestResponse(BaseModel):
    """Toplu ekleme yaniti."""

    status: str
    added_count: int
    duplicate_count: int = 0
    failed_count: int = 0
    entry_ids: list[int]


class CheckLibraryRequest(BaseModel):
    """Kutuphanede kayitli makale kontrolu istegi."""

    external_ids: list[str] = Field(..., min_length=1, max_length=5000)


class CheckLibraryResponse(BaseModel):
    """Kutuphanede kayitli makale kontrolu yaniti."""

    saved_ids: list[str]


@router.post("/check", response_model=CheckLibraryResponse)
async def check_library_papers(
    request: CheckLibraryRequest,
    db: AsyncSession = Depends(get_db),
) -> CheckLibraryResponse:
    """Verilen external_id'lerin kutuphanede kayitli olup olmadigini kontrol eder."""
    service = LibraryService(db)
    saved_ids = await service.get_saved_external_ids(request.external_ids)
    return CheckLibraryResponse(saved_ids=list(saved_ids))


@router.post("/ingest/bulk", response_model=BulkIngestResponse)
async def bulk_ingest_papers(
    request: BulkIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> BulkIngestResponse:
    """Birden fazla makaleyi toplu olarak kutuphanye ekler."""
    service = LibraryService(db)
    entry_ids: list[int] = []
    duplicate_count = 0
    failed_count = 0

    for paper in request.papers:
        try:
            # Duplikasyon kontrolu
            if await service.is_paper_in_library(paper):
                duplicate_count += 1
                continue

            entry = await service.add_paper_to_library(paper, request.search_query)
            entry_ids.append(entry.id)
            try:
                download_paper_task.delay(entry_id=entry.id)
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Bulk ingest failed: {paper.title[:50]} - {e}")
            failed_count += 1
            continue

    return BulkIngestResponse(
        status="queued" if entry_ids else "no_new_papers",
        added_count=len(entry_ids),
        duplicate_count=duplicate_count,
        failed_count=failed_count,
        entry_ids=entry_ids,
    )


@router.get("", response_model=LibraryListResponse)
async def list_library(
    page: int = Query(default=1, ge=1, description="Sayfa numarası"),
    limit: int = Query(default=20, ge=1, le=100, description="Sayfa başına öğe sayısı"),
    tag: Optional[str] = Query(default=None, description="Etikete göre filtrele"),
    status: Optional[str] = Query(default=None, description="İndirme durumuna göre filtrele (pending, completed, failed)"),
    min_citations: Optional[int] = Query(default=None, ge=0, description="Minimum atıf sayısı"),
    year_start: Optional[int] = Query(default=None, ge=1900, le=2100, description="Başlangıç yılı"),
    year_end: Optional[int] = Query(default=None, ge=1900, le=2100, description="Bitiş yılı"),
    search: Optional[str] = Query(default=None, description="Başlık, yazar veya etiket araması"),
    db: AsyncSession = Depends(get_db),
) -> LibraryListResponse:
    """Kütüphanedeki makaleleri listeler.

    Args:
        page: Sayfa numarası (1'den başlar)
        limit: Sayfa başına öğe sayısı (max 100)
        tag: Opsiyonel etiket filtresi
        status: Opsiyonel indirme durumu filtresi
        min_citations: Opsiyonel minimum atıf filtresi
        year_start: Opsiyonel başlangıç yılı filtresi
        year_end: Opsiyonel bitiş yılı filtresi
        search: Opsiyonel anahtar kelime araması (başlık, yazar, etiket)
        db: Veritabanı oturumu

    Returns:
        Sayfalanmış kütüphane listesi
    """
    # Base query with joinedload to avoid N+1
    query = select(LibraryEntry).options(
        joinedload(LibraryEntry.paper),
        joinedload(LibraryEntry.tags),
    )

    # Paper tablosuyla join (filtreler icin)
    query = query.join(LibraryEntry.paper)

    # Status filtresi
    if status:
        try:
            status_enum = DownloadStatus(status.lower())
            query = query.where(LibraryEntry.download_status == status_enum)
        except ValueError:
            pass  # Geçersiz status değeri, filtreleme yapma

    # Tag filtresi
    if tag:
        query = query.join(LibraryEntry.tags).where(Tag.name == tag.lower())

    # Min citations filtresi
    if min_citations is not None:
        query = query.where(Paper.citation_count >= min_citations)

    # Year range filtresi
    if year_start is not None:
        query = query.where(Paper.year >= year_start)
    if year_end is not None:
        query = query.where(Paper.year <= year_end)

    # Keyword search (baslik, yazar, etiket)
    if search:
        search_term = f"%{search.lower()}%"
        # Yazar ve tag icin subquery kullan
        author_subquery = (
            select(LibraryEntry.id)
            .join(LibraryEntry.paper)
            .join(Paper.authors)
            .where(func.lower(Author.name).like(search_term))
        )
        tag_subquery = (
            select(LibraryEntry.id)
            .join(LibraryEntry.tags)
            .where(func.lower(Tag.name).like(search_term))
        )
        query = query.where(
            func.lower(Paper.title).like(search_term)
            | LibraryEntry.id.in_(author_subquery)
            | LibraryEntry.id.in_(tag_subquery)
        )

    # Total count (filtreleme sonrası)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(LibraryEntry.id.desc())

    # Execute query
    result = await db.execute(query)
    entries = result.unique().scalars().all()

    # Convert to schema
    items = []
    for entry in entries:
        # Paper authors'ı yükle
        await db.refresh(entry.paper, ["authors"])

        paper_schema = PaperDetailSchema(
            id=entry.paper.id,
            title=entry.paper.title,
            abstract=entry.paper.abstract,
            year=entry.paper.year,
            citation_count=entry.paper.citation_count,
            venue=entry.paper.venue,
            doi=entry.paper.doi,
            pdf_url=entry.paper.pdf_url,
            authors=[AuthorSchema(name=a.name) for a in entry.paper.authors],
            created_at=entry.paper.created_at,
        )

        entry_schema = LibraryEntrySchema(
            id=entry.id,
            source=PaperSource(entry.source.value),
            download_status=entry.download_status.value,
            file_path=entry.file_path,
            is_favorite=entry.is_favorite,
            tags=[TagSchema(id=t.id, name=t.name) for t in entry.tags],
            paper=paper_schema,
        )
        items.append(entry_schema)

    return LibraryListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )


class RetryDownloadsResponse(BaseModel):
    """İndirmeleri tekrar deneme yanıtı."""

    status: str
    message: str


@router.post("/retry-downloads", response_model=RetryDownloadsResponse)
async def retry_downloads() -> RetryDownloadsResponse:
    """Tamamlanmamis tum indirmeleri tekrar kuyruga ekler.

    pending, downloading ve failed durumdaki TUM kayitlari bulur,
    durumlarini sifirlar ve tekrar indirme kuyruguna ekler.
    """
    try:
        result = retry_all_incomplete_downloads.delay()
        logger.info("Retry all incomplete downloads task queued")
        return RetryDownloadsResponse(
            status="queued",
            message="Tum tamamlanmamis indirmeler tekrar kuyruga eklendi",
        )
    except Exception as e:
        logger.error(f"Failed to queue retry task: {e}")
        return RetryDownloadsResponse(
            status="error",
            message=f"Gorev kuyruga eklenemedi: {e}",
        )


class DownloadStatsResponse(BaseModel):
    """Indirme istatistikleri yaniti."""

    pending: int = 0
    downloading: int = 0
    completed: int = 0
    failed: int = 0
    total: int = 0
    failed_entries: list[dict] = []


@router.get("/download-stats", response_model=DownloadStatsResponse)
async def download_stats(
    db: AsyncSession = Depends(get_db),
) -> DownloadStatsResponse:
    """Indirme durumu istatistiklerini dondurur.

    Her durum icin sayi + basarisiz kayitlarin detaylarini verir.
    """
    # Status bazli sayimlar
    count_query = (
        select(
            LibraryEntry.download_status,
            func.count(LibraryEntry.id),
        )
        .group_by(LibraryEntry.download_status)
    )
    result = await db.execute(count_query)
    counts = {row[0].value: row[1] for row in result.all()}

    pending = counts.get("pending", 0)
    downloading = counts.get("downloading", 0)
    completed = counts.get("completed", 0)
    failed = counts.get("failed", 0)

    # Basarisiz kayitlarin detaylari
    failed_query = (
        select(LibraryEntry)
        .options(joinedload(LibraryEntry.paper))
        .where(LibraryEntry.download_status == DownloadStatus.FAILED)
        .order_by(LibraryEntry.updated_at.desc())
        .limit(50)
    )
    failed_result = await db.execute(failed_query)
    failed_entries_list = failed_result.unique().scalars().all()

    failed_entries = []
    for entry in failed_entries_list:
        failed_entries.append({
            "id": entry.id,
            "paper_id": entry.paper_id,
            "title": entry.paper.title if entry.paper else "Bilinmeyen",
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        })

    return DownloadStatsResponse(
        pending=pending,
        downloading=downloading,
        completed=completed,
        failed=failed,
        total=pending + downloading + completed + failed,
        failed_entries=failed_entries,
    )


@router.get("/export")
async def export_library(
    format: Literal["csv", "xlsx"] = Query(
        default="xlsx",
        description="Dışa aktarma formatı (csv veya xlsx)",
    ),
    search_query: Optional[str] = Query(
        default=None,
        description="Etiket filtresi (virgülle ayrılmış)",
    ),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Kütüphane verilerini CSV veya XLSX formatında dışa aktarır.

    Args:
        format: Çıktı formatı ("csv" veya "xlsx", varsayılan: xlsx)
        search_query: Opsiyonel etiket filtresi (virgülle ayrılmış)
        db: Veritabanı oturumu

    Returns:
        StreamingResponse: Dosya içeriği
    """
    service = ExportService(db)
    buffer, content_type, filename = await service.export_library(
        format=format,
        search_query=search_query,
    )

    logger.info(f"Library exported: format={format}, filename={filename}")

    return StreamingResponse(
        content=buffer,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
