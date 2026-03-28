# Current Sprint Tasks

**Last Updated:** 2026-03-28
**Active Sprints:** Sprint 12, Sprint 13

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

**Status:** In Progress (Testing Phase)
**Goal:** Implement PostgreSQL full-text search, database-backed runtime settings, and dynamic provider control.

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
| Adapters: Proxy support | ✅ | All providers |
| Adapters: API key override | ✅ | Runtime > .env |
| Downloader: DB-based proxy | ✅ | tasks/downloader.py |
| Downloader: Proxy fallback | ✅ | .env if DB read fails |
| Tests: Runtime provider control | ✅ | test_search_runtime_provider_control.py |
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

### Sprint 14 (Proposed): Performance & Scale
- [ ] Redis-backed pagination (cursor-based)
- [ ] Search result caching
- [ ] Database query optimization (EXPLAIN ANALYZE)
- [ ] Celery worker autoscaling

### Sprint 15 (Proposed): Advanced Features
- [ ] Paper annotations/notes
- [ ] Collections/folders
- [ ] Sharing & collaboration
- [ ] Citation network visualization

### Sprint 16 (Proposed): Multi-tenancy
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

*For detailed sprint documentation, see `/sprints/sprint12.md` and `/sprints/sprint13.md`*
