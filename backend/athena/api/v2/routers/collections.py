"""Collections API - Koleksiyon/Proje CRUD endpoint'leri."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from athena.core.database import get_db
from athena.models.associations import collection_entries
from athena.models.collection import Collection
from athena.models.library import LibraryEntry

router = APIRouter(prefix="/collections", tags=["Collections"])


# ==================== Tag Metadata ====================

TAG_METADATA = {
    "summary_list": "Koleksiyon Listesi",
    "summary_create": "Yeni Koleksiyon Oluştur",
    "summary_delete": "Koleksiyon Sil",
    "summary_sync": "Koleksiyon İçeriğini Senkronize Et",
    "summary_add": "Koleksiyona Makale Ekle",
    "summary_by_entry": "Makalenin Koleksiyonlarını Getir",
}


# ==================== Schemas ====================


class CollectionCreate(BaseModel):
    """Koleksiyon oluşturma isteği."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Koleksiyon adı (benzersiz olmalı)",
        examples=["Tez Literatürü"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Koleksiyon açıklaması",
        examples=["Yüksek lisans tezi için toplanan makaleler"],
    )


class CollectionSchema(BaseModel):
    """Koleksiyon detay DTO'su."""

    id: int = Field(..., description="Koleksiyon ID", examples=[1])
    name: str = Field(..., description="Koleksiyon adı", examples=["Tez Literatürü"])
    description: Optional[str] = Field(
        default=None,
        description="Koleksiyon açıklaması",
    )
    created_at: str = Field(..., description="Oluşturulma tarihi (ISO 8601)", examples=["2024-01-15T10:30:00"])
    entry_count: int = Field(default=0, description="Koleksiyondaki makale sayısı", examples=[24])

    model_config = {"from_attributes": True}


class CollectionListResponse(BaseModel):
    """Koleksiyon listeleme yanıtı."""

    items: list[CollectionSchema] = Field(..., description="Koleksiyon listesi")


class SyncEntriesRequest(BaseModel):
    """Koleksiyon içerik senkronizasyon isteği. Mevcut içerik bu listeyle değiştirilir."""

    entry_ids: list[int] = Field(
        default_factory=list,
        description="Koleksiyonun yeni içeriğini oluşturacak entry ID listesi",
        examples=[[1, 5, 12, 23]],
    )


class SyncEntriesResponse(BaseModel):
    """Senkronizasyon yanıtı."""

    status: str = Field(..., description="İşlem durumu", examples=["synced"])
    added: int = Field(default=0, description="Eklenen makale sayısı", examples=[3])
    removed: int = Field(default=0, description="Çıkarılan makale sayısı", examples=[1])


class AddEntriesRequest(BaseModel):
    """Koleksiyona makale ekleme isteği. Mevcut içerik korunur."""

    entry_ids: list[int] = Field(
        default_factory=list,
        description="Eklenecek entry ID listesi",
        examples=[[10, 11, 12]],
    )


class AddEntriesResponse(BaseModel):
    """Ekleme yanıtı."""

    status: str = Field(..., description="İşlem durumu", examples=["added"])
    added: int = Field(default=0, description="Yeni eklenen makale sayısı", examples=[2])
    already_exists: int = Field(default=0, description="Zaten mevcut olan makale sayısı", examples=[1])


class EntryCollectionsResponse(BaseModel):
    """Makalenin koleksiyon üyelikleri yanıtı."""

    collection_ids: list[int] = Field(
        ...,
        description="Makalenin ait olduğu koleksiyon ID listesi",
        examples=[[1, 3]],
    )


# ==================== Endpoints ====================


@router.get(
    "",
    response_model=CollectionListResponse,
    summary=TAG_METADATA["summary_list"],
    response_description="Tüm koleksiyonlar ve makale sayıları",
)
async def list_collections(
    db: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """Sistemdeki tüm koleksiyonları (projeleri) listeler.

    Her koleksiyon için içerdiği makale sayısı (`entry_count`) hesaplanarak döndürülür.
    """
    query = select(Collection).order_by(Collection.name)
    result = await db.execute(query)
    collections = result.scalars().all()

    # Her koleksiyonun entry sayisini hesapla
    count_query = (
        select(
            collection_entries.c.collection_id,
            func.count(collection_entries.c.entry_id).label("cnt"),
        )
        .group_by(collection_entries.c.collection_id)
    )
    count_result = await db.execute(count_query)
    counts = {row[0]: row[1] for row in count_result.all()}

    items = [
        CollectionSchema(
            id=c.id,
            name=c.name,
            description=c.description,
            created_at=c.created_at.isoformat(),
            entry_count=counts.get(c.id, 0),
        )
        for c in collections
    ]

    return CollectionListResponse(items=items)


@router.post(
    "",
    response_model=CollectionSchema,
    summary=TAG_METADATA["summary_create"],
    response_description="Oluşturulan koleksiyonun detayları",
)
async def create_collection(
    data: CollectionCreate,
    db: AsyncSession = Depends(get_db),
) -> CollectionSchema:
    """Yeni bir koleksiyon (proje) oluşturur.

    Aynı isimde koleksiyon varsa **409 Conflict** hatası döner.
    """
    # Ayni isimde koleksiyon var mi kontrol et
    existing = await db.execute(
        select(Collection).where(Collection.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Bu isimde bir koleksiyon zaten mevcut")

    collection = Collection(name=data.name, description=data.description)
    db.add(collection)
    await db.commit()
    await db.refresh(collection)

    logger.info(f"Collection created: id={collection.id}, name='{collection.name}'")

    return CollectionSchema(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at.isoformat(),
        entry_count=0,
    )


@router.delete(
    "/{collection_id}",
    summary=TAG_METADATA["summary_delete"],
    response_description="Silme onay mesajı",
)
async def delete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Belirtilen koleksiyonu siler.

    Koleksiyondaki makaleler **silinmez**, yalnızca koleksiyon ilişkileri kaldırılır.
    """
    collection = await db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Koleksiyon bulunamadi")

    await db.delete(collection)
    await db.commit()

    logger.info(f"Collection deleted: id={collection_id}, name='{collection.name}'")

    return {"status": "deleted", "id": collection_id}


@router.post(
    "/{collection_id}/entries",
    response_model=SyncEntriesResponse,
    summary=TAG_METADATA["summary_sync"],
    response_description="Eklenen ve çıkarılan makale sayıları",
)
async def sync_collection_entries(
    collection_id: int,
    data: SyncEntriesRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncEntriesResponse:
    """Koleksiyonun makale listesini gönderilen ID listesiyle **tam senkronize** eder.

    - Listede olup koleksiyonda olmayan entry'ler **eklenir**.
    - Koleksiyonda olup listede olmayan entry'ler **çıkarılır**.
    - Bu endpoint koleksiyonun tüm içeriğini yeniden tanımlar (replace semantics).
    """
    collection = await db.execute(
        select(Collection)
        .options(selectinload(Collection.entries))
        .where(Collection.id == collection_id)
    )
    collection_obj = collection.scalar_one_or_none()
    if not collection_obj:
        raise HTTPException(status_code=404, detail="Koleksiyon bulunamadi")

    # Mevcut entry ID'leri
    current_ids = {e.id for e in collection_obj.entries}
    target_ids = set(data.entry_ids)

    # Eklenecek ve silinecek ID'leri hesapla
    to_add = target_ids - current_ids
    to_remove = current_ids - target_ids

    # Yeni entry'leri ekle
    if to_add:
        entries_result = await db.execute(
            select(LibraryEntry).where(LibraryEntry.id.in_(to_add))
        )
        new_entries = entries_result.scalars().all()
        for entry in new_entries:
            collection_obj.entries.append(entry)

    # Cikarilacak entry'leri kaldir
    if to_remove:
        collection_obj.entries = [e for e in collection_obj.entries if e.id not in to_remove]

    await db.commit()

    logger.info(
        f"Collection entries synced: collection_id={collection_id}, "
        f"added={len(to_add)}, removed={len(to_remove)}"
    )

    return SyncEntriesResponse(
        status="synced",
        added=len(to_add),
        removed=len(to_remove),
    )


@router.post(
    "/{collection_id}/entries/add",
    response_model=AddEntriesResponse,
    summary=TAG_METADATA["summary_add"],
    response_description="Eklenen ve zaten mevcut olan makale sayıları",
)
async def add_entries_to_collection(
    collection_id: int,
    data: AddEntriesRequest,
    db: AsyncSession = Depends(get_db),
) -> AddEntriesResponse:
    """Koleksiyona yeni makaleler ekler (mevcut içerik korunur).

    Sync endpoint'inden farklı olarak **sadece ekleme** yapar, çıkartma yapmaz.
    Zaten koleksiyonda olan entry'ler atlanır ve `already_exists` sayısında raporlanır.
    """
    collection = await db.execute(
        select(Collection)
        .options(selectinload(Collection.entries))
        .where(Collection.id == collection_id)
    )
    collection_obj = collection.scalar_one_or_none()
    if not collection_obj:
        raise HTTPException(status_code=404, detail="Koleksiyon bulunamadi")

    # Mevcut entry ID'leri
    current_ids = {e.id for e in collection_obj.entries}
    requested_ids = set(data.entry_ids)

    # Sadece yeni olanları ekle
    to_add = requested_ids - current_ids
    already_exists = requested_ids & current_ids

    # Yeni entry'leri ekle
    if to_add:
        entries_result = await db.execute(
            select(LibraryEntry).where(LibraryEntry.id.in_(to_add))
        )
        new_entries = entries_result.scalars().all()
        for entry in new_entries:
            collection_obj.entries.append(entry)

    await db.commit()

    logger.info(
        f"Entries added to collection: collection_id={collection_id}, "
        f"added={len(to_add)}, already_exists={len(already_exists)}"
    )

    return AddEntriesResponse(
        status="added",
        added=len(to_add),
        already_exists=len(already_exists),
    )


@router.get(
    "/by-entry/{entry_id}",
    response_model=EntryCollectionsResponse,
    summary=TAG_METADATA["summary_by_entry"],
    response_description="Makalenin ait olduğu koleksiyon ID listesi",
)
async def get_entry_collections(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
) -> EntryCollectionsResponse:
    """Belirtilen library entry'nin hangi koleksiyonlara ait olduğunu döndürür.

    Frontend'de proje atama dialog'unda mevcut üyelikleri ön-işaretlemek için kullanılır.
    """
    entry = await db.execute(
        select(LibraryEntry)
        .options(selectinload(LibraryEntry.collections))
        .where(LibraryEntry.id == entry_id)
    )
    entry_obj = entry.scalar_one_or_none()
    if not entry_obj:
        raise HTTPException(status_code=404, detail="Library entry bulunamadi")

    collection_ids = [c.id for c in entry_obj.collections]

    logger.debug(f"Entry collections fetched: entry_id={entry_id}, count={len(collection_ids)}")

    return EntryCollectionsResponse(collection_ids=collection_ids)
