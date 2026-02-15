# Project Athena v2.0.0 - Claude Reference Document

## Proje Bilgileri
- **Versiyon**: 2.0.0-develop
- **Mimari**: Modüler Monolit
- **Python**: ^3.11
- **Framework**: FastAPI

## Branch Yapısı
- `main` - Production branch
- `fix/search-results-and-save-ux` - Eski fix branch (v1.0 ile ilgili)
- `v2.0.0-develop` - Aktif geliştirme branch'i (CURRENT)

## Sprint Dokümantasyonu
- [Sprint 0 - Proje Altyapısı](docs/sprint0.md)
- [Sprint 1 - Veritabanı Modelleri](docs/sprint1.md)
- [Sprint 2 - Arama Altyapısı](docs/sprint2.md)
- [Sprint 3 - Kütüphane Yönetimi](docs/sprint3.md)
- [Sprint 4 - Hata Yönetimi ve Loglama](docs/sprint4.md) ✅
- [Sprint 5 - Frontend Kurulumu](docs/sprint5.md) ✅
- [Sprint 6 - Frontend Entegrasyonu ve UX](docs/sprint6.md) ✅
- [Sprint 7 - Arama İyileştirmeleri ve UX Düzeltmeleri](docs/sprint7.md) ✅
- [Sprint 8 - Çoklu Kaynak Entegrasyonu](docs/sprint8.md) ✅
- [Sprint 9 - Docker Deployment Düzeltmeleri ve E2E Test](docs/sprint9.md) ✅
- [Sprint 10 - Arama Motoru Optimizasyonu](docs/sprint10.md) ✅
- [Sprint 11 - Kütüphane Filtreleme ve UX İyileştirmeleri](docs/sprint11.md) ⏳

## Dizin Yapısı

```
Project-Athena/
├── backend/
│   ├── athena/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v2/
│   │   │       ├── __init__.py
│   │   │       └── routers/
│   │   │           ├── __init__.py
│   │   │           ├── library.py
│   │   │           ├── search.py
│   │   │           └── system.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── exceptions.py
│   │   │   ├── logging.py
│   │   │   └── middleware.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── export.py
│   │   │   ├── library.py
│   │   │   └── search.py
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── downloader.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── arxiv.py
│   │   │   ├── base.py
│   │   │   ├── core.py
│   │   │   ├── crossref.py
│   │   │   ├── openalex.py
│   │   │   └── semantic.py
│   │   ├── repositories/
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── associations.py
│   │   │   ├── author.py
│   │   │   ├── library.py
│   │   │   ├── paper.py
│   │   │   └── tag.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── error.py
│   │       ├── library.py
│   │       └── search.py
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/            # ShadCN/UI bileşenleri (+ dialog, label)
│   │   │   ├── LibraryItem.tsx
│   │   │   ├── LibraryList.tsx
│   │   │   ├── PaperCard.tsx
│   │   │   ├── PaperDetail.tsx
│   │   │   ├── PaperList.tsx
│   │   │   ├── SearchForm.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── dashboard.tsx
│   │   │   └── settings.tsx
│   │   ├── layouts/
│   │   │   └── DashboardLayout.tsx
│   │   ├── lib/
│   │   │   ├── api.ts         # Axios client + request/response interceptor
│   │   │   ├── react-query.ts
│   │   │   └── utils.ts
│   │   ├── services/
│   │   │   ├── library.ts     # Library API service
│   │   │   └── search.ts      # Search API service
│   │   ├── stores/
│   │   │   └── ui-store.ts
│   │   ├── types/
│   │   │   └── api.ts         # TypeScript API interfaces
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── components.json
│   └── tsconfig.json
├── docs/
│   ├── sprint0.md
│   ├── sprint1.md
│   ├── sprint2.md
│   ├── sprint3.md
│   ├── sprint4.md
│   └── sprint5.md
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.frontend.conf
├── CLAUDE.md
└── GEMINI.md
```

## Modül Açıklamaları

| Modül | Açıklama |
|-------|----------|
| `api/v2/routers/` | FastAPI endpoint tanımları |
| `core/` | Yapılandırma, veritabanı, Celery, exception'lar, logging, middleware |
| `services/` | İş mantığı (business logic) |
| `tasks/` | Celery background task'ları |
| `adapters/` | Dış servis entegrasyonları (API provider'lar) |
| `repositories/` | Veritabanı erişim katmanı (CRUD operasyonları) |
| `models/` | SQLAlchemy ORM modelleri |
| `schemas/` | Pydantic şemaları (request/response) |

## Docker Servisleri

| Servis | Image | Port | Açıklama |
|--------|-------|------|----------|
| `postgres_db` | postgres:16-alpine | 5433:5432 | Ana veritabanı |
| `redis_cache` | redis:7-alpine | 6379 | Cache ve Celery result backend |
| `rabbitmq_broker` | rabbitmq:3-management-alpine | 5672, 15672 | Message broker (15672: Yönetim paneli) |
| `backend` | Dockerfile.backend | 8000 | FastAPI backend (uvicorn) |
| `celery_worker` | Dockerfile.backend | - | Celery Worker (PDF indirme) |
| `frontend` | Dockerfile.frontend | 3000:80 | React frontend (nginx) |

### Docker Komutları
```bash
# Tüm servisleri başlat (build dahil)
docker-compose up -d --build

# Orphan container'ları temizle
docker-compose up -d --remove-orphans

# Sadece altyapı servislerini başlat (development)
docker-compose up -d postgres_db redis_cache rabbitmq_broker

# Logları izle
docker-compose logs -f backend frontend

# Sağlık kontrolü
docker-compose ps

# RabbitMQ yönetim paneli
# http://localhost:15672
```

### Docker Dosyaları
| Dosya | Açıklama |
|-------|----------|
| `Dockerfile.backend` | Python 3.11 + Poetry 1.8.5 + uvicorn |
| `Dockerfile.frontend` | Node 20 (build) + nginx (serve) multi-stage |
| `nginx.frontend.conf` | SPA routing + /api proxy to backend (180s timeout) |

## Core Modül Detayları

### config.py
- `Settings` sınıfı: Pydantic `BaseSettings` ile .env'den yapılandırma okur
- `get_settings()`: Cached settings instance döner

**API Ayarları (.env):**
| Ayar | Açıklama |
|------|----------|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API key (rate limit artırır) |
| `OPENALEX_EMAIL` | OpenAlex Polite Pool için email |
| `UNPAYWALL_EMAIL` | Unpaywall API için email |
| `OPENAI_API_KEY` | OpenAI API key |
| `CORE_API_KEY` | CORE API key (opsiyonel, https://core.ac.uk/services/api) |

### database.py
- `engine`: AsyncEngine (asyncpg sürücüsü)
- `async_session_factory`: AsyncSession factory
- `Base`: SQLAlchemy 2.0 DeclarativeBase (tüm modeller buradan türetilir)
- `get_db()`: FastAPI Dependency Injection için async generator

## Alembic (Database Migrations)

### Komutlar
```bash
cd backend

# Yeni migration oluştur (autogenerate)
poetry run alembic revision --autogenerate -m "description"

# Migration'ları uygula
poetry run alembic upgrade head

# Migration'ları geri al
poetry run alembic downgrade -1

# Mevcut durumu göster
poetry run alembic current

# Migration geçmişini göster
poetry run alembic history
```

### Yapılandırma
- `alembic.ini`: Alembic konfigürasyonu (URL env.py'dan alınır)
- `migrations/env.py`: Async migration desteği, Base.metadata kullanır
- `migrations/versions/`: Migration dosyaları

```python
# Kullanım örneği
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from athena.core.database import get_db

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

## API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/` | Root endpoint |
| GET | `/api/v2/health` | Health check (DB + Redis) |
| POST | `/api/v2/search` | Makale araması → SearchResponse{results, meta} |
| POST | `/api/v2/library/ingest` | Makaleyi kütüphaneye ekle (tekli) |
| POST | `/api/v2/library/ingest/bulk` | Toplu makale ekleme (duplikasyon kontrolü, max 100) |
| POST | `/api/v2/library/check` | Kütüphanede kayıtlı makale kontrolü (DOI, max 5000) |
| GET | `/api/v2/library` | Kütüphane listesi (pagination + filter) |
| POST | `/api/v2/library/retry-downloads` | Takılı indirmeleri tekrar kuyruğa ekle |
| GET | `/api/v2/library/export` | Kütüphane dışa aktarma (CSV/XLSX) |
| POST | `/api/v2/system/reset` | Sistem sıfırlama (DİKKAT!) |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

### Health Check Response
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "2.0.0"
}
```

## Bağımlılıklar

### Production
- fastapi ^0.109.0
- uvicorn[standard] ^0.27.0
- sqlalchemy[asyncio] ^2.0.25
- asyncpg ^0.29.0
- pydantic-settings ^2.1.0
- redis ^5.0.1
- aio-pika ^9.4.0
- loguru ^0.7.2
- alembic ^1.13.0
- httpx ^0.27.0
- celery[redis] ^5.3.0
- aiofiles ^23.2.0
- psycopg2-binary ^2.9.9
- pandas ^2.2.0
- openpyxl ^3.1.0
- feedparser ^6.0.0

### Development
- pytest ^8.0.0
- pytest-asyncio ^0.23.0
- black ^24.1.0
- isort ^5.13.0

## Geliştirme Notları

### Prompt 0.1 (Tamamlandı)
- [x] Dizin yapısı oluşturuldu
- [x] Poetry (pyproject.toml) yapılandırıldı
- [x] CLAUDE.md referans dosyası oluşturuldu

### Prompt 0.2 (Tamamlandı)
- [x] docker-compose.yml oluşturuldu
- [x] PostgreSQL 16 (alpine) servisi tanımlandı
- [x] Redis 7 (alpine) cache servisi tanımlandı
- [x] RabbitMQ 3 (management-alpine) broker servisi tanımlandı
- [x] .env.example güncellendi (RABBITMQ credentials, service hostnames)

### Prompt 0.3 (Tamamlandı)
- [x] core/config.py oluşturuldu (Pydantic BaseSettings)
- [x] core/database.py oluşturuldu (SQLAlchemy Async)
- [x] AsyncEngine ve AsyncSession yapılandırıldı
- [x] get_db() Dependency Injection fonksiyonu yazıldı
- [x] Base (DeclarativeBase) SQLAlchemy 2.0 style tanımlandı

### Prompt 0.4 (Tamamlandı) - Sprint 0 DoD
- [x] main.py oluşturuldu (FastAPI app + CORS middleware)
- [x] api/v2/routers/system.py oluşturuldu
- [x] GET /api/v2/health endpoint'i yazıldı (DB + Redis check)
- [x] Router main.py'a /api/v2 prefix ile include edildi

---

## Sprint 1

### Prompt 1.1 (Tamamlandı)
- [x] Alembic bağımlılığı eklendi (^1.13.0)
- [x] `alembic init -t async migrations` ile async migration yapısı oluşturuldu
- [x] `alembic.ini` düzenlendi (URL env.py'dan alınacak)
- [x] `migrations/env.py` düzenlendi:
  - sys.path ayarlandı
  - `athena.core.config` ve `athena.core.database` import edildi
  - `target_metadata = Base.metadata` ayarlandı
  - URL `settings.database_url`'den alınıyor

### Prompt 1.2 (Tamamlandı)
- [x] `models/associations.py` oluşturuldu (paper_authors, library_tags)
- [x] `models/paper.py` oluşturuldu (Paper modeli)
- [x] `models/author.py` oluşturuldu (Author modeli)
- [x] `models/library.py` oluşturuldu (LibraryEntry, SourceType, DownloadStatus)
- [x] `models/tag.py` oluşturuldu (Tag modeli)
- [x] `models/__init__.py` güncellendi (tüm modeller export)
- [x] `migrations/env.py` güncellendi (modeller import edildi)

## SQLAlchemy Modelleri

### Paper
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | Integer | Primary Key |
| doi | String(255) | DOI (unique, nullable) |
| title | Text | Makale başlığı |
| title_slug | String(255) | URL-friendly başlık |
| abstract | Text | Özet (nullable) |
| year | Integer | Yayın yılı (nullable) |
| citation_count | Integer | Atıf sayısı (default: 0) |
| venue | String(500) | Yayınlandığı yer (nullable) |
| pdf_url | String(1000) | PDF URL'i (nullable) |
| created_at | DateTime | Oluşturulma tarihi |

### Author
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | Integer | Primary Key |
| name | String(255) | Yazar adı |
| slug | String(255) | URL-friendly isim (indexed) |

### LibraryEntry
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | Integer | Primary Key |
| paper_id | Integer | FK → papers.id (unique, CASCADE) |
| source | SourceType | semantic, openalex, manual |
| download_status | DownloadStatus | pending, downloading, completed, failed |
| file_path | String(500) | PDF dosya yolu (nullable) |
| is_favorite | Boolean | Favori mi (default: False) |

### Tag
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | Integer | Primary Key |
| name | String(100) | Tag adı (unique) |

### İlişkiler (Relationships)
- **Paper ↔ Author**: Many-to-Many (paper_authors tablosu)
- **Paper → LibraryEntry**: One-to-One
- **LibraryEntry ↔ Tag**: Many-to-Many (library_tags tablosu)

### Prompt 1.3 (Tamamlandı) - Sprint 1 DoD ✅
- [x] Migration oluşturuldu: `create_initial_tables`
- [x] Migration uygulandı: `alembic upgrade head`
- [x] Veritabanı tabloları doğrulandı:
  - `papers`, `authors`, `tags`
  - `library_entries`
  - `paper_authors`, `library_tags` (association tables)
  - `alembic_version` (migration tracking)

---

## Sprint 2

### Prompt 2.1 (Tamamlandı)
- [x] `schemas/search.py` oluşturuldu
- [x] `PaperSource` enum tanımlandı (semantic, openalex, manual)
- [x] `AuthorSchema` Pydantic modeli oluşturuldu
- [x] `PaperResponse` Pydantic modeli oluşturuldu
- [x] `SearchFilters` Pydantic modeli oluşturuldu
- [x] `schemas/__init__.py` güncellendi (tüm şemalar export)

### Prompt 2.2 (Tamamlandı)
- [x] `adapters/base.py` oluşturuldu
- [x] `BaseSearchProvider` ABC (Abstract Base Class) tanımlandı
- [x] `search(filters: SearchFilters) -> list[PaperResponse]` soyut metod tanımlandı
- [x] `adapters/__init__.py` güncellendi

### Prompt 2.3 (Tamamlandı)
- [x] `httpx` bağımlılığı eklendi (^0.27.0)
- [x] `adapters/semantic.py` oluşturuldu
- [x] `SemanticScholarProvider` sınıfı implement edildi
- [x] API endpoint: `https://api.semanticscholar.org/graph/v1/paper/search`
- [x] Fields: `title,abstract,year,citationCount,venue,authors,externalIds,openAccessPdf`
- [x] Client-side filtreleme (year_start, year_end, min_citations)
- [x] Hata yönetimi (429, 500 → boş liste + log)

### Prompt 2.4 (Tamamlandı)
- [x] `core/config.py`'a `contact_email` ayarı eklendi
- [x] `adapters/openalex.py` oluşturuldu
- [x] `OpenAlexProvider` sınıfı implement edildi
- [x] API endpoint: `https://api.openalex.org/works`
- [x] Polite Pool: User-Agent header'ında email gönderiliyor
- [x] Nested mapping: `authorships[].author.display_name`, `best_oa_location.pdf_url`
- [x] Client-side filtreleme (year_start, year_end, min_citations)

### Prompt 2.5 (Tamamlandı)
- [x] `services/search.py` oluşturuldu
- [x] `SearchService` sınıfı implement edildi
- [x] `asyncio.gather` ile paralel arama
- [x] Sonuçları flatten (tek liste)
- [x] Deduplication: DOI veya title bazlı tekilleştirme
- [x] Öncelik: Semantic Scholar sonuçları korunur

### Prompt 2.6 (Tamamlandı) - Sprint 2 DoD ✅
- [x] `api/v2/routers/search.py` oluşturuldu
- [x] `POST /api/v2/search` endpoint'i tanımlandı
- [x] Request Body: `SearchFilters`
- [x] Response: `List[PaperResponse]`
- [x] `routers/__init__.py` güncellendi
- [x] Router `main.py`'a include edildi

## Adapter Pattern

### BaseSearchProvider (ABC)
```python
from athena.adapters import BaseSearchProvider

class MySearchProvider(BaseSearchProvider):
    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        # Implementation here
        pass
```

| Metod | Parametreler | Dönüş Tipi | Açıklama |
|-------|--------------|------------|----------|
| `search` | `filters: SearchFilters` | `list[PaperResponse]` | Soyut arama metodu |

### SemanticScholarProvider (Standard Search)
| Özellik | Değer |
|---------|-------|
| Base URL | `https://api.semanticscholar.org/graph/v1/paper/search` |
| Results Per Page | 100 (offset + limit pagination) |
| Max Results | 1000 |
| Timeout | 60 saniye |
| Sort | API varsayılan keyword relevance sıralaması |
| Server-side Filters | `year`, `minCitationCount` |
| Rate Limit | `asyncio.sleep(0.5)` istekler arası |
| API Key | `x-api-key` header (opsiyonel, rate limit artırır) |
| Hata Yönetimi | HTTP hata → o ana kadar toplanan kısmi sonuçlar döner |

### OpenAlexProvider (Cursor Pagination)
| Özellik | Değer |
|---------|-------|
| Base URL | `https://api.openalex.org/works` |
| Results Per Page | 100 (cursor bazlı pagination) |
| Max Results | 1000 |
| Timeout | 60 saniye |
| Cursor | İlk: `cursor=*`, sonraki: `meta.next_cursor` |
| Server-side Filters | `publication_year` (filter parametresi) |
| Rate Limit | 100 req/s, search 1000 kredi/istek (günde 100K free) |
| Polite Pool | User-Agent: `Athena/2.0 (mailto:contact_email)` |
| Abstract | `abstract_inverted_index` → düz metin dönüşümü |

### ArxivProvider
| Özellik | Değer |
|---------|-------|
| Base URL | `http://export.arxiv.org/api/query` |
| Results Per Page | 100 |
| Max Results | 1000 |
| Timeout | 60 saniye |
| Format | Atom/XML (feedparser ile parse) |
| Pagination | `start` + `max_results` parametreleri |
| Rate Limit | `asyncio.sleep(0.5)` istekler arası |
| Auth | Yok |
| DOI | `arxiv_doi` alanı, fallback: arXiv ID |
| PDF | Links'ten `application/pdf` type |
| Venue | `arxiv_primary_category.term` (örn: cs.LG) |

### CrossrefProvider
| Özellik | Değer |
|---------|-------|
| Base URL | `https://api.crossref.org/works` |
| Results Per Page | 100 |
| Max Results | 1000 |
| Timeout | 60 saniye |
| Pagination | `offset` + `rows` parametreleri |
| Rate Limit | `asyncio.sleep(0.5)` istekler arası |
| Polite Pool | User-Agent: `Athena/2.0 (mailto:email)` |
| Server-side Filters | `from-pub-date`, `until-pub-date` |
| Citation Count | `is-referenced-by-count` |
| DOI | Her zaman mevcut |

### CoreProvider
| Özellik | Değer |
|---------|-------|
| Base URL | `https://api.core.ac.uk/v3/search/works` |
| Results Per Page | 100 |
| Max Results | 1000 |
| Timeout | 60 saniye |
| Pagination | `offset` + `limit` parametreleri |
| Rate Limit | `asyncio.sleep(0.5)` istekler arası |
| Auth | Bearer token (`CORE_API_KEY`) |
| API Key yoksa | Boş liste + warning log |
| PDF | `downloadUrl` alanı |
| DOI | `identifiers` array veya `doi` alanı |

## Service Layer

### SearchService
```python
from athena.services import SearchService
from athena.schemas import SearchFilters

service = SearchService()
results = await service.search_papers(SearchFilters(query="machine learning"))
```

| Metod | Açıklama |
|-------|----------|
| `search_papers(filters)` | Paralel arama + deduplication |

**Deduplication Pipeline:**
1. Keyword Relevance Filter: Virgülle ayrılan konsept grupları AND mantığıyla filtrelenir (her gruptan en az 1 kelime geçmeli)
2. DOI Dedup: DOI bazlı tekilleştirme (hash O(1))
3. Normalized Title Dedup: `_normalize_title()` ile agresif temizleme + hash O(1)
   - Unicode → ASCII, noktalama kaldır, stop word temizle
- Çakışma → Öncelik sırası: 1.Semantic Scholar 2.Crossref 3.arXiv 4.OpenAlex 5.CORE

**Hata Toleransı:**
- `asyncio.gather(*tasks, return_exceptions=True)` ile paralel arama
- Bir provider hata verirse diğerleri etkilenmez
- Hata veren provider `logger.error()` ile loglanır, `meta.errors` listesine eklenir

## Pydantic Şemaları (DTO)

### PaperSource (Enum)
| Değer | Açıklama |
|-------|----------|
| `semantic` | Semantic Scholar |
| `openalex` | OpenAlex |
| `arxiv` | arXiv |
| `crossref` | Crossref |
| `core` | CORE |
| `manual` | Manuel ekleme |

### AuthorSchema
| Alan | Tip | Açıklama |
|------|-----|----------|
| name | str | Yazar adı |

### PaperResponse
| Alan | Tip | Açıklama |
|------|-----|----------|
| title | str | Makale başlığı |
| abstract | str \| None | Özet |
| year | int \| None | Yayın yılı |
| citation_count | int | Atıf sayısı (default: 0) |
| venue | str \| None | Yayınlandığı yer |
| authors | list[AuthorSchema] | Yazarlar listesi |
| source | PaperSource | Veri kaynağı |
| external_id | str \| None | DOI veya kaynak ID |
| pdf_url | str \| None | PDF URL'i |

### SearchFilters
| Alan | Tip | Açıklama |
|------|-----|----------|
| query | str | Arama sorgusu (zorunlu, min 1 karakter) |
| year_start | int \| None | Başlangıç yılı (1900-2100) |
| year_end | int \| None | Bitiş yılı (1900-2100) |
| min_citations | int \| None | Minimum atıf sayısı (>=0) |

### SearchMeta
| Alan | Tip | Açıklama |
|------|-----|----------|
| raw_semantic | int | Semantic Scholar ham sonuç sayısı |
| raw_openalex | int | OpenAlex ham sonuç sayısı |
| raw_arxiv | int | arXiv ham sonuç sayısı |
| raw_crossref | int | Crossref ham sonuç sayısı |
| raw_core | int | CORE ham sonuç sayısı |
| duplicates_removed | int | Elenen mükerrer sonuç sayısı |
| total | int | Dedup sonrası toplam sonuç sayısı |
| errors | list[str] | Hata veren kaynak bilgileri (boş ise hata yok) |

### SearchResponse
| Alan | Tip | Açıklama |
|------|-----|----------|
| results | list[PaperResponse] | Tekilleştirilmiş makale listesi |
| meta | SearchMeta | Ham/dedup istatistikleri |

---

## Sprint 3

### Prompt 3.1 (Tamamlandı)
- [x] `services/library.py` oluşturuldu
- [x] `LibraryService` sınıfı implement edildi
- [x] `add_paper_to_library(paper_data, search_query)` metodu
- [x] Deduplication: DOI veya title_slug ile kontrol
- [x] Auto-tagging: search_query'den virgülle ayrılmış etiketler
- [x] `slugify()` helper fonksiyonu

### LibraryService
```python
from athena.services import LibraryService
from athena.core.database import get_db

async def save_paper(db: AsyncSession):
    service = LibraryService(db)
    entry = await service.add_paper_to_library(paper_data, "machine learning, AI")
```

| Metod | Açıklama |
|-------|----------|
| `add_paper_to_library(paper_data, search_query)` | Makaleyi kütüphaneye ekler |

**İş Mantığı:**
1. DOI/title_slug ile deduplication
2. Paper + Author kayıtları oluştur
3. LibraryEntry oluştur (source, download_status=pending)
4. Auto-tagging (virgülle ayrılmış terimler)

### Prompt 3.2 (Tamamlandı)
- [x] `core/celery_app.py` oluşturuldu
- [x] `tasks/__init__.py` oluşturuldu
- [x] `tasks/downloader.py` oluşturuldu
- [x] `download_paper_task` Celery task'i implement edildi
- [x] Paper modeline `pdf_url` alanı eklendi
- [x] LibraryService `pdf_url`'i kaydetmek üzere güncellendi
- [x] Yeni bağımlılıklar: `celery[redis]`, `aiofiles`, `psycopg2-binary`

## Celery

### Yapılandırma
```python
from athena.core.celery_app import celery_app
```

| Ayar | Değer |
|------|-------|
| Broker | RabbitMQ (amqp://rabbitmq_broker:5672) |
| Result Backend | Redis (redis://redis_cache:6379/0) |
| Serializer | JSON |
| Timezone | UTC |

### Worker Başlatma
```bash
cd backend
poetry run celery -A athena.core.celery_app worker --loglevel=info
```

### Download Task
```python
from athena.tasks.downloader import download_paper_task

# Task'i kuyruğa ekle
download_paper_task.delay(entry_id=123)
```

| Parametre | Açıklama |
|-----------|----------|
| `entry_id` | LibraryEntry ID |

**Task Özellikleri:**
- Auto-retry: HTTP hataları için otomatik yeniden deneme
- Exponential backoff: 600 saniyeye kadar artan bekleme süresi
- Max retries: 5
- User-Agent rotasyonu: 5 farklı browser User-Agent'ı
- Dosya yolu formatı: `{data_dir}/{paper_id}/{year}_{author_slug}_{title_slug}.pdf`

**Status Durumları:**
| Durum | Açıklama |
|-------|----------|
| `pending` | İndirme bekliyor |
| `downloading` | İndirme devam ediyor |
| `completed` | Başarıyla tamamlandı |
| `failed` | Başarısız (max retry aşıldı veya PDF URL yok) |

### Prompt 3.3 (Tamamlandı)
- [x] `api/v2/routers/library.py` oluşturuldu
- [x] `POST /api/v2/library/ingest` endpoint'i tanımlandı
- [x] `IngestRequest` schema: paper (PaperResponse) + search_query (str)
- [x] `IngestResponse` schema: status + entry_id
- [x] LibraryService.add_paper_to_library çağrısı
- [x] download_paper_task.delay(entry_id) tetikleme
- [x] Router main.py'a include edildi

### Library API

#### POST /api/v2/library/ingest
Makaleyi kütüphaneye ekler ve PDF indirme görevini başlatır.

**Request Body:**
```json
{
  "paper": {
    "title": "Machine Learning for NLP",
    "abstract": "...",
    "year": 2024,
    "citation_count": 100,
    "venue": "ACL",
    "authors": [{"name": "John Doe"}],
    "source": "semantic",
    "external_id": "10.1234/example",
    "pdf_url": "https://example.com/paper.pdf"
  },
  "search_query": "machine learning, nlp"
}
```

**Response:**
```json
{
  "status": "queued",
  "entry_id": 123
}
```

#### GET /api/v2/library
Kütüphanedeki makaleleri listeler (pagination ve filtreleme destekli).

**Query Parameters:**
| Parametre | Tip | Default | Açıklama |
|-----------|-----|---------|----------|
| `page` | int | 1 | Sayfa numarası |
| `limit` | int | 20 | Sayfa başına öğe sayısı (max 100) |
| `tag` | str | - | Etikete göre filtrele |
| `status` | str | - | İndirme durumuna göre filtrele (pending, completed, failed) |
| `min_citations` | int | - | Minimum atıf sayısı filtresi (>=0) |
| `year_start` | int | - | Başlangıç yılı filtresi (1900-2100) |
| `year_end` | int | - | Bitiş yılı filtresi (1900-2100) |
| `search` | str | - | Başlık, yazar veya etiket araması |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "source": "semantic",
      "download_status": "pending",
      "file_path": null,
      "is_favorite": false,
      "tags": [{"id": 1, "name": "machine learning"}],
      "paper": {
        "id": 1,
        "title": "Paper Title",
        "abstract": "...",
        "year": 2024,
        "citation_count": 100,
        "venue": "ACL",
        "doi": "10.1234/example",
        "pdf_url": "https://...",
        "authors": [{"name": "John Doe"}],
        "created_at": "2024-01-01T00:00:00Z"
      }
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

### Prompt 3.4 (Tamamlandı) - Sprint 3 DoD ✅
- [x] `schemas/library.py` oluşturuldu
- [x] `LibraryEntrySchema`, `LibraryListResponse`, `PaperDetailSchema`, `TagSchema` tanımlandı
- [x] `GET /api/v2/library` endpoint'i eklendi
- [x] Pagination: `page`, `limit` parametreleri
- [x] Filtreleme: `tag`, `status` parametreleri
- [x] SQLAlchemy `joinedload` ile N+1 sorgu önlendi

---

## Sprint 4

### Prompt 4.1 (Tamamlandı)
- [x] `core/exceptions.py` güncellendi
- [x] `ErrorCode` enum tanımlandı (PROVIDER_TIMEOUT, DOWNLOAD_NO_PDF_URL, vb.)
- [x] `AthenaError` base class oluşturuldu
- [x] `ProviderError`, `LibraryError`, `ValidationError`, `DownloadError` sınıfları
- [x] `schemas/error.py` oluşturuldu (ErrorDetail, ErrorResponse)
- [x] Global exception handler'lar main.py'a eklendi

### Prompt 4.2 (Tamamlandı)
- [x] `core/logging.py` oluşturuldu (Loguru yapılandırması)
- [x] `core/middleware.py` oluşturuldu (RequestLoggingMiddleware)
- [x] `config.py`'a `log_level` ayarı eklendi
- [x] Production: JSON format log output
- [x] Development: Renkli console output
- [x] Her istek için unique `request_id` (UUID)
- [x] Process time ölçümü (milliseconds)
- [x] Correlation ID: Hata yanıtlarına `request_id` eklendi
- [x] `X-Request-ID` response header eklendi
- [x] `core/__init__.py` güncellendi (yeni export'lar)

### Prompt 4.3 (Tamamlandı)
- [x] `services/export.py` oluşturuldu (ExportService)
- [x] `pandas` ve `openpyxl` bağımlılıkları eklendi
- [x] `GET /api/v2/library/export` endpoint'i eklendi
- [x] CSV ve XLSX format desteği
- [x] Tag filtresi ile filtreleme
- [x] StreamingResponse ile dosya indirme
- [x] TDD Bölüm 3.5'e uygun sütunlar

### Prompt 4.4 (Tamamlandı) - Sprint 4 DoD ✅
- [x] `POST /api/v2/system/reset` endpoint'i eklendi
- [x] Güvenlik kontrolü: "DELETE-ALL-DATA" onay kodu
- [x] Yanlış kod → 403 Forbidden
- [x] Veritabanı temizleme: TRUNCATE CASCADE
- [x] Dosya temizleme: /data/library/ klasörü
- [x] CRITICAL seviyesinde loglama

---

## Sprint 5

### Prompt 5.1 (Tamamlandı)
- [x] `frontend/` dizininde Vite + React + TypeScript projesi oluşturuldu
- [x] Tailwind CSS v3, postcss, autoprefixer kuruldu ve yapılandırıldı
- [x] `tsconfig.json` ve `vite.config.ts` dosyalarına `@/*` path alias'ı eklendi
- [x] ShadCN/UI projesi başlatıldı ve temel bileşenler eklendi (button, input, card, etc.)
- [x] Vite config'e `/api` için proxy ayarı eklendi

### Prompt 5.2 (Tamamlandı)
- [x] State management ve routing için bağımlılıklar eklendi (`react-query`, `zustand`, `react-router-dom`)
- [x] `react-router-dom` ile temel sayfa yönlendirmesi (`/` ve `/settings`) yapıldı
- [x] `react-query` için `QueryClient` oluşturuldu ve `main.tsx`'e eklendi
- [x] `zustand` ile `ui-store` oluşturuldu (`isSidebarOpen`, `activeTab`)

### Prompt 5.3 (Tamamlandı)
- [x] Axios kurulumu ve yapılandırması (`src/lib/api.ts`)
- [x] Response interceptor (global error handling + toast notifications)
- [x] TypeScript interfaces (`src/types/api.ts`) - Backend Pydantic modelleri ile uyumlu
- [x] Search service (`src/services/search.ts`)
- [x] `sonner.tsx` düzeltildi (next-themes bağımlılığı kaldırıldı)

### Prompt 5.4 (Tamamlandı)
- [x] `DashboardLayout.tsx` - 3 sütunlu Zotero-like layout
- [x] Sidebar (240px) + Paper List (320px) + Detail Panel (flex)
- [x] Responsive tasarım (sidebar collapse desteği)

### Prompt 5.5 (Tamamlandı) - Sprint 5 DoD ✅
- [x] `SearchForm.tsx` - Arama formu (useMutation ile)
- [x] `PaperCard.tsx` - Paper kart bileşeni
- [x] `PaperList.tsx` - Liste bileşeni (Loading/Empty/Success states)
- [x] `PaperDetail.tsx` - Detail panel (seçili makale görüntüleme)
- [x] `Sidebar.tsx` - Navigation + SearchForm entegrasyonu
- [x] UI Store güncellendi (`selectedPaperId`, `searchResults`, `isSearching`)
- [x] Docker container'lar (frontend + backend) oluşturuldu ve test edildi

## Error Handling

### Hata Kodları (ErrorCode)
| Kod | Açıklama |
|-----|----------|
| `INTERNAL_ERROR` | Beklenmeyen sunucu hatası |
| `VALIDATION_ERROR` | Veri doğrulama hatası |
| `NOT_FOUND` | Kaynak bulunamadı |
| `PROVIDER_TIMEOUT` | Dış servis zaman aşımı |
| `PROVIDER_RATE_LIMIT` | API rate limit aşıldı |
| `PROVIDER_UNAVAILABLE` | Dış servis kullanılamıyor |
| `LIBRARY_DUPLICATE` | Makale zaten kütüphanede |
| `LIBRARY_NOT_FOUND` | Kütüphane kaydı bulunamadı |
| `DOWNLOAD_NO_PDF_URL` | PDF URL'i yok |
| `DOWNLOAD_FAILED` | İndirme başarısız |

### Standart Hata Yanıtı
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "İstek verisi doğrulanamadı",
    "suggestion": "Lütfen gönderdiğiniz verileri kontrol edin",
    "details": "body -> query: Field required"
  }
}
```

### Exception Sınıfları
```python
from athena.core.exceptions import (
    AthenaError,
    ProviderError,
    LibraryError,
    ValidationError,
    DownloadError,
    ErrorCode,
)

# Kullanım örneği
raise ProviderError(
    code=ErrorCode.PROVIDER_TIMEOUT,
    message="Semantic Scholar yanıt vermedi",
    suggestion="Lütfen birkaç dakika sonra tekrar deneyin",
    details="Timeout after 30s",
)
```

## Structured Logging

### Yapılandırma
```python
from athena.core.logging import setup_logging

# Uygulama başlatılırken çağrılır
setup_logging()
```

| Mod | Log Format | Açıklama |
|-----|------------|----------|
| Development (`debug=True`) | Renkli console | Okunabilir, renkli çıktı |
| Production (`debug=False`) | JSON | Yapısal, parse edilebilir |

### Log Level Ayarı (.env)
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Request Logging Middleware
Her HTTP isteği için otomatik loglama:

| Alan | Açıklama |
|------|----------|
| `request_id` | Unique UUID (correlation için) |
| `method` | HTTP method (GET, POST, vb.) |
| `path` | İstek path'i |
| `status_code` | Response status kodu |
| `process_time_ms` | İstek süresi (ms) |
| `client_ip` | Client IP adresi |

### Correlation ID
- Her istek için `X-Request-ID` response header eklenir
- Hata yanıtlarında `request_id` alanı bulunur
- Log'larda `request_id` ile filtreleme yapılabilir

**Örnek Hata Yanıtı:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "İstek verisi doğrulanamadı",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Context Variables
```python
from athena.core.logging import get_request_id, set_request_id, clear_request_id

# Mevcut request_id'yi al
request_id = get_request_id()

# Manuel set etme (middleware otomatik yapar)
set_request_id("my-custom-id")
```

## Library Export

### ExportService
```python
from athena.services import ExportService

service = ExportService(db)
buffer, content_type, filename = await service.export_library(
    format="xlsx",  # veya "csv"
    search_query="deep learning, nlp",  # opsiyonel tag filtresi
)
```

### GET /api/v2/library/export

Kütüphane verilerini CSV veya XLSX formatında dışa aktarır.

**Query Parameters:**
| Parametre | Tip | Default | Açıklama |
|-----------|-----|---------|----------|
| `format` | string | xlsx | Çıktı formatı: "csv" veya "xlsx" |
| `search_query` | string | - | Etiket filtresi (virgülle ayrılmış) |

**Response Headers:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="athena_library_export.xlsx"
```

**Export Sütunları (TDD Bölüm 3.5):**
| Sütun | Açıklama |
|-------|----------|
| ID | LibraryEntry ID |
| Title | Makale başlığı |
| Authors | Yazarlar (virgülle ayrılmış) |
| Year | Yayın yılı |
| Venue | Yayınlandığı yer |
| DOI | Digital Object Identifier |
| Citation Count | Atıf sayısı |
| Source | Veri kaynağı (semantic, openalex, manual) |
| Tags | Etiketler (virgülle ayrılmış) |

## System Reset

### POST /api/v2/system/reset

⚠️ **DİKKAT:** Bu işlem geri alınamaz! Tüm veriler silinir.

**Request Body:**
```json
{
  "confirmation": "DELETE-ALL-DATA"
}
```

**Success Response:**
```json
{
  "status": "system_reset_completed",
  "deleted_files_count": 15
}
```

**Error Response (403 Forbidden):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Geçersiz onay kodu. Sistemi sıfırlamak için 'DELETE-ALL-DATA' girin.",
    "request_id": "..."
  }
}
```

**Temizlenen Veriler:**
| Kaynak | Temizleme Yöntemi |
|--------|-------------------|
| `library_tags` | TRUNCATE CASCADE |
| `paper_authors` | TRUNCATE CASCADE |
| `library_entries` | TRUNCATE CASCADE |
| `papers` | TRUNCATE CASCADE |
| `authors` | TRUNCATE CASCADE |
| `tags` | TRUNCATE CASCADE |
| `/data/library/*` | Dosya silme |

---
*Son Güncelleme: Sprint 7 Tamamlandı - 2026-02-14*

---

## Frontend (React + Vite)

### Dizin Yapısı
```
frontend/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── ui/                    # ShadCN/UI bileşenleri (+ dialog, label)
│   │   ├── LibraryItem.tsx        # Kütüphane kart bileşeni
│   │   ├── LibraryList.tsx        # Kütüphane liste bileşeni
│   │   ├── PaperCard.tsx          # Paper kart + Ekle butonu
│   │   ├── PaperDetail.tsx        # Detail panel + PDF Viewer
│   │   ├── PaperList.tsx          # Paper listesi
│   │   ├── SearchForm.tsx         # Arama formu
│   │   ├── Sidebar.tsx            # Sol panel + kütüphane filtreleri
│   │   ├── dashboard.tsx
│   │   └── settings.tsx           # API Key, Export, Danger Zone
│   ├── layouts/
│   │   └── DashboardLayout.tsx    # 3-sütunlu Zotero-like layout
│   ├── lib/
│   │   ├── api.ts                 # Axios client + request/response interceptor
│   │   ├── react-query.ts         # QueryClient yapılandırması
│   │   └── utils.ts               # ShadCN cn() helper
│   ├── services/
│   │   ├── library.ts             # Library API (fetchLibrary, ingestPaper)
│   │   └── search.ts              # Search API service
│   ├── stores/
│   │   └── ui-store.ts            # Zustand UI store (genişletilmiş)
│   ├── types/
│   │   └── api.ts                 # TypeScript API interfaces
│   ├── App.tsx                    # Router yapılandırması
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Tailwind + CSS Variables
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
└── components.json                # ShadCN yapılandırması
```

### Teknoloji Stack
| Kategori | Teknoloji | Versiyon |
|----------|-----------|----------|
| Framework | React | 19.x |
| Build Tool | Vite | 7.x |
| Dil | TypeScript | 5.x |
| UI Kit | ShadCN/UI | latest |
| Styling | Tailwind CSS | 3.x |
| Icons | Lucide React | latest |
| State (Server) | React Query | 5.x |
| State (Client) | Zustand | 5.x |
| Routing | React Router DOM | 7.x |

### ShadCN/UI Bileşenleri
| Bileşen | Açıklama |
|---------|----------|
| `button` | Buton bileşeni |
| `input` | Input alanı |
| `card` | Kart bileşeni |
| `badge` | Etiket/rozet |
| `separator` | Ayırıcı çizgi |
| `scroll-area` | Kaydırılabilir alan |
| `skeleton` | Yükleme placeholder'ı |
| `sonner` | Toast bildirimleri |
| `dialog` | Modal dialog |
| `label` | Form label |

### Komutlar
```bash
cd frontend

# Bağımlılıkları yükle
npm install

# Geliştirme sunucusunu başlat (port 5173)
npm run dev

# Production build oluştur
npm run build

# Yeni ShadCN bileşeni ekle
npx shadcn@latest add <component-name>
```

### Vite Proxy
Backend API'sine istekleri yönlendirmek için `/api` path'i `http://localhost:8000` adresine proxy'lenmiştir.

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### State Management

**React Query (Server State):**
```typescript
import { useQuery, useMutation } from '@tanstack/react-query'

// Örnek kullanım
const { data, isLoading } = useQuery({
  queryKey: ['library'],
  queryFn: () => fetch('/api/v2/library').then(res => res.json()),
})
```

**Zustand (Client State):**
```typescript
import { useUIStore } from '@/stores/ui-store'

// Örnek kullanım
const { isSidebarOpen, toggleSidebar } = useUIStore()
```

---

## Axios API Client

### Yapılandırma
```typescript
// src/lib/api.ts
const api = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Request Interceptor - localStorage'dan API key varsa header'a ekle
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('semantic_scholar_api_key');
  if (apiKey) {
    config.headers['x-api-key'] = apiKey;
  }
  return config;
});

// Response Interceptor - Global Error Handling
api.interceptors.response.use(
  (response) => response.data,  // Otomatik .data unwrap
  (error) => {
    const errorMessage = error.response?.data?.error?.message || 'Bir hata oluştu';
    toast.error(errorMessage);
    return Promise.reject(error);
  }
);
```

### TypeScript Interfaces
```typescript
// src/types/api.ts
export interface SearchFilters {
  query: string;
  year_start?: number | null;
  year_end?: number | null;
  min_citations?: number | null;
}

export interface PaperResponse {
  title: string;
  abstract: string | null;
  year: number | null;
  citation_count: number;
  venue: string | null;
  authors: Author[];
  source: 'semantic' | 'openalex' | 'manual';
  external_id: string | null;
  pdf_url: string | null;
}
```

### Service Layer
```typescript
// src/services/search.ts
export async function searchPapers(filters: SearchFilters): Promise<PaperResponse[]> {
  return api.post<never, PaperResponse[]>('/search', filters);
}

// src/services/library.ts
export async function fetchLibrary(params: LibraryParams): Promise<LibraryListResponse> { ... }
export async function ingestPaper(data: IngestRequest): Promise<IngestResponse> { ... }
export async function bulkIngestPapers(data: BulkIngestRequest): Promise<BulkIngestResponse> { ... }
export async function checkLibraryPapers(external_ids: string[]): Promise<CheckLibraryResponse> { ... }
```

---

## Zustand Store (Güncel)

```typescript
// src/stores/ui-store.ts
interface UIState {
  isSidebarOpen: boolean;
  activeTab: 'search' | 'library';
  selectedPaperId: string | null;
  searchResults: PaperResponse[];
  isSearching: boolean;
  lastSearchQuery: string;
  // Pagination
  currentPage: number;           // Mevcut sayfa (1-based)
  itemsPerPage: number;          // Sayfa başına makale (50)
  // Selection (bulk save)
  selectedPaperIds: Set<string>;  // Checkbox ile seçili makaleler
  // Saved papers tracking
  savedPaperIds: Set<string>;     // Kütüphanede kayıtlı makale DOI'leri
  // Search result filters (client-side)
  searchFilterMinCitations: number | null;
  searchFilterOpenAccess: boolean;
  searchFilterSource: PaperSource | null;
  // Library filters
  libraryFilterTag: string | null;
  libraryFilterStatus: string | null;

  // Actions
  toggleSidebar: () => void;
  setActiveTab: (tab) => void;
  setSelectedPaperId: (id) => void;
  setSearchResults: (results) => void;  // Filtreleri ve seçimi sıfırlar
  setIsSearching: (isSearching) => void;
  setLastSearchQuery: (query) => void;
  setCurrentPage: (page) => void;
  togglePaperSelection: (id) => void;
  selectAllOnPage: () => void;
  clearSelection: () => void;
  setSavedPaperIds: (ids: string[]) => void;
  addSavedPaperIds: (ids: string[]) => void;
  setSearchFilterMinCitations: (value) => void;  // currentPage=1'e sıfırlar
  setSearchFilterOpenAccess: (value) => void;
  setSearchFilterSource: (value) => void;
  setLibraryFilterTag: (tag) => void;
  setLibraryFilterStatus: (status) => void;
}
```

---

## Geliştirme Durumu

### Tamamlanan Sprintler
- ✅ Sprint 0 - Proje Altyapısı
- ✅ Sprint 1 - Veritabanı Modelleri
- ✅ Sprint 2 - Arama Altyapısı
- ✅ Sprint 3 - Kütüphane Yönetimi
- ✅ Sprint 4 - Hata Yönetimi ve Loglama
- ✅ Sprint 5 - Frontend Kurulumu (5.1 - 5.5)
- ✅ Sprint 6 - Frontend Entegrasyonu ve UX (6.1 - 6.5)
- ✅ Sprint 7 - Arama İyileştirmeleri ve UX Düzeltmeleri (7.1 - 7.14)
- ✅ Sprint 8 - Çoklu Kaynak Entegrasyonu (8.1 - 8.6)
- ✅ Sprint 9 - Docker Deployment Düzeltmeleri ve E2E Test (9.1 - 9.4)
- ✅ Sprint 10 - Arama Motoru Optimizasyonu (10.1 - 10.7)
- ⏳ Sprint 11 - Kütüphane Filtreleme ve UX İyileştirmeleri (11.1 - devam ediyor)

### Sıradaki Sprint
- ⏳ Sprint 11 devam ediyor

---

## Devam Etme Promptu (VSCode Restart)

Aşağıdaki promptu VSCode restart sonrası kullanarak kaldığınız yerden devam edebilirsiniz:

```
Project Athena V2 geliştirmesine devam ediyoruz.

Durum:
- Sprint 0-10 tamamlandı
- Backend: FastAPI + SQLAlchemy 2.0 (async) + Celery
- Frontend: React 19 + Vite + TypeScript + ShadCN/UI + Zustand + React Query
- Docker: PostgreSQL, Redis, RabbitMQ + backend + celery_worker + frontend
- Tüm servisler çalışır ve test edilmiş durumda

Tamamlanan son işler (Sprint 11 - Kütüphane Filtreleme ve UX):
- Backend: GET /api/v2/library'ye min_citations, year_start, year_end, search parametreleri eklendi
- Backend: Paper join + Author/Tag subquery ile keyword search
- Backend: LibraryEntry.updated_at kolonu + migration eklendi
- Backend: download_paper_task detaylı loglama, timeout 60s→120s
- Backend: retry_stuck_downloads Celery task (1 saatten eski pending/downloading kayıtları tekrar kuyruğa ekler)
- Backend: POST /api/v2/library/retry-downloads endpoint
- Frontend: Zustand store'a library filtre state'leri eklendi
- Frontend: Sidebar'da kütüphane filtreleri (arama, yıl aralığı, min atıf)
- Frontend: LibraryItem'a citation count badge eklendi
- Frontend: "İndirmeleri Tekrar Dene" butonu (pending/downloading varken görünür)
- Bug fix: Yıl filtresi ara değer validasyon hatası düzeltildi (>= 1900 kontrolü)

Referans dökümanlar:
- CLAUDE.md: Proje referans dokümanı
- docs/sprint11.md: Sprint 11 detayları

Sprint 11 devam ediyor, yeni prompt'u bekliyorum.
```

---
*Son Güncelleme: Sprint 11.2 - 2026-02-15*
