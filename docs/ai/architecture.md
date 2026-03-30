# Kalem - Kasghar System Architecture

## System Overview

**Kalem - Kasghar** (Project Athena v2.0.0) is an academic paper research and library management application built with a modular monolith architecture.

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | ^0.109.0 |
| Language | Python | ^3.11 |
| ORM | SQLAlchemy (async) | ^2.0.25 |
| Database Driver | asyncpg | ^0.29.0 |
| Task Queue | Celery | ^5.3.0 |
| HTTP Client | httpx | ^0.27.0 |

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 19.x |
| Build Tool | Vite | 7.x |
| Language | TypeScript | 5.x |
| UI Library | ShadCN/UI | latest |
| Styling | Tailwind CSS | 3.x |
| State (Server) | React Query | 5.x |
| State (Client) | Zustand | 5.x |
| Routing | React Router | 7.x |

### Infrastructure
| Service | Image | Purpose |
|---------|-------|---------|
| PostgreSQL | postgres:16-alpine | Primary database |
| Redis | redis:7-alpine | Cache & Celery result backend |
| RabbitMQ | rabbitmq:3-management-alpine | Message broker |

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                  │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐   │
│  │ Components│  │  Services │  │ Stores (UI)  │   │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘   │
│        └───────────────┴────────────────┘           │
│                      │                              │
│              React Query (API State)                │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────┴──────────────────────────────┐
│              Backend (FastAPI)                      │
│  ┌─────────────────────────────────────────────┐   │
│  │         API Layer (routers/)                │   │
│  │    /search  /library  /settings  /system   │   │
│  └────────────────┬────────────────────────────┘   │
│  ┌────────────────┴────────────────────────────┐   │
│  │         Service Layer (services/)           │   │
│  │   SearchService  LibraryService  etc.       │   │
│  └────────────────┬────────────────────────────┘   │
│  ┌────────────────┴────────────────────────────┐   │
│  │      Adapter Layer (adapters/)              │   │
│  │   Semantic Scholar | OpenAlex | arXiv       │   │
│  │   Crossref | CORE                           │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │    Repository Layer (repositories/)         │   │
│  │           Database Access (CRUD)            │   │
│  └────────────────┬────────────────────────────┘   │
└───────────────────┼──────────────────────────────┬─┘
                    │                              │
                    │                         Celery Tasks
                    │                         (downloader)
                    │                              │
┌───────────────────┴──────────────────────────────┴─┐
│              PostgreSQL Database                    │
│  ┌─────────────────────────────────────────────┐   │
│  │   papers • authors • library_entries        │   │
│  │   tags • user_settings                      │   │
│  │   FTS: search_vector (TSVECTOR + GIN)       │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Module Breakdown

### Backend Modules

| Module | Purpose | Key Components |
|--------|---------|----------------|
| `api/v2/routers/` | REST API endpoints | search.py, library.py, settings.py, system.py |
| `core/` | Core infrastructure | config, database, logging, middleware, exceptions |
| `services/` | Business logic | SearchService, LibraryService, ExportService, SettingsService |
| `adapters/` | External API integrations | SemanticScholarProvider, OpenAlexProvider, ArxivProvider, CrossrefProvider, CoreProvider |
| `repositories/` | Data access layer | CRUD operations (planned) |
| `models/` | SQLAlchemy ORM models | Paper, Author, LibraryEntry, Tag, UserSettings |
| `schemas/` | Pydantic DTOs | Request/Response validation |
| `tasks/` | Background jobs | download_paper_task, retry_stuck_downloads |

### Frontend Modules

| Module | Purpose | Key Components |
|--------|---------|----------------|
| `components/` | React components | SearchForm, PaperCard, PaperList, LibraryItem, Settings |
| `components/ui/` | ShadCN UI primitives | button, input, card, dialog, tabs, switch |
| `services/` | API client functions | search.ts, library.ts, settings.ts |
| `stores/` | Client state (Zustand) | ui-store.ts |
| `types/` | TypeScript interfaces | api.ts |
| `lib/` | Utilities | api.ts (axios), utils.ts |

## Data Flow

### Search Flow
```
User Input (SearchForm)
  → POST /api/v2/search (filters)
    → SearchService.search_papers()
      → Parallel provider queries (asyncio.gather)
        → [Semantic, OpenAlex, arXiv, Crossref, CORE]
      → Deduplication (DOI + normalized title)
      → Keyword relevance filtering
    → PaperResponse[] + metadata
  → Display in PaperList
    → User selects paper
      → POST /api/v2/library/ingest
        → LibraryService.add_paper_to_library()
          → Create Paper + Authors + LibraryEntry + Tags
          → Trigger download_paper_task.delay()
```

### Library Query Flow (Full-Text Search)
```
User Input (Library Search)
  → GET /api/v2/library?search=query
    → LibraryService.get_library_entries()
      → PRIMARY: PostgreSQL FTS
        → websearch_to_tsquery('english', query)
        → Paper.search_vector @@ ts_query
        → ORDER BY ts_rank(...).desc()
      → FALLBACK: ILIKE + Author/Tag match
    → LibraryEntrySchema[] with pagination
  → Display in LibraryList
```

### PDF Download Flow
```
LibraryEntry created with pdf_url
  → Celery task: download_paper_task.delay(entry_id)
    → Load UserSettings (proxy, etc.)
    → HTTP GET with rotating User-Agents
    → Save to /data/library/{paper_id}/{filename}.pdf
    → Update LibraryEntry.download_status
      → pending → downloading → completed/failed
    → Auto-retry on failure (max 5, exponential backoff)
```

## Database Schema

### Core Tables
```sql
-- Papers table
papers
  id              SERIAL PRIMARY KEY
  doi             VARCHAR(255) UNIQUE
  title           TEXT NOT NULL
  title_slug      VARCHAR(255)
  abstract        TEXT
  year            INTEGER
  citation_count  INTEGER DEFAULT 0
  venue           VARCHAR(500)
  pdf_url         VARCHAR(1000)
  search_vector   TSVECTOR  -- FTS index (GIN)
  created_at      TIMESTAMP DEFAULT NOW()

-- Authors table
authors
  id              SERIAL PRIMARY KEY
  name            VARCHAR(255) NOT NULL
  slug            VARCHAR(255) INDEXED

-- Library entries
library_entries
  id              SERIAL PRIMARY KEY
  paper_id        INTEGER UNIQUE FK → papers.id (CASCADE)
  source          ENUM (semantic, openalex, arxiv, crossref, core, manual)
  download_status ENUM (pending, downloading, completed, failed)
  file_path       VARCHAR(500)
  is_favorite     BOOLEAN DEFAULT FALSE
  updated_at      TIMESTAMP

-- Tags
tags
  id              SERIAL PRIMARY KEY
  name            VARCHAR(100) UNIQUE

-- User settings (singleton)
user_settings
  id                      SERIAL PRIMARY KEY
  openai_api_key          TEXT
  semantic_scholar_api_key TEXT
  core_api_key            TEXT
  openalex_email          VARCHAR(255)
  enabled_providers       JSONB DEFAULT '["semantic","openalex","arxiv","crossref","core"]'
  proxy_url               VARCHAR(500)
  proxy_enabled           BOOLEAN DEFAULT FALSE
```

### Many-to-Many Relations
```sql
paper_authors (paper_id, author_id)
library_tags  (library_entry_id, tag_id)
```

## API Endpoints

### Core API Routes
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v2/health` | Health check (DB + Redis) |
| POST | `/api/v2/search` | Multi-source paper search |
| POST | `/api/v2/library/ingest` | Add paper to library (single) |
| POST | `/api/v2/library/ingest/bulk` | Bulk add papers (max 100) |
| POST | `/api/v2/library/check` | Check if papers exist (max 5000 DOIs) |
| GET | `/api/v2/library` | List library with filters |
| POST | `/api/v2/library/retry-downloads` | Retry stuck downloads |
| GET | `/api/v2/library/export` | Export library (CSV/XLSX) |
| GET | `/api/v2/library/download-zip` | Download PDFs as ZIP |
| DELETE | `/api/v2/library/{entry_id}` | Delete library entry + PDF |
| PUT | `/api/v2/library/{entry_id}/tags` | Update entry tags (overwrite) |
| GET | `/api/v2/collections` | List collections with counts |
| POST | `/api/v2/collections` | Create collection |
| DELETE | `/api/v2/collections/{id}` | Delete collection |
| POST | `/api/v2/collections/{id}/entries/add` | Add entries to collection |
| DELETE | `/api/v2/collections/{cid}/entries/{eid}` | Remove entry from collection |
| GET | `/api/v2/collections/by-entry/{eid}` | Get entry's collections |
| GET | `/api/v2/system/settings` | Get runtime settings |
| PUT | `/api/v2/system/settings` | Update runtime settings |
| POST | `/api/v2/system/reset` | Reset system (requires confirmation) |

## External API Integrations

### Search Providers

| Provider | Base URL | Rate Limit | Auth |
|----------|----------|------------|------|
| Semantic Scholar | api.semanticscholar.org | 100 req/s (free) | Optional API key (x-api-key) |
| OpenAlex | api.openalex.org | 100 req/s | Email in User-Agent (Polite Pool) |
| arXiv | export.arxiv.org | ~3 req/s | None |
| Crossref | api.crossref.org | 50 req/s | Email in User-Agent |
| CORE | api.core.ac.uk | Varies | Bearer token (API key) |

### Provider Features
| Provider | DOI | Citation Count | PDF URL | Abstract | Full-Text |
|----------|-----|----------------|---------|----------|-----------|
| Semantic Scholar | ✅ | ✅ | ✅ (openAccessPdf) | ✅ | Limited |
| OpenAlex | ✅ | ✅ | ✅ (best_oa_location) | ✅ (inverted index) | No |
| arXiv | ✅ | No | ✅ | ✅ | No |
| Crossref | ✅ | ✅ | Limited | ✅ | No |
| CORE | ✅ | No | ✅ (downloadUrl) | ✅ | Limited |

## Security & Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://...

# Redis
REDIS_URL=redis://redis_cache:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq_broker:5672

# API Keys (fallback, overridden by DB settings)
SEMANTIC_SCHOLAR_API_KEY=
OPENALEX_EMAIL=
CORE_API_KEY=
OPENAI_API_KEY=

# Logging
LOG_LEVEL=INFO
```

### Runtime Configuration (DB-first)
- Settings stored in `user_settings` table
- Fallback to `.env` if DB record doesn't exist
- API keys masked in responses (`sk-***`)
- Provider enable/disable switches
- Proxy settings for PDF downloads

## Error Handling

### Exception Hierarchy
```python
AthenaError (base)
  ├── ProviderError (external API failures)
  ├── LibraryError (library operations)
  ├── ValidationError (request validation)
  └── DownloadError (PDF download failures)
```

### Standardized Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "suggestion": "How to fix",
    "details": "Technical details",
    "request_id": "UUID for correlation"
  }
}
```

## Logging & Observability

### Structured Logging (Loguru)
- **Development:** Colored console output
- **Production:** JSON format
- **Request ID:** UUID tracked across logs + response headers
- **Middleware:** Auto-logs all HTTP requests (method, path, status, duration)

### Health Checks
- Database connection test
- Redis connection test
- Version metadata

## Performance Optimizations

### Database
- **GIN Index:** Full-text search on `papers.search_vector`
- **TSVECTOR:** `title + abstract + authors.name` combined
- **Triggers:** Auto-update `search_vector` on insert/update
- **N+1 Prevention:** SQLAlchemy `joinedload` for relationships

### Caching
- React Query: Client-side API response cache
- Redis: Celery task results

### Async Operations
- SQLAlchemy async engine (asyncpg)
- httpx async HTTP client
- Parallel provider queries (asyncio.gather)
- Background PDF downloads (Celery)

## Deployment

### Docker Compose Services
```yaml
services:
  postgres_db:    # PostgreSQL 16
  redis_cache:    # Redis 7
  rabbitmq_broker: # RabbitMQ 3 (management)
  backend:        # FastAPI (uvicorn)
  celery_worker:  # Celery worker
  frontend:       # React (nginx)
```

### Container Communication
- Backend → PostgreSQL: `postgres_db:5432`
- Backend → Redis: `redis_cache:6379`
- Backend → RabbitMQ: `rabbitmq_broker:5672`
- Frontend → Backend: nginx proxy `/api → backend:8000`

### Ports Exposed
| Service | Port | Accessible |
|---------|------|------------|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| PostgreSQL | 5433 | localhost:5433 (mapped from 5432) |
| Redis | 6379 | localhost:6379 |
| RabbitMQ | 5672, 15672 | 15672 = management UI |

## Scalability Considerations

### Current Architecture
- **Modular Monolith:** Single backend codebase, logically separated
- **Async-first:** Non-blocking I/O for high concurrency
- **Task Queue:** Celery for background jobs (horizontally scalable)

### Future Improvements
- Separate read/write endpoints (CQRS pattern)
- Redis-backed result pagination
- CDN for static frontend assets
- Multi-worker Celery deployment

---
*Last Updated: 2026-03-28*
