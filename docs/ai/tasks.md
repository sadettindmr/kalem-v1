# Current Sprint Tasks

**Last Updated:** 2026-03-30
**Active Sprints:** Sprint 16 (✅ Completed), Sprint 15 (✅ Completed), Sprint 14 (✅ Completed)

---

## Sprint 16 - API Documentation / OpenAPI

**Date:** 2026-03-30
**Status:** ✅ Completed
**Goal:** FastAPI Swagger UI ve ReDoc dokumantasyonlarini profesyonel hale getirmek.

### 16.1 - Ana Uygulama Metadata

| Component | Change | Status |
|-----------|--------|--------|
| `main.py` FastAPI title/description | Proje adi, Markdown ozellik listesi | ✅ |
| `main.py` version/contact/license | v1.0.0, Kalem Core Team, Apache 2.0 | ✅ |
| `main.py` openapi_tags | 5 tag grubu (Search, Library, Collections, Settings, System) | ✅ |

### 16.2 - Router Tag/Summary/Docstring

| Component | Change | Status |
|-----------|--------|--------|
| `search.py` | 1 endpoint: summary + Markdown docstring | ✅ |
| `library.py` | 9 endpoint: summary + response_description + docstring | ✅ |
| `collections.py` | 6 endpoint: summary + response_description + docstring | ✅ |
| `settings.py` | 2 endpoint: summary + docstring, tag="Settings" | ✅ |
| `system.py` | 2 endpoint: summary + response_description + docstring | ✅ |

### 16.3 - Pydantic Schema Zenginlestirme

| Component | Change | Status |
|-----------|--------|--------|
| `schemas/search.py` | Field descriptions, examples, json_schema_extra | ✅ |
| `schemas/library.py` | Field descriptions, examples | ✅ |
| `schemas/error.py` | Field descriptions, examples, json_schema_extra | ✅ |
| Router inline models | Tum model alanlarina description + examples | ✅ |

**Test Results:** Python syntax 9/9 OK, Frontend 6/6 passed, tsc clean, vite build clean

---

## Sprint 15 - Koleksiyonlar / Proje Alanlari

**Date:** 2026-03-29
**Status:** ✅ Completed
**Goal:** Kutuphane icin "Koleksiyon/Proje" altyapisini kurmak, makaleleri projelere atamak ve filtreleme/disa aktarma islemlerini projeye ozel hale getirmek.

### 15.1 - Backend: Koleksiyon Modelleri ve API

| Component | Change | Status |
|-----------|--------|--------|
| `Collection` model | id, name (unique), description, created_at | ✅ |
| `collection_entries` M2M table | collection_id + entry_id association | ✅ |
| `LibraryEntry.collections` relationship | back_populates="entries" | ✅ |
| Alembic migration `d7f2a3b8c901` | Creates collections + collection_entries tables | ✅ |
| `GET /api/v2/collections` | List all collections with entry_count | ✅ |
| `POST /api/v2/collections` | Create new collection | ✅ |
| `DELETE /api/v2/collections/{id}` | Delete collection | ✅ |
| `POST /api/v2/collections/{id}/entries` | Sync entry list (add/remove) | ✅ |
| `_apply_library_filters()` | Added `collection_id` subquery filter | ✅ |
| `GET /api/v2/library` | `collection_id` query param | ✅ |
| `GET /api/v2/library/download-zip` | `collection_id` query param | ✅ |
| `GET /api/v2/library/export` | `collection_id` query param | ✅ |
| `LibraryService.get_library_entries()` | `collection_id` filter | ✅ |
| `ExportService.export_library()` | `collection_id` filter | ✅ |

### 15.2 - Frontend: Koleksiyon Arayuzu

| Component | Change | Status |
|-----------|--------|--------|
| `Collection` + `CollectionListResponse` types | api.ts | ✅ |
| `collections.ts` service | fetchCollections, create, delete, syncEntries | ✅ |
| `library.ts` service | `collection_id` param support | ✅ |
| `ui-store.ts` | `selectedCollectionId` state + action | ✅ |
| Sidebar "Projelerim" section | Collection badges, create dialog, delete | ✅ |
| PaperDetail "Projeye Ekle" dialog | Checkbox list, sync mutation | ✅ |
| LibraryList | `collection_id` in query key + fetch + ZIP | ✅ |
| Settings export | `collection_id` in export URLs | ✅ |

**Test Results:** Backend 17/17, Frontend 6/6, tsc clean, vite build clean

---

## Sprint 14 - QA & CI/CD Pipeline

**Date:** 2026-03-29
**Status:** ✅ Completed
**Goal:** Frontend unit test infrastructure, E2E testing, and GitHub Actions CI/CD pipeline.

### 14.1 - Frontend Unit Tests (Vitest)

| Component | Change | Status |
|-----------|--------|--------|
| `vitest` + `@testing-library/react` | Installed as dev dependencies | ✅ |
| `vite.config.ts` | Added `test` config (jsdom, globals, setupFiles) | ✅ |
| `tsconfig.app.json` | Added `vitest/globals` to types | ✅ |
| `tsconfig.node.json` | Added `vitest/config` to types | ✅ |
| `src/test/setup.ts` | Created with jest-dom import | ✅ |
| `SearchForm.test.tsx` | 6 unit tests (render, input, submit, year filters) | ✅ |
| `package.json` | Added `test` and `test:watch` scripts | ✅ |

**Test Results:** 6/6 passed

### 14.2 - E2E Testing (Playwright)

| Component | Change | Status |
|-----------|--------|--------|
| `@playwright/test` | Installed with Chromium browser | ✅ |
| `playwright.config.ts` | Chromium project, configurable baseURL | ✅ |
| `tests/main-flow.spec.ts` | Full search-and-add-to-library flow | ✅ |
| `package.json` | Added `test:e2e` script | ✅ |

**E2E Test Flow:**
1. Navigate to app
2. Search "Machine Learning"
3. Wait for results
4. Click "Kutuphaneme Ekle" on first result
5. Verify success toast

**Test Results:** 1/1 passed (~40s)

### 14.3 - CI/CD Pipeline (GitHub Actions)

| Component | Change | Status |
|-----------|--------|--------|
| `.github/workflows/ci.yml` | Created CI workflow | ✅ |
| Backend job | Python 3.11, Poetry, black, isort, pytest | ✅ |
| Frontend job | Node 20, npm ci, tsc -b, vitest run | ✅ |

**Triggers:** Push/PR to `main` branch

---

## Sprint 13.7 - Hotfix: Enum Fix & Proxy trust_env

**Date:** 2026-03-28
**Status:** ✅ Completed
**Goal:** Fix arXiv/Crossref ingest failure (enum case mismatch) and proxy-affecting-search (httpx trust_env).

### Implemented Changes

| Component | Change | Status |
|-----------|--------|--------|
| `c4e8a1f9b302` migration | Add uppercase ARXIV, CROSSREF, CORE to source_type enum | ✅ |
| `semantic.py` adapter | Added `trust_env=False` to httpx client | ✅ |
| `openalex.py` adapter | Added `trust_env=False` to httpx client | ✅ |
| `arxiv.py` adapter | Added `trust_env=False` to httpx client | ✅ |
| `crossref.py` adapter | Added `trust_env=False` to httpx client | ✅ |
| `core.py` adapter | Added `trust_env=False` to httpx client | ✅ |

**Root Causes Fixed:**
- **arXiv/Crossref ingest failure:** Migration `ea63d692364c` added lowercase `arxiv`/`crossref`/`core` enum values, but SQLAlchemy writes Python enum **names** (uppercase: `ARXIV`/`CROSSREF`/`CORE`). New migration adds the uppercase variants.
- **Proxy affecting search:** `httpx.AsyncClient()` defaults to `trust_env=True`, which reads `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY` OS env vars automatically. Adding `trust_env=False` prevents Docker proxy env vars from affecting search requests.

**Impact:**
- ✅ arXiv and Crossref papers can now be added to library
- ✅ Search works regardless of proxy settings
- ✅ 17/17 tests pass

---

## Sprint 13.6 - Hotfix: Proxy Isolation

**Date:** 2026-03-28
**Status:** ✅ Completed
**Goal:** Isolate proxy usage to PDF download service only, remove from search adapters.

### Implemented Changes

| Component | Change | Status |
|-----------|--------|--------|
| `semantic.py` adapter | Removed proxy client configuration | ✅ |
| `openalex.py` adapter | Removed proxy usage | ✅ |
| `arxiv.py` adapter | Removed proxy client_kwargs | ✅ |
| `crossref.py` adapter | Removed proxy support | ✅ |
| `core.py` adapter | Removed proxy configuration | ✅ |
| `downloader.py` task | Kept proxy support (DB-based) | ✅ |

**Impact:**
- ✅ Search requests now use standard network (faster, no proxy overhead)
- ✅ PDF downloads still respect `UserSettings.proxy_enabled` and `proxy_url`
- ✅ Code is simpler and more maintainable
- ✅ Proxy configuration only needed for institutional PDF access

---

## Sprint 12: Advanced Export & Archiving

**Status:** In Progress (Testing Phase)
**Goal:** Export library data with academic citation formats, enable PDF archiving, and implement relevance-based search.

### Completed Features

#### 12.1 - Advanced Excel Export (Bibliographic Data)
| Task | Status | Notes |
|------|--------|-------|
| Backend: ExportService refactoring | ✅ | 14 columns with citation formats |
| APA citation formatter | ✅ | `format_apa(...)` |
| IEEE citation formatter | ✅ | `format_ieee(...)` |
| Dynamic "Citation as of [DATE]" header | ✅ | dd.mm.yyyy format |
| Article type classification | ✅ | Journal/Conference/Other |
| DOI/Link selection logic | ✅ | Prefers DOI over PDF URL |
| Downloaded status column | ✅ | YES/NO based on download_status |
| Code/Data availability detection | ✅ | GitHub/GitLab/Zenodo heuristics |
| XLSX auto-width columns | ✅ | Content-based, max 80 chars |

**Export Columns:**
1. Makale Adı (Title)
2. Yazar(lar) (Authors)
3. Yayın Yılı (Year)
4. Makale Türü (Article Type)
5. Yayın Platformu / Dergi (Venue)
6. DOI / Link
7. Keywords
8. Search Words
9. Citation (APA)
10. Citation (IEEE)
11. Citation as of [DATE]
12. Source
13. Downloaded
14. Kod/Veri Erişilebilirliği (Code/Data Availability)

#### 12.2 - Bulk PDF Download (ZIP Archive)
| Task | Status | Notes |
|------|--------|-------|
| Backend: `GET /api/v2/library/download-zip` | ✅ | Streaming response |
| Query filter support | ✅ | search, tag, status, citations, year |
| Filter logic shared with list endpoint | ✅ | `_apply_library_filters(...)` |
| ZIP generation (in-memory) | ✅ | BytesIO + zipfile.ZipFile |
| File verification | ✅ | Only includes existing PDFs |
| Frontend: LibraryList ZIP button | ✅ | Header action |
| Frontend: Settings ZIP button | ✅ | Fallback action |

**ZIP Behavior:**
- Only includes `completed` downloads
- Filename format: `{entry_id}_{original_filename}.pdf`
- Respects current library filters
- Streams response to avoid memory issues

### Pending Tests (DoD)

| Test | Type | Expected Result |
|------|------|------------------|
| Export XLSX column structure | Manual | 14 columns with correct headers |
| APA/IEEE citation format | Manual | Best-effort citation text |
| Dynamic citation date | Manual | Header shows `dd.mm.yyyy` |
| Downloaded column | Manual | `EVET`/`HAYIR` correctly written |
| Code/Data availability | Manual | GitHub/Zenodo links detected |
| ZIP download | Manual | Valid ZIP file with PDFs |
| ZIP filter accuracy | Manual | Filtered papers match export |

---

## Sprint 13: Configuration Center & Search Intelligence

**Status:** ✅ Completed (with Sprint 13.6 Hotfix)
**Goal:** Implement PostgreSQL full-text search, database-backed runtime settings, and dynamic provider control.

### Sprint 13.6 Hotfix Summary

**Completed:** 2026-03-28

Proxy usage isolated to PDF download service only:
- All search adapters (Semantic Scholar, OpenAlex, arXiv, Crossref, CORE) now use standard network
- Only `downloader.py` respects `UserSettings.proxy_enabled` and `proxy_url`
- Rationale: Search APIs don't require proxy; proxy is typically needed for institutional PDF downloads only

### Completed Features

#### 13.1 - Full-Text Search (Relevance Infrastructure)
| Task | Status | Notes |
|------|--------|-------|
| Database: `search_vector` column (TSVECTOR) | ✅ | `papers` table |
| Database: GIN index | ✅ | `ix_papers_search_vector` |
| Migration | ✅ | `f13a1c9d0b77_add_search_vector_fts.py` |
| Trigger: Auto-update on insert/update | ✅ | Includes author changes |
| Backfill: Existing papers | ✅ | Migration script |
| Model: `Paper.search_vector` field | ✅ | SQLAlchemy model |
| Service: `get_library_entries(...)` | ✅ | FTS + fallback logic |
| Search query: `websearch_to_tsquery` | ✅ | English language |
| Ranking: `ts_rank(...)` | ✅ | Sorted by relevance |
| Fallback: ILIKE + author/tag match | ✅ | Combined with OR |
| Router: List endpoint integration | ✅ | Uses LibraryService |
| Router: ZIP endpoint integration | ✅ | Shares filter logic |
| Alembic: Conditional imports | ✅ | Fixes loguru import error |

**Search Strategy:**
1. **Primary:** PostgreSQL FTS
   - Query: `websearch_to_tsquery('english', query)`
   - Filter: `Paper.search_vector @@ ts_query`
   - Sort: `ts_rank(...)` DESC
2. **Fallback:** Pattern matching
   - `title ILIKE %query%`
   - `abstract ILIKE %query%`
   - Author/tag matches

#### 13.2 - User Settings Model & API (Backend)
| Task | Status | Notes |
|------|--------|-------|
| Database: `user_settings` singleton table | ✅ | Migration `3c4a09dd9c21` |
| Model: `UserSettings` | ✅ | backend/athena/models/settings.py |
| Service: `get_settings()` | ✅ | Creates default from .env |
| Service: `update_settings(data)` | ✅ | Partial updates, masked secrets |
| API: `GET /api/v2/system/settings` | ✅ | Returns masked keys |
| API: `PUT /api/v2/system/settings` | ✅ | Updates runtime config |
| Frontend: Settings service | ✅ | fetchSystemSettings, updateSystemSettings |
| Frontend: API Keys tab | ✅ | OpenAI, Semantic, CORE |
| Frontend: Providers tab | ✅ | Enable/disable checkboxes |
| Frontend: Proxy settings | ✅ | URL + enable switch |
| Reset: Clears user_settings | ✅ | system.py updated |

**Settings Schema:**
```python
user_settings:
  - openai_api_key (TEXT)
  - semantic_scholar_api_key (TEXT)
  - core_api_key (TEXT)
  - openalex_email (VARCHAR)
  - enabled_providers (JSONB)  # ["semantic", "openalex", ...]
  - proxy_url (VARCHAR)
  - proxy_enabled (BOOLEAN)
```

#### 13.3 - Provider & Proxy Integration (Backend Logic)
| Task | Status | Notes |
|------|--------|-------|
| SearchService: Dynamic settings loading | ✅ | DB-first, .env fallback |
| SearchService: Provider filtering | ✅ | Skips disabled providers |
| SearchService: Runtime injection | ✅ | API keys, email, proxy |
| SearchService: Post-filter by source | ✅ | Security layer |
| Router: DB dependency in /search | ✅ | `db: AsyncSession = Depends(get_db)` |
| Adapter: `configure_runtime(...)` | ✅ | base.py |
| Adapters: Proxy support | ⚠️ REMOVED (Sprint 13.6) | Only in downloader.py |
| Adapters: API key override | ✅ | Runtime > .env |
| Downloader: DB-based proxy | ✅ | tasks/downloader.py |
| Downloader: Proxy fallback | ✅ | .env if DB read fails |
| Tests: Runtime provider control | ✅ | test_search_runtime_provider_control.py (Sprint 13.6 ile güncellendi) |
| Tests: Proxy resolution | ✅ | test_downloader_proxy_resolution.py |

**Runtime Configuration Flow:**
1. User updates settings via UI
2. `PUT /api/v2/system/settings` writes to DB
3. Next search loads settings from DB
4. Providers are configured with runtime keys/proxy
5. PDF downloads use runtime proxy settings

#### 13.4 - Advanced Settings UI (Frontend)
| Task | Status | Notes |
|------|--------|-------|
| UI: Tabs-based page structure | ✅ | 3 tabs: Kaynaklar, Ağ/Proxy, Sistem |
| Tab 1: Provider enable/disable switches | ✅ | ShadCN Switch component |
| Tab 1: API key inputs | ✅ | Semantic, CORE, OpenAI |
| Tab 1: Email inputs | ✅ | OpenAlex, Crossref |
| Tab 1: arXiv note | ✅ | No authentication required |
| Tab 2: Proxy enable switch | ✅ | proxy_enabled |
| Tab 2: Proxy URL input | ✅ | proxy_url |
| Tab 2: Info note | ✅ | Institutional access instructions |
| Tab 3: Export section | ✅ | Moved from main page |
| Tab 3: Danger Zone (Reset) | ✅ | Moved from main page |
| Tab 3: Download management | ✅ | Preserved from previous sprint |
| Service: fetchSettings/updateSettings | ✅ | settings.ts |
| Backward compatibility: Aliases | ✅ | fetchSystemSettings still works |

#### 13.5 - Reset UX Improvement
| Task | Status | Notes |
|------|--------|-------|
| Success toast (5 seconds) | ✅ | "Sistem Sıfırlandı" message |
| Delayed redirect | ✅ | 3.5s delay before reload |
| Remove instant reload | ✅ | No more jarring UX |
| Error toast | ✅ | Shows backend error message |

### Pending Tests (DoD)

| Test | Type | Expected Result |
|------|------|------------------|
| Relevance ranking | Manual | "Learning" search ranks title matches higher |
| FTS fallback | Manual | Partial terms still return results |
| Provider switch | Manual | Disabled provider returns no results |
| Credential injection | Manual | API key appears in request headers |
| Proxy download | Manual | PDF downloads use DB proxy setting |
| Reset UX | Manual | Success toast shown, delayed redirect |
| Full Docker smoke test | Manual | All containers build and start cleanly |

---

## Sprint 12 Carry-over Items

These tests require manual validation in running environment:

- [ ] Export Test: Excel output has `Citation (APA)` filled
- [ ] Export Test: Non-downloaded papers show `Downloaded = HAYIR`
- [ ] ZIP Test: Downloaded `.zip` file extracts successfully
- [ ] ZIP Test: PDFs inside archive open correctly
- [ ] Search Test: Relevance ranking works as expected

---

## Known Issues

### Issue #1: Frontend npm Vulnerabilities
**Severity:** Medium (6 vulnerabilities: 2 moderate, 4 high)
**Status:** Deferred
**Reason:** Development dependencies, not production risk
**Action:** Run `npm audit fix` in next maintenance window

### Issue #2: Docker BuildKit Export Warnings
**Severity:** Low
**Status:** Mitigated
**Reason:** Some docker-compose versions don't support SBOM/provenance
**Workaround:** Use `BUILDX_NO_DEFAULT_ATTESTATIONS=1` flag

---

## Next Steps (Backlog)

### Sprint 16 (Proposed): Performance & Scale
- [ ] Redis-backed pagination (cursor-based)
- [ ] Search result caching
- [ ] Database query optimization (EXPLAIN ANALYZE)
- [ ] Celery worker autoscaling

### Sprint 17 (Proposed): Advanced Features
- [ ] Paper annotations/notes
- [ ] Sharing & collaboration
- [ ] Citation network visualization

### Sprint 18 (Proposed): Multi-tenancy
- [ ] User authentication
- [ ] Team/organization support
- [ ] Access control (RBAC)
- [ ] Quota management

---

## Testing Checklist

### Before Deployment
- [ ] All unit tests pass (`pytest`)
- [ ] Frontend builds without errors (`npm run build`)
- [ ] Alembic migrations apply cleanly (`alembic upgrade head`)
- [ ] Docker containers start successfully (`docker-compose up -d`)
- [ ] Health endpoint returns 200 (`GET /api/v2/health`)
- [ ] Frontend loads without console errors (http://localhost:3000)

### Smoke Tests
- [ ] Search returns results
- [ ] Paper can be added to library
- [ ] PDF download starts (check Celery logs)
- [ ] Library filters work (search, year, citations)
- [ ] Export downloads successfully (Excel, CSV)
- [ ] ZIP archive downloads and extracts
- [ ] Settings tab loads and saves
- [ ] Provider switches work
- [ ] Reset clears all data

### Regression Tests
- [ ] Existing library papers still visible
- [ ] Search deduplication still works
- [ ] Celery retries still happen
- [ ] Logs show request IDs

---

*For detailed sprint documentation, see `docs/sprints/sprint12.md` through `sprint16.md`*
