# Sprint 8 - Coklu Kaynak Entegrasyonu

## Sprint Ozeti
**Amac:** Arama altyapisina arXiv, Crossref ve CORE kaynaklarini eklemek, deduplication oncelik sistemini guncellemek, frontend'i yeni kaynaklara uyumlu hale getirmek ve Celery Worker'i Docker ortamina entegre etmek.

**Durum:** Tamamlandi

---

## Tamamlanan Prompt'lar

### 8.1 - Altyapi Hazirlik (Schema, Config, Bagimliliklar)
- [x] `PaperSource` enum'a `ARXIV`, `CROSSREF`, `CORE` degerleri eklendi
- [x] `SearchMeta`'ya `raw_arxiv`, `raw_crossref`, `raw_core` alanlari eklendi (default=0)
- [x] `config.py`'a `core_api_key: Optional[str] = None` eklendi
- [x] `pyproject.toml`'a `feedparser ^6.0.0` bagimliligi eklendi
- [x] `.env.example`'a `CORE_API_KEY=` eklendi
- [x] `docker-compose.yml`'a `CORE_API_KEY` env var eklendi
- [x] `models/library.py` `SourceType` enum'a `arxiv`, `crossref`, `core` eklendi
- [x] Alembic migration: `ALTER TYPE source_type ADD VALUE IF NOT EXISTS`
- [x] Frontend `types/api.ts`: `PaperSource` union type ve `SearchMeta` interface guncellendi
- [x] Frontend `ui-store.ts`: `searchMeta` state ve `setSearchMeta` action eklendi
- [x] Frontend `Sidebar.tsx`: 5 kaynak istatistigi ve filtre badge'leri eklendi

### 8.2 - arXiv Adapter
- [x] `adapters/arxiv.py` olusturuldu
- [x] arXiv API: `http://export.arxiv.org/api/query` (Atom/XML format)
- [x] `feedparser` ile XML parsing
- [x] `follow_redirects=True` (http->https yonlendirme)
- [x] Pagination: `start` + `max_results`, RESULTS_PER_PAGE=100, MAX_RESULTS=500
- [x] DOI cikarimi: `arxiv_doi` alani, fallback arXiv ID
- [x] PDF URL: links'ten `application/pdf` type
- [x] Venue: `arxiv_primary_category.term` (ornek: cs.LG)
- [x] Client-side yil ve citation filtresi
- [x] `adapters/__init__.py` guncellendi

### 8.3 - Crossref ve CORE Adapterleri
- [x] `adapters/crossref.py` olusturuldu
  - API: `https://api.crossref.org/works`
  - Polite Pool: User-Agent header ile email
  - Pagination: `offset` + `rows`, RESULTS_PER_PAGE=100, MAX_RESULTS=500
  - Server-side yil filtresi: `from-pub-date` / `until-pub-date`
  - Abstract XML tag temizleme (regex)
  - Citation count: `is-referenced-by-count`
- [x] `adapters/core.py` olusturuldu
  - API: `https://api.core.ac.uk/v3/search/works`
  - Bearer token auth (`CORE_API_KEY`)
  - API key yoksa bos liste + warning log
  - Pagination: `offset` + `limit`, RESULTS_PER_PAGE=100, MAX_RESULTS=500
  - `downloadUrl` -> `pdf_url`
  - DOI: `identifiers` array veya `doi` alani

### 8.4 - SearchService Guncelleme
- [x] 5 provider `self.providers` listesine eklendi
- [x] Meta sayim: provider sinif adina gore dinamik (`"Semantic" in provider_name`)
- [x] Deduplication oncelik sirasi guncellendi:
  1. Semantic Scholar (en zengin metadata)
  2. Crossref (en dogru DOI)
  3. arXiv (en guncel pre-print)
  4. OpenAlex
  5. CORE
- [x] `SOURCE_PRIORITY` dict ve `_has_higher_priority()` metodu eklendi

### 8.5 - Frontend Guncelleme
- [x] `PaperCard.tsx` badge renkleri:
  - SS: `border-blue-300 text-blue-600`
  - OA: `border-orange-300 text-orange-600`
  - arXiv: `bg-red-100 text-red-800 border-red-200`
  - CR: `bg-cyan-100 text-cyan-800 border-cyan-200`
  - CORE: `bg-purple-100 text-purple-600 border-purple-200`
- [x] `Sidebar.tsx` sourceStats: 5 kaynak icin dedup sonrasi sayim

### 8.6 - Celery Worker Docker Entegrasyonu
- [x] `docker-compose.yml`'e `celery_worker` servisi eklendi
  - Backend ile ayni Dockerfile
  - Command: `celery -A athena.core.celery_app worker --loglevel=info`
  - `athena_library` volume (PDF dosyalari icin)
  - RabbitMQ, Redis, PostgreSQL bagimliliklari
- [x] Backend servisine eklendi:
  - `CELERY_BROKER_URL` ve `CELERY_RESULT_BACKEND` env vars
  - `athena_library` volume
  - `DATA_DIR=/data/library`
- [x] Worker RabbitMQ'ya basariyla baglandi
- [x] PDF indirme pipeline dogrulandi (task received -> download -> completed)

---

## Mimari

### Adapter Pattern (5 Kaynak)

| Adapter | API URL | Auth | Pagination | Max |
|---------|---------|------|-----------|-----|
| SemanticScholarProvider | `graph/v1/paper/search` | x-api-key (opsiyonel) | offset+limit | 1000 |
| OpenAlexProvider | `api.openalex.org/works` | Polite Pool (email) | page+per_page | 500 |
| ArxivProvider | `export.arxiv.org/api/query` | Yok | start+max_results | 500 |
| CrossrefProvider | `api.crossref.org/works` | Polite Pool (email) | offset+rows | 500 |
| CoreProvider | `api.core.ac.uk/v3/search/works` | Bearer token | offset+limit | 500 |

### Deduplication Oncelik Sirasi

```
1. Semantic Scholar  (priority=1) - En zengin metadata
2. Crossref          (priority=2) - En dogru DOI
3. arXiv             (priority=3) - En guncel pre-print
4. OpenAlex          (priority=4)
5. CORE              (priority=5)
```

Ayni DOI veya title yakalandiginda yuksek oncelikli kaynak korunur.

### Docker Servisleri (Guncellenmis)

| Servis | Container | Aciklama |
|--------|-----------|----------|
| postgres_db | athena_postgres | PostgreSQL 16 |
| redis_cache | athena_redis | Redis 7 (cache + Celery result) |
| rabbitmq_broker | athena_rabbitmq | RabbitMQ 3 (message broker) |
| backend | athena_backend | FastAPI (uvicorn) |
| celery_worker | athena_celery_worker | Celery Worker (PDF indirme) |
| frontend | athena_frontend | React (nginx) |

### Shared Volume

```
athena_library:/data/library
  -> backend (task dispatch + dosya erisimi)
  -> celery_worker (PDF indirme + dosya yazma)
```

---

## Test Sonuclari

### Arama Sonuclari ("deep learning")

| Kaynak | Ham Sonuc | Dedup Sonrasi |
|--------|-----------|---------------|
| Semantic Scholar | 1000 | 1000 |
| OpenAlex | 1000 | 794 |
| arXiv | 500 | 491 |
| Crossref | 500 | 461 |
| CORE | 0 (API key yok) | 0 |
| **Duplikasyon elenen** | - | **254** |
| **Toplam** | **3000** | **2746** |

### Celery Worker

| Adim | Sonuc |
|------|-------|
| RabbitMQ baglantisi | Connected |
| Task alimi | download_paper_task received |
| PDF indirme | 200 OK (0.69s) |
| DB guncelleme | download_status: completed |

---

## Degisiklik Yapilan Dosyalar

### Backend
- `athena/schemas/search.py` - PaperSource enum + SearchMeta alanlari
- `athena/core/config.py` - core_api_key eklendi
- `athena/adapters/arxiv.py` - **YENi** arXiv adapter
- `athena/adapters/crossref.py` - **YENi** Crossref adapter
- `athena/adapters/core.py` - **YENi** CORE adapter
- `athena/adapters/__init__.py` - Yeni adapter export'lari
- `athena/services/search.py` - 5 provider + oncelikli deduplication
- `athena/models/library.py` - SourceType enum guncellendi
- `migrations/versions/ea63d692364c_add_new_source_types.py` - Enum migration
- `pyproject.toml` - feedparser bagimliligi

### Frontend
- `src/types/api.ts` - PaperSource, SearchMeta guncellendi
- `src/stores/ui-store.ts` - searchMeta state
- `src/services/search.ts` - SearchResponse return type
- `src/components/SearchForm.tsx` - data.results/meta ayirimi
- `src/components/PaperCard.tsx` - 5 kaynak badge rengi
- `src/components/Sidebar.tsx` - 5 kaynak istatistik + filtre

### Altyapi
- `docker-compose.yml` - celery_worker servisi + athena_library volume
- `.env.example` - CORE_API_KEY eklendi
