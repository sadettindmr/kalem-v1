# Release Notes

## v1.3.0 (2026-03-30)

### Added

- **Kütüphaneden Silme:** Makaleler kütüphaneden kalıcı olarak silinebilir hale geldi. PDF dosyaları da diskten temizlenir.
- **Projeden Çıkarma:** Koleksiyon görünümünde makaleler projeden çıkarılabilir (kütüphaneden silinmez).
- **Etiket Düzenleme:** Makale detay panelinde etiketler inline olarak düzenlenebilir.
- `DELETE /api/v2/library/{entry_id}` - Kütüphane kaydı + PDF silme endpoint'i.
- `DELETE /api/v2/collections/{cid}/entries/{eid}` - Koleksiyondan çıkarma endpoint'i.
- `PUT /api/v2/library/{entry_id}/tags` - Etiket güncelleme (overwrite) endpoint'i.
- LibraryItem kartlarına "Sil" (kırmızı) ve "Çıkar" (turuncu, koleksiyon seçiliyken) butonları eklendi.
- Silme işlemi öncesi onay dialog'u eklendi.
- PaperDetail'de kalem ikonu ile inline etiket düzenleme arayüzü eklendi.

### Technical Notes

- Backend:
  - `LibraryService.delete_library_entry()` - PDF temizliği + DB silme.
  - `LibraryService.update_tags()` - Tag overwrite (find-or-create).
  - `collections.py` router'a `remove_entry_from_collection` endpoint'i eklendi.
- Frontend:
  - `LibraryItem.tsx` - Dialog onay, Sil/Çıkar butonları (her zaman görünür, outline stil).
  - `PaperDetail.tsx` - Inline tag editor (Pencil ikon, Input, Kaydet/Vazgeç).
  - `LibraryList.tsx` - `deleteMutation`, `removeFromCollectionMutation` eklendi.
  - `library.ts` / `collections.ts` - Yeni API fonksiyonları.

---

## v1.2.0 (2026-03-30)

### Added

- **EZProxy Enstitü Erişimi:** Ücretli makaleleri üniversite kütüphane proxy'si üzerinden indirme desteği.
- Settings sayfasına "Enstitü Erişimi (EZProxy)" bölümü eklendi.
- EZProxy prefix URL ve oturum çerezi (cookie) yapılandırması.
- PDF indirici 401/402/403 hatalarında otomatik EZProxy fallback.

### Fixed

- CI workflow `snok/install-poetry` action ismi düzeltildi.

### Technical Notes

- Backend:
  - `UserSettings` modeline `ezproxy_prefix` ve `ezproxy_cookie` alanları eklendi.
  - Migration `7245dcd6adc4_add_ezproxy_settings.py` oluşturuldu.
  - `downloader.py`'ye EZProxy fallback helper fonksiyonları eklendi.
  - `_download_file()` metoduna `headers_override` parametresi eklendi.
- Frontend:
  - Network tab'a EZProxy konfigürasyon arayüzü eklendi.
  - TypeScript interface'leri güncellendi.
- CI:
  - `snoks/install-poetry` → `snok/install-poetry` typo düzeltildi.

---

## v1.1.3 (2026-03-30)

### Added

- Swagger UI / ReDoc dokümantasyonu zenginleştirildi (metadata, tag grupları, örnekler).
- API şemalarında kapsamlı örnek veri ve açıklamalar eklendi.

### Fixed

- Docker Compose’da `DEBUG` ortam değişkeni artık her ortamda geçerli boolean olacak şekilde sabitlendi.
- Kütüphane sayfası için sayfalama (pagination) eklendi.

### Technical Notes

- Backend:
  - OpenAPI metadata ve tag açıklamaları detaylandırıldı.
  - Router endpoint summary/response_description/docstring eklendi.
  - Schema alanlarında `Field` description/example iyileştirildi.
- Docker:
  - `DEBUG=false` ile backend startup hatası giderildi.

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
