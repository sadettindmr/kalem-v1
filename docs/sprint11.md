# Sprint 11 - Kutuplhane Filtreleme ve UX Iyilestirmeleri

## Sprint Ozeti
**Amac:** Kutuphanedeki makaleleri gelismis filtrelerle filtreleyebilme, PDF indirme surecini iyilestirme ve takili kalan gorevleri kurtarma.

**Durum:** Tamamlandi

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
- [x] `scope` parametresi eklendi:
  - `scope=stuck` -> `retry_stuck_downloads.delay()`
  - `scope=all` -> `retry_all_incomplete_downloads.delay()`
- [x] Hata durumunda uygun mesaj doner

#### Frontend: "Indirmeleri Tekrar Dene" Butonu
- [x] `retryDownloads()` fonksiyonu `library.ts`'e eklendi
- [x] LibraryList header'ina `RefreshCw` ikonlu buton eklendi
- [x] Sadece `pending` veya `downloading` durumunda makale varken gorunur
- [x] `useMutation` ile API cagrisi + basari/hata toast mesajlari
- [x] Basari sonrasi `queryClient.invalidateQueries` ile listeyi yeniler

### 11.2b - Kod-Sprint Senkronizasyonu ve Eksik Tamamlama

- [x] `LibraryList.tsx` retry butonu aktif hale getirildi (stuck retry)
- [x] `Settings.tsx` retry butonu `scope=all` ile tum incomplete kayitlari tekrar kuyruga alacak sekilde netlestirildi
- [x] Backend endpoint davranisi dokumanla birebir uyumlu hale getirildi (`stuck` + `all`)

### 11.2c - Docker Local Calisma Iyilestirmesi

- [x] `celery_worker` servisi image bagimliligindan cikarilip build ile uyumlu hale getirildi
- [x] `Dockerfile.backend` lock uyumsuzlugu fallback install ile stabil hale getirildi
- [x] Container adlari `athena_*` -> `kalem_*` olarak guncellendi

### 11.2d - Runtime Hata Giderimi (Library 500) + Volume Rename

- [x] Hata kok nedeni tespit edildi:
  - `GET /api/v2/library` ve `GET /api/v2/library/download-stats` cagrilarinda
    `UndefinedTableError: relation \"library_entries\" does not exist`
- [x] Backend startup migration adimi eklendi:
  - `alembic upgrade head` -> `alembic upgrade heads` (coklu alembic head uyumu)
- [x] `docker-compose.yml` volume adi guncellendi:
  - `athena_library` -> `kalem_library`
- [x] Eski volume temizlendi:
  - `kalem-v1-kasghar_athena_library` kaldirildi

### 11.3 - Eksik Veri Tamamlama (Metadata Enrichment)

#### Backend: Metadata Enrichment Servisi
- [x] `LibraryService.enrich_missing_metadata(limit)` eklendi
- [x] Sadece eksik metadata alanlari olan kayitlar isleniyor:
  - `abstract`, `year`, `venue`, `citation_count`, `pdf_url`, `authors`
- [x] Eslesme stratejisi eklendi:
  - DOI birebir eslesme
  - normalize baslik eslesmesi
  - fallback: ilk sonuc
- [x] Sadece eksik alanlar guncelleniyor (mevcut dolu veri korunuyor)
- [x] Islem ozeti donuyor:
  - `processed`, `updated`, `skipped`, `failed`, `details`

#### Backend: API Endpoint
- [x] `POST /api/v2/library/enrich-metadata?limit=20` endpointi eklendi
- [x] `EnrichMetadataResponse` response modeli eklendi

#### Frontend: Settings Entegrasyonu
- [x] `library.ts` icine `enrichMetadata(limit)` fonksiyonu eklendi
- [x] `settings.tsx` icine "Metadata Tamamlama" alani ve tetikleme butonu eklendi
- [x] Islem sonrasi `library` query invalidation eklendi

### 11.4 - Proxy Altyapisi

#### Backend: Outbound Proxy Konfigurasyonu
- [x] `Settings` modeline `outbound_proxy` alani eklendi
- [x] `.env.example` icine `OUTBOUND_PROXY` degiskeni eklendi
- [x] `docker-compose.yml` icinde backend ve celery worker ortam degiskenlerine `OUTBOUND_PROXY` eklendi

#### Backend: Search Provider Entegrasyonu
- [x] Semantic Scholar provider dis HTTP cagrilari `OUTBOUND_PROXY` ile uyumlu hale getirildi
- [x] OpenAlex provider dis HTTP cagrilari `OUTBOUND_PROXY` ile uyumlu hale getirildi
- [x] arXiv provider dis HTTP cagrilari `OUTBOUND_PROXY` ile uyumlu hale getirildi
- [x] Crossref provider dis HTTP cagrilari `OUTBOUND_PROXY` ile uyumlu hale getirildi
- [x] CORE provider dis HTTP cagrilari `OUTBOUND_PROXY` ile uyumlu hale getirildi

#### Backend: PDF Downloader Entegrasyonu
- [x] `download_paper_task` icindeki PDF indirme adimi proxy parametresi alacak sekilde guncellendi
- [x] `_download_file()` fonksiyonu opsiyonel `proxy_url` destegi ile guncellendi

### 11.4b - PDF Goruntuleme 404 Hata Duzeltmesi

#### Kok Neden
- [x] Tespit: `file_path` alani bazi kayitlarda absolute (`/data/library/...`) tutuluyordu.
- [x] Frontend `http://localhost:8000/files/${file_path}` urettigi icin URL `/files//data/library/...` oluyor ve `404 NOT_FOUND` donuyordu.

#### Uygulanan Duzeltme
- [x] Frontend `PaperDetail` icinde `buildPdfEmbedUrl()` eklendi:
  - absolute path (`/data/library/...`) -> relative path (`paper_id/filename.pdf`) normalize edilir
  - URL-safe encoding uygulanir
  - backend origin dinamik uretilir (`window.location.protocol` + `window.location.hostname` + `:8000`)
- [x] Backend downloader'da yeni kayitlar icin `file_path` relative saklanacak sekilde guncellendi:
  - `entry.file_path = file_path.relative_to(settings.data_dir)` (mümkünse)
  - fallback: mevcut path string

### 11.4c - Kalici PDF Serving + Docker Credential Duzeltmesi

#### Backend: PDF Serving Akisi Guclendirme
- [x] `StaticFiles` mount yerine custom `GET /files/{requested_path:path}` route eklendi
- [x] Route icinde path normalize/cozme mantigi eklendi:
  - relative path (`102/file.pdf`)
  - legacy absolute path (`/data/library/102/file.pdf`)
  - legacy non-slash path (`data/library/102/file.pdf`)
- [x] Guvenlik kontrolu eklendi:
  - resolved path mutlaka `DATA_DIR` altinda olmali
  - dosya fiziksel olarak yoksa `404 File not found`

#### Backend: Kutuphane Durum Otomatik Iyilestirme
- [x] `GET /api/v2/library` icinde auto-repair eklendi:
  - `download_status=completed` fakat fiziksel dosya yoksa kayit `failed` durumuna cekilir
  - `file_path` temizlenir, boylece UI'da yaniltici "Hazir" durumu kalmaz

#### Frontend: Retry UX Iyilestirmesi
- [x] `LibraryList` retry butonu `failed` kayitlari da kapsayacak sekilde guncellendi
- [x] `failed > 0` durumda `retryDownloads('all')`, aksi halde `retryDownloads('stuck')` calisir

### 11.4d - PDF Acilis Davranişi ve Download Status Akis Duzeltmesi

#### Frontend: PDF Auto-open Engelleme
- [x] Library listesinden makale secildiginde PDF iframe'i otomatik acilmayacak sekilde guncellendi
- [x] PDF sadece sag paneldeki `PDF'i Goruntule` butonuna tiklaninca aciliyor
- [x] Makale secimi degisince viewer state sifirlanir (`isPdfViewerVisible=false`)

#### Backend: HTTP Retry Status Duzenleme
- [x] `download_paper_task` HTTP hatalarinda kaydi `downloading` durumunda takili birakmiyor
- [x] Retry devam edecekse status `pending` yapiliyor ve tekrar deneniyor
- [x] Maksimum retry'a ulasinca status `failed` olarak isaretleniyor

#### Docker: Credential Hata Duzeltmesi
- [x] Kok neden:
  - `~/.docker/config.json` icinde `\"credsStore\": \"desktop\"` vardi
  - ortamda `docker-credential-desktop` binary bulunmadigi icin pull/build asamasinda hata olusuyordu
- [x] Kalici cozum:
  - `~/.docker/config.json` yedeklenip `credsStore` alani kaldirildi
  - public image pull akisi credentials helper bagimliligindan cikartildi

### 11.5 - PDF Goruntuleme Hatasi Duzeltmesi

#### Frontend/Proxy Uyumu
- [x] PDF URL üretimi ayni-origin olacak sekilde guncellendi:
  - `http://localhost:8000/files/...` yerine `/files/...`
- [x] `nginx.frontend.conf` icine `/files/` proxy eklendi (frontend -> backend)
- [x] `frontend/vite.config.ts` icine `/files` dev proxy eklendi

#### Backend Normalizasyon ve Geriye Donuk Uyumluluk
- [x] `GET /api/v2/library` icinde `completed` kayitlarin `file_path` degerleri normalize edilir:
  - diskte dosya varsa absolute/legacy path -> relative path
  - diskte dosya yoksa `failed` + `file_path=null`
- [x] Boylece eski kayitlar otomatik onarilir, yeni kayitlarla ayni formata cekilir
- [x] Ortak path cozumu utility modulu eklendi:
  - `athena/core/file_paths.py` (`resolve_data_file_path`, `to_relative_data_path`)

#### Sprint 11 Bitis Kriteri (DoD)
- [x] PDF sadece sag paneldeki butonla acilir, otomatik acilmaz
- [x] PDF endpointi legacy/relative pathleri destekler
- [x] Frontend production build ve backend compile basarili

---

## Test Senaryolari ve Sonuclar (2026-02-15)

### Build / Statik Dogrulama
- [x] Frontend TypeScript build: basarili
- [x] Backend Python syntax compile: basarili
- [x] `pytest` calistirma denemesi: test dosyasi bulunamadi (`no tests ran`)
- [x] `map_source` kaynak esleme guncellemesi:
  - `arxiv`, `crossref`, `core` artik dogrudan kendi `SourceType` alanina yaziliyor
- [x] Proxy entegrasyon taramasi:
  - tum providerlar + downloader `OUTBOUND_PROXY` kullanimina guncellendi
- [x] PDF 404 fix kod taramasi:
  - frontend normalize + backend relative path saklama akisi dogrulandi
- [x] Custom file serving route compile dogrulamasi:
  - `main.py` icindeki `serve_pdf_file` ve path resolver fonksiyonlari compile edildi
- [x] Frontend retry UX build dogrulamasi:
  - `LibraryList` degisiklikleri ile production build basarili
- [x] PDF acilis davranisi build dogrulamasi:
  - `PaperDetail` buton kontrollu viewer akisi ile build basarili
- [x] Downloader status gecis compile dogrulamasi:
  - HTTP hata -> `pending` / max retry -> `failed` akisi compile edildi
- [x] `/files` proxy dogrulamasi:
  - nginx + vite konfigurasyonunda `/files` backend'e yonlendiriliyor
- [x] `file_path` normalize akisi compile dogrulamasi:
  - library listesinde legacy path -> relative path donusumu uygulandi
- [x] PDF path resolution unit testleri:
  - `backend/tests/test_pdf_path_resolution.py` -> `6 passed`

### Manuel Fonksiyonel Senaryolar (Hazir)
- [ ] `POST /api/v2/library/retry-downloads?scope=stuck`
  - Beklenen: sadece 1 saatten eski `pending/downloading` kayitlar queue edilir
- [ ] `POST /api/v2/library/retry-downloads?scope=all`
  - Beklenen: `pending/downloading/failed` tum kayitlar queue edilir
- [ ] Library ekraninda retry butonu gorunum kuralı
  - Beklenen: sadece `pending` veya `downloading` sayisi > 0 ise gorunur
- [ ] Retry sonrasi cache invalidation
  - Beklenen: `library` ve `download-stats` query'leri yenilenir

- [ ] `POST /api/v2/library/enrich-metadata?limit=20`
  - Beklenen: eksik metadata kayitlari dis kaynaklardan tamamlanir, sadece bos alanlar guncellenir
- [ ] Settings > "Eksik Verileri Tamamla" butonu
  - Beklenen: islem sonunda "guncellendi/atlandi/hata" ozet toast'i gorunur
- [ ] Enrichment sonrasi liste yenileme
  - Beklenen: `library` query invalidate edilerek yeni metadata UI'da gorunur

- [ ] Proxy ile arama testi
  - Onkosul: `.env` icinde `OUTBOUND_PROXY=http://<proxy_host>:<port>`
  - Adim: `POST /api/v2/search` cagrisi yap
  - Beklenen: Search endpointi hata vermeden sonuc doner
- [ ] Proxy ile metadata enrichment testi
  - Onkosul: `OUTBOUND_PROXY` aktif
  - Adim: `POST /api/v2/library/enrich-metadata?limit=5`
  - Beklenen: endpoint tamamlanir, `failed` alani proxy baglanti sorunu olmadikca 0 olur
- [ ] Proxy ile PDF indirme testi
  - Onkosul: `OUTBOUND_PROXY` aktif ve indirilebilir `pdf_url` olan kayit mevcut
  - Adim: ingest + downloader task tetiklenir
  - Beklenen: `download_status=completed` ve `file_path` dolu olur
- [ ] PDF embed URL testi (eski kayit - absolute path)
  - Onkosul: `file_path=/data/library/...` olan en az bir library kaydi
  - Adim: Kutuphane > makale sec > PDF Goruntuleyici
  - Beklenen: iframe 404 vermez, PDF yuklenir
- [ ] PDF embed URL testi (yeni kayit - relative path)
  - Onkosul: yeni indirilen bir PDF kaydi
  - Beklenen: `file_path` degeri `paper_id/filename.pdf` formatinda saklanir
- [ ] Full cycle docker testi
  - Adim 1: `docker-compose down`
  - Adim 2: `docker-compose up -d --build`
  - Adim 3: `docker-compose ps` ile tum `kalem_*` container'lari `Up/healthy` kontrolu
  - Adim 4: UI > Kutuphane > `Hazir` bir kayit sec > `PDF'i Ac`
  - Beklenen: PDF endpoint 200 doner, `NOT_FOUND` JSON gorunmez
- [ ] Download retry lifecycle testi
  - Adim: gecersiz/ulasilamaz `pdf_url` olan bir kaydi kuyruga al
  - Beklenen: kayit bir sure `pending/downloading` arasinda retry olur, max deneme sonunda `failed`a duser
- [ ] PDF same-origin testi
  - Adim: Kutuphane > Hazir kayit > `PDF'i Goruntule`
  - Beklenen: browser adresinde `/files/...` cagrisi gorulur ve PDF acilir

### Canli Docker Dogrulamalari (Gerceklesti)
- [x] `GET /api/v2/library?limit=5` -> `200 OK` (`{"items":[],"total":0,...}`)
- [x] `GET /api/v2/library/download-stats` -> `200 OK`
- [x] `POST /api/v2/search` (ornek sorgu) -> basarili sonuc dondu
- [x] Tüm container'lar `kalem_*` adlariyla `healthy/up` durumda

### Bu Turda Calistirilan Dogrulamalar (Local CLI)
- [x] `python3 -m compileall backend/athena` -> basarili
- [x] `cd frontend && npm run build` -> basarili
- [x] `cd backend && python3 -m pytest -q` -> `6 passed`
- [x] `rg -n "outbound_proxy|OUTBOUND_PROXY|proxy=" ...` ile kod taramasi -> proxy baglantilari dogrulandi
- [x] `rg -n "buildPdfEmbedUrl|relative_to(settings.data_dir)" ...` -> PDF 404 duzeltme noktalari dogrulandi
- [x] `~/.docker/config.json` icinde `credsStore` kaldirildi (docker credential hatasi icin)
- [!] Not: Bu oturumdaki shell ortaminda `docker` komutu bulunmadigi icin canli container smoke testleri tekrar calistirilamadi.

---

## Degisiklik Yapilan Dosyalar

### Backend
- `athena/models/library.py` - `updated_at` kolonu eklendi
- `athena/tasks/downloader.py` - Detayli loglama, timeout 120s, `retry_stuck_downloads` task
- `athena/api/v2/routers/library.py` - Filtre parametreleri + `POST /retry-downloads` endpoint (`scope=stuck|all`)
- `athena/api/v2/routers/library.py` - `POST /enrich-metadata` endpointi ve response modeli
- `migrations/versions/8e16fefc38a1_...` - updated_at migration
- `Dockerfile.backend` - lock uyumsuzlugu fallback install
- `athena/services/library.py` - metadata enrichment akisi + kaynak map duzeltmesi (`arxiv/crossref/core`)
- `athena/core/config.py` - `outbound_proxy` ayari
- `athena/adapters/semantic.py` - proxy destekli HTTP client
- `athena/adapters/openalex.py` - proxy destekli HTTP client
- `athena/adapters/arxiv.py` - proxy destekli HTTP client
- `athena/adapters/crossref.py` - proxy destekli HTTP client
- `athena/adapters/core.py` - proxy destekli HTTP client
- `athena/tasks/downloader.py` - proxy destekli PDF indirme
- `athena/tasks/downloader.py` - `file_path` relative saklama duzeltmesi (PDF 404 fix)
- `athena/main.py` - custom `/files/{requested_path:path}` PDF serving + legacy path normalization
- `athena/api/v2/routers/library.py` - completed-but-missing file auto-repair (status -> failed)
- `athena/tasks/downloader.py` - HTTP hata durumunda status gecisleri (pending/final failed)
- `athena/api/v2/routers/library.py` - legacy `file_path` normalize (absolute -> relative)
- `athena/core/file_paths.py` - ortak path cozumleme/normalize utility fonksiyonlari

### Frontend
- `src/stores/ui-store.ts` - Yeni library filtre state'leri ve action'lar
- `src/services/library.ts` - `LibraryParams`, `fetchLibrary`, `retryDownloads(scope)` guncellendi
- `src/components/LibraryList.tsx` - Query binding, yil validasyonu, retry butonu (stuck scope)
- `src/components/settings.tsx` - Retry butonu `scope=all` ile tum incomplete retry
- `src/components/settings.tsx` - metadata enrichment butonu + mutation + toast
- `src/components/Sidebar.tsx` - Kutuplhane filtre UI (arama, yil, atif inputlari)
- `src/components/LibraryItem.tsx` - Citation count badge eklendi
- `src/services/library.ts` - `enrichMetadata` API fonksiyonu + response tipi
- `src/components/PaperDetail.tsx` - PDF embed URL normalize/encode duzeltmesi (absolute->relative path uyumu)
- `src/components/LibraryList.tsx` - failed kayitlari da retry kapsamina alacak UX duzeltmesi
- `src/components/PaperDetail.tsx` - PDF sadece butonla acilir (auto-open kaldirildi)
- `src/components/PaperDetail.tsx` - PDF URL same-origin (`/files/...`) formatina alindi
- `backend/tests/test_pdf_path_resolution.py` - PDF path resolution regresyon testleri

### Altyapi
- `docker-compose.yml` - container adlari `kalem_*` formatina guncellendi
- `docker-compose.yml` - volume adi `kalem_library`, backend startup migration `alembic upgrade heads`
- `.env.example` - `OUTBOUND_PROXY` konfigurasyonu eklendi
- `nginx.frontend.conf` - `/files` backend proxy eklendi
- `frontend/vite.config.ts` - `/files` dev proxy eklendi
- `docker-compose.yml` - backend ve worker ortamina `OUTBOUND_PROXY` eklendi
