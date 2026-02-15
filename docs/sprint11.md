# Sprint 11 - Kutuplhane Filtreleme ve UX Iyilestirmeleri

## Sprint Ozeti
**Amac:** Kutuphanedeki makaleleri gelismis filtrelerle filtreleyebilme, PDF indirme surecini iyilestirme ve takili kalan gorevleri kurtarma.

**Durum:** Devam Ediyor

---

## Tamamlanan Prompt'lar

### 11.1 - Kutuplhane Filtreleme

#### Backend: GET /api/v2/library Filtre Parametreleri
- [x] `min_citations` query param eklendi (ge=0)
- [x] `year_start` query param eklendi (ge=1900, le=2100)
- [x] `year_end` query param eklendi (ge=1900, le=2100)
- [x] `search` query param eklendi (baslik, yazar, etiket araması)
- [x] `Paper` tablosuyla `join` eklendi (filtreler icin)
- [x] `Paper.citation_count >= min_citations` filtresi
- [x] `Paper.year >= year_start` ve `Paper.year <= year_end` filtreleri
- [x] Keyword search: `Paper.title LIKE` + Author subquery + Tag subquery (OR mantigi)
- [x] `count_query` filtreleme sonrasi toplam sayiyi dogru hesapliyor

#### Frontend: Store Guncelleme
- [x] `libraryFilterMinCitations: number | null` state eklendi
- [x] `libraryFilterYearStart: number | null` state eklendi
- [x] `libraryFilterYearEnd: number | null` state eklendi
- [x] `libraryFilterSearch: string` state eklendi
- [x] Setter action'lar eklendi

#### Frontend: Service Guncelleme
- [x] `LibraryParams` interface'ine `min_citations`, `year_start`, `year_end`, `search` eklendi
- [x] `fetchLibrary` fonksiyonu yeni parametreleri URL'e ekliyor

#### Frontend: LibraryList Binding
- [x] `useQuery` queryKey'e tum filtreler eklendi (7 parametre)
- [x] `fetchLibrary` cagirisina filtre parametreleri eklendi
- [x] Yil filtreleri sadece >= 1900 ise gonderiliyor (ara degerler 422 hatasi onlendi)

#### Frontend: Sidebar Filtre UI
- [x] Anahtar Kelime Arama inputu (baslik, yazar, etiket)
- [x] Yil Araligi inputlari (baslangic - bitis)
- [x] Min. Atif inputu
- [x] Calendar ve BookOpen ikonlari eklendi

### 11.1b - Bug Fix ve UX Iyilestirmeleri
- [x] Yil filtresi validation hatasi duzeltildi
  - Sorun: Yil inputuna yazarken ara degerler (202, 20, 2) backend `ge=1900` validasyonuna takiliyordu → 422
  - Cozum: `year_start` ve `year_end` sadece >= 1900 oldugunda API'ye gonderiliyor
- [x] Kutuplhane makale kartlarina citation sayisi eklendi
  - `LibraryItem.tsx`'e `Quote` ikonu ile `paper.citation_count` badge'i eklendi
  - Sadece citation_count > 0 olan makalelerde gosteriliyor

### 11.2 - PDF Indirme Iyilestirmesi ve Stuck Task Recovery

#### Backend: LibraryEntry Model Guncelleme
- [x] `updated_at` kolonu eklendi (`DateTime(timezone=True)`, `server_default=func.now()`, `onupdate=func.now()`)
- [x] Alembic migration olusturuldu ve uygulandi (`8e16fefc38a1_add_updated_at_to_library_entries`)

#### Backend: download_paper_task Iyilestirmesi
- [x] Detayli loglama eklendi:
  - `[Download]` prefix ile tutarli log formati
  - Retry bilgisi: `(attempt 2/6)` seklinde
  - Paper detaylari: id, title, doi
  - PDF URL bilgisi (ilk 120 karakter)
  - Dosya boyutu kontrolu ve loglama
  - Hata tipi (`error_type`) loglama
- [x] Timeout suresi arttirildi: `60s → 120s` (`DOWNLOAD_TIMEOUT` sabiti)
- [x] Dosya boyutu kontrolu: < 1KB ise uyari logu

#### Backend: retry_stuck_downloads Task
- [x] Yeni Celery task: `retry_stuck_downloads`
- [x] Kriterleri:
  - `download_status = 'pending'` veya `'downloading'`
  - `updated_at` degeri 1 saatten eski
- [x] Bulunan kayitlarin durumunu `pending`'e cevirir
- [x] `download_paper_task.delay()` ile tekrar kuyruga ekler
- [x] Detayli loglama (`[RetryStuck]` prefix)

#### Backend: POST /api/v2/library/retry-downloads Endpoint
- [x] `RetryDownloadsResponse` schema tanimlandi
- [x] `retry_stuck_downloads.delay()` ile Celery task'i tetikler
- [x] Hata durumunda uygun mesaj doner

#### Frontend: "Indirmeleri Tekrar Dene" Butonu
- [x] `retryDownloads()` fonksiyonu `library.ts`'e eklendi
- [x] LibraryList header'ina `RefreshCw` ikonlu buton eklendi
- [x] Sadece `pending` veya `downloading` durumunda makale varken gorunur
- [x] `useMutation` ile API cagrisi + basari/hata toast mesajlari
- [x] Basari sonrasi `queryClient.invalidateQueries` ile listeyi yeniler

---

## Degisiklik Yapilan Dosyalar

### Backend
- `athena/models/library.py` - `updated_at` kolonu eklendi
- `athena/tasks/downloader.py` - Detayli loglama, timeout 120s, `retry_stuck_downloads` task
- `athena/api/v2/routers/library.py` - Filtre parametreleri + `POST /retry-downloads` endpoint
- `migrations/versions/8e16fefc38a1_...` - updated_at migration

### Frontend
- `src/stores/ui-store.ts` - Yeni library filtre state'leri ve action'lar
- `src/services/library.ts` - `LibraryParams`, `fetchLibrary`, `retryDownloads` guncellendi
- `src/components/LibraryList.tsx` - Query binding, yil validasyonu, retry butonu
- `src/components/Sidebar.tsx` - Kutuplhane filtre UI (arama, yil, atif inputlari)
- `src/components/LibraryItem.tsx` - Citation count badge eklendi
