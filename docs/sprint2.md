# Sprint 2 - Arama Altyapısı

## 📋 Sprint Özeti
**Amaç:** Akademik makale arama altyapısını oluşturmak - Pydantic şemaları, Adapter Pattern, API entegrasyonları ve servis katmanı.

**Durum:** ✅ Tamamlandı

---

## 🎯 Tamamlanan Prompt'lar

### Prompt 2.1 - Pydantic Şemaları (DTO)
- [x] `schemas/search.py` oluşturuldu
- [x] `PaperSource` enum: semantic, openalex, manual
- [x] `AuthorSchema`: Yazar bilgisi
- [x] `PaperResponse`: Makale yanıt modeli
- [x] `SearchFilters`: Arama filtreleri

### Prompt 2.2 - Adapter Pattern (Interface)
- [x] `adapters/base.py` oluşturuldu
- [x] `BaseSearchProvider` ABC tanımlandı
- [x] `search(filters) -> list[PaperResponse]` soyut metod

### Prompt 2.3 - Semantic Scholar Entegrasyonu
- [x] `adapters/semantic.py` oluşturuldu
- [x] `httpx` bağımlılığı eklendi
- [x] API: `https://api.semanticscholar.org/graph/v1/paper/search`
- [x] API Key desteği (`x-api-key` header)
- [x] Hata yönetimi (429, 500 → boş liste + log)

### Prompt 2.4 - OpenAlex Entegrasyonu
- [x] `adapters/openalex.py` oluşturuldu
- [x] `openalex_email` config ayarı eklendi
- [x] API: `https://api.openalex.org/works`
- [x] Polite Pool: User-Agent header

### Prompt 2.5 - SearchService
- [x] `services/search.py` oluşturuldu
- [x] `asyncio.gather` ile paralel arama
- [x] Sonuçları flatten (tek liste)
- [x] Deduplication (DOI/title bazlı)

### Prompt 2.6 - Search Endpoint (DoD)
- [x] `api/v2/routers/search.py` oluşturuldu
- [x] `POST /api/v2/search` endpoint'i
- [x] Router main.py'a include edildi

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Router                          │
│                  POST /api/v2/search                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     SearchService                            │
│  • asyncio.gather (paralel çalıştırma)                      │
│  • Flatten (sonuçları birleştir)                            │
│  • Deduplication (tekilleştir)                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│ SemanticScholarProvider│   │   OpenAlexProvider    │
│  • httpx AsyncClient  │   │  • httpx AsyncClient  │
│  • Timeout: 30s       │   │  • Polite Pool        │
└───────────────────────┘   └───────────────────────┘
            │                           │
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│   Semantic Scholar    │   │       OpenAlex        │
│        API            │   │         API           │
└───────────────────────┘   └───────────────────────┘
```

---

## 📊 API Endpoint

### POST /api/v2/search

**Request Body:**
```json
{
  "query": "machine learning",
  "year_start": 2020,
  "year_end": 2024,
  "min_citations": 10
}
```

**Response:**
```json
[
  {
    "title": "Attention Is All You Need",
    "abstract": "...",
    "year": 2017,
    "citation_count": 50000,
    "venue": "NeurIPS",
    "authors": [{"name": "Ashish Vaswani"}, ...],
    "source": "semantic",
    "external_id": "10.xxxx/xxxxx",
    "pdf_url": "https://..."
  }
]
```

---

## 🔑 API Ayarları (.env)

| Değişken | Açıklama |
|----------|----------|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API key (rate limit artırır) |
| `OPENALEX_EMAIL` | OpenAlex Polite Pool için email |
| `UNPAYWALL_EMAIL` | Unpaywall API için email |
| `OPENAI_API_KEY` | OpenAI API key |

---

## 🔧 Deduplication Kuralları

| Durum | Tekilleştirme Kriteri | Öncelik |
|-------|----------------------|---------|
| DOI var | DOI (lowercase) | Semantic Scholar |
| DOI yok | Title (lowercase) | Semantic Scholar |

---

## 📁 Oluşturulan/Değiştirilen Dosyalar

```
backend/
├── athena/
│   ├── main.py                      (güncellendi)
│   ├── api/v2/routers/
│   │   ├── __init__.py              (güncellendi)
│   │   └── search.py                (yeni)
│   ├── schemas/
│   │   ├── __init__.py              (güncellendi)
│   │   └── search.py                (yeni)
│   ├── adapters/
│   │   ├── __init__.py              (güncellendi)
│   │   ├── base.py                  (yeni)
│   │   ├── semantic.py              (yeni)
│   │   └── openalex.py              (yeni)
│   ├── services/
│   │   ├── __init__.py              (güncellendi)
│   │   └── search.py                (yeni)
│   └── core/
│       └── config.py                (güncellendi - contact_email)
└── pyproject.toml                   (güncellendi - httpx)
```

---

## 🆕 Eklenen Bağımlılıklar

| Paket | Versiyon | Açıklama |
|-------|----------|----------|
| httpx | ^0.27.0 | Async HTTP client |

---

## ✅ DoD Doğrulama

```bash
# 1. Uygulamayı başlat
cd backend
poetry run uvicorn athena.main:app --reload --port 8000

# 2. Swagger UI
http://localhost:8000/docs

# 3. Endpoint testi
curl -X POST "http://localhost:8000/api/v2/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Machine Learning", "year_start": 2023}'

# Beklenen:
# - JSON array döner
# - Hem semantic hem openalex kaynaklarından veri
# - Mükerrer DOI'ler elenmiş
```

---

*Sprint 2 Tamamlanma Tarihi: 2026-02-09*
