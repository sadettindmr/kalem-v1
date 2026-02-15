# Sprint 10 - Arama Motoru Optimizasyonu

## Sprint Ozeti
**Amac:** Semantic Scholar adapter'ini standart endpoint'e gecirmek, tum kaynaklarin sonuc limitlerini artirmak, deduplication mantigi ve kelime eslesmesini iyilestirmek, frontend pagination ve toplu ekleme ozelliklerini guncellemek.

**Durum:** Tamamlandi

---

## Tamamlanan Prompt'lar

### 10.1 - Semantic Scholar Adapter Yeniden Yapilandirma
- [x] `/paper/search/bulk` → `/paper/search` (standart endpoint)
- [x] `sort: citationCount:desc` kaldirildi → API varsayilan keyword relevance siralamasi
- [x] Token-bazli pagination → offset + limit pagination (100/sayfa, max 1000)
- [x] `asyncio.sleep(0.5)` rate limit onleme eklendi
- [x] Server-side `year` ve `minCitationCount` filtreleri korundu
- [x] Hata yonetimi: HTTP hatalarinda kismi sonuc dondurme
- [x] Timeout: 60 saniye

### 10.2 - Diger Kaynak Limitlerini Artirma
- [x] `arxiv.py`: `MAX_RESULTS: 500 → 1000`, `asyncio.sleep(0.5)` eklendi
- [x] `crossref.py`: `MAX_RESULTS: 500 → 1000`, `asyncio.sleep(0.5)` eklendi
- [x] `core.py`: `MAX_RESULTS: 500 → 1000`, `asyncio.sleep(0.5)` eklendi
- [x] Tum kaynaklardan 1000'er sonuc toplanabilir durumda

### 10.3 - Deduplication ve Kelime Eslesmesi Iyilestirmesi
- [x] `_normalize_title()` fonksiyonu eklendi:
  - Unicode normalizasyonu (aksanli → ASCII)
  - Noktalama isaretlerini kaldirma
  - Stop word temizleme (the, a, an, of, in, on, for, and, or, to, with)
  - Ornek: "Deep Learning: A Review" == "deep learning review"
- [x] 2 adimli cross-source dedup:
  - Adim 1: DOI eslesmesi (kesin)
  - Adim 2: Normalized title eslesmesi
- [x] `_filter_by_relevance()` keyword filtresi eklendi:
  - Virgullerle ayrilmis konsept gruplari → AND mantigi
  - Her gruptan en az bir kelime baslik/ozette gecmeli
  - Alakasiz/spam sonuclar elenir
- [x] Fuzzy match (SequenceMatcher %95) eklendi ancak O(n²) performans sorunu nedeniyle kaldirildi
  - DOI + normalized title zaten yeterli dedup sagliyor

### 10.4 - Frontend Guncellemeleri
- [x] `itemsPerPage: 50 → 100` (sayfa basina 100 sonuc)
- [x] "Tumunu Ekle" butonu: Tum arama sonuclarini kutupaneye ekleme
  - Onay dialog'u (makale sayisi ve paket bilgisi)
  - 100'erli batching ile API'ye gonderim
  - Progress gostergesi (1/32, 2/32...)
  - Detayli sonuc toast mesaji
- [x] Axios timeout: `30s → 180s` (5 kaynak paralel arama icin)
- [x] Nginx proxy timeout: `60s → 180s` (proxy_read_timeout, proxy_send_timeout)

### 10.5 - Performans Duzeltmesi (Timeout Sorunu)
- [x] Fuzzy match O(n²) performans darbogazinin tespiti ve kaldirilmasi
  - 4000 paper icin ~107 saniye → <1 saniye
  - SequenceMatcher 8 milyon karsilastirma yapiyordu
- [x] Toplam arama suresi: ~130 saniye → ~20 saniye
- [x] Tum timeout degerleri tutarli hale getirildi (180s)

### 10.6 - Hata Toleransi (Provider Error Handling)
- [x] `asyncio.gather(*tasks, return_exceptions=True)` zaten mevcut - Exception parse iyilestirildi
- [x] Provider mapping ile okunabilir hata mesajlari (provider_raw_keys dict)
- [x] Exception durumunda `logger.error()` ile loglama
- [x] Hata veren provider icin `raw_count = 0` atanmasi
- [x] `SearchMeta.errors: list[str]` alani eklendi (frontend'e hata bilgisi)
- [x] Test: SS timeout simülasyonunda diger 3 kaynak sorunsuz calisti (2671 sonuc)

### 10.7 - Bug Fix: Validation Hatalari ve Coklu Anahtar Kelime
- [x] `BulkIngestRequest.papers` limiti `max_length: 50 → 100` (frontend BATCH_SIZE=100 ile uyumlu)
  - Frontend 100'erli batch gonderiyordu, backend 50 limitiyle reddediyordu (422 hatasi)
- [x] `_filter_by_relevance()` AND mantigi eklendi:
  - Virgullerle ayrilmis terimler konsept gruplarina bolunuyor
  - "federated learning, sepsis" → [["federated", "learning"], ["sepsis"]]
  - Her konsept grubundan en az bir kelime baslik/ozette gecmeli
  - Ornek: 3472 ham sonuc → 123 alakali sonuc (her iki konuyu iceren)
- [x] Tek kelime aramalarda davranis degismedi (geriye uyumlu)
- [x] `CheckLibraryRequest.external_ids` limiti `max_length: 1000 → 5000`
  - Dedup sonrasi ~3100 sonucun ~2057 unique external_id'si vardi, 1000 limitini asiyordu (422 hatasi)
  - 5 kaynaktan max 5000 sonuc gelebilecegi icin limit 5000'e cikarildi

---

## Mimari

### Adapter Limitleri (Guncellenmis)

| Adapter | API URL | Pagination | Max | Rate Limit |
|---------|---------|-----------|-----|------------|
| SemanticScholarProvider | `/graph/v1/paper/search` | offset+limit (100/sayfa) | 1000 | 0.5s/istek |
| OpenAlexProvider | `api.openalex.org/works` | cursor pagination (100/sayfa) | 1000 | Polite Pool |
| ArxivProvider | `export.arxiv.org/api/query` | start+max_results (100/sayfa) | 1000 | 0.5s/istek |
| CrossrefProvider | `api.crossref.org/works` | offset+rows (100/sayfa) | 1000 | 0.5s/istek |
| CoreProvider | `api.core.ac.uk/v3/search/works` | offset+limit (100/sayfa) | 1000 | 0.5s/istek |

### Deduplication Pipeline

```
4000 ham sonuc (5 kaynaktan)
  → Keyword Relevance Filter (~100 alakasiz elenir)
  → DOI Dedup (kesin eslesme, O(1) hash lookup)
  → Normalized Title Dedup (agresif temizleme + hash lookup)
  → ~3150 tekil sonuc (~750 duplikasyon + ~100 alakasiz)
```

### Title Normalizasyonu

```python
"Deep Learning: A Review"          → "deep learning review"
"The Impact of AI on Healthcare"   → "impact ai healthcare"
"Über die Quantenmechanik"         → "uber quantenmechanik"
```

### Timeout Zinciri

| Katman | Timeout | Aciklama |
|--------|---------|----------|
| httpx (adapter) | 60s | Her bir API istegi |
| Axios (frontend) | 180s | Frontend → nginx |
| nginx proxy | 180s | nginx → backend |
| uvicorn | Yok | Backend isleme suresi |

---

## Test Sonuclari

### Arama Performansi ("deep learning")

| Metrik | Sprint 9 Sonrasi | Sprint 10 Sonrasi |
|--------|-----------------|-------------------|
| SS ham | 1000 | 1000 |
| OpenAlex ham | 1000 | 1000 |
| arXiv ham | 500 | **1000** |
| Crossref ham | 500 | **1000** |
| CORE ham | 0 | 0 |
| Toplam ham | 3000 | **4000** |
| Duplikasyon elenen | 432 | **726** |
| Relevance elenen | 0 | **~108** |
| Final sonuc | 2568 | **~3150** |
| Arama suresi | ~25s | **~20s** |
| Keyword relevance | Yok | **Konsept grubu AND mantigi** |

### Coklu Anahtar Kelime Testi ("federated learning, sepsis")

| Metrik | Deger |
|--------|-------|
| SS ham | 1000 |
| OpenAlex ham | 472 |
| arXiv ham | 1000 |
| Crossref ham | 1000 |
| Toplam ham | 3472 |
| Relevance elenen | **3296** |
| Dedup elenen | 53 |
| Final sonuc | **123** |

### Dedup Dogrulugu
- Tekrarlayan DOI: **0** (sifir duplikasyon)
- Tekrarlayan normalized title: **0** (sifir duplikasyon)

---

## Degisiklik Yapilan Dosyalar

### Backend
- `athena/adapters/semantic.py` - Bulk → standart endpoint, offset pagination, relevance siralama
- `athena/adapters/arxiv.py` - MAX_RESULTS: 500→1000, asyncio.sleep(0.5)
- `athena/adapters/crossref.py` - MAX_RESULTS: 500→1000, asyncio.sleep(0.5)
- `athena/adapters/core.py` - MAX_RESULTS: 500→1000, asyncio.sleep(0.5)
- `athena/services/search.py` - _normalize_title, 2-adimli dedup, _filter_by_relevance (AND mantigi), hata toleransi
- `athena/schemas/search.py` - SearchMeta.errors alani eklendi
- `athena/api/v2/routers/library.py` - BulkIngestRequest.papers max_length: 50→100, CheckLibraryRequest.external_ids max_length: 1000→5000

### Frontend
- `src/stores/ui-store.ts` - itemsPerPage: 50→100
- `src/components/PaperList.tsx` - "Tumunu Ekle" butonu, onay dialog, batching
- `src/lib/api.ts` - timeout: 30s→180s

### Altyapi
- `nginx.frontend.conf` - proxy timeout: 180s
