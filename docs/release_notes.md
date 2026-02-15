# Release Notes

## v1.0.2 (2026-02-15)

### Fixed
- Search result totals for multi-term queries are now more stable across repeated runs.
- Added a retry path for arXiv low-result anomalies (for broad/multi-term queries) to reduce sudden drops like `107 -> 61`.

### Investigation Summary
- Query checked: `federated learning, sepsis` (`year_start=2020`, `year_end=2026`).
- Intermittent result drop was observed from arXiv raw count fluctuations (`833` vs `83`) while other providers stayed stable.
- Dedup/relevance math remained consistent; the volatility source was upstream provider response variability.

### Technical Notes
- Backend:
  - `ArxivProvider.search` now retries once when a multi-term query returns unexpectedly low result count.
  - Retry uses short backoff and preserves existing parsing/filter logic.

## v1.0.1-p1 (2026-02-15)

### Added
- Settings page now includes a new `Hakkinda` subsection under the `Sistem` tab.
- Header logo area now shows the application version directly below the app name.

### Technical Notes
- Frontend:
  - Added centralized app constants: `APP_NAME`, `APP_VERSION`.
  - Version label rendered in dashboard header.
  - About card rendered in settings system tab.

## v1.0.1 (2026-02-15)

### Fixed
- Search result metrics are now more transparent in the UI:
  - Added `relevance_removed` to search metadata payload.
  - Added `Alaka disi elenen` row in the search sidebar to show relevance-based eliminations.
- This clarifies the count flow for users:
  - `Ham kaynak sonuclari - Alaka disi elenen - Mukerrer elenen = Toplam`

### Changed
- Project release version updated to `v1.0.1` in application-facing version references.

### Technical Notes
- Backend:
  - `/api/v2/search` response `meta` now includes `relevance_removed`.
- Frontend:
  - Sidebar statistics panel renders `relevance_removed` when greater than zero.
