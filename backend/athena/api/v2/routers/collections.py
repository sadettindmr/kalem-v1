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


# ==================== Schemas ====================


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class CollectionSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: str
    entry_count: int = 0

    model_config = {"from_attributes": True}


class CollectionListResponse(BaseModel):
    items: list[CollectionSchema]


class SyncEntriesRequest(BaseModel):
    """Koleksiyona eklenecek entry ID listesi. Mevcut icerik bu listeyle senkronize edilir."""
    entry_ids: list[int] = Field(default_factory=list)


class SyncEntriesResponse(BaseModel):
    status: str
    added: int = 0
    removed: int = 0


class AddEntriesRequest(BaseModel):
    """Koleksiyona eklenecek entry ID listesi. Mevcut icerik korunur, sadece yeniler eklenir."""
    entry_ids: list[int] = Field(default_factory=list)


class AddEntriesResponse(BaseModel):
    status: str
    added: int = 0
    already_exists: int = 0


class EntryCollectionsResponse(BaseModel):
    collection_ids: list[int]


# ==================== Endpoints ====================


@router.get("", response_model=CollectionListResponse)
async def list_collections(
    db: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """Tum koleksiyonlari listeler."""
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


@router.post("", response_model=CollectionSchema)
async def create_collection(
    data: CollectionCreate,
    db: AsyncSession = Depends(get_db),
) -> CollectionSchema:
    """Yeni koleksiyon olusturur."""
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


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Koleksiyonu siler (makaleler silinmez, sadece iliskiler kalkar)."""
    collection = await db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Koleksiyon bulunamadi")

    await db.delete(collection)
    await db.commit()

    logger.info(f"Collection deleted: id={collection_id}, name='{collection.name}'")

    return {"status": "deleted", "id": collection_id}


@router.post("/{collection_id}/entries", response_model=SyncEntriesResponse)
async def sync_collection_entries(
    collection_id: int,
    data: SyncEntriesRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncEntriesResponse:
    """Koleksiyondaki makale listesini senkronize eder.

    Gonderilen entry_ids listesi koleksiyonun yeni icerigini belirler.
    Listede olmayan mevcut iliskiler silinir, yeni olanlar eklenir.
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


@router.post("/{collection_id}/entries/add", response_model=AddEntriesResponse)
async def add_entries_to_collection(
    collection_id: int,
    data: AddEntriesRequest,
    db: AsyncSession = Depends(get_db),
) -> AddEntriesResponse:
    """Koleksiyona yeni entry'ler ekler (mevcut icerik korunur).

    Sync endpoint'inden farki: sadece ekleme yapar, cikartma yapmaz.
    Zaten koleksiyonda olan entry'ler atlanir.
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


@router.get("/by-entry/{entry_id}", response_model=EntryCollectionsResponse)
async def get_entry_collections(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
) -> EntryCollectionsResponse:
    """Bir entry'nin hangi koleksiyonlarda oldugunu doner."""
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
