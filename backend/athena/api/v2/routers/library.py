from typing import Literal, Optional
from pathlib import Path
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from athena.core.database import get_db
from athena.core.config import get_settings
from athena.core.file_paths import resolve_data_file_path, to_relative_data_path
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


def _apply_library_filters(
    query,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    min_citations: Optional[int] = None,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    search: Optional[str] = None,
):
    """Library listeleme ve ZIP indirme endpointleri icin ortak filtre uygulayici."""
    query = query.join(LibraryEntry.paper)

    if status:
        try:
            status_enum = DownloadStatus(status.lower())
            query = query.where(LibraryEntry.download_status == status_enum)
        except ValueError:
            pass

    if tag:
        query = query.join(LibraryEntry.tags).where(Tag.name == tag.lower())

    if min_citations is not None:
        query = query.where(Paper.citation_count >= min_citations)

    if year_start is not None:
        query = query.where(Paper.year >= year_start)
    if year_end is not None:
        query = query.where(Paper.year <= year_end)

    if search:
        search_term = f"%{search.lower()}%"
        ts_query = func.websearch_to_tsquery("english", search)
        fts_match = Paper.search_vector.op("@@")(ts_query)
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
        fallback_match = (
            func.lower(Paper.title).like(search_term)
            | func.lower(func.coalesce(Paper.abstract, "")).like(search_term)
            | LibraryEntry.id.in_(author_subquery)
            | LibraryEntry.id.in_(tag_subquery)
        )
        query = query.where(fts_match | fallback_match)

    return query


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
    service = LibraryService(db)
    entries, total = await service.get_library_entries(
        page=page,
        limit=limit,
        tag=tag,
        status=status,
        min_citations=min_citations,
        year_start=year_start,
        year_end=year_end,
        search=search,
    )

    # "completed" kayitlarin file_path degerini normalize et ve
    # fiziksel dosyasi olmayanlari otomatik iyilestir.
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    status_repaired = False
    for entry in entries:
        if entry.download_status == DownloadStatus.COMPLETED and entry.file_path:
            resolved = resolve_data_file_path(entry.file_path, data_dir)
            if resolved is None:
                entry.download_status = DownloadStatus.FAILED
                entry.file_path = None
                status_repaired = True
                continue

            # Legacy absolute path'leri relative formata cevir.
            normalized_relative = to_relative_data_path(resolved, data_dir)

            if normalized_relative != entry.file_path:
                entry.file_path = normalized_relative
                status_repaired = True

    if status_repaired:
        await db.commit()

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


@router.get("/download-zip")
async def download_zip_archive(
    tag: Optional[str] = Query(default=None, description="Etikete gore filtrele"),
    status: Optional[str] = Query(default=None, description="Indirme durumuna gore filtrele"),
    min_citations: Optional[int] = Query(default=None, ge=0, description="Minimum atif sayisi"),
    year_start: Optional[int] = Query(default=None, ge=1900, le=2100, description="Baslangic yili"),
    year_end: Optional[int] = Query(default=None, ge=1900, le=2100, description="Bitis yili"),
    search: Optional[str] = Query(default=None, description="Baslik, yazar veya etiket aramasi"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Filtrelenmis ve indirilmeye hazir PDF dosyalarini ZIP olarak dondurur."""
    query = select(LibraryEntry).options(
        joinedload(LibraryEntry.paper),
        joinedload(LibraryEntry.tags),
    )
    query = _apply_library_filters(
        query=query,
        tag=tag,
        status=status,
        min_citations=min_citations,
        year_start=year_start,
        year_end=year_end,
        search=search,
    ).order_by(LibraryEntry.id.desc())

    result = await db.execute(query)
    entries = result.unique().scalars().all()

    settings = get_settings()
    data_dir = Path(settings.data_dir)

    zip_buffer = BytesIO()
    added_count = 0

    with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        for entry in entries:
            if entry.download_status != DownloadStatus.COMPLETED:
                continue
            if not entry.file_path:
                continue

            resolved = resolve_data_file_path(entry.file_path, data_dir)
            if not resolved:
                continue

            arc_name = f"{entry.id}_{resolved.name}"
            archive.write(resolved, arcname=arc_name)
            added_count += 1

    zip_buffer.seek(0)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"kalem_library_archive_{date_str}.zip"

    logger.info(f"ZIP archive created: files={added_count}, filename={filename}")

    return StreamingResponse(
        content=zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class RetryDownloadsResponse(BaseModel):
    """İndirmeleri tekrar deneme yanıtı."""

    status: str
    message: str


@router.post("/retry-downloads", response_model=RetryDownloadsResponse)
async def retry_downloads(
    scope: Literal["stuck", "all"] = Query(
        default="stuck",
        description="Retry kapsami: stuck (1 saatten eski pending/downloading) veya all (tum incomplete)",
    ),
) -> RetryDownloadsResponse:
    """Indirmeleri tekrar kuyruga ekler.

    - scope=stuck: 1 saatten eski pending/downloading kayitlari tekrar dener
    - scope=all: pending/downloading/failed tum kayitlari tekrar dener
    """
    try:
        if scope == "all":
            retry_all_incomplete_downloads.delay()
            logger.info("Retry all incomplete downloads task queued")
            message = "Tum tamamlanmamis indirmeler tekrar kuyruga eklendi"
        else:
            retry_stuck_downloads.delay()
            logger.info("Retry stuck downloads task queued")
            message = "Takili kalan indirmeler tekrar kuyruga eklendi"

        return RetryDownloadsResponse(
            status="queued",
            message=message,
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


class EnrichMetadataResponse(BaseModel):
    """Eksik metadata tamamlama yaniti."""

    status: str
    message: str
    processed: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    details: list[dict] = []


@router.post("/enrich-metadata", response_model=EnrichMetadataResponse)
async def enrich_metadata(
    limit: int = Query(default=20, ge=1, le=100, description="Maksimum islenecek kayit"),
    db: AsyncSession = Depends(get_db),
) -> EnrichMetadataResponse:
    """Kutuphanedeki eksik metadata alanlarini dis kaynaklarla tamamlar."""
    service = LibraryService(db)
    result = await service.enrich_missing_metadata(limit=limit)

    return EnrichMetadataResponse(
        status="completed",
        message="Eksik metadata tamamlama islemi tamamlandi",
        processed=result["processed"],
        updated=result["updated"],
        skipped=result["skipped"],
        failed=result["failed"],
        details=result["details"],
    )


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
