# Sprint 12 - Gelismis Disa Aktarim ve Arsivleme

## Sprint Ozeti
**Amac:** Kutuphane verilerini akademik standartlarda disa aktarmak, PDF arsivleme/indirme akislarini guclendirmek ve aramayi relevance odakli hale getirmek.

**Durum:** Devam Ediyor

---

## Tamamlanan Prompt'lar

### 12.1 - Gelismis Excel Export (Bibliyografik Veri)

#### Backend: ExportService Yeniden Yapilandirma
- [x] `backend/athena/services/export.py` Sprint 12.1 kolon yapisina gore guncellendi.
- [x] Yeni kolonlar eklendi:
  1. Makale Adı
  2. Yazar(lar)
  3. Yayın Yılı
  4. Makale Türü
  5. Yayın Platformu / Dergi
  6. DOI / Link
  7. Keywords
  8. Search Words
  9. Citation (APA)
  10. Citation (IEEE)
  11. Citation as of [bugun]
  12. Source
  13. Downloaded
  14. Kod/Veri Erişilebilirliği
- [x] Makale turu siniflandirmasi eklendi:
  - `venue` icinde "journal" -> "Dergi Makalesi"
  - `venue` icinde "conf" -> "Bildiri"
  - diger -> "Diğer"
- [x] DOI/Link secimi eklendi:
  - DOI varsa `https://doi.org/{doi}`
  - yoksa `pdf_url`
  - yoksa bos
- [x] APA formatlayici eklendi: `format_apa(...)`
- [x] IEEE formatlayici eklendi: `format_ieee(...)`
- [x] "Citation as of [BUGUN]" basligi dinamik tarih ile eklendi (`dd.mm.yyyy`)
- [x] "Downloaded" alani:
  - `completed` -> `EVET`
  - diger -> `HAYIR`
- [x] "Kod/Veri Erişilebilirliği" kontrolu:
  - `pdf_url` veya `abstract` icinde `github.com`, `gitlab.com`, `zenodo` -> `Muhtemelen Var`
  - aksi halde -> `Belirtilmemiş`
- [x] XLSX auto-width eklendi (kolon icerigine gore, max 80)

### 12.2 - Toplu PDF Indirme (ZIP Archive)

#### Backend: ZIP Endpoint
- [x] Endpoint eklendi: `GET /api/v2/library/download-zip`
- [x] Query filtreleri destekleniyor:
  - `search`, `tag`, `status`, `min_citations`, `year_start`, `year_end`
- [x] Filtre mantigi listeleme endpointi ile ortaklastirildi:
  - `_apply_library_filters(...)`
- [x] Sadece su kayitlar arsive ekleniyor:
  - `download_status == completed`
  - `file_path` dolu
  - fiziksel dosya mevcut (`resolve_data_file_path`)
- [x] ZIP uretilmesi:
  - `io.BytesIO` + `zipfile.ZipFile` in-memory
  - dosya adi formati: `{entry.id}_{filename}.pdf`
- [x] Streaming response:
  - `application/zip`
  - dosya adi: `kalem_library_archive_YYYYMMDD.zip`

#### Frontend: ZIP Indirme Aksiyonu
- [x] `LibraryList` header'a `PDF Arsivi Indir (.zip)` butonu eklendi
- [x] Buton mevcut library filtrelerini query string'e cevirip endpoint'e aciyor (`window.open`)
- [x] `Settings` > `Kutuphanemi Indir` alanina da `PDF Arsivi Indir (.zip)` butonu eklendi
- [x] Gorunurluk fallback'i saglandi:
  - Library header gorunmedigi durumlarda ayni aksiyon Ayarlar ekranindan tetiklenebilir

---

## Test Senaryolari ve Sonuclar (2026-02-15)

### Build / Teknik Dogrulama
- [x] `python3 -m compileall backend/athena` -> basarili
- [x] `cd backend && python3 -m pytest -q` -> `6 passed`
- [x] `cd frontend && npm run build` -> basarili
- [x] ZIP endpoint kod taramasi:
  - `download-zip`, `ZipFile`, `_apply_library_filters` noktalarinin eklendigi dogrulandi

### Manuel Fonksiyonel Senaryolar (Hazir)
- [ ] Export XLSX kolon yapisi testi
  - Adim: `GET /api/v2/library/export?format=xlsx`
  - Beklenen: 14 kolon, istenen basliklarla olusur
- [ ] Citation format testi (APA/IEEE)
  - Adim: Export dosyasinda ilgili satirlari kontrol et
  - Beklenen: best-effort formatlarda atif metni uretilir
- [ ] Dynamic citation date testi
  - Adim: dosya kolon basligini kontrol et
  - Beklenen: `Citation as of dd.mm.yyyy` formatinda bugunun tarihi yer alir
- [ ] Downloaded kolonu testi
  - Adim: `completed` ve `failed/pending` kayitlariyla export al
  - Beklenen: `EVET` / `HAYIR` dogru yazilir
- [ ] Kod/Veri Erişilebilirliği testi
  - Adim: `pdf_url` veya `abstract` icinde `github.com` gecen kayitla export al
  - Beklenen: `Muhtemelen Var`
- [ ] ZIP indirme (filtrelenmis)
  - Adim: Kutuphane filtrele (ornek: tag + yil), `PDF Arsivi Indir (.zip)` butonuna tikla
  - Beklenen: `kalem_library_archive_YYYYMMDD.zip` indirilir
- [ ] ZIP icerik kontrolu
  - Adim: indirilen ZIP'i ac
  - Beklenen: sadece `completed + mevcut file_path` kayitlari vardir
  - Beklenen: dosya adlari `entryid_filename.pdf` formatindadir
- [ ] ZIP endpoint dogrudan API testi
  - Adim: `GET /api/v2/library/download-zip?search=<terim>&year_start=2020`
  - Beklenen: `application/zip` doner

---

## Degisiklik Yapilan Dosyalar
- `backend/athena/services/export.py` - Sprint 12.1 bibliyografik export mantigi
- `backend/athena/api/v2/routers/library.py` - Sprint 12.2 ZIP archive endpointi + ortak filtre uygulayici
- `frontend/src/components/LibraryList.tsx` - Sprint 12.2 ZIP indirme butonu + filtreli query string
- `docs/sprint12.md` - Sprint 12 dokumantasyonu (yeni)
