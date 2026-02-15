# Project Athena v2.0.0 - Gemini Reference Document

## Proje Bilgileri
- **Versiyon**: 2.0.0-develop
- **Mimari**: Modüler Monolit
- **Python**: ^3.11
- **Framework**: FastAPI
- **Branch**: `v2.0.0-develop`

## Genel Bakış
Project Athena, akademik makaleleri aramak, kişisel bir kütüphaneye kaydetmek, PDF'lerini indirmek ve bu kütüphaneyi yönetmek için geliştirilmiş bir backend servisidir. FastAPI üzerine kurulu modüler bir monolit mimariye sahiptir. Docker ile PostgreSQL, Redis ve RabbitMQ servislerini kullanır.

## Dizin Yapısı ve Modüller

| Modül | Açıklama |
|---|---|
| `main.py` | FastAPI uygulamasının giriş noktası. Middleware ve router'lar burada yapılandırılır. |
| `api/v2/routers/` | API endpoint tanımlarının (router) bulunduğu dizin. `library.py`, `search.py`, `system.py` dosyalarını içerir. |
| `core/` | Uygulamanın çekirdek bileşenleri: veritabanı bağlantısı (`database.py`), Pydantic ile ayar yönetimi (`config.py`), global hata yönetimi (`exceptions.py`), yapılandırılmış loglama (`logging.py`) ve request middleware (`middleware.py`). |
| `services/` | İş mantığının (business logic) bulunduğu katman. `SearchService`, `LibraryService`, `ExportService` gibi servisleri barındırır. |
| `adapters/` | Dış dünya ile entegrasyonu sağlayan katman (Adapter Pattern). `SemanticScholarProvider` ve `OpenAlexProvider` gibi arama motoru entegrasyonlarını içerir. |
| `repositories/` | Veritabanı erişim katmanı (henüz tam olarak implemente edilmemiş, mantık servis katmanında). |
| `models/` | SQLAlchemy ORM modelleri. `Paper`, `Author`, `LibraryEntry`, `Tag` gibi veritabanı tablolarını tanımlar. |
| `schemas/` | Pydantic şemaları. API istek ve yanıt gövdeleri için veri transfer nesneleri (DTO) olarak kullanılır. |
| `tasks/` | Arka plan görevleri (Celery). `downloader.py` içinde PDF indirme task'ı bulunur. |
| `migrations/` | Alembic veritabanı göç (migration) dosyaları. |

## Temel Özellikler ve API Endpoints

### 1. Arama (`/api/v2/search`)
- **Method:** `POST`
- **Açıklama:** Semantic Scholar ve OpenAlex API'lerini kullanarak paralel makale araması yapar.
- **İşleyiş:** `SearchService`, `asyncio.gather` ile her iki provider'ı aynı anda çalıştırır. Sonuçlar birleştirilir ve DOI veya başlık bazında tekilleştirilir (Semantic Scholar öncelikli).
- **Request Body:** `SearchFilters` şeması (query, year_start, year_end, min_citations).
- **Response:** `List[PaperResponse]`.

### 2. Kütüphaneye Ekleme (`/api/v2/library/ingest`)
- **Method:** `POST`
- **Açıklama:** Arama sonucundan gelen bir makaleyi veritabanındaki kütüphaneye kaydeder ve PDF indirme görevini başlatır.
- **İşleyiş:** `LibraryService`, makalenin kütüphanede olup olmadığını (DOI/başlık ile) kontrol eder. Paper, Author ve Tag'leri veritabanına kaydeder. `download_paper_task` Celery görevini RabbitMQ kuyruğuna gönderir.
- **Auto-tagging:** `search_query` içindeki terimleri virgülle ayırarak otomatik etiketler oluşturur.
- **Request Body:** `IngestRequest` şeması (paper, search_query).

### 3. Kütüphaneyi Listeleme (`/api/v2/library`)
- **Method:** `GET`
- **Açıklama:** Kütüphanedeki makaleleri sayfalanmış ve filtrelenmiş olarak listeler.
- **Parametreler:** `page`, `limit`, `tag`, `status` (indirme durumu).
- **Performans:** N+1 probleminden kaçınmak için SQLAlchemy `joinedload` kullanılır.
- **Response:** `LibraryListResponse` şeması (items, total, page, limit).

### 4. Kütüphaneyi Dışa Aktarma (`/api/v2/library/export`)
- **Method:** `GET`
- **Açıklama:** Kütüphane verilerini CSV veya XLSX formatında indirir.
- **İşleyiş:** `ExportService`, `pandas` kullanarak veriyi DataFrame'e dönüştürür ve `StreamingResponse` ile dosyayı oluşturur.
- **Parametreler:** `format` (csv/xlsx), `search_query` (etiketlere göre filtreleme).

### 5. Sistem Sağlığı (`/api/v2/health`)
- **Method:** `GET`
- **Açıklama:** Veritabanı ve Redis bağlantılarını kontrol ederek sistemin genel durumunu raporlar.

### 6. Sistemi Sıfırlama (`/api/v2/system/reset`)
- **Method:** `POST`
- **Açıklama:** ⚠️ **Tehlikeli!** Tüm veritabanı tablolarını (`TRUNCATE CASCADE`) ve indirilmiş PDF dosyalarını siler.
- **Güvenlik:** `confirmation: "DELETE-ALL-DATA"` onayı gerektirir.

## Arka Plan Görevleri (Celery)
- **Task:** `download_paper_task`
- **Broker:** RabbitMQ
- **Worker:** Ayrı bir process olarak çalışır (`celery -A ... worker`).
- **İşleyiş:** Kütüphaneye eklenen makalenin PDF'ini `pdf_url`'den indirir.
- **Hata Yönetimi:** HTTP hatalarında otomatik yeniden deneme (exponential backoff ile max 5 kez).
- **Dosya Sistemi:** İndirilen dosyalar `/data/library/{paper_id}/{year}_{author}_{title}.pdf` formatında kaydedilir.
- **Durum Takibi:** `LibraryEntry.download_status` alanı güncellenir (`pending` -> `downloading` -> `completed`/`failed`).

## Hata Yönetimi ve Loglama
- **Hata Yapısı:** `AthenaError` base class'ından türeyen custom exception'lar kullanılır. Her hatanın bir `ErrorCode` (enum) ve standart bir JSON yanıt formatı vardır.
- **Global Handlers:** FastAPI `app.exception_handler` ile global hata yakalama mekanizması kurulmuştur.
- **Yapılandırılmış Loglama:** `Loguru` kullanılır. Geliştirme ortamında renkli, production ortamında JSON formatında log basar.
- **Correlation ID:** Her isteğe `RequestLoggingMiddleware` tarafından atanan bir `request_id` (UUID) ile loglar ve hatalar arasında ilişki kurulur. Bu ID, `X-Request-ID` header'ı olarak da yanıta eklenir.

## Veritabanı
- **ORM:** SQLAlchemy 2.0 (Async)
- **Driver:** `asyncpg`
- **Migration:** `Alembic` (async modda)
- **Modeller:** `Paper`, `Author`, `Tag`, `LibraryEntry` ve bunlar arasındaki ilişkileri tanımlayan `paper_authors`, `library_tags` tabloları.

## Docker Servisleri
- `postgres_db`: PostgreSQL 16 veritabanı.
- `redis_cache`: Redis 7, Celery için result backend ve genel amaçlı cache.
- `rabbitmq_broker`: RabbitMQ 3, Celery için message broker.

## Frontend (React + Vite)
- **Framework**: React 18
- **Build Tool**: Vite
- **UI Kit**: ShadCN/UI
- **Styling**: Tailwind CSS
- **Routing**: React Router DOM
- **State Management**:
  - **Server State**: React Query (`@tanstack/react-query`)
  - **Client State**: Zustand
- **API İletişimi**: Vite proxy (`/api` -> `http://localhost:8000`)

## Gelecek Adımlar ve Potansiyel Geliştirmeler
- **Frontend Geliştirme:** Sprint 5.1 ve 5.2 ile temel kurulumu ve state management altyapısı hazırlanan frontend'in geliştirilerek backend API'leri ile entegre edilmesi. Arama, kütüphaneye ekleme ve listeleme gibi özelliklerin arayüzlerinin oluşturulması.
- **Repository Pattern:** Veritabanı sorguları şu anda servis katmanında. Bunları ayrı `repository` sınıflarına taşımak, iş mantığı ile veri erişimini daha iyi ayırabilir.
- **Full-text Search:** Makale metinleri içinde arama yapmak için Elasticsearch veya benzeri bir çözüm entegre edilebilir.
- **Kullanıcı Yönetimi:** Çok kullanıcılı bir sisteme geçiş için kullanıcı authentication ve authorization eklenebilir.
- **Test Kapsamı:** Birim ve entegrasyon testlerinin artırılması.
- **Vektör Veritabanı:** `semantic.py` içinde `semantic` adında bir adapter bulunuyor. Bu, gelecekte anlamsal arama için bir vektör veritabanı (örn. Pinecone, Weaviate) entegrasyonuna işaret ediyor olabilir.

*Bu doküman, `claude.md` ve `docs/` altındaki sprint özetleri incelenerek oluşturulmuştur.*
