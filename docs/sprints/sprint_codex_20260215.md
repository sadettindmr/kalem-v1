# Sprint Codex - 2026-02-15

## Sprint Adı
**Kalem v1.0.0 - Kasghar | İsim Dönüşümü ve Dokümantasyon Senkronizasyonu**

## Amaç
`Project Athena` / `Athena` marka ifadelerini, mevcut yapıyı bozmadan `Kalem - Kasghar` standardına geçirmek ve güncel teknik envanteri tek bir Codex dokümanında toplamak.

## Kapsam
- Kullanıcıya görünen backend/frontend adlarının güncellenmesi
- Dış API User-Agent marka adının güncellenmesi
- Konfigürasyon başlık/fallback değerlerinin güncellenmesi
- Export dosya adlarının yeni isim standardına çekilmesi
- `docs/Codex.md` dosyasının oluşturulması

## Yapılan Değişiklikler

### 1. Uygulama Kimliği Güncellendi
- Backend API title ve root mesajı `Kalem - Kasghar` yapıldı.
- Frontend dashboard başlığı `Kalem - Kasghar` olarak değiştirildi.
- Logo harfi `K` olarak güncellendi.

### 2. Provider Kimliği Güncellendi
- OpenAlex ve Crossref User-Agent değerleri `Kalem-Kasghar/1.0.0` standardına alındı.

### 3. Konfigürasyon ve Çıktı İsimleri Güncellendi
- `.env.example` başlığı yeni proje adına geçirildi.
- `docker-compose.yml` varsayılan e-posta fallback değerleri güncellendi.
- Backend export dosya adları `kalem_kasghar_library_export.*` olarak değiştirildi.
- `backend/pyproject.toml` açıklaması yeni proje adına geçirildi.

## Değişen Dosyalar
- `.env.example`
- `Dockerfile.backend`
- `backend/athena/adapters/crossref.py`
- `backend/athena/adapters/openalex.py`
- `backend/athena/core/config.py`
- `backend/athena/core/exceptions.py`
- `backend/athena/main.py`
- `backend/athena/services/export.py`
- `backend/pyproject.toml`
- `docker-compose.yml`
- `frontend/src/layouts/DashboardLayout.tsx`
- `docs/Codex.md` (yeni)
- `docs/sprint_codex_20260215.md` (yeni)

## Bilinçli Olarak Değiştirilmeyen Alanlar
Mevcut sistemi bozmamak adına aşağıdaki teknik isimler korunmuştur:
- Python package/import yolu: `athena.*`
- Uvicorn/Celery module pathleri: `athena.main:app`, `athena.core.celery_app`
- DB user ve modül yollarındaki `athena` adları

## Ek Güncelleme - Docker Local Çalıştırma (2026-02-15)
- `celery_worker` servisinde `image: project-athena-backend:latest` kaldırıldı, `Dockerfile.backend` ile build'e alındı.
- `Dockerfile.backend` içinde `poetry.lock` uyumsuzluğunda fallback install adımı eklendi.
- Container adları `kalem_*` standardına geçirildi:
  - `kalem_postgres`
  - `kalem_redis`
  - `kalem_rabbitmq`
  - `kalem_backend`
  - `kalem_celery_worker`
  - `kalem_frontend`
- Shared volume adı `athena_library` -> `kalem_library` olarak güncellendi.
- Backend startup migration komutu `alembic upgrade heads` olarak eklendi.
- Çözülen runtime hata:
  - `GET /api/v2/library` ve `GET /api/v2/library/download-stats` çağrılarında görülen
    `relation \"library_entries\" does not exist` kaynaklı 500 hatası giderildi.

## Sonuç
İsim dönüşümü, uygulamanın görünen yüzünde ve ilgili konfigürasyon/çıktı katmanlarında tamamlandı. Mimari bütünlük korunarak geliştirmeye devam edilebilir.

## Ek Güncelleme - Sprint 11.3 Metadata Enrichment (2026-02-15)
- `POST /api/v2/library/enrich-metadata?limit=20` endpointi eklendi.
- Eksik metadata tamamlama servisi yazildi:
  - hedef alanlar: `abstract`, `year`, `venue`, `citation_count`, `pdf_url`, `authors`
  - eslesme: DOI > normalize baslik > fallback ilk sonuc
  - sadece bos alanlar guncellenir, mevcut veri korunur
- Settings sayfasina "Eksik Verileri Tamamla" aksiyonu eklendi.
- Enrichment sonrasi `library` query invalidate edilerek ekran yenileme akisi tamamlandi.
- Kaynak map duzeltmesi:
  - `arxiv`, `crossref`, `core` kayitlari artik `manual` yerine dogru `SourceType` ile saklaniyor.

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena` -> basarili
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `no tests ran`
- Not: Oturum shell'inde `docker` binary bulunmadigi icin canli docker smoke testi tekrar kosulamadi.

## Ek Guncelleme - Sprint 11.4 Proxy Altyapisi (2026-02-15)
- Tum dis kaynak aramalarinda proxy destegi eklendi:
  - Semantic Scholar, OpenAlex, arXiv, Crossref, CORE adapterlari
- PDF indirme task'i proxy ile calisacak sekilde guncellendi.
- Konfigurasyon:
  - `OUTBOUND_PROXY` env degiskeni eklendi
  - `backend` ve `celery_worker` servisleri bu degiskeni docker-compose uzerinden aliyor
- Dokuman ve ornek env:
  - `.env.example` icine proxy konfigurasyonu eklendi

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena` -> basarili
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `no tests ran`
- `rg -n "outbound_proxy|OUTBOUND_PROXY|proxy=" ...` -> proxy entegrasyon noktalari dogrulandi
- Not: Oturum shell'inde `docker` binary bulunmadigi icin canli docker smoke testi tekrar kosulamadi.

## Ek Guncelleme - PDF Goruntuleme 404 Duzeltmesi (2026-02-15)
- Tespit edilen hata:
  - Frontend'de uretilen PDF URL `/files//data/library/...` formatina donusuyor ve backend `NOT_FOUND` donuyordu.
- Yapilan duzeltmeler:
  - `frontend/src/components/PaperDetail.tsx`:
    - PDF path normalize (absolute -> relative)
    - URL segment encode
    - backend origin dinamik olusturma
  - `backend/athena/tasks/downloader.py`:
    - yeni kayitlarda `file_path` relative formatta saklama

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena` -> basarili
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `no tests ran`
- `rg -n "buildPdfEmbedUrl|relative_to(settings.data_dir)" ...` -> duzeltme noktalari dogrulandi

## Ek Guncelleme - PDF Serving Dayaniklilik + Docker Credential (2026-02-15)
- `backend/athena/main.py`
  - custom `GET /files/{requested_path:path}` route ile legacy/relative path uyumlulugu eklendi.
- `backend/athena/api/v2/routers/library.py`
  - "completed ama dosya yok" kayitlar icin auto-repair eklendi (`failed` + `file_path=null`).
- `frontend/src/components/LibraryList.tsx`
  - Retry butonu `failed` kayitlarini da kapsar; gerekiyorsa `scope=all` ile tekrar kuyruga alir.
- `frontend/src/components/PaperDetail.tsx`
  - PDF auto-open davranisi kapatildi, sadece butonla goruntuleme akisi getirildi.
- `backend/athena/tasks/downloader.py`
  - HTTP hata durumunda status `pending`/`failed` gecisleri netlestirildi (takili downloading azaltildi).
- Docker credential duzeltmesi:
  - `~/.docker/config.json` icindeki `credsStore=desktop` kaldirildi (yedek alinarak).
  - `docker-credential-desktop not found` hatasini kalici olarak engeller.

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena` -> basarili
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `no tests ran`
- `~/.docker/config.json` dogrulama -> `credsStore` alani kaldirildi

## Ek Guncelleme - Sprint 11.5 PDF Goruntuleme Hatasi Duzeltmesi (2026-02-15)
- Frontend PDF URL ayni-origin formata alindi:
  - `http://localhost:8000/files/...` yerine `/files/...`
- Proxy konfigurasyonlari guncellendi:
  - `nginx.frontend.conf` -> `/files/` backend proxy
  - `frontend/vite.config.ts` -> `/files` dev proxy
- Backend legacy path normalize:
  - `GET /api/v2/library` donusunde `completed` kayitlarda absolute path'ler relative formata cevrilir
  - dosyasi olmayan kayitlar `failed` durumuna cekilir
- Path utility modul:
  - `backend/athena/core/file_paths.py` ile path cozumleme/normalize tek noktaya tasindi
- Otomasyon testi:
  - `backend/tests/test_pdf_path_resolution.py` eklendi

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena` -> basarili
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `6 passed`
- `rg -n "location /files/|'/files'|normalized_relative" ...` -> proxy/path normalize degisiklikleri dogrulandi

## Ek Guncelleme - Sprint 12.1 Gelismis Excel Export (2026-02-15)
- `backend/athena/services/export.py` yeniden yapilandirildi.
- Yeni bibliyografik kolon yapisi eklendi (14 kolon):
  - Makale adi, yazarlar, yil, tur, venue, DOI/link, keywords, search words
  - APA/IEEE atif metinleri
  - dynamic `Citation as of dd.mm.yyyy`
  - source, downloaded (EVET/HAYIR), kod/veri erisilebilirligi
- APA/IEEE formatlayicilari best-effort string mantigi ile eklendi.
- XLSX auto-width eklendi.
- Sprint dokumani:
  - `docs/sprint12.md` olusturuldu.

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena` -> basarili
- `cd backend && python3 -m pytest -q` -> `6 passed`
- `cd frontend && npm run build` -> basarili

## Ek Guncelleme - Sprint 12.2 Toplu PDF Indirme (ZIP Archive) (2026-02-15)
- Backend:
  - `GET /api/v2/library/download-zip` endpointi eklendi.
  - `search/tag/status/min_citations/year_start/year_end` filtreleri destekleniyor.
  - Yalnizca `completed + mevcut file_path` dosyalari ZIP'e aliniyor.
  - ZIP dosya isimleri: `entryid_filename.pdf`
  - Cikti dosya adi: `kalem_library_archive_YYYYMMDD.zip`
- Frontend:
  - `LibraryList` header'a `PDF Arsivi Indir (.zip)` butonu eklendi.
  - Buton aktif filtreleri query string olarak endpoint'e gonderiyor.

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena` -> basarili
- `cd backend && python3 -m pytest -q` -> `6 passed`
- `cd frontend && npm run build` -> basarili
- `rg -n "download-zip|ZipFile|_apply_library_filters|PDF Arsivi Indir" ...` -> endpoint + UI baglantisi dogrulandi

## Ek Guncelleme - Sprint 13.1 Full-Text Search (Relevance Altyapisi) (2026-02-15)
- Altyapi duzeltmesi:
  - `backend/athena/core/__init__.py` logging/middleware importlari kosullu hale getirildi.
  - Boylesce sistem Python uzerinden migration kosarken gorulen
    `ModuleNotFoundError: loguru` hatasi giderildi.
- Veritabani:
  - `papers.search_vector` (`TSVECTOR`) kolonu eklendi.
  - `ix_papers_search_vector` GIN index eklendi.
  - migration: `backend/migrations/versions/f13a1c9d0b77_add_search_vector_fts.py`
  - `title + abstract + authors.name` kaynakli trigger tabanli guncelleme ve backfill SQL eklendi.
- Backend servis:
  - `backend/athena/services/library.py` icinde `get_library_entries(...)` ile FTS arama akisi eklendi.
  - `websearch_to_tsquery('english', query)` + `Paper.search_vector @@ ts_query` ile filtreleme.
  - `ts_rank(...).desc()` ile relevance siralama.
  - `ilike` tabanli fallback (title/abstract/author/tag) `OR` kosulu ile korundu.
- Router:
  - `backend/athena/api/v2/routers/library.py` listeleme endpointi service tabanli FTS akisina alindi.
  - ZIP endpointte kullanilan ortak filtreleyici FTS+fallback uyumlu hale getirildi.
- Dokuman:
  - `docs/sprint13.md` 13.1 maddeleri ve test senaryolariyla guncellendi.

### Bu Oturumda Calistirilan Testler
- `cd backend && alembic heads` -> `f13a1c9d0b77 (head)`
- `cd backend && /Users/sdemir/anaconda3/bin/alembic upgrade heads` -> basarili
- `python3 -m compileall backend/athena backend/migrations/versions` -> basarili
- `cd backend && python3 -m pytest -q` -> `6 passed`
- `cd frontend && npm run build` -> basarili

## Ek Guncelleme - Sprint 13.2 User Settings Modeli ve API (2026-02-15)
- Veritabani:
  - `user_settings` singleton tablosu eklendi.
  - migration: `backend/migrations/versions/3c4a09dd9c21_add_user_settings_table.py`
  - `enabled_providers` JSONB default list ve `proxy_enabled=false` server default tanimlandi.
- Model/Servis:
  - `backend/athena/models/settings.py` ile `UserSettings` modeli eklendi.
  - `backend/athena/services/settings.py` ile:
    - `get_settings()` (DB'de yoksa `.env` degerlerinden default kayit olusturma)
    - `update_settings()` (parcali guncelleme, maskeli secret koruma, provider normalize)
    - akislari eklendi.
- API:
  - `backend/athena/api/v2/routers/settings.py` eklendi.
  - `GET /api/v2/system/settings`: secret alanlari maskeli doner (`sk-***`).
  - `PUT /api/v2/system/settings`: ayar guncelleme endpointi.
  - `backend/athena/main.py` icine router entegre edildi.
- Ek dayaniklilik:
  - `backend/athena/services/__init__.py` icinde opsiyonel import yapisi ile
    eksik `loguru` ortamlarinda import zinciri kirilmasi engellendi.
  - `backend/athena/api/v2/routers/system.py` reset akisina `user_settings` tablosu eklendi.
- Test:
  - `backend/tests/test_settings_helpers.py` eklendi
    (secret maskeleme + provider normalize senaryolari).
- Frontend entegrasyonu:
  - `frontend/src/services/settings.ts` ile settings API cagrilari eklendi.
  - `frontend/src/components/settings.tsx` icinde API Ayarlari bolumu genisletildi:
    - OpenAI key, Semantic key, CORE key
    - OpenAlex/Crossref e-posta
    - Provider aktif/pasif checkboxlari
    - Proxy aktif/pasif + URL
  - Ayarlar artik localStorage yerine DB tabanli `/api/v2/system/settings` endpointleriyle yonetiliyor.
- Docker stabilizasyonu:
  - `build.sbom` / `build.provenance` alanlarinin bazi compose surumlerinde gecersiz oldugu goruldu.
  - Bu nedenle YAML tarafinda bu alanlar geri alindi.
  - Fallback calistirma yontemi:
    - `BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build`
    - gerekirse `docker builder prune -af`

### Bu Oturumda Calistirilan Testler
- `cd backend && /Users/sdemir/anaconda3/bin/alembic heads` -> `3c4a09dd9c21 (head)`
- `cd backend && /Users/sdemir/anaconda3/bin/alembic upgrade heads` -> basarili
- `python3 -m compileall backend/athena backend/migrations/versions backend/tests` -> basarili
- `cd backend && python3 -m pytest -q` -> `9 passed`
- `python3` async smoke (UserSettingsService.get_settings) -> singleton kayit olusturma dogrulandi
- `cd frontend && npm run build` -> basarili
- `curl/HTTP smoke`:
  - `GET http://localhost:8000/api/v2/system/settings` -> basarili
  - `PUT http://localhost:8000/api/v2/system/settings` -> basarili
  - gecersiz provider degeri normalize edilerek disarida birakildi
- Not: Bu shell'de `docker` komutu olmadigi icin `docker-compose up -d --build` canli tekrar testi burada calistirilamadi.

## Ek Guncelleme - Sprint 13.3 Provider ve Proxy Entegrasyonu (2026-02-15)
- Search runtime ayarlari:
  - `backend/athena/services/search.py` DB'den `UserSettings` okuyarak
    `enabled_providers` filtrelemesi uygular hale getirildi.
  - ek savunma: donen sonuclar `paper.source` bazinda da etkin provider listesiyle filtreleniyor.
  - provider bazli runtime deger enjeksiyonu eklendi:
    - `semantic` -> api_key
    - `core` -> api_key
    - `openalex/crossref` -> contact email
    - tum providerlar -> proxy_url
  - DB ayari yoksa `.env` fallback korunuyor.
- Search endpoint:
  - `backend/athena/api/v2/routers/search.py` icine `db` dependency eklendi.
  - `SearchService(db)` kullanimi aktif edildi.
- Library integration:
  - `backend/athena/services/library.py` icindeki enrichment akisi da
    DB bagimli `SearchService(db)` kullanacak sekilde guncellendi.
- Adapter katmani:
  - `backend/athena/adapters/base.py` -> `provider_id` + `configure_runtime(...)`
  - `semantic/openalex/crossref/arxiv/core` providerlarinda runtime proxy/key/email override destegi.
- Downloader:
  - `backend/athena/tasks/downloader.py` task baslangicinda DB'den proxy ayari okuyup
    indirme isteklerini buna gore yonlendirir hale getirildi.
  - DB okunamazsa env fallback korundu.
- Testler:
  - `backend/tests/test_search_runtime_provider_control.py` eklendi.
  - `backend/tests/test_downloader_proxy_resolution.py` eklendi.

### Bu Oturumda Calistirilan Testler
- `python3 -m compileall backend/athena backend/migrations/versions backend/tests` -> basarili
- `cd backend && python3 -m pytest -q` -> `13 passed`
- `cd frontend && npm run build` -> basarili

## Ek Guncelleme - Sprint 13.4 Gelismis Ayarlar Arayuzu (2026-02-15)
- Frontend Settings sayfasi Tabs tabanli yapiya tasindi:
  - `Kaynaklar`
  - `Ag/Proxy`
  - `Sistem`
- Kaynaklar tabi:
  - Provider bazli `Switch` aktif/pasif kontrolleri eklendi.
  - Provider gereksinimine gore key/email alanlari duzenlendi.
  - Kaydet akisi `PUT /api/v2/system/settings` ile baglandi.
- Ag/Proxy tabi:
  - `Proxy Kullan` switch'i + Proxy URL inputu eklendi.
  - Kurum proxy kullanim notu eklendi.
- Sistem tabi:
  - Export ve Danger Zone bolumleri bu taba tasindi.
  - Indirme yonetimi ve metadata tamamlama bolumleri sistem tabinda korunarak calisiyor.
- Servis katmani:
  - `frontend/src/services/settings.ts` icine `fetchSettings` ve `updateSettings` eklendi.
  - Eski isimlerle geriye donuk alias korundu.
- UI altyapisi:
  - `frontend/src/components/ui/tabs.tsx`
  - `frontend/src/components/ui/switch.tsx`
  eklendi.
- Paket bagimliliklari:
  - `@radix-ui/react-tabs`
  - `@radix-ui/react-switch`
  eklendi.

### Bu Oturumda Calistirilan Testler
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `14 passed`
- `python3 -m compileall backend/athena backend/tests` -> basarili

## Ek Guncelleme - Sprint 13.5 Reset UX Iyilestirmesi (2026-02-15)
- `frontend/src/components/settings.tsx`
  - Reset basarili oldugunda anlik `window.location.reload()` kaldirildi.
  - 5 sn sureli toast eklendi:
    - Baslik: `Sistem Sifirlandi`
    - Mesaj: `Tum veriler temizlendi. Kalem - Kasghar baslangic durumuna donuyor...`
  - 3.5 sn gecikme ile `/` adresine yonlendirme + yenileme uygulandi.
  - Hata durumunda backend mesajini gosteren kirmizi toast eklendi.

### Bu Oturumda Calistirilan Testler
- `cd frontend && npm run build` -> basarili
- `cd backend && python3 -m pytest -q` -> `14 passed`
- `rg -n \"Sistem Sifirlandi|setTimeout|Sifirlama Basarisiz\" frontend/src/components/settings.tsx` -> UX akisi dogrulandi
