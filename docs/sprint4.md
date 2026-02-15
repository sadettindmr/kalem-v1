# Sprint 4 - Hata Yönetimi ve Loglama

## 📋 Sprint Özeti
**Amaç:** Hata yönetimi altyapısı, yapılandırılmış loglama, kütüphane dışa aktarma ve sistem sıfırlama özelliklerini eklemek.

**Durum:** ✅ Tamamlandı

---

## 🎯 Tamamlanan Prompt'lar

### Prompt 4.1 - Standart Hata Yönetimi
- [x] `core/exceptions.py` güncellendi
- [x] `ErrorCode` enum tanımlandı (13 hata kodu)
- [x] `AthenaError` base class oluşturuldu
- [x] Alt sınıflar: `ProviderError`, `LibraryError`, `ValidationError`, `DownloadError`
- [x] `schemas/error.py` oluşturuldu (ErrorDetail, ErrorResponse)
- [x] 4 global exception handler main.py'a eklendi

### Prompt 4.2 - Structured Logging
- [x] `core/logging.py` oluşturuldu (Loguru yapılandırması)
- [x] `core/middleware.py` oluşturuldu (RequestLoggingMiddleware)
- [x] `config.py`'a `log_level` ayarı eklendi
- [x] Production: JSON format log output
- [x] Development: Renkli console output
- [x] Her istek için unique `request_id` (UUID)
- [x] Process time ölçümü (ms)
- [x] Correlation ID: Hata yanıtlarına `request_id` eklendi

### Prompt 4.3 - Library Export
- [x] `services/export.py` oluşturuldu (ExportService)
- [x] `pandas` ve `openpyxl` bağımlılıkları eklendi
- [x] `GET /api/v2/library/export` endpoint'i eklendi
- [x] CSV ve XLSX format desteği
- [x] Tag filtresi ile filtreleme
- [x] StreamingResponse ile dosya indirme
- [x] TDD Bölüm 3.5'e uygun 9 sütun

### Prompt 4.4 - System Reset (DoD)
- [x] `POST /api/v2/system/reset` endpoint'i eklendi
- [x] Güvenlik kontrolü: "DELETE-ALL-DATA" onay kodu
- [x] Yanlış kod → 403 Forbidden
- [x] Veritabanı temizleme: TRUNCATE CASCADE (6 tablo)
- [x] Dosya temizleme: /data/library/ klasörü
- [x] CRITICAL seviyesinde loglama

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│              (main.py - Global Exception Handlers)           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                  RequestLoggingMiddleware                    │
│  • UUID request_id                                          │
│  • Process time (ms)                                        │
│  • X-Request-ID header                                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────────┐ ┌───────────────────┐
│  Error Handler  │ │    Loguru     │ │   ExportService   │
│  • AthenaError  │ │  • JSON/Color │ │  • CSV            │
│  • HTTP Error   │ │  • Levels     │ │  • XLSX           │
│  • Validation   │ │  • Context    │ │  • Pandas         │
└─────────────────┘ └───────────────┘ └───────────────────┘
```

---

## 📊 API Endpoints

### POST /api/v2/system/reset

⚠️ Sistemi fabrika ayarlarına döndürür (GERİ ALINAMAZ!)

**Request Body:**
```json
{
  "confirmation": "DELETE-ALL-DATA"
}
```

**Response (200 OK):**
```json
{
  "status": "system_reset_completed",
  "deleted_files_count": 15
}
```

**Response (403 Forbidden):**
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Geçersiz onay kodu...",
    "request_id": "..."
  }
}
```

---

### GET /api/v2/library/export

**Query Parameters:**
| Parametre | Tip | Default | Açıklama |
|-----------|-----|---------|----------|
| `format` | string | xlsx | "csv" veya "xlsx" |
| `search_query` | string | - | Etiket filtresi |

**Response Headers:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="athena_library_export.xlsx"
```

**Export Sütunları (TDD Bölüm 3.5):**
| # | Sütun | Açıklama |
|---|-------|----------|
| 1 | ID | LibraryEntry ID |
| 2 | Title | Makale başlığı |
| 3 | Authors | Yazarlar (virgülle ayrılmış) |
| 4 | Year | Yayın yılı |
| 5 | Venue | Yayınlandığı yer |
| 6 | DOI | Digital Object Identifier |
| 7 | Citation Count | Atıf sayısı |
| 8 | Source | semantic, openalex, manual |
| 9 | Tags | Etiketler (virgülle ayrılmış) |

---

## 🔧 Hata Kodları (ErrorCode)

| Kod | HTTP | Açıklama |
|-----|------|----------|
| `INTERNAL_ERROR` | 500 | Beklenmeyen sunucu hatası |
| `VALIDATION_ERROR` | 422 | Veri doğrulama hatası |
| `NOT_FOUND` | 404 | Kaynak bulunamadı |
| `PROVIDER_TIMEOUT` | 503 | Dış servis zaman aşımı |
| `PROVIDER_RATE_LIMIT` | 429 | API rate limit aşıldı |
| `PROVIDER_UNAVAILABLE` | 503 | Dış servis kullanılamıyor |
| `PROVIDER_INVALID_RESPONSE` | 502 | Geçersiz API yanıtı |
| `LIBRARY_DUPLICATE` | 409 | Makale zaten kütüphanede |
| `LIBRARY_NOT_FOUND` | 404 | Kütüphane kaydı bulunamadı |
| `DOWNLOAD_NO_PDF_URL` | 400 | PDF URL'i yok |
| `DOWNLOAD_FAILED` | 500 | İndirme başarısız |
| `DOWNLOAD_TIMEOUT` | 504 | İndirme zaman aşımı |

---

## 📝 Standart Hata Yanıtı

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "İstek verisi doğrulanamadı",
    "suggestion": "Lütfen gönderdiğiniz verileri kontrol edin",
    "details": "body -> query: Field required",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 🔧 Logging Yapılandırması

### Environment Variables (.env)
```bash
DEBUG=True          # Development mode (renkli log)
LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR
```

### Log Formatları

**Development (Renkli):**
```
2026-02-11 21:26:53 | INFO     | abc123... | athena.main | Request completed
```

**Production (JSON):**
```json
{
  "time": "2026-02-11T21:26:53",
  "level": "INFO",
  "request_id": "abc123...",
  "message": "Request completed",
  "method": "GET",
  "path": "/api/v2/library",
  "status_code": 200,
  "process_time_ms": 45.23
}
```

---

## 📁 Oluşturulan/Değiştirilen Dosyalar

```
backend/
├── athena/
│   ├── main.py                          (güncellendi - exception handlers, middleware)
│   ├── api/v2/routers/
│   │   └── system.py                    (güncellendi - reset endpoint)
│   ├── core/
│   │   ├── __init__.py                  (güncellendi - export'lar)
│   │   ├── config.py                    (güncellendi - log_level)
│   │   ├── exceptions.py                (güncellendi - ErrorCode, exception classes)
│   │   ├── logging.py                   (yeni)
│   │   └── middleware.py                (yeni)
│   ├── services/
│   │   ├── __init__.py                  (güncellendi)
│   │   └── export.py                    (yeni)
│   └── schemas/
│       ├── __init__.py                  (güncellendi)
│       └── error.py                     (yeni)
└── pyproject.toml                       (güncellendi - pandas, openpyxl)
```

---

## 🆕 Eklenen Bağımlılıklar

| Paket | Versiyon | Açıklama |
|-------|----------|----------|
| pandas | ^2.2.0 | DataFrame işlemleri |
| openpyxl | ^3.1.0 | XLSX dosya yazma |

---

## ✅ DoD Doğrulama

```bash
# 1. Uygulamayı başlat
cd backend
poetry run uvicorn athena.main:app --reload --port 8000

# 2. TEST 1: Hata formatı kontrolü (eksik parametre)
curl -X POST "http://localhost:8000/api/v2/system/reset" \
  -H "Content-Type: application/json" \
  -d '{}'

# Beklenen: 422 - {"success": false, "error": {"code": "VALIDATION_ERROR", ...}}

# 3. TEST 2: Export UTF-8 kontrolü
curl -o test.csv "http://localhost:8000/api/v2/library/export?format=csv"
# Excel veya metin editörde aç - Türkçe karakterler düzgün görünmeli

# 4. TEST 3a: Yanlış şifre
curl -X POST "http://localhost:8000/api/v2/system/reset" \
  -H "Content-Type: application/json" \
  -d '{"confirmation": "reset"}'

# Beklenen: 403 Forbidden

# 5. TEST 3b: Doğru şifre
curl -X POST "http://localhost:8000/api/v2/system/reset" \
  -H "Content-Type: application/json" \
  -d '{"confirmation": "DELETE-ALL-DATA"}'

# Beklenen: {"status": "system_reset_completed", "deleted_files_count": X}

# 6. Doğrulama: Veritabanı boş
curl "http://localhost:8000/api/v2/library"

# Beklenen: {"items": [], "total": 0, "page": 1, "limit": 20}
```

---

*Sprint 4 Tamamlanma Tarihi: 2026-02-11*
