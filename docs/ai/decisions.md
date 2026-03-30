# Architectural Decision Records (ADR)

This document captures key architectural decisions made during the development of Kalem - Kasghar, including the rationale and trade-offs.

---

## ADR-001: Modular Monolith Architecture

**Date:** Sprint 0
**Status:** Accepted
**Context:** Need a scalable yet maintainable architecture for an academic paper management system.

### Decision

Use a modular monolith architecture instead of microservices.

### Rationale

- **Simplicity:** Single deployment unit, easier local development
- **Performance:** No network overhead between modules
- **Transaction Support:** Database transactions across modules
- **Team Size:** Small team, microservices overhead not justified
- **Future-proof:** Modules can be extracted as microservices if needed

### Trade-offs

- ✅ Faster development cycles
- ✅ Simpler deployment and monitoring
- ✅ Strong consistency guarantees
- ⚠️ All modules share same runtime (failure isolation limited)
- ⚠️ Scaling requires scaling entire application

---

## ADR-002: FastAPI + SQLAlchemy 2.0 Async

**Date:** Sprint 0
**Status:** Accepted
**Context:** Need high-performance backend with async I/O for external API calls.

### Decision

Use FastAPI with SQLAlchemy 2.0 async engine (asyncpg driver).

### Rationale

- **Async-first:** Non-blocking I/O for concurrent API requests
- **Type Safety:** Pydantic validation + Python type hints
- **Performance:** uvicorn ASGI server, async ORM queries
- **Modern ORM:** SQLAlchemy 2.0 style (declarative models)
- **Auto Docs:** Built-in Swagger/ReDoc generation

### Trade-offs

- ✅ High concurrency (1000+ req/s possible)
- ✅ Type-safe request/response
- ✅ Excellent developer experience
- ⚠️ Async learning curve for team
- ⚠️ Must be careful with blocking operations

---

## ADR-003: PostgreSQL Full-Text Search (FTS)

**Date:** Sprint 13
**Status:** Accepted
**Context:** Library search needed relevance ranking, not just exact matches.

### Decision

Implement PostgreSQL FTS with `TSVECTOR` and `GIN` index instead of Elasticsearch.

### Rationale

- **No Extra Dependency:** PostgreSQL already in stack
- **Sufficient Scale:** Handles <1M papers efficiently
- **Native Integration:** No sync lag between DB and search index
- **Relevance Ranking:** `ts_rank()` for scoring
- **Fallback Support:** Can combine FTS + ILIKE for mixed queries

### Trade-offs

- ✅ Zero operational overhead
- ✅ Strong consistency (single source of truth)
- ✅ Good performance with GIN index
- ⚠️ Less powerful than Elasticsearch for complex queries
- ⚠️ Limited to PostgreSQL (vendor lock-in)

### Implementation

```sql
-- Composite search vector (title + abstract + authors)
ALTER TABLE papers ADD COLUMN search_vector TSVECTOR;
CREATE INDEX ix_papers_search_vector ON papers USING GIN(search_vector);

-- Auto-update trigger
CREATE TRIGGER papers_search_vector_update ...
```

---

## ADR-004: Multi-Provider Search with Deduplication

**Date:** Sprint 2
**Status:** Accepted
**Context:** Need to aggregate results from 5+ academic databases.

### Decision

Query all enabled providers in parallel (asyncio.gather), then deduplicate client-side.

### Rationale

- **Coverage:** Different providers have different papers
- **Reliability:** One provider failure doesn't block search
- **Parallel Execution:** Async calls minimize latency
- **Client-side Dedup:** Full control over merge logic

### Deduplication Strategy

1. **DOI-based:** Hash DOI (O(1) lookup)
2. **Title-normalized:** Aggressive normalization + hash
3. **Priority Order:** Semantic > Crossref > arXiv > OpenAlex > CORE

### Trade-offs

- ✅ Maximum paper coverage
- ✅ Fault-tolerant (provider failures isolated)
- ✅ Fast (parallel queries)
- ⚠️ More API quota consumed
- ⚠️ Complexity in dedup logic

### Code Example

```python
async def search_papers(filters):
    tasks = [
        semantic_provider.search(filters),
        openalex_provider.search(filters),
        # ... other providers
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return deduplicate(flatten(results))
```

---

## ADR-005: Celery for Background PDF Downloads

**Date:** Sprint 3
**Status:** Accepted
**Context:** PDF downloads can take 5-30 seconds, blocking HTTP requests is unacceptable.

### Decision

Use Celery with RabbitMQ broker for async PDF downloads.

### Rationale

- **Non-blocking:** Return HTTP 202 immediately
- **Retry Logic:** Auto-retry failed downloads (exponential backoff)
- **Status Tracking:** Database-backed status (pending → downloading → completed/failed)
- **Scalability:** Horizontal scaling via multiple workers

### Architecture

```
FastAPI (ingest) → RabbitMQ → Celery Worker → Download PDF → Update DB
```

### Trade-offs

- ✅ User doesn't wait for download
- ✅ Automatic retries on failure
- ✅ Can scale workers independently
- ⚠️ Added infrastructure (RabbitMQ)
- ⚠️ Eventual consistency (status updates delayed)

---

## ADR-006: React Query + Zustand for State Management

**Date:** Sprint 5
**Status:** Accepted
**Context:** Need efficient state management for server + client state.

### Decision

Use React Query for server state, Zustand for UI state.

### Rationale

- **Separation of Concerns:** Server state != Client state
- **React Query Benefits:**
  - Auto caching, refetching, invalidation
  - Loading/error states built-in
  - Optimistic updates support
- **Zustand Benefits:**
  - Minimal boilerplate
  - Zero dependencies
  - TypeScript-first

### State Division

| State Type   | Example                        | Tool        |
| ------------ | ------------------------------ | ----------- |
| Server State | Library papers, search results | React Query |
| UI State     | Selected paper, sidebar open   | Zustand     |

### Trade-offs

- ✅ Best-in-class caching (React Query)
- ✅ Simple UI state (Zustand)
- ✅ No prop drilling
- ⚠️ Two state management paradigms to learn

---

## ADR-007: ShadCN/UI for Component Library

**Date:** Sprint 5
**Status:** Accepted
**Context:** Need consistent, accessible, and customizable UI components.

### Decision

Use ShadCN/UI (Tailwind-based) instead of Material-UI or Ant Design.

### Rationale

- **Copy-Paste Philosophy:** Components live in your codebase (not npm)
- **Full Control:** Easy to customize without fighting library defaults
- **Accessibility:** Built on Radix primitives (WAI-ARIA compliant)
- **Tailwind Integration:** Consistent with our styling approach
- **No Runtime Cost:** Components are just JSX + Tailwind classes

### Trade-offs

- ✅ Complete customization freedom
- ✅ No version upgrade nightmares
- ✅ Lightweight (no large bundle)
- ⚠️ Manual component updates (no auto-upgrade)
- ⚠️ Smaller ecosystem than Material-UI

---

## ADR-008: Database-First Runtime Configuration

**Date:** Sprint 13
**Status:** Accepted
**Context:** Users need to configure API keys and proxy without redeploying.

### Decision

Store runtime settings in `user_settings` table, fallback to `.env` if not set.

### Rationale

- **User Control:** Change settings via UI, no server restart
- **Security:** API keys stored in DB (encrypted at rest via PostgreSQL)
- **Flexibility:** Per-user settings possible in future
- **Fallback:** `.env` still works for initial setup

### Settings Hierarchy

```
1. Database (user_settings table) ← PRIMARY
2. .env file ← FALLBACK
```

### Trade-offs

- ✅ Zero-downtime config changes
- ✅ User-friendly (UI-based)
- ✅ Supports multi-tenant future
- ⚠️ Database required for settings (can't run stateless)
- ⚠️ Migration needed if schema changes

---

## ADR-009: Docker Compose for Local Development

**Date:** Sprint 0
**Status:** Accepted
**Context:** Need reproducible development environment.

### Decision

Use Docker Compose for all services (PostgreSQL, Redis, RabbitMQ, backend, frontend, Celery).

### Rationale

- **Reproducibility:** Same environment across machines
- **Isolation:** No conflict with local installations
- **Production Parity:** Docker images match production
- **Dependency Management:** All services defined in one file

### Services

```yaml
postgres_db: Port 5433 (mapped from 5432)
redis_cache: Port 6379
rabbitmq_broker: Port 5672 + 15672 (management)
backend: Port 8000
frontend: Port 3000
celery_worker: No exposed port
```

### Trade-offs

- ✅ Consistent environment
- ✅ Easy onboarding (docker-compose up)
- ✅ Matches production
- ⚠️ Resource overhead (6 containers)
- ⚠️ Docker Desktop required on Mac

---

## ADR-010: Alembic for Database Migrations

**Date:** Sprint 1
**Status:** Accepted
**Context:** Need version-controlled database schema changes.

### Decision

Use Alembic (SQLAlchemy's migration tool) with async support.

### Rationale

- **Version Control:** Schema changes tracked in git
- **Auto-generation:** `alembic revision --autogenerate` detects model changes
- **Rollback Support:** Downgrade migrations for safety
- **Async Support:** Compatible with our async SQLAlchemy setup

### Workflow

```bash
# Create migration
alembic revision --autogenerate -m "add search_vector"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Trade-offs

- ✅ Safe schema evolution
- ✅ Team collaboration (migrations in git)
- ✅ Production-ready (tested rollback)
- ⚠️ Manual review needed (auto-generate not perfect)

---

## ADR-011: Adapter Pattern for Search Providers

**Date:** Sprint 2
**Status:** Accepted
**Context:** Need to support 5+ academic APIs with different interfaces.

### Decision

Define `BaseSearchProvider` abstract class, implement per-provider adapters.

### Rationale

- **Consistency:** All providers expose same `search(filters)` interface
- **Extensibility:** Adding new providers doesn't change core logic
- **Testability:** Easy to mock providers
- **Encapsulation:** API-specific logic isolated

### Structure

```python
class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        pass

class SemanticScholarProvider(BaseSearchProvider):
    async def search(self, filters):
        # API-specific implementation
```

### Trade-offs

- ✅ Clean separation of concerns
- ✅ Easy to add new providers
- ✅ Provider failures don't crash system
- ⚠️ Some duplicated logic (pagination, retries)

---

## ADR-012: Export to Excel/CSV + ZIP Archives

**Date:** Sprint 12
**Status:** Accepted
**Context:** Users need to export library for offline analysis.

### Decision

Support both tabular exports (Excel/CSV) and ZIP archives of PDFs.

### Rationale

- **Excel:** Most users prefer Excel for bibliographies
- **CSV:** Machine-readable, import to other tools
- **ZIP:** Backup/transfer entire library with PDFs
- **Streaming:** Use `StreamingResponse` to avoid memory issues

### Export Columns

| Column         | Description                 |
| -------------- | --------------------------- |
| ID             | LibraryEntry ID             |
| Title          | Paper title                 |
| Authors        | Comma-separated authors     |
| Year           | Publication year            |
| Citation (APA) | Auto-generated APA citation |
| DOI            | Digital Object Identifier   |
| Downloaded     | YES/NO (based on file_path) |

### Trade-offs

- ✅ Flexibility (multiple formats)
- ✅ Memory-efficient (streaming)
- ✅ Complete backups (ZIP with PDFs)
- ⚠️ Large libraries slow to export
- ⚠️ ZIP can be huge (GBs)

---

## ADR-013: Loguru for Structured Logging

**Date:** Sprint 4
**Status:** Accepted
**Context:** Need production-ready logging with correlation IDs.

### Decision

Use Loguru instead of Python's standard logging module.

### Rationale

- **Simplicity:** No complex config (handlers, formatters, etc.)
- **Structured Output:** JSON format in production
- **Context Variables:** `request_id` tracked across logs
- **Colored Dev Logs:** Readable console output
- **Auto-rotation:** File size/time-based rotation built-in

### Log Formats

```python
# Development
2024-01-15 10:30:00 | INFO | Request completed | path=/api/v2/search | status=200

# Production (JSON)
{"timestamp":"2024-01-15T10:30:00Z","level":"INFO","message":"Request completed","path":"/api/v2/search","status":200,"request_id":"550e8400-..."}
```

### Trade-offs

- ✅ Developer-friendly API
- ✅ Production-ready (JSON, rotation)
- ✅ Request correlation built-in
- ⚠️ Non-standard (not stdlib logging)

---

## ADR-014: Frontend Proxy via Nginx

**Date:** Sprint 5
**Status:** Accepted
**Context:** Need to serve React SPA and proxy API requests in production.

### Decision

Use nginx in frontend container to serve static files + proxy `/api` to backend.

### Rationale

- **Single Origin:** Avoid CORS issues
- **Production-grade:** nginx is battle-tested for static files
- **Routing:** SPA routing (try_files $uri /index.html)
- **Performance:** nginx faster than Node.js for static files

### nginx Config

```nginx
location / {
    try_files $uri /index.html;
}

location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
}
```

### Trade-offs

- ✅ No CORS needed
- ✅ Fast static file serving
- ✅ Simple SPA routing
- ⚠️ Extra nginx layer (dev uses Vite proxy)

---

## Future Decisions (Under Consideration)

### FD-001: Move to Microservices?

**Status:** Deferred
**Reason:** Current monolith handles scale, no need yet. Revisit at 10K+ users.

### FD-002: Add Elasticsearch?

**Status:** Deferred
**Reason:** PostgreSQL FTS sufficient for now. Consider if query complexity increases.

### FD-003: Redis-backed Pagination?

**Status:** Proposed (Sprint 14)
**Reason:** Current offset pagination slow for large result sets. Cursor-based pagination with Redis cache.

### FD-004: Multi-tenancy?

**Status:** Backlog
**Reason:** `user_settings` designed for single-user. Schema refactor needed for teams/orgs.

---

## ADR-012: EZProxy Institutional Access

**Date:** Sprint 17
**Status:** Accepted
**Context:** Many academic papers are behind paywalls. University libraries provide EZProxy systems for authenticated access.

### Decision

Implement EZProxy fallback mechanism in the PDF downloader service when direct download fails (401/402/403).

### Rationale

- **Institutional Access:** Universities pay for journal subscriptions accessible via EZProxy
- **User-Configurable:** Each user can input their institution's EZProxy prefix and session cookie
- **Graceful Fallback:** System first tries open access, then falls back to EZProxy
- **Cookie-Based Auth:** EZProxy uses session cookies, which users can extract from browser DevTools

### Trade-offs

- ✅ Enables access to paywalled content legally through institutional subscriptions
- ✅ No additional infrastructure (uses existing HTTP client)
- ✅ Works with any EZProxy-compatible institution
- ⚠️ Cookies expire - users must periodically update
- ⚠️ Manual cookie extraction required (no OAuth flow)

### Implementation Details

```python
# Fallback flow in downloader.py
if download_fails(401, 402, 403) and ezproxy_settings_configured():
    target_url = f"{ezproxy_prefix}{original_url}"
    headers = {"Cookie": ezproxy_cookie}
    retry_download(target_url, headers)
```

---

_Last Updated: 2026-03-30_
