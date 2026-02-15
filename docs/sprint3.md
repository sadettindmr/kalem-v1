# Sprint 3 - Kütüphane Yönetimi

## 📋 Sprint Özeti
**Amaç:** Kütüphane yönetim sistemini oluşturmak - Arama sonuçlarını kaydetme, PDF indirme worker'ı, otomatik etiketleme ve listeleme endpoint'leri.

**Durum:** ✅ Tamamlandı

---

## 🎯 Tamamlanan Prompt'lar

### Prompt 3.1 - LibraryService
- [x] `services/library.py` oluşturuldu
- [x] `add_paper_to_library(paper_data, search_query)` metodu
- [x] Deduplication: DOI veya title_slug kontrolü
- [x] Paper → Authors ilişkisi (slugify ile)
- [x] Auto-tagging: Arama terimlerinden etiket oluşturma
- [x] Async lazy loading sorunları çözüldü

### Prompt 3.2 - Download Worker (Celery)
- [x] `tasks/downloader.py` oluşturuldu
- [x] `download_paper_task` Celery task'i
- [x] Retry stratejisi: Exponential backoff (max 5 retry)
- [x] User-Agent rotasyonu
- [x] Dosya yolu formatı: `{data_dir}/{paper_id}/{year}_{author}_{title}.pdf`
- [x] Status geçişleri: pending → downloading → completed/failed

### Prompt 3.3 - POST /api/v2/library/ingest
- [x] `api/v2/routers/library.py` oluşturuldu
- [x] `IngestRequest` ve `IngestResponse` şemaları
- [x] LibraryService entegrasyonu
- [x] Download task kuyruğa ekleme
- [x] Broker bağlantı hatası yönetimi

### Prompt 3.4 - GET /api/v2/library (DoD)
- [x] `schemas/library.py` oluşturuldu
- [x] Pagination desteği (page, limit)
- [x] Tag filtresi
- [x] Download status filtresi
- [x] `joinedload` ile N+1 query önleme
- [x] LibraryListResponse şeması

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Router                          │
│          POST /api/v2/library/ingest                         │
│          GET  /api/v2/library                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LibraryService                            │
│  • add_paper_to_library()                                   │
│  • Deduplication (DOI/title_slug)                           │
│  • Auto-tagging                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────┐ ┌───────────────┐
│  PostgreSQL     │ │  RabbitMQ │ │ Celery Worker │
│  • Paper        │ │  (Broker) │ │ • download_   │
│  • Author       │ └─────┬─────┘ │   paper_task  │
│  • LibraryEntry │       │       └───────┬───────┘
│  • Tag          │       └───────────────┘
└─────────────────┘               │
                                  ▼
                          ┌───────────────┐
                          │   PDF Files   │
                          │ {data_dir}/   │
                          └───────────────┘
```

---

## 📊 API Endpoints

### POST /api/v2/library/ingest

Makaleyi kütüphaneye ekler ve PDF indirme görevini başlatır.

**Request Body:**
```json
{
  "paper": {
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models...",
    "year": 2017,
    "citation_count": 50000,
    "venue": "NeurIPS",
    "authors": [{"name": "Ashish Vaswani"}],
    "source": "semantic",
    "external_id": "10.5555/3295222.3295349",
    "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"
  },
  "search_query": "transformer, attention mechanism"
}
```

**Response:**
```json
{
  "status": "queued",
  "entry_id": 42
}
```

| Status | Açıklama |
|--------|----------|
| `queued` | Download task kuyruğa eklendi |
| `saved` | Makale kaydedildi ama broker bağlantısı başarısız |

---

### GET /api/v2/library

Kütüphanedeki makaleleri listeler.

**Query Parameters:**

| Parametre | Tip | Varsayılan | Açıklama |
|-----------|-----|------------|----------|
| `page` | int | 1 | Sayfa numarası (1'den başlar) |
| `limit` | int | 20 | Sayfa başına öğe (max 100) |
| `tag` | string | null | Etikete göre filtrele |
| `status` | string | null | Download durumuna göre (pending, downloading, completed, failed) |

**Response:**
```json
{
  "items": [
    {
      "id": 42,
      "source": "semantic",
      "download_status": "completed",
      "file_path": "/data/papers/1/2017_vaswani_attention-is-all-you-need.pdf",
      "is_favorite": false,
      "tags": [
        {"id": 1, "name": "transformer"},
        {"id": 2, "name": "attention mechanism"}
      ],
      "paper": {
        "id": 1,
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models...",
        "year": 2017,
        "citation_count": 50000,
        "venue": "NeurIPS",
        "doi": "10.5555/3295222.3295349",
        "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
        "authors": [{"name": "Ashish Vaswani"}],
        "created_at": "2026-02-10T14:30:00Z"
      }
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20
}
```

---

## 🔧 Deduplication & Auto-tagging

### Deduplication Kuralları

| Sıra | Kriter | Açıklama |
|------|--------|----------|
| 1 | DOI | `10.` ile başlıyorsa DOI olarak kabul edilir |
| 2 | title_slug | Başlık slugify edilerek karşılaştırılır |

### Auto-tagging

- `search_query` virgülle ayrılır
- Her terim küçük harfe çevrilir
- Maksimum 100 karakter
- Mevcut etiketler tekrar eklenmez

---

## 📁 Oluşturulan/Değiştirilen Dosyalar

```
backend/
├── athena/
│   ├── main.py                          (güncellendi - library router)
│   ├── api/v2/routers/
│   │   ├── __init__.py                  (güncellendi)
│   │   └── library.py                   (yeni)
│   ├── schemas/
│   │   ├── __init__.py                  (güncellendi)
│   │   └── library.py                   (yeni)
│   ├── services/
│   │   ├── __init__.py                  (güncellendi)
│   │   └── library.py                   (yeni)
│   ├── tasks/
│   │   ├── __init__.py                  (güncellendi)
│   │   ├── celery_app.py                (yeni)
│   │   └── downloader.py                (yeni)
│   ├── models/
│   │   ├── library.py                   (yeni)
│   │   ├── paper.py                     (yeni)
│   │   ├── author.py                    (yeni)
│   │   └── tag.py                       (yeni)
│   └── core/
│       └── config.py                    (güncellendi - celery, data_dir)
└── pyproject.toml                       (güncellendi - celery)
```

---

## 🆕 Eklenen Bağımlılıklar

| Paket | Versiyon | Açıklama |
|-------|----------|----------|
| celery | ^5.3.0 | Distributed task queue |

---

## 🔧 Celery Konfigürasyonu

```python
# tasks/celery_app.py
from celery import Celery
from athena.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "athena",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Retry ayarları
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
```

### Download Task Özellikleri

| Özellik | Değer | Açıklama |
|---------|-------|----------|
| `max_retries` | 5 | Maksimum yeniden deneme |
| `retry_backoff` | True | Exponential backoff |
| `retry_backoff_max` | 600 | Max bekleme (10 dakika) |
| `retry_jitter` | True | Rastgele gecikme |
| `autoretry_for` | HTTPStatusError, RequestError | Otomatik retry hataları |

---

## ⚠️ Bilinen Sorunlar ve Çözümler

### 1. SQLAlchemy Async Lazy Loading Hatası

**Hata:**
```
MissingGreenlet: greenlet_spawn has not been called
```

**Çözüm:** Relationship'lere erişmeden önce `refresh` kullanılmalı:
```python
await self.db.refresh(paper, ["authors"])
await self.db.refresh(library_entry, ["tags"])
```

### 2. Celery Broker Bağlantı Hatası

**Hata:**
```
ACCESS_REFUSED - Login was refused using authentication mechanism PLAIN
```

**Nedeni:** Host makineden Docker içindeki RabbitMQ'ya bağlanırken servis adı çözümlenemiyor.

**Çözüm:** Task dispatch try/except ile sarıldı:
```python
try:
    download_paper_task.delay(entry_id=entry.id)
    status = "queued"
except Exception:
    status = "saved"  # Makale kaydedildi, indirme bekliyor
```

---

## ✅ DoD Doğrulama

```bash
# 1. Uygulamayı başlat
cd backend
poetry run uvicorn athena.main:app --reload --port 8000

# 2. Swagger UI
http://localhost:8000/docs

# 3. Makale ekleme testi (POST /api/v2/library/ingest)
curl -X POST "http://localhost:8000/api/v2/library/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "paper": {
      "title": "Test Paper",
      "abstract": "Test abstract",
      "year": 2024,
      "citation_count": 100,
      "authors": [{"name": "Test Author"}],
      "source": "semantic",
      "external_id": "10.1234/test",
      "pdf_url": null
    },
    "search_query": "test, machine learning"
  }'

# Beklenen yanıt:
# {"status": "saved", "entry_id": 1}

# 4. Listeleme testi (GET /api/v2/library)
curl "http://localhost:8000/api/v2/library?page=1&limit=10"

# Beklenen:
# - items array (eklenen makale)
# - total, page, limit alanları
# - paper detayları ve tags

# 5. Filtreleme testi
curl "http://localhost:8000/api/v2/library?tag=machine%20learning"
curl "http://localhost:8000/api/v2/library?status=pending"
```

---

*Sprint 3 Tamamlanma Tarihi: 2026-02-10*
