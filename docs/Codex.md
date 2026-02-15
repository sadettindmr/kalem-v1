# Codex.md

## Proje Kimliği
- Yeni ad: **Kalem v1.0.0 - Kasghar**
- Kod içinde kullanıcıya görünen proje adı standardı: **Kalem - Kasghar**
- Durum tarihi: **2026-02-15**

## Yapılan İsim Değişikliği Güncellemeleri

### Backend
- `backend/athena/main.py`
  - FastAPI başlığı: `Project Athena` -> `Kalem - Kasghar`
  - Root mesajı: `Project Athena API` -> `Kalem - Kasghar API`
  - Athena hata açıklaması -> Kalem - Kasghar açıklaması
- `backend/athena/adapters/openalex.py`
  - User-Agent: `Athena/2.0 ...` -> `Kalem-Kasghar/1.0.0 ...`
- `backend/athena/adapters/crossref.py`
  - User-Agent: `Athena/2.0 ...` -> `Kalem-Kasghar/1.0.0 ...`
- `backend/athena/core/exceptions.py`
  - Dosya ve sınıf docstring metinleri Kalem - Kasghar olarak güncellendi
- `backend/athena/core/config.py`
  - Varsayılan `openalex_email` ve `unpaywall_email` -> `kalem.kasghar@example.com`
- `backend/athena/services/export.py`
  - Export dosya adları -> `kalem_kasghar_library_export.csv/.xlsx`
- `backend/pyproject.toml`
  - Paket açıklaması -> `Kalem v1.0.0 - Kasghar - Modular Monolith Backend`

### Frontend
- `frontend/src/layouts/DashboardLayout.tsx`
  - Header başlığı: `Project Athena` -> `Kalem - Kasghar`
  - Logo harfi: `A` -> `K`

### Altyapı / Konfigürasyon
- `.env.example`
  - Başlık: `Project Athena - Environment Configuration` -> `Kalem v1.0.0 - Kasghar - Environment Configuration`
- `docker-compose.yml`
  - Varsayılan e-posta fallback değerleri -> `kalem.kasghar@example.com`

## Not (Bilerek Korunan Teknik Kimlikler)
Aşağıdaki teknik kimlikler çalışır yapıyı bozmamak için korunmuştur:
- Python paket yolu: `athena.*`
- Uvicorn modül hedefi: `athena.main:app`
- Celery app yolu: `athena.core.celery_app`
- DB kullanıcı adları (`athena`)

Bu alanların da yeniden adlandırılması istenirse ayrı bir migration/refactor sprinti ile yapılmalıdır.

## Proje Yapısı (Güncel)

### Kök Dizin
- `backend/` - FastAPI + SQLAlchemy + Celery backend
- `frontend/` - React + Vite + Zustand + React Query frontend
- `docs/` - Sprint ve teknik dokümantasyonlar
- `docker-compose.yml` - Servis orkestrasyonu
- `Dockerfile.backend` - Backend imajı
- `Dockerfile.frontend` - Frontend imajı
- `nginx.frontend.conf` - Frontend nginx + `/api` proxy
- `CLAUDE.md`, `GEMINI.md` - referans dokümanları

### Backend Yapısı
- `backend/athena/main.py` - FastAPI app, middleware, router mount, exception handlers
- `backend/athena/api/v2/routers/`
  - `search.py` - `/api/v2/search`
  - `library.py` - kütüphane, ingest, export, retry endpointleri
  - `system.py` - health/reset vb. sistem endpointleri
- `backend/athena/core/`
  - `config.py` - settings
  - `database.py` - async DB bağlantısı
  - `celery_app.py` - celery tanımı
  - `exceptions.py` - standart hata tipleri
  - `logging.py`, `middleware.py` - request/log altyapısı
- `backend/athena/models/`
  - `paper.py`, `author.py`, `library.py`, `tag.py`, `associations.py`
- `backend/athena/schemas/`
  - `search.py`, `library.py`, `error.py`
- `backend/athena/services/`
  - `search.py`, `library.py`, `export.py`
- `backend/athena/adapters/`
  - `semantic.py`, `openalex.py`, `arxiv.py`, `crossref.py`, `core.py`
- `backend/athena/tasks/`
  - `downloader.py` - PDF indirme/retry Celery taskları
- `backend/migrations/` - Alembic migration dosyaları

### Frontend Yapısı
- `frontend/src/App.tsx` - route tanımları
- `frontend/src/layouts/DashboardLayout.tsx` - 3 sütunlu ana layout
- `frontend/src/components/`
  - `SearchForm.tsx`, `PaperList.tsx`, `PaperCard.tsx`, `PaperDetail.tsx`
  - `LibraryList.tsx`, `LibraryItem.tsx`, `Sidebar.tsx`, `settings.tsx`
  - `ui/` - shadcn bileşenleri
- `frontend/src/services/`
  - `search.ts`, `library.ts` - API çağrıları
- `frontend/src/stores/ui-store.ts` - Zustand UI state
- `frontend/src/lib/api.ts` - axios client/interceptor
- `frontend/src/types/api.ts` - tipler

### Docker Servisleri
- `postgres_db` - PostgreSQL
- `redis_cache` - Redis
- `rabbitmq_broker` - RabbitMQ
- `backend` - FastAPI
- `celery_worker` - Celery worker
- `frontend` - Nginx üstünde React build

### Container Adlari (Guncel)
- `kalem_postgres`
- `kalem_redis`
- `kalem_rabbitmq`
- `kalem_backend`
- `kalem_celery_worker`
- `kalem_frontend`

## Geliştirme Hazırlık Durumu
- İsim değişikliği kullanıcıya görünen katmanlarda uygulandı.
- Mevcut mimari ve çalışma yolları korunmuştur.
- Teknik paket/import kimlikleri kırılmadan bırakılmıştır.

## 2026-02-15 Docker Local Calistirma Guncellemesi
- `docker-compose.yml` icinde `celery_worker` servisi image yerine build'e alindi.
- `Dockerfile.backend` icine lock uyumsuzlugu durumunda `pyproject` ile fallback install eklendi.
- Container adlari `athena_*` -> `kalem_*` olarak guncellendi.
- Shared volume adi `athena_library` -> `kalem_library` olarak guncellendi.
- Eski volume (`kalem-v1-kasghar_athena_library`) kaldirildi.
- Backend baslangicina migration adimi eklendi: `alembic upgrade heads`.
  - Cozulen hata: Library ve download-stats endpointlerinde `UndefinedTableError (library_entries does not exist)` kaynakli
    \"Beklenmeyen bir hata oluştu\" mesaji.

## 2026-02-15 Sprint 11.3 - Metadata Enrichment
- `backend/athena/services/library.py`
  - `enrich_missing_metadata(limit)` eklendi.
  - Eksik metadata alanlari (`abstract/year/venue/citation_count/pdf_url/authors`) dis kaynaklardan tamamlanacak sekilde servis akisi yazildi.
  - Eslesme stratejisi: DOI > normalize baslik > ilk sonuc.
  - Sadece eksik alanlar guncelleniyor, mevcut dolu alanlar korunuyor.
  - `map_source` fonksiyonu `arxiv`, `crossref`, `core` icin dogru enum eslemesi yapacak sekilde guncellendi.
- `backend/athena/api/v2/routers/library.py`
  - `POST /api/v2/library/enrich-metadata` endpointi eklendi.
  - `EnrichMetadataResponse` modeli eklendi.
- `frontend/src/services/library.ts`
  - `enrichMetadata(limit)` fonksiyonu ve response tipi eklendi.
- `frontend/src/components/settings.tsx`
  - "Metadata Tamamlama" bolumu ve "Eksik Verileri Tamamla" butonu eklendi.
  - Islem sonrasi `library` query invalidate edilerek ekranin guncel veri gostermesi saglandi.

## 2026-02-15 Sprint 11.4 - Proxy Altyapisi
- `backend/athena/core/config.py`
  - `outbound_proxy` ayari eklendi (env: `OUTBOUND_PROXY`).
- `backend/athena/adapters/semantic.py`
  - Semantic Scholar HTTP client, `OUTBOUND_PROXY` aktifse proxy uzerinden cikacak sekilde guncellendi.
- `backend/athena/adapters/openalex.py`
  - OpenAlex HTTP client, `OUTBOUND_PROXY` aktifse proxy uzerinden cikacak sekilde guncellendi.
- `backend/athena/adapters/arxiv.py`
  - arXiv provider'a settings baglandi ve HTTP client proxy destekli hale getirildi.
- `backend/athena/adapters/crossref.py`
  - Crossref HTTP client proxy destekli hale getirildi.
- `backend/athena/adapters/core.py`
  - CORE HTTP client proxy destekli hale getirildi.
- `backend/athena/tasks/downloader.py`
  - PDF indirme adimi, opsiyonel proxy URL alacak sekilde guncellendi.
- `.env.example`
  - `OUTBOUND_PROXY` degiskeni eklendi.
- `docker-compose.yml`
  - backend ve celery worker servislerine `OUTBOUND_PROXY` ortam degiskeni eklendi.

## 2026-02-15 Ek Duzeltme - PDF Goruntuleme 404
- Kok neden:
  - Bazi library kayitlarinda `file_path` absolute (`/data/library/...`) formatindaydi.
  - Frontend URL üretimi `/files/${file_path}` oldugu icin `/files//data/library/...` URI'si olusup 404 donuyordu.
- `frontend/src/components/PaperDetail.tsx`
  - `buildPdfEmbedUrl()` eklendi.
  - Absolute path'leri relative path'e normalize ediyor.
  - URL segmentlerini encode ediyor.
  - Backend origin'i dinamik üretiyor (`<protocol>//<hostname>:8000`).
- `backend/athena/tasks/downloader.py`
  - Yeni indirilen kayitlarda `file_path` relative saklanacak sekilde guncellendi
    (`paper_id/filename.pdf`).
  - Bu sayede `/files` static mount'u ile path uyumlulugu kalici hale getirildi.

## 2026-02-15 Ek Duzeltme - PDF Serving Dayaniklilik + Docker Credential
- `backend/athena/main.py`
  - `StaticFiles` mount'u yerine custom `GET /files/{requested_path:path}` route eklendi.
  - Legacy path formatlarini normalize ederek (absolute/relative) fiziksel dosyayi bulma mantigi eklendi.
  - Dosya path'i `DATA_DIR` disina cikamaz (guvenlik kontrolu).
- `backend/athena/api/v2/routers/library.py`
  - `GET /api/v2/library` donusunde `completed` gorunen ancak diskte dosyasi olmayan kayitlar
    otomatik `failed` durumuna cekiliyor.
  - Bu sayede UI'da "Hazir" gorunup PDF 404 veren yaniltici kayitlar temizleniyor.
- `frontend/src/components/LibraryList.tsx`
  - Retry butonu `failed` kayitlari da kapsayacak sekilde guncellendi.
  - `failed > 0` iken `scope=all` ile retry tetikleniyor.
- `frontend/src/components/PaperDetail.tsx`
  - Makale seciminde PDF otomatik acilmasi kaldirildi.
  - PDF goruntuleme sadece `PDF'i Goruntule` butonuyla tetikleniyor.
- `backend/athena/tasks/downloader.py`
  - HTTP hatalarinda kayit `downloading` durumunda takili kalmaz.
  - Retry devam edecekse `pending`, max deneme asiminda `failed` durumuna gecis saglandi.
- `frontend/src/components/PaperDetail.tsx`
  - PDF URL olusturma ayni-origin `/files/...` formatina cekildi (hardcoded `:8000` kaldirildi).
- `nginx.frontend.conf`
  - `/files/` path'i backend'e proxylenir hale getirildi.
- `frontend/vite.config.ts`
  - local development icin `/files` proxy eklendi.
- `backend/athena/api/v2/routers/library.py`
  - `completed` kayitlarin legacy absolute `file_path` degerleri listede otomatik relative formata normalize edilir.
  - dosya bulunamazsa kayit `failed` + `file_path=null` yapilarak PDF 404 akisi temizlenir.
- `backend/athena/core/file_paths.py`
  - PDF/file path normalize-cozumleme mantigi ortak utility modüle tasindi.
- Docker credential hatasi:
  - Kok neden: `~/.docker/config.json` icindeki `credsStore=desktop` ve eksik `docker-credential-desktop` binary.
  - Uygulanan duzeltme: `credsStore` kaldirildi, config yedeklendi.

## 2026-02-15 Sprint 12.1 - Gelismis Excel Export (Bibliyografik Veri)
- `backend/athena/services/export.py`
  - Export kolonlari akademik formatta yeniden yazildi (14 kolon).
  - `format_apa(...)` ve `format_ieee(...)` helper fonksiyonlari eklendi.
  - Makale turu siniflandirmasi (`Dergi Makalesi/Bildiri/Diğer`) eklendi.
  - DOI/Link secimi (`doi -> doi.org`, yoksa `pdf_url`) eklendi.
  - `Citation as of dd.mm.yyyy` dinamik kolon basligi eklendi.
  - `Downloaded` alani `EVET/HAYIR` formatina cekildi.
  - `Kod/Veri Erişilebilirliği` heuristigi eklendi (`github/gitlab/zenodo`).
  - XLSX export icin auto-width eklendi.
- `docs/sprint12.md`
  - Sprint 12.1 kapsam, test senaryolari ve sonuc kaydi olusturuldu.

## 2026-02-15 Sprint 12.2 - Toplu PDF Indirme (ZIP Archive)
- `backend/athena/api/v2/routers/library.py`
  - `GET /api/v2/library/download-zip` endpointi eklendi.
  - Listeleme endpointi ile ortak filtre uygulayici (`_apply_library_filters`) eklendi.
  - Filtrelenmis kayitlardan yalnizca `completed + mevcut file_path` dosyalari ZIP'e ekleniyor.
  - ZIP dosya adlari `entryid_filename.pdf` formatinda uretiliyor.
  - Cikti `application/zip` ve `kalem_library_archive_YYYYMMDD.zip` dosya adiyla donuyor.
- `frontend/src/components/LibraryList.tsx`
  - Header'a `PDF Arsivi Indir (.zip)` butonu eklendi.
  - Mevcut kutuphane filtreleri query string'e cevrilip `download-zip` endpointine yonlendiriliyor.
- `frontend/src/components/settings.tsx`
  - Gorunurluk problemi icin ayni ZIP indirme aksiyonu Ayarlar > Kutuphanemi Indir bolumune de eklendi.
- `docs/sprint12.md`
  - Sprint 12.2 kapsam ve test senaryolari eklendi.

## 2026-02-15 Sprint 13.1 - Full-Text Search (Relevance Altyapisi)
- `backend/athena/core/__init__.py`
  - Alembic gibi lightweight import akislari icin logging/middleware importlari kosullu hale getirildi.
  - Cozulen hata: `alembic upgrade heads` calisirken `ModuleNotFoundError: loguru`.
- `backend/athena/models/paper.py`
  - `search_vector` (`TSVECTOR`) alanı eklendi.
  - `ix_papers_search_vector` GIN index model seviyesinde tanimlandi.
- `backend/migrations/versions/f13a1c9d0b77_add_search_vector_fts.py`
  - `papers.search_vector` kolonu ve GIN index eklendi.
  - `title + abstract + authors.name` birlesiminden `search_vector` olusturan trigger/function yapisi eklendi.
  - `papers`, `paper_authors`, `authors` degisimlerinde vector guncellemesi saglandi.
  - mevcut kayitlar icin backfill SQL eklendi.
- `backend/athena/services/library.py`
  - `get_library_entries(...)` metodu eklendi.
  - `websearch_to_tsquery` + `@@` + `ts_rank` ile relevance siralama eklendi.
  - `ilike` tabanli fallback (title/abstract/author/tag) `OR` kosulu ile korundu.
- `backend/athena/api/v2/routers/library.py`
  - `GET /api/v2/library` endpointi service tabanli FTS aramaya gecirildi.
  - ZIP endpoint filter helper'i de FTS+fallback ile uyumlu hale getirildi.
- `docs/sprint13.md`
  - Sprint 13.1 kapsam, test senaryolari ve DoD takip maddeleri eklendi.

## 2026-02-15 Sprint 13.2 - User Settings Modeli ve API (Backend)
- `backend/athena/models/settings.py`
  - `UserSettings` singleton modeli eklendi.
  - Alanlar: API keyler, `openalex_email`, `enabled_providers` (JSONB), `proxy_url`, `proxy_enabled`.
- `backend/migrations/versions/3c4a09dd9c21_add_user_settings_table.py`
  - `user_settings` tablosu eklendi.
  - `enabled_providers` default: `["semantic","openalex","arxiv","crossref","core"]`
  - `proxy_enabled` default: `false`
- `backend/athena/services/settings.py`
  - `get_settings()`:
    - DB'de ayar yoksa `.env` kaynakli default singleton kayit olusturur.
  - `update_settings(...)`:
    - parcali guncelleme yapar.
    - `***` ile gelen maskeli secret inputlarinda mevcut degeri korur.
    - provider listesinde normalize (duplicate/gecersiz ayiklama) uygular.
- `backend/athena/api/v2/routers/settings.py`
  - `GET /api/v2/system/settings` endpointi eklendi (secret alanlari maskeli doner).
  - `PUT /api/v2/system/settings` endpointi eklendi.
  - Secret input alanlarinda `SecretStr` kullanildi.
- `backend/athena/main.py`
  - settings router `/api/v2` altina eklendi.
- `backend/athena/api/v2/routers/system.py`
  - reset akisinda `user_settings` tablosu da temizlenecek sekilde guncellendi.
- `backend/athena/services/__init__.py`
  - lightweight ortamlarda (`loguru` eksik) import zinciri kirilmasin diye opsiyonel import yaklasimi eklendi.
- `backend/tests/test_settings_helpers.py`
  - secret maskeleme ve provider normalize davranislarini test eden unit testler eklendi.
- `frontend/src/services/settings.ts`
  - `/api/v2/system/settings` endpointleri icin fetch/update servisleri eklendi.
- `frontend/src/components/settings.tsx`
  - Ayarlar sayfasi DB tabanli settings API ile entegre edildi.
  - Semantic disinda OpenAI, CORE, OpenAlex/Crossref alanlari eklendi.
  - Provider enable/disable checkboxlari ve proxy ayarlari eklendi.
- `frontend/src/types/api.ts`
  - `UserSettingsResponse` ve `UserSettingsUpdateRequest` tipleri eklendi.
- `docker-compose.yml`
  - `build.sbom` / `build.provenance` alanlari compose surum uyumlulugu icin geri alindi.
  - Bu hata senaryosu icin CLI fallback:
    - `BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build`
    - gerekirse `docker builder prune -af`

## 2026-02-15 Sprint 13.3 - Provider ve Proxy Entegrasyonu (Backend Logic)
- `backend/athena/services/search.py`
  - Search akisi DB tabanli runtime ayarlara baglandi.
  - `enabled_providers` disindaki providerlar cagrilmiyor.
  - ek savunma olarak sonuc payload'i `paper.source` bazinda da `enabled_providers` ile filtreleniyor.
  - Providerlara runtime `api_key`, `contact_email`, `proxy_url` enjekte ediliyor.
  - DB ayari yoksa `.env` fallback korunuyor.
- `backend/athena/api/v2/routers/search.py`
  - endpoint DB dependency alacak sekilde guncellendi (`SearchService(db)`).
- `backend/athena/services/library.py`
  - enrichment icin kullanilan `SearchService` DB bagimli hale getirildi.
- `backend/athena/adapters/base.py`
  - `provider_id` ve `configure_runtime(...)` altyapisi eklendi.
- `backend/athena/adapters/semantic.py`
  - runtime `semantic` key ve proxy override destegi eklendi.
- `backend/athena/adapters/openalex.py`
  - runtime contact email ve proxy override destegi eklendi.
- `backend/athena/adapters/crossref.py`
  - runtime contact email ve proxy override destegi eklendi.
- `backend/athena/adapters/arxiv.py`
  - runtime proxy override destegi eklendi.
- `backend/athena/adapters/core.py`
  - runtime CORE key ve proxy override destegi eklendi.
- `backend/athena/tasks/downloader.py`
  - task baslangicinda DB'den guncel proxy ayari okunuyor.
  - proxy aktifse PDF indirme istegi DB proxy'si uzerinden gidiyor.
  - DB hatasinda env proxy fallback korunuyor.
- `backend/tests/test_search_runtime_provider_control.py`
  - aktif provider filtreleme ve runtime enjeksiyon davranisi test edildi.
- `backend/tests/test_downloader_proxy_resolution.py`
  - downloader proxy secim/fallback davranisi test edildi.

## 2026-02-15 Sprint 13.4 - Gelismis Ayarlar Arayuzu (Frontend)
- `frontend/src/components/settings.tsx`
  - Ayarlar sayfasi Tabs tabanli yapiya tasindi:
    - `Kaynaklar`
    - `Ag/Proxy`
    - `Sistem`
  - Provider switch + key/email alanlari tek ekranda yonetilir hale geldi.
  - Proxy switch + proxy URL + kurum proxy bilgilendirme metni eklendi.
  - Export ve Danger Zone bolumleri System tabina tasindi.
- `frontend/src/services/settings.ts`
  - `fetchSettings` ve `updateSettings` fonksiyonlari eklendi.
  - Geriye donuk alias'lar korundu.
- `frontend/src/components/ui/tabs.tsx`
  - ShadCN Tabs bileşeni eklendi.
- `frontend/src/components/ui/switch.tsx`
  - ShadCN Switch bileşeni eklendi.
- `frontend/package.json`
  - `@radix-ui/react-tabs` ve `@radix-ui/react-switch` bagimliliklari eklendi.

## 2026-02-15 Sprint 13.5 - Reset UX Iyilestirmesi
- `frontend/src/components/settings.tsx`
  - Reset basari akisinda ani reload kaldirildi.
  - 5 sn sureli basari toast eklendi:
    - `Sistem Sifirlandi`
    - `Tum veriler temizlendi. Kalem - Kasghar baslangic durumuna donuyor...`
  - 3.5 sn bekleme sonrasi `/` yonlendirmesi ve yenileme eklendi.
  - Hata durumunda backend mesajini gosteren kirmizi toast eklendi.

## Bu Oturumdaki Test Durumu
- `cd backend && alembic heads` -> `3c4a09dd9c21 (head)`
- `cd backend && /Users/sdemir/anaconda3/bin/alembic upgrade heads` -> basarili
- `python3 -m compileall backend/athena` -> basarili
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `14 passed`
- `cd frontend && npm run build` -> basarili (13.4 Tabs/Switch)
- `GET http://localhost:8000/api/v2/system/settings` smoke -> basarili
- `PUT http://localhost:8000/api/v2/system/settings` smoke -> basarili
  - `invalid-provider` gonderiminde normalize edilip disarida birakildigi dogrulandi
- `python3 -m compileall backend/athena backend/migrations/versions backend/tests` -> basarili
- Not: Bu shell ortaminda `docker` komutu olmadigi icin `docker-compose up --build` canli smoke testi burada calistirilamadi.
- `backend/athena/services/export.py` compile dogrulamasi -> basarili
- `backend/athena/api/v2/routers/library.py` ZIP endpoint compile dogrulamasi -> basarili
- `python3 -m compileall backend/athena backend/migrations/versions` -> basarili (FTS migration dahil)
- `backend/tests/test_pdf_path_resolution.py` -> relative/legacy/traversal/missing senaryolari kapsaniyor
- `rg -n "outbound_proxy|OUTBOUND_PROXY|proxy=" ...` -> proxy entegrasyon noktalarinin kod tabanina uygulandigi dogrulandi
- `rg -n "buildPdfEmbedUrl|relative_to(settings.data_dir)" ...` -> PDF 404 duzeltme noktalarinin uygulandigi dogrulandi
- `~/.docker/config.json` icinden `credsStore` kaldirilarak docker build credential hatasi giderildi
- `rg -n \"location /files/|'/files'|normalized_relative\" ...` -> PDF same-origin proxy + path normalize noktalarinin uygulandigi dogrulandi
- Not: Bu shell ortaminda `docker` komutu bulunmadigi icin canli container testleri bu oturumda tekrar calistirilamadi.
