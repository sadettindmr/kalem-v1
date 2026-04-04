from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from athena.core.config import get_settings
from athena.core.database import get_db
from athena.core.file_paths import resolve_data_file_path, to_relative_data_path
from athena.models.associations import collection_entries
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
from athena.tasks.downloader import (
    download_paper_task,
    retry_all_incomplete_downloads,
    retry_stuck_downloads,
)

router = APIRouter(prefix="/library", tags=["Library"])


def _apply_library_filters(
    query,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    min_citations: Optional[int] = None,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    search: Optional[str] = None,
    collection_id: Optional[int] = None,
):
    """Library listeleme ve ZIP indirme endpointleri icin ortak filtre uygulayici."""
    query = query.join(LibraryEntry.paper)

    if collection_id is not None:
        query = query.where(
            LibraryEntry.id.in_(
                select(collection_entries.c.entry_id).where(
                    collection_entries.c.collection_id == collection_id
                )
            )
        )

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

    paper: PaperResponse = Field(..., description="Eklenecek makale verisi")
    search_query: str = Field(
        default="",
        description="Arama terimi (virgülle ayrılarak etiket olarak kaydedilir)",
        examples=["machine learning, deep learning"],
    )


class IngestResponse(BaseModel):
    """Kütüphaneye makale ekleme yanıtı."""

    status: str = Field(
        ..., description="İşlem durumu (queued veya saved)", examples=["queued"]
    )
    entry_id: int = Field(
        ..., description="Oluşturulan library entry ID", examples=[42]
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Makaleyi Kütüphaneye Ekle",
    response_description="Eklenen makalenin entry ID'si ve işlem durumu",
)
async def ingest_paper(
    request: IngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Arama sonuçlarından bir makaleyi kütüphaneye kaydeder ve PDF indirme görevini başlatır.

    - Makale DOI veya başlık bazında tekilleştirilerek veritabanına eklenir.
    - `search_query` alanı virgülle ayrılarak otomatik etiketleme yapılır.
    - PDF indirme görevi Celery kuyruğuna eklenir (broker hatası durumunda makale yine kaydedilir).
    """
    # 1. LibraryService ile makaleyi kaydet
    service = LibraryService(db)
    entry = await service.add_paper_to_library(request.paper, request.search_query)

    logger.info(
        f"Paper added to library: entry_id={entry.id}, paper_id={entry.paper_id}"
    )

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
    """Toplu kütüphaneye ekleme isteği."""

    papers: list[PaperResponse] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Eklenecek makale listesi (maks. 100)",
    )
    search_query: str = Field(
        default="",
        description="Arama terimi (etiketleme için)",
        examples=["neural networks"],
    )


class BulkIngestResponse(BaseModel):
    """Toplu ekleme yanıtı."""

    status: str = Field(..., description="İşlem durumu", examples=["queued"])
    added_count: int = Field(
        ..., description="Yeni eklenen makale sayısı", examples=[5]
    )
    duplicate_count: int = Field(
        default=0, description="Zaten kayıtlı mükerrer sayısı", examples=[2]
    )
    failed_count: int = Field(
        default=0, description="Başarısız ekleme sayısı", examples=[0]
    )
    entry_ids: list[int] = Field(
        ...,
        description="Eklenen makalelerin entry ID listesi",
        examples=[[10, 11, 12, 13, 14]],
    )


class CheckLibraryRequest(BaseModel):
    """Kütüphanede kayıtlı makale kontrolü isteği."""

    external_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Kontrol edilecek external ID (DOI) listesi",
        examples=[["10.1038/s41586-021-03819-2", "10.48550/arXiv.1706.03762"]],
    )


class CheckLibraryResponse(BaseModel):
    """Kütüphanede kayıtlı makale kontrolü yanıtı."""

    saved_ids: list[str] = Field(
        ...,
        description="Kütüphanede bulunan external ID listesi",
        examples=[["10.1038/s41586-021-03819-2"]],
    )


@router.post(
    "/check",
    response_model=CheckLibraryResponse,
    summary="Kütüphane Kayıt Kontrolü",
    response_description="Kütüphanede bulunan external ID'lerin listesi",
)
async def check_library_papers(
    request: CheckLibraryRequest,
    db: AsyncSession = Depends(get_db),
) -> CheckLibraryResponse:
    """Verilen external ID listesinin kütüphanede kayıtlı olup olmadığını toplu kontrol eder.

    Frontend'de arama sonuçlarındaki \"zaten kayıtlı\" durumunu göstermek için kullanılır.
    """
    service = LibraryService(db)
    saved_ids = await service.get_saved_external_ids(request.external_ids)
    return CheckLibraryResponse(saved_ids=list(saved_ids))


@router.post(
    "/ingest/bulk",
    response_model=BulkIngestResponse,
    summary="Toplu Makale Ekleme",
    response_description="Eklenen, mükerrer ve başarısız makale sayıları",
)
async def bulk_ingest_papers(
    request: BulkIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> BulkIngestResponse:
    """Birden fazla makaleyi tek seferde kütüphaneye ekler.

    - Maksimum 100 makale gönderilebilir.
    - Her makale için tekilleştirme kontrolü yapılır.
    - Mükerrer makaleler atlanır, başarısız olanlar sayılır.
    - Başarılı eklemeler için PDF indirme görevleri kuyruğa eklenir.
    """
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

            # Her makaleyi savepoint ile izole et — bir makale hata verirse
            # sadece o makalenin değişiklikleri geri alınır, session temiz kalır.
            async with db.begin_nested():
                entry = await service.add_paper_to_library(
                    paper, request.search_query, auto_commit=False
                )
            # Savepoint başarılı — değişiklikleri kalıcı yap
            await db.commit()
            entry_ids.append(entry.id)
            try:
                download_paper_task.delay(entry_id=entry.id)
            except Exception:
                pass
        except Exception as e:
            logger.warning(
                f"Bulk ingest skipped: {paper.title[:50]} - {type(e).__name__}: {e}"
            )
            failed_count += 1
            # Savepoint otomatik rollback edildi, session hâlâ kullanılabilir.
            # Güvenlik için açık rollback yaparak session'ın temiz olduğunu garanti et.
            await db.rollback()
            continue

    return BulkIngestResponse(
        status="queued" if entry_ids else "no_new_papers",
        added_count=len(entry_ids),
        duplicate_count=duplicate_count,
        failed_count=failed_count,
        entry_ids=entry_ids,
    )


@router.get(
    "",
    response_model=LibraryListResponse,
    summary="Kütüphane Listesi",
    response_description="Sayfalanmış makale listesi ve toplam kayıt sayısı",
)
async def list_library(
    page: int = Query(default=1, ge=1, description="Sayfa numarası"),
    limit: int = Query(default=20, ge=1, le=100, description="Sayfa başına öğe sayısı"),
    tag: Optional[str] = Query(default=None, description="Etikete göre filtrele"),
    status: Optional[str] = Query(
        default=None,
        description="İndirme durumuna göre filtrele (pending, completed, failed)",
    ),
    min_citations: Optional[int] = Query(
        default=None, ge=0, description="Minimum atıf sayısı"
    ),
    year_start: Optional[int] = Query(
        default=None, ge=1900, le=2100, description="Başlangıç yılı"
    ),
    year_end: Optional[int] = Query(
        default=None, ge=1900, le=2100, description="Bitiş yılı"
    ),
    search: Optional[str] = Query(
        default=None, description="Başlık, yazar veya etiket araması"
    ),
    collection_id: Optional[int] = Query(
        default=None, description="Koleksiyon ID filtresi"
    ),
    db: AsyncSession = Depends(get_db),
) -> LibraryListResponse:
    """Kütüphanedeki makaleleri filtreli ve sayfalanmış olarak listeler.

    **Desteklenen Filtreler:**
    - `tag`: Etikete göre filtreleme
    - `status`: İndirme durumu (pending, downloading, completed, failed)
    - `min_citations`: Minimum atıf sayısı eşiği
    - `year_start` / `year_end`: Yayın yılı aralığı
    - `search`: PostgreSQL FTS ile başlık/özet/yazar/etiket araması
    - `collection_id`: Belirli bir koleksiyondaki makaleler
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
        collection_id=collection_id,
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


@router.get(
    "/download-zip",
    summary="PDF Arşivi İndir (ZIP)",
    response_description="Filtrelenmiş PDF dosyalarını içeren ZIP arşivi",
)
async def download_zip_archive(
    tag: Optional[str] = Query(default=None, description="Etikete gore filtrele"),
    status: Optional[str] = Query(
        default=None, description="Indirme durumuna gore filtrele"
    ),
    min_citations: Optional[int] = Query(
        default=None, ge=0, description="Minimum atif sayisi"
    ),
    year_start: Optional[int] = Query(
        default=None, ge=1900, le=2100, description="Baslangic yili"
    ),
    year_end: Optional[int] = Query(
        default=None, ge=1900, le=2100, description="Bitis yili"
    ),
    search: Optional[str] = Query(
        default=None, description="Baslik, yazar veya etiket aramasi"
    ),
    collection_id: Optional[int] = Query(
        default=None, description="Koleksiyon ID filtresi"
    ),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Filtrelenmiş ve indirilmeye hazır PDF dosyalarını ZIP arşivi olarak döndürür.

    Yalnızca `download_status=completed` olan ve fiziksel dosyası mevcut olan makaleler dahil edilir.
    Kütüphane listeleme ile aynı filtre parametrelerini destekler.
    """
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
        collection_id=collection_id,
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

    status: str = Field(
        ..., description="İşlem durumu (queued veya error)", examples=["queued"]
    )
    message: str = Field(
        ...,
        description="Sonuç mesajı",
        examples=["Takili kalan indirmeler tekrar kuyruga eklendi"],
    )


@router.post(
    "/retry-downloads",
    response_model=RetryDownloadsResponse,
    summary="İndirmeleri Tekrar Dene",
    response_description="Kuyruğa ekleme durumu ve mesajı",
)
async def retry_downloads(
    scope: Literal["stuck", "all"] = Query(
        default="stuck",
        description="Retry kapsami: stuck (1 saatten eski pending/downloading) veya all (tum incomplete)",
    ),
) -> RetryDownloadsResponse:
    """Tamamlanamamış PDF indirmelerini tekrar Celery kuyruğuna ekler.

    **Kapsam Seçenekleri:**
    - `stuck`: 1 saatten eski pending/downloading kayıtları tekrar dener
    - `all`: pending, downloading ve failed tüm kayıtları tekrar dener
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
    """İndirme istatistikleri yanıtı."""

    pending: int = Field(default=0, description="Bekleyen indirme sayısı", examples=[3])
    downloading: int = Field(
        default=0, description="Devam eden indirme sayısı", examples=[1]
    )
    completed: int = Field(
        default=0, description="Tamamlanan indirme sayısı", examples=[120]
    )
    failed: int = Field(default=0, description="Başarısız indirme sayısı", examples=[5])
    total: int = Field(default=0, description="Toplam kayıt sayısı", examples=[129])
    failed_entries: list[dict] = Field(
        default_factory=list, description="Başarısız kayıtların detayları"
    )


class EnrichMetadataResponse(BaseModel):
    """Eksik metadata tamamlama yanıtı."""

    status: str = Field(..., description="İşlem durumu", examples=["completed"])
    message: str = Field(
        ...,
        description="Sonuç mesajı",
        examples=["Eksik metadata tamamlama islemi tamamlandi"],
    )
    processed: int = Field(default=0, description="İşlenen kayıt sayısı", examples=[20])
    updated: int = Field(
        default=0, description="Güncellenen kayıt sayısı", examples=[15]
    )
    skipped: int = Field(default=0, description="Atlanan kayıt sayısı", examples=[3])
    failed: int = Field(default=0, description="Başarısız kayıt sayısı", examples=[2])
    details: list[dict] = Field(
        default_factory=list, description="Kayıt bazlı işlem detayları"
    )


@router.post(
    "/enrich-metadata",
    response_model=EnrichMetadataResponse,
    summary="Eksik Metadata Tamamlama",
    response_description="İşlenen, güncellenen, atlanan ve başarısız kayıt sayıları",
)
async def enrich_metadata(
    limit: int = Query(
        default=20, ge=1, le=100, description="Maksimum islenecek kayit"
    ),
    db: AsyncSession = Depends(get_db),
) -> EnrichMetadataResponse:
    """Kütüphanedeki eksik metadata alanlarını (yıl, atıf, özet vb.) dış kaynaklardan tamamlar.

    DOI veya başlık kullanarak Crossref ve OpenAlex'ten güncel bilgileri çeker.
    """
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


@router.get(
    "/download-stats",
    response_model=DownloadStatsResponse,
    summary="İndirme İstatistikleri",
    response_description="Durum bazlı indirme sayıları ve başarısız kayıt detayları",
)
async def download_stats(
    db: AsyncSession = Depends(get_db),
) -> DownloadStatsResponse:
    """PDF indirme durumu istatistiklerini döndürür.

    Her durum (pending, downloading, completed, failed) için sayım yapar.
    Başarısız kayıtların detaylarını (id, başlık, son güncelleme) içerir.
    """
    # Status bazli sayimlar
    count_query = select(
        LibraryEntry.download_status,
        func.count(LibraryEntry.id),
    ).group_by(LibraryEntry.download_status)
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
        failed_entries.append(
            {
                "id": entry.id,
                "paper_id": entry.paper_id,
                "title": entry.paper.title if entry.paper else "Bilinmeyen",
                "updated_at": entry.updated_at.isoformat()
                if entry.updated_at
                else None,
            }
        )

    return DownloadStatsResponse(
        pending=pending,
        downloading=downloading,
        completed=completed,
        failed=failed,
        total=pending + downloading + completed + failed,
        failed_entries=failed_entries,
    )


@router.get(
    "/export",
    summary="Kütüphane Dışa Aktarma",
    response_description="CSV veya XLSX formatında bibliyografik veri dosyası",
)
async def export_library(
    format: Literal["csv", "xlsx"] = Query(
        default="xlsx",
        description="Dışa aktarma formatı (csv veya xlsx)",
    ),
    search_query: Optional[str] = Query(
        default=None,
        description="Etiket filtresi (virgülle ayrılmış)",
    ),
    collection_id: Optional[int] = Query(
        default=None, description="Koleksiyon ID filtresi"
    ),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Kütüphane verilerini CSV veya XLSX formatında dışa aktarır.

    **XLSX formatı 14 sütun içerir:**
    Başlık, Yazarlar, Yıl, Tür, Dergi, DOI, Anahtar Kelimeler,
    Arama Terimleri, APA Atıf, IEEE Atıf, Atıf Tarihi, Kaynak, İndirildi, Kod/Veri Erişimi.
    """
    service = ExportService(db)
    buffer, content_type, filename = await service.export_library(
        format=format,
        search_query=search_query,
        collection_id=collection_id,
    )

    logger.info(f"Library exported: format={format}, filename={filename}")

    return StreamingResponse(
        content=buffer,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete(
    "/{entry_id}",
    summary="Kütüphaneden Makale Sil",
    response_description="Silme onay mesajı",
)
async def delete_library_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Kütüphaneden bir makaleyi siler.

    Fiziksel PDF dosyası varsa diskten de kaldırılır.
    Koleksiyon ilişkileri CASCADE ile otomatik silinir.
    """
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    service = LibraryService(db)
    deleted = await service.delete_library_entry(entry_id, data_dir)

    if not deleted:
        raise HTTPException(status_code=404, detail="Library entry bulunamadi")

    logger.info(f"Library entry deleted: id={entry_id}")
    return {"status": "deleted", "id": entry_id}


class UpdateTagsRequest(BaseModel):
    """Etiket güncelleme isteği."""

    tags: list[str] = Field(
        ...,
        description="Yeni etiket listesi (mevcut etiketlerin yerine geçer)",
        examples=[["makine öğrenmesi", "derin öğrenme"]],
    )


@router.put(
    "/{entry_id}/tags",
    summary="Etiketleri Güncelle",
    response_description="Güncellenmiş etiket listesi",
)
async def update_library_tags(
    entry_id: int,
    data: UpdateTagsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Kütüphane kaydının etiketlerini günceller (overwrite).

    Mevcut etiketler kaldırılır ve gönderilen liste ile değiştirilir.
    Yeni etiketler otomatik oluşturulur.
    """
    service = LibraryService(db)
    entry = await service.update_tags(entry_id, data.tags)

    if not entry:
        raise HTTPException(status_code=404, detail="Library entry bulunamadi")

    logger.info(f"Tags updated: entry_id={entry_id}, tags={[t.name for t in entry.tags]}")
    return {
        "status": "updated",
        "entry_id": entry_id,
        "tags": [{"id": t.id, "name": t.name} for t in entry.tags],
    }
