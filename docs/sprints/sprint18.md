# Sprint 18 - Kütüphane Yönetimi: Silme, Projeden Çıkarma ve Etiket Düzenleme

**Date:** 2026-03-30
**Status:** ✅ Completed
**Version:** v1.3.0
**Branch:** `feature/sprint-18-library-management`

---

## Goal

Kullanıcının kütüphanesindeki makaleleri silebilmesini, projelerinden (koleksiyonlardan) çıkarabilmesini ve makale etiketlerini güncelleyebilmesini sağlamak.

---

## 18.1 - Kütüphaneden Silme (Delete from Library)

### Backend

| Component | Change | Status |
|-----------|--------|--------|
| `LibraryService.delete_library_entry()` | Entry silme + PDF dosya temizliği | ✅ |
| `DELETE /api/v2/library/{entry_id}` | Silme endpoint'i | ✅ |
| PDF cleanup | `resolve_data_file_path` ile dosya bulup `Path.unlink()` | ✅ |
| CASCADE | `collection_entries` ve `library_tags` otomatik silinir | ✅ |

### Frontend

| Component | Change | Status |
|-----------|--------|--------|
| `library.ts` | `deleteLibraryEntry(id)` API fonksiyonu | ✅ |
| `LibraryItem.tsx` | Kırmızı "Sil" butonu (her zaman görünür, outline stil) | ✅ |
| `LibraryItem.tsx` | Onay dialog'u (Dialog + destructive button) | ✅ |
| `LibraryList.tsx` | `deleteMutation` + toast + invalidateQueries | ✅ |

### Silme Akışı

```
Kullanıcı "Sil" butonuna tıklar
  → Onay dialog'u açılır ("Bu işlem geri alınamaz")
  → "Sil" onaylanır
  → DELETE /api/v2/library/{id}
  → Backend: PDF dosyasını diskten siler
  → Backend: LibraryEntry kaydını siler (CASCADE ile M2M ilişkiler de gider)
  → Frontend: toast.success + queryClient.invalidateQueries
```

---

## 18.2 - Projeden Çıkarma (Remove from Collection)

### Backend

| Component | Change | Status |
|-----------|--------|--------|
| `DELETE /api/v2/collections/{collection_id}/entries/{entry_id}` | Yeni endpoint | ✅ |
| Koleksiyon ilişkisi kaldırma | `collection_entries` M2M kaydı silinir | ✅ |
| Kütüphane korunur | LibraryEntry silinmez | ✅ |

### Frontend

| Component | Change | Status |
|-----------|--------|--------|
| `collections.ts` | `removeEntryFromCollection(collectionId, entryId)` API fonksiyonu | ✅ |
| `LibraryItem.tsx` | Turuncu "Çıkar" butonu (sadece koleksiyon seçiliyken görünür) | ✅ |
| `LibraryList.tsx` | `removeFromCollectionMutation` + `selectedCollectionId` kontrolü | ✅ |

### Çıkarma Akışı

```
Sidebar'da bir proje/koleksiyon seçiliyken:
  → Her makale kartında turuncu "Çıkar" butonu görünür
  → Tıklanınca DELETE /api/v2/collections/{cid}/entries/{eid}
  → Makale o proje listesinden kaybolur
  → "Tüm Makaleler" (Kütüphanem) bölümünde durmaya devam eder
```

---

## 18.3 - Etiketleri Düzenleme (Edit Tags)

### Backend

| Component | Change | Status |
|-----------|--------|--------|
| `LibraryService.update_tags()` | Etiketleri overwrite eden servis metodu | ✅ |
| `PUT /api/v2/library/{entry_id}/tags` | Etiket güncelleme endpoint'i | ✅ |
| Tag find-or-create | Yeni etiketler otomatik oluşturulur | ✅ |
| Request body | `{"tags": ["etiket1", "etiket2"]}` | ✅ |

### Frontend

| Component | Change | Status |
|-----------|--------|--------|
| `library.ts` | `updateLibraryTags(entryId, tags)` API fonksiyonu | ✅ |
| `PaperDetail.tsx` | Etiket bölümüne "Düzenle" (Pencil) ikonu | ✅ |
| `PaperDetail.tsx` | Inline tag editor (virgülle ayrılmış Input) | ✅ |
| `PaperDetail.tsx` | Kaydet/Vazgeç butonları + Enter/Escape kısayolları | ✅ |

### Düzenleme Akışı

```
Detay panelinde etiketlerin yanındaki kalem ikonuna tıkla
  → Etiketler virgülle ayrılmış Input alanına dönüşür
  → Düzenle ve "Kaydet" veya Enter tuşuna bas
  → PUT /api/v2/library/{id}/tags
  → Backend: Mevcut etiketler temizlenir, yeni liste atanır
  → Frontend: toast.success + invalidateQueries
  → Sidebar filtrelerde yeni etiketlerle aranabilir
```

---

## Değişen Dosyalar

### Backend
- `backend/athena/services/library.py` - `delete_library_entry()`, `update_tags()` metotları
- `backend/athena/api/v2/routers/library.py` - `DELETE /{entry_id}`, `PUT /{entry_id}/tags` endpoint'leri
- `backend/athena/api/v2/routers/collections.py` - `DELETE /{collection_id}/entries/{entry_id}` endpoint'i

### Frontend
- `frontend/src/services/library.ts` - `deleteLibraryEntry()`, `updateLibraryTags()`
- `frontend/src/services/collections.ts` - `removeEntryFromCollection()`
- `frontend/src/components/LibraryItem.tsx` - Sil butonu + onay dialog + Çıkar butonu
- `frontend/src/components/LibraryList.tsx` - Delete/remove mutation'ları
- `frontend/src/components/PaperDetail.tsx` - Tag edit UI

---

## Test Sonuçları

- TypeScript: ✅ `tsc --noEmit` temiz
- Vite Build: ✅ Başarılı (2.67s)
- Python Syntax: ✅ 3/3 dosya OK

## DoD (Definition of Done)

| Kriter | Durum |
|--------|-------|
| Makale silindiğinde listeden kaybolur | ✅ |
| PDF dosyası diskten silinir | ✅ |
| Projeden çıkarılan makale "Tüm Makaleler"de kalır | ✅ |
| Etiketler güncellendiğinde sidebar filtrelerinde aranabilir | ✅ |
| Onay dialog'u ile yanlışlıkla silme önlenir | ✅ |
