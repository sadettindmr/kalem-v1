# Kalem v1.0.2 - Kasghar

Kalem - Kasghar; akademik makale arama, kaynak birleştirme, PDF indirme, kütüphane yönetimi, dışa aktarma ve arşivleme için geliştirilmiş bir uygulamadır.

## İçerik

1. [Özellikler](#özellikler)
2. [Teknoloji Yığını](#teknoloji-yığını)
3. [Mimari ve Servisler](#mimari-ve-servisler)
4. [Gereksinimler](#gereksinimler)
5. [Kurulum (Linux / Windows / macOS)](#kurulum-linux--windows--macos)
6. [Çalışma Akışı](#çalışma-akışı)
7. [Ayarlar ve Konfigürasyon](#ayarlar-ve-konfigürasyon)
8. [API Özeti](#api-özeti)
9. [Geliştirme ve Test](#geliştirme-ve-test)
10. [Sorun Giderme](#sorun-giderme)
11. [Kullanılan Modeller ve Sağlayıcılar (Citation)](#kullanılan-modeller-ve-sağlayıcılar-citation)
12. [Release Notes](#release-notes)

## Özellikler

- Çoklu kaynak arama: Semantic Scholar, OpenAlex, arXiv, Crossref, CORE
- Full-Text Search (PostgreSQL TSVECTOR) ile alaka düzeyi yüksek kütüphane araması
- Dinamik provider yönetimi: kaynaklar ayarlardan aç/kapat
- API key, e-posta ve proxy ayarlarını veritabanında yönetme (`user_settings`)
- PDF indirme kuyruğu (Celery + RabbitMQ + Redis)
- Toplu PDF arşivi indirme (`.zip`)
- Gelişmiş bibliyografik export (`.xlsx`, `.csv`, APA/IEEE alanları)
- Metadata enrichment (eksik alanları dış kaynaklardan tamamlama)

## Teknoloji Yığını

- Frontend: React + TypeScript + Vite + TanStack Query + Zustand + ShadCN UI
- Backend: FastAPI + SQLAlchemy (async) + Alembic
- Worker: Celery
- Database: PostgreSQL
- Queue/Broker: RabbitMQ
- Cache/Result Backend: Redis
- Containerization: Docker + Docker Compose

## Mimari ve Servisler

`docker-compose.yml` içinde ayağa kalkan ana servisler:

- `postgres_db` (`kalem_postgres`) - PostgreSQL
- `redis_cache` (`kalem_redis`) - Redis
- `rabbitmq_broker` (`kalem_rabbitmq`) - RabbitMQ
- `backend` (`kalem_backend`) - FastAPI (`:8000`)
- `celery_worker` (`kalem_celery_worker`) - Asenkron indirme/iş kuyruğu
- `frontend` (`kalem_frontend`) - Nginx üzerinde React build (`:3000`)

## Gereksinimler

- Docker (Linux: Docker Engine, Windows/macOS: Docker Desktop)
- Docker Compose
  - Tercih: `docker compose` (v2)
  - Alternatif: `docker-compose` (v1)

## Kurulum (Linux / Windows / macOS)

### 1) Repo klonlama

```bash
git clone https://github.com/sadettindmr/kalem-v1.git
cd kalem-v1
```

### 2) Ortam dosyası

```bash
cp .env.example .env
```

### 3) Servisleri ayağa kaldırma

Compose v2:

```bash
docker compose down
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker compose up -d --build
```

Compose v1:

```bash
docker-compose down
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build
```

### 4) Erişim adresleri

- Uygulama: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- OpenAPI/Swagger: `http://localhost:8000/docs`
- RabbitMQ UI: `http://localhost:15672`

## Çalışma Akışı

1. Arama ekranından sorgu gönderilir (`/api/v2/search`).
2. Aktif provider’lar paralel sorgulanır.
3. Sonuçlar normalize/dedup edilip kullanıcıya döner.
4. Seçilen makaleler kütüphaneye alınır (`/api/v2/library/ingest`).
5. Celery worker PDF indirme task’lerini yürütür.
6. Kütüphane ekranından filtreleme, export, zip arşivleme yapılır.
7. Ayarlar ekranından provider/proxy/credential yönetilir.

## Ayarlar ve Konfigürasyon

### Ortam değişkenleri (`.env`)

Temel değişkenler:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL`
- `SEMANTIC_SCHOLAR_API_KEY`
- `OPENALEX_EMAIL`
- `CORE_API_KEY`
- `OUTBOUND_PROXY`

### Veritabanı tabanlı ayarlar (`user_settings`)

Ayarlar ekranı üzerinden yönetilen alanlar:

- `enabled_providers`
- `semantic_scholar_api_key`
- `core_api_key`
- `openalex_email`
- `proxy_enabled`
- `proxy_url`

Not: Uygulama bu ayarları öncelikli kullanır, gerekirse `.env` fallback uygulanır.

## API Özeti

Base path: `/api/v2`

### System

- `GET /health` - servis sağlık kontrolü
- `POST /system/reset` - fabrika ayarlarına dönüş
- `GET /system/settings` - mevcut ayarlar (maskeli secret alanlar)
- `PUT /system/settings` - ayar güncelleme

### Search

- `POST /search` - çoklu provider araması

### Library

- `POST /library/ingest` - tek makale ekleme
- `POST /library/ingest/bulk` - toplu ekleme
- `POST /library/check` - kayıtlı DOI kontrolü
- `GET /library` - kütüphane listeleme/filtreleme
- `GET /library/export?format=xlsx|csv` - dışa aktarma
- `GET /library/download-zip` - filtreye göre PDF zip arşivi
- `GET /library/download-stats` - indirme kuyruk istatistikleri
- `POST /library/retry-downloads` - kuyruk tekrar deneme
- `POST /library/enrich-metadata` - metadata zenginleştirme

## Geliştirme ve Test

Backend test:

```bash
cd backend
python3 -m pytest -q
```

Frontend build:

```bash
cd frontend
npm run build
```

Backend syntax/compile kontrol:

```bash
python3 -m compileall backend/athena backend/tests
```

## Sorun Giderme

### 1) BuildKit snapshot / export hataları

```bash
docker builder prune -af
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker compose up -d --build
```

### 2) `docker: command not found`

- Docker Desktop açık mı kontrol edin.
- PATH içinde docker binary olduğundan emin olun.
- Gerekirse yeni terminal açın.

### 3) Compose komutu yok

- `docker compose` çalışmıyorsa `docker-compose` deneyin.

### 4) Migration ve şema problemleri

Backend container başlangıcında migration çalışır.
Manuel doğrulama için:

```bash
cd backend
alembic heads
alembic upgrade heads
```

### 5) Aynı arama farklı toplam dönüyor

- Dış sağlayıcılar (özellikle arXiv) anlık olarak değişken ham sonuç döndürebilir.
- `v1.0.2` ile arXiv düşük-sonuç anomalileri için otomatik retry eklendi.
- Teşhis için sol panelde şu akışı kontrol edin:
  - `Ham kaynak sonuçları`
  - `Alaka dışı elenen`
  - `Mükerrer elenen`
  - `Toplam`

## Kullanılan Modeller ve Sağlayıcılar (Citation)

Bu projede geliştirme sürecinde kullanılan AI asistanları ve uygulama içinde arama/indirme için kullanılan dış sağlayıcılar aşağıda belirtilmiştir.

### 11.1 Geliştirme Sürecinde Kullanılan AI Modelleri

- Claude (Anthropic) - planlama, dokümantasyon ve kod refactor süreçlerinde yardımcı model.
- Codex (OpenAI) - kod üretimi, düzeltme, test ve entegrasyon süreçlerinde yardımcı model.
- Gemini (Google) - alternatif çözüm üretimi ve karşılaştırmalı geliştirme desteği.

### 11.2 Uygulamada Kullanılan Arama/İndirme Sağlayıcıları

- Semantic Scholar API - akademik arama sonuçları.
- OpenAlex API - akademik work/metadata araması.
- arXiv API - preprint araması.
- Crossref REST API - DOI/metadata araması.
- CORE API - açık erişim içerik araması.
- Unpaywall (opsiyonel/fallback akışı için referans) - DOI üzerinden açık erişim PDF tespiti.

### 11.3 Citation / Referanslar

1. Anthropic. (n.d.). *Claude*. [https://claude.ai](https://claude.ai)  
2. OpenAI. (n.d.). *Codex*. [https://openai.com/codex](https://openai.com/codex)  
3. Google. (n.d.). *Gemini*. [https://gemini.google.com](https://gemini.google.com)  
4. Semantic Scholar. (n.d.). *Semantic Scholar API Documentation*. [https://api.semanticscholar.org/api-docs/](https://api.semanticscholar.org/api-docs/)  
5. OpenAlex. (n.d.). *OpenAlex Documentation*. [https://docs.openalex.org/](https://docs.openalex.org/)  
6. arXiv. (n.d.). *arXiv API*. [https://info.arxiv.org/help/api/](https://info.arxiv.org/help/api/)  
7. Crossref. (n.d.). *REST API*. [https://api.crossref.org/](https://api.crossref.org/)  
8. CORE. (n.d.). *CORE API Documentation*. [https://api.core.ac.uk/docs/v3](https://api.core.ac.uk/docs/v3)  
9. Unpaywall. (n.d.). *Unpaywall Data/API*. [https://unpaywall.org/products/api](https://unpaywall.org/products/api)  

## Release Notes

- `v1.0.2`: `docs/release_notes.md`
