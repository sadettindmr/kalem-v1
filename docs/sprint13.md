# Sprint 13 - Konfigurasyon Merkezi ve Arama Zekasi

## Sprint Ozeti
**Amac:** Sprint 12'den devralinan relevance altyapisini tamamlamak ve ayar merkezilesmesine temel hazirlik yapmak.

**Durum:** Devam Ediyor

---

## Tamamlanan Prompt'lar

### 13.1 - Full-Text Search (Relevance Altyapisi)

#### Veritabani / Migration
- [x] `papers` tablosuna `search_vector` (`TSVECTOR`) kolonu eklendi.
- [x] `search_vector` icin `GIN` index eklendi: `ix_papers_search_vector`.
- [x] Alembic migration eklendi:
  - `backend/migrations/versions/f13a1c9d0b77_add_search_vector_fts.py`
- [x] `search_vector` doldurma stratejisi:
  - `title` + `abstract` + iliskili `authors.name` birlesimi
  - trigger + function tabanli guncelleme (insert/update/author relation degisimi)
  - mevcut kayitlar icin backfill SQL eklendi

#### Model Guncellemesi
- [x] `backend/athena/models/paper.py`
  - `search_vector` alanı eklendi
  - GIN index model seviyesinde tanimlandi

#### Backend Service (Relevance Search)
- [x] `backend/athena/services/library.py` icine `get_library_entries(...)` eklendi.
- [x] Search mantigi FTS'e tasindi:
  - `websearch_to_tsquery('english', query)`
  - filtre: `Paper.search_vector @@ ts_query`
  - siralama: `ts_rank(...).desc()`, sonra `LibraryEntry.id.desc()`
- [x] Fallback mantigi korundu:
  - `title/abstract ilike` + author/tag eslesmeleri ile `OR` baglandi

#### Router Entegrasyonu
- [x] `GET /api/v2/library` endpointi listeleme icin `LibraryService.get_library_entries(...)` kullanir hale getirildi.
- [x] ZIP endpoint filtre mantigi da FTS+fallback ile uyumlu hale getirildi (`_apply_library_filters`).

#### Alembic Calisma Duzeltmesi
- [x] `backend/athena/core/__init__.py` icinde logging/middleware importlari kosullu hale getirildi.
- [x] Boylesce `alembic upgrade heads` calisirken `ModuleNotFoundError: loguru` blokaji kaldirildi.

### 13.2 - User Settings Modeli ve API (Backend)

#### Veritabani / Migration
- [x] `user_settings` singleton tablosu eklendi.
- [x] Alembic migration eklendi:
  - `backend/migrations/versions/3c4a09dd9c21_add_user_settings_table.py`
- [x] Kolonlar:
  - `openai_api_key`, `semantic_scholar_api_key`, `core_api_key`
  - `openalex_email`
  - `enabled_providers` (JSONB, default: `["semantic","openalex","arxiv","crossref","core"]`)
  - `proxy_url`, `proxy_enabled`

#### Model / Service
- [x] `backend/athena/models/settings.py`
  - `UserSettings` modeli olusturuldu.
- [x] `backend/athena/services/settings.py`
  - `get_settings()`: DB kaydi yoksa `.env` ile varsayilan singleton kayit olusturur.
  - `update_settings(data)`: parcali guncelleme yapar.
  - maskeli deger (`***`) geldiyse mevcut secret korunur.
  - provider listesinde gecersiz/tekrarli degerler normalize edilir.

#### Router / API
- [x] `backend/athena/api/v2/routers/settings.py` eklendi.
- [x] `GET /api/v2/system/settings` endpointi eklendi.
- [x] `PUT /api/v2/system/settings` endpointi eklendi.
- [x] Hassas key alanlari response'ta maskeleniyor (`sk-***`).
- [x] Secret input alanlari icin `SecretStr` kullanildi.
- [x] `backend/athena/main.py` icine router eklendi.

#### Frontend Ayarlar Entegrasyonu
- [x] `frontend/src/services/settings.ts` eklendi (`fetchSystemSettings`, `updateSystemSettings`).
- [x] `frontend/src/components/settings.tsx` API ayarlari bolumu genisletildi:
  - OpenAI API Key
  - Semantic Scholar API Key
  - CORE API Key
  - OpenAlex/Crossref e-posta alani
  - Provider aktif/pasif checkboxlari (`semantic`, `openalex`, `arxiv`, `crossref`, `core`)
  - Proxy aktif/pasif ve proxy URL alanlari
- [x] Ayarlar sayfasi localStorage yerine `/api/v2/system/settings` ile DB tabanli kayit okuma/yazma yapiyor.
- [x] `frontend/src/types/api.ts` icine `UserSettingsResponse` ve `UserSettingsUpdateRequest` tipleri eklendi.

#### Docker Build Stabilizasyonu
- [x] BuildKit export/snapshot hatalari icin CLI tabanli fallback stratejisi belirlendi:
  - `BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build`
  - gerekirse `docker builder prune -af` ile cache temizleme
- [x] Not: `build.sbom`/`build.provenance` alanlari bazi `docker-compose` surumlerinde desteklenmedigi icin YAML'dan cikarildi.

#### Ek Dayaniklilik
- [x] `backend/athena/services/__init__.py` importlari opsiyonel hale getirildi.
  - eksik `loguru` olan lightweight ortamlarda import zinciri kirilmaz.
- [x] `backend/athena/api/v2/routers/system.py`
  - reset akisi `user_settings` tablosunu da temizleyecek sekilde guncellendi.

### 13.3 - Provider ve Proxy Entegrasyonu (Backend Logic)

#### SearchService Dinamik Ayarlar
- [x] `backend/athena/services/search.py`
  - `search_papers` icinde `UserSettings` tabanli runtime ayarlari yukleniyor.
  - `enabled_providers` disindaki kaynaklar provider dongusunden cikariliyor.
  - ek guvenlik: donen sonuclar `paper.source` bazinda tekrar `enabled_providers` ile filtreleniyor.
  - Providerlara runtime `api_key`, `contact_email`, `proxy_url` enjekte ediliyor.
  - DB ayari yoksa `.env` fallback korunuyor.
- [x] `backend/athena/api/v2/routers/search.py`
  - `db: AsyncSession = Depends(get_db)` eklendi.
  - `SearchService(db)` ile DB tabanli runtime ayarlari aktif edildi.
- [x] `backend/athena/services/library.py`
  - enrichment akisi da DB bagimli `SearchService(db)` kullanacak sekilde guncellendi.

#### Adapter Runtime Entegrasyonu
- [x] `backend/athena/adapters/base.py`
  - `provider_id` ve `configure_runtime(...)` eklendi.
  - runtime `proxy/api_key/contact_email` alanlari tanimlandi.
- [x] Alt siniflar (`semantic/openalex/arxiv/crossref/core`)
  - `super().__init__()` eklendi.
  - `httpx.AsyncClient` olustururken runtime proxy tercih ediliyor.
  - API key / email alanlari runtime degerlerle override ediliyor.

#### Downloader Dinamik Proxy
- [x] `backend/athena/tasks/downloader.py`
  - task basinda DB'den `UserSettings` okunup guncel proxy belirleniyor.
  - `proxy_enabled=True` ve `proxy_url` varsa indirme bu proxy ile yapiliyor.
  - DB okuma hatasinda env proxy fallback korunuyor.

### 13.4 - Gelismis Ayarlar Arayuzu (Frontend)

#### Tabs Tabanli Sayfa Yapisi
- [x] `frontend/src/components/settings.tsx` yeniden tasarlandi.
- [x] ShadCN Tabs ile sayfa 3 bolume ayrildi:
  - `Kaynaklar`
  - `Ag/Proxy`
  - `Sistem`
- [x] Yeni UI bileşenleri eklendi:
  - `frontend/src/components/ui/tabs.tsx`
  - `frontend/src/components/ui/switch.tsx`

#### Tab 1 - Kaynaklar
- [x] Her provider icin aktif/pasif `Switch` eklendi.
- [x] Gerekli kimlik alanlari eklendi:
  - Semantic -> API key
  - OpenAlex/Crossref -> email
  - CORE -> API key
  - arXiv -> kimlik gerekmiyor notu
- [x] OpenAI key alani korundu.
- [x] Kaydet butonu `PUT /api/v2/system/settings` ile baglandi.

#### Tab 2 - Ag/Proxy
- [x] `Proxy Kullan` switch'i eklendi.
- [x] Proxy URL input alani eklendi.
- [x] Bilgi notu eklendi:
  - "Enstitu abonelikleri uzerinden PDF indirmek icin buraya kurum proxy adresini giriniz."
- [x] Kaydet butonu ayarlari API'ye yazar.

#### Tab 3 - Sistem
- [x] Export bolumu bu taba tasindi.
- [x] Danger Zone (Reset) bu taba tasindi.
- [x] Mevcut `Indirme Yonetimi` ve `Metadata Tamamlama` bolumleri Sistem tabinda korunup calisir halde tutuldu.

#### Servis Katmani
- [x] `frontend/src/services/settings.ts` icinde:
  - `fetchSettings`
  - `updateSettings`
  fonksiyonlari eklendi.
- [x] Geriye donuk uyumluluk icin `fetchSystemSettings` / `updateSystemSettings` alias'lari korundu.

### 13.5 - Reset UX Iyilestirmesi

#### Basarili Reset Akisi
- [x] `frontend/src/components/settings.tsx` icinde `handleReset` guncellendi.
- [x] Basarili reset sonrasi ani `window.location.reload()` kaldirildi.
- [x] 5 sn sureli basari toast eklendi:
  - Baslik: `Sistem Sifirlandi`
  - Mesaj: `Tum veriler temizlendi. Kalem - Kasghar baslangic durumuna donuyor...`
- [x] 3.5 sn gecikme ile `/` adresine yonlendirme + yenileme eklendi.

#### Hata Akisi
- [x] Reset hatasinda kirmizi toast gosterimi eklendi.
- [x] Backend'den gelen `error.message` varsa toast aciklamasinda gosteriliyor.

---

## Test Senaryolari ve Sonuclar (2026-02-15)

### Build / Teknik Dogrulama
- [x] `cd backend && alembic heads` -> `3c4a09dd9c21 (head)`
- [x] `cd backend && /Users/sdemir/anaconda3/bin/alembic upgrade heads` -> basarili
- [x] `python3 -m compileall backend/athena backend/migrations/versions` -> basarili
- [x] `cd backend && python3 -m pytest -q` -> `14 passed`
- [x] `cd frontend && npm run build` -> basarili (Tabs/Switch dahil)
- [x] `python3 -m compileall backend/athena backend/migrations/versions backend/tests` -> basarili
- [x] Kod tarama:
  - `search_vector`, `websearch_to_tsquery`, `ts_rank`, `@@`, `GIN` ifadeleri dogrulandi

### 13.2 Fonksiyonel Senaryolar
- [x] Migration uygulama testi
  - Adim: `cd backend && alembic upgrade heads`
  - Sonuc: `user_settings` tablosu olustu.
- [x] Ilk kayit olusturma testi
  - Adim: `UserSettingsService.get_settings()` cagrisini bos tabloda calistir.
  - Sonuc: `.env` degerleri ile `id=1` singleton kayit olusuyor.
- [x] Secret maskeleme testi
  - Adim: `GET /api/v2/system/settings`
  - Beklenen: key alanlari ham deger yerine maskeli (`sk-***`) doner.
- [x] Guncelleme testi
  - Adim: `PUT /api/v2/system/settings` ile `enabled_providers`, `proxy_*`, email alanlarini guncelle.
  - Beklenen: kayit parcali guncellenir; gecersiz provider degerleri disarida birakilir.
- [x] Frontend alan gorunurluk testi
  - Adim: Ayarlar sayfasi acilip API Ayarlari bolumu kontrol edilir.
  - Beklenen: Semantic disinda OpenAI, CORE, OpenAlex/Crossref ve provider/proxy alanlari gorunur.
- [x] Test dosyalari
  - `backend/tests/test_settings_helpers.py` ile maskeleme ve provider normalize senaryolari dogrulandi.
- [x] 13.3 unit testleri
  - `backend/tests/test_search_runtime_provider_control.py`:
    - sadece etkin provider'in calistigi ve runtime ayarlarin enjekte edildigi dogrulandi.
  - `backend/tests/test_downloader_proxy_resolution.py`:
    - DB proxy secimi ve fallback davranisi dogrulandi.
- [ ] Docker full-cycle smoke (local)
  - Adim: `docker-compose down && docker-compose up -d --build`
  - Beklenen: frontend image export asamasi snapshot hatasi vermeden tamamlanir.
  - Not: Bu adim docker binary gerektirdigi icin kod ortaminda calistirilamadi; local makinede dogrulanmali.

### Manuel Fonksiyonel Senaryolar (Hazir)
- [ ] Migration uygulama testi
  - Adim: `cd backend && alembic upgrade heads`
  - Beklenen: `papers.search_vector` kolonu + `ix_papers_search_vector` indeksi olusur
- [ ] Relevance siralama testi (`Deep Learning`)
  - Adim: Kutuphane arama kutusuna `Deep Learning` yaz
  - Beklenen: baslikta gecen makale, sadece abstract'ta gecenden ustte listelenir
- [ ] Relevance siralama testi (`Neural`)
  - Adim: `Neural` arat
  - Beklenen: basligi `Neural Networks` olan kayit, basligi farkli olup abstract'ta gecen kaydin ustunde cikar
- [ ] Fallback testi
  - Adim: FTS'in kacirabilecegi kismi bir terim ara
  - Beklenen: `ilike` fallback sayesinde sonuc tamamen bos donmez

### Sprint 13 DoD Durumu
- [ ] Akilli Arama
  - `Learning` aramasinda title eslesmesi abstract eslesmesinin ustunde olmali.
  - Not: Manuel UI dogrulama gerekli.
- [ ] Kaynak Kontrolu
  - arXiv switch kapaliyken yeni aramada arXiv sonucu gelmemeli.
  - Not: Canli container ortaminda manuel dogrulama gerekli.
- [ ] Credential Testi
  - Semantic key girildiginde backend isteklerinde header olarak gonderilmeli.
  - Not: Canli network/log dogrulamasi gerekli.
- [ ] Proxy Testi
  - Proxy aktifken PDF indirme istekleri DB proxy ayariyla cikmali.
  - Not: Canli network/log dogrulamasi gerekli.
- [x] Reset UX
  - Basarili reset sonrasi "Sistem Sifirlandi" mesaji gorunur, ekran aniden yenilenmez.

---

## Sprint 12 DoD Kontrolu (Carry-over)
- [ ] Export Testi
  - Excel ciktisinda `Citation (APA)` dolu olmali
  - indirilemeyen makalelerde `Downloaded = HAYIR` olmali
- [ ] ZIP Testi
  - `PDF Arsivi Indir` ile `.zip` inmeli
  - arsiv icindeki PDF dosyalari acilabilir olmali
- [ ] Arama Testi
  - `Neural` aramasinda relevance ranking beklendigi gibi olmali

---

## Degisiklik Yapilan Dosyalar
- `backend/athena/core/__init__.py` - Alembic import zinciri icin kosullu logging/middleware importu
- `backend/athena/services/__init__.py` - lightweight ortamlarda opsiyonel servis importlari
- `backend/athena/models/paper.py` - `search_vector` + GIN index
- `backend/migrations/versions/f13a1c9d0b77_add_search_vector_fts.py` - FTS migration + trigger/backfill
- `backend/athena/services/library.py` - `get_library_entries` + FTS rank/fallback arama
- `backend/athena/api/v2/routers/library.py` - list endpoint service entegrasyonu + FTS uyumlu filter helper
- `backend/athena/models/settings.py` - `UserSettings` modeli
- `backend/athena/services/settings.py` - settings get/update servisi
- `backend/athena/api/v2/routers/settings.py` - settings API endpointleri
- `backend/migrations/versions/3c4a09dd9c21_add_user_settings_table.py` - user_settings migration
- `backend/tests/test_settings_helpers.py` - maskeleme ve normalize testleri
- `backend/athena/api/v2/routers/system.py` - reset akisina `user_settings` eklendi
- `backend/athena/main.py` - settings router entegrasyonu
- `backend/athena/services/search.py` - DB tabanli provider filtreleme ve runtime ayar enjeksiyonu
- `backend/athena/api/v2/routers/search.py` - search endpoint DB dependency entegrasyonu
- `backend/athena/adapters/base.py` - runtime configure altyapisi
- `backend/athena/adapters/semantic.py` - runtime api_key/proxy desteği
- `backend/athena/adapters/openalex.py` - runtime email/proxy desteği
- `backend/athena/adapters/crossref.py` - runtime email/proxy desteği
- `backend/athena/adapters/arxiv.py` - runtime proxy desteği
- `backend/athena/adapters/core.py` - runtime api_key/proxy desteği
- `backend/athena/tasks/downloader.py` - DB tabanli proxy cozumleme
- `backend/tests/test_search_runtime_provider_control.py` - 13.3 search runtime testleri
- `backend/tests/test_downloader_proxy_resolution.py` - 13.3 downloader proxy testleri
- `frontend/src/components/settings.tsx` - tum provider key/mail/proxy alanlari ve DB tabanli ayar kaydetme
- `frontend/src/services/settings.ts` - system settings API servisi
- `frontend/src/types/api.ts` - user settings tipleri
- `frontend/src/components/ui/tabs.tsx` - ShadCN Tabs bileşeni
- `frontend/src/components/ui/switch.tsx` - ShadCN Switch bileşeni
- `frontend/src/components/settings.tsx` - reset toast + gecikmeli yonlendirme UX
- `docker-compose.yml` - compose surum uyumlulugu icin build alanlari sade tutuldu
- `docs/sprint13.md` - Sprint 13 dokumani (yeni)
