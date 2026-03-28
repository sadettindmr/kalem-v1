# Sprint 15 - Alt Koleksiyonlar / Proje Alanlari

## Sprint Ozeti
**Amac:** Kutuphane icin "Koleksiyon/Proje" altyapisini kurmak, makaleleri projelere atamak ve filtreleme/disa aktarma islemlerini projeye ozel hale getirmek.

**Durum:** Tamamlandi
**Tarih:** 2026-03-29

---

## ADIM 1: Backend - Koleksiyon Modelleri ve API

### 1.1 Veritabani Modelleri

#### `backend/athena/models/collection.py` (Yeni)
- `Collection` modeli: `id`, `name` (unique, 200 char), `description` (nullable, 1000 char), `created_at`
- `LibraryEntry` ile Many-to-Many iliski (`collection_entries` association table uzerinden)

#### `backend/athena/models/associations.py` (Guncellendi)
- `collection_entries` tablosu eklendi: `collection_id` + `entry_id` (her ikisi de FK + PK)

#### `backend/athena/models/library.py` (Guncellendi)
- `LibraryEntry.collections` relationship eklendi (back_populates="entries")

#### `backend/athena/models/__init__.py` (Guncellendi)
- `Collection` ve `collection_entries` export listesine eklendi

#### Alembic Migration
- `d7f2a3b8c901_add_collections.py`: `collections` ve `collection_entries` tablolarini olusturur

### 1.2 API Router

#### `backend/athena/api/v2/routers/collections.py` (Yeni)
| Endpoint | Method | Aciklama |
|----------|--------|----------|
| `GET /api/v2/collections` | GET | Tum koleksiyonlari listele (entry_count ile) |
| `POST /api/v2/collections` | POST | Yeni koleksiyon olustur |
| `DELETE /api/v2/collections/{id}` | DELETE | Koleksiyonu sil |
| `POST /api/v2/collections/{id}/entries` | POST | Koleksiyondaki makale listesini senkronize et |

**Sync Entries Davranisi:**
- Gonderilen `entry_ids` listesi koleksiyonun yeni icerigini belirler
- Listede olmayan mevcut iliskiler silinir, yeni olanlar eklenir

### 1.3 Filtreleme Guncellemesi

#### `_apply_library_filters()` (library.py router)
- `collection_id: Optional[int]` parametresi eklendi
- `collection_entries` tablosu uzerinden subquery ile filtre uygulanir

#### Guncellenen Endpoint'ler
| Endpoint | Parametre | Etki |
|----------|-----------|------|
| `GET /api/v2/library` | `collection_id` | Sadece o koleksiyondaki makaleleri listeler |
| `GET /api/v2/library/download-zip` | `collection_id` | Sadece o koleksiyondaki PDF'leri indirir |
| `GET /api/v2/library/export` | `collection_id` | Sadece o koleksiyondaki verileri disari aktarir |

#### `LibraryService.get_library_entries()` (services/library.py)
- `collection_id` parametresi eklendi, subquery ile filtre uygulanir

#### `ExportService.export_library()` (services/export.py)
- `collection_id` parametresi eklendi, `_fetch_library_entries` guncelendi

---

## ADIM 2: Frontend - Koleksiyon Arayuzu

### 2.1 Tipler ve Servisler

#### `frontend/src/types/api.ts` (Guncellendi)
- `Collection` ve `CollectionListResponse` interface'leri eklendi

#### `frontend/src/services/collections.ts` (Yeni)
- `fetchCollections()` - GET /collections
- `createCollection(name, description?)` - POST /collections
- `deleteCollection(id)` - DELETE /collections/{id}
- `syncCollectionEntries(collectionId, entryIds)` - POST /collections/{id}/entries

#### `frontend/src/services/library.ts` (Guncellendi)
- `LibraryParams.collection_id` eklendi
- `fetchLibrary()` URL'e `collection_id` parametresini ekler

### 2.2 Store

#### `frontend/src/stores/ui-store.ts` (Guncellendi)
- `selectedCollectionId: number | null` state eklendi
- `setSelectedCollectionId(id)` action eklendi

### 2.3 Sidebar Koleksiyon Bolumu

#### `frontend/src/components/Sidebar.tsx` (Guncellendi)
- "Projelerim" bolumu eklendi (Library tab'inda gorulur)
- Koleksiyon badge'leri (tiklanabilir, secili olanin vurgulu gorunumu)
- "Tum Makaleler" secenegi (selectedCollectionId = null)
- Her koleksiyonda entry_count gosterimi
- Hover'da silme ikonu (Trash2)
- "+" butonu ile yeni koleksiyon olusturma Dialog'u
- Koleksiyonlar `react-query` ile cekilir ve cache'lenir

### 2.4 Makaleyi Projeye Ekleme

#### `frontend/src/components/PaperDetail.tsx` (Guncellendi)
- "Projeye Ekle / Yonet" butonu (sadece library makaleleri icin)
- Checkbox listesi ile proje atamasi Dialog'u
- `syncCollectionEntries` ile kaydetme
- Basarili kaydetme sonrasi koleksiyon ve library cache invalidation

### 2.5 Export & ZIP Entegrasyonu

#### `frontend/src/components/LibraryList.tsx` (Guncellendi)
- `selectedCollectionId` query key'e eklendi
- `fetchLibrary()` cagirisina `collection_id` parametresi eklendi
- ZIP indirme URL'sine `collection_id` parametresi eklendi

#### `frontend/src/components/settings.tsx` (Guncellendi)
- Excel, CSV ve ZIP export URL'lerine `collection_id` parametresi eklendi
- `useUIStore` import edilerek `selectedCollectionId` okunuyor

---

## Test Sonuclari

| Test Suite | Sonuc |
|-----------|-------|
| Backend pytest | 17/17 passed |
| Frontend Vitest | 6/6 passed |
| TypeScript build | Success |
| Frontend build | Success |

---

## Dosya Listesi

### Yeni Dosyalar
- `backend/athena/models/collection.py`
- `backend/athena/api/v2/routers/collections.py`
- `backend/migrations/versions/d7f2a3b8c901_add_collections.py`
- `frontend/src/services/collections.ts`

### Degisiklik Yapilan Dosyalar (Backend)
- `backend/athena/models/associations.py` - collection_entries tablosu
- `backend/athena/models/library.py` - collections relationship
- `backend/athena/models/__init__.py` - Collection export
- `backend/athena/main.py` - collections router dahil
- `backend/athena/api/v2/routers/library.py` - collection_id filtresi
- `backend/athena/services/library.py` - collection_id filtresi
- `backend/athena/services/export.py` - collection_id filtresi

### Degisiklik Yapilan Dosyalar (Frontend)
- `frontend/src/types/api.ts` - Collection tipleri
- `frontend/src/stores/ui-store.ts` - selectedCollectionId
- `frontend/src/services/library.ts` - collection_id parametresi
- `frontend/src/components/Sidebar.tsx` - Projelerim bolumu
- `frontend/src/components/PaperDetail.tsx` - Projeye ekle dialog
- `frontend/src/components/LibraryList.tsx` - collection_id filtresi
- `frontend/src/components/settings.tsx` - export collection_id
