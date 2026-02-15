# Release Notes

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
