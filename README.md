# Kalem v1.0.0 - Kasghar

Akademik makale arama, indirme, arşivleme ve kütüphane yönetimi uygulaması.

## Gereksinimler

- Docker Engine (Linux) veya Docker Desktop (Windows/macOS)
- Docker Compose
  - Tercih edilen: `docker compose` (Compose v2)
  - Alternatif: `docker-compose` (Compose v1)

## Hızlı Başlangıç

1. Bu repoyu klonlayın.
2. Kök dizinde `.env` dosyası oluşturun:

```bash
cp .env.example .env
```

3. Servisleri ayağa kaldırın:

```bash
docker compose down
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker compose up -d --build
```

Eğer sisteminizde `docker compose` yoksa:

```bash
docker-compose down
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build
```

4. Uygulama adresleri:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## İlk Çalıştırma Notları

- Backend başlangıçta migration çalıştırır (`alembic upgrade heads`).
- `user_settings` kaydı ilk kullanımda otomatik oluşturulur.
- Ayarlar ekranından provider, credential ve proxy konfigürasyonu yönetilebilir.

## Sorun Giderme

- BuildKit snapshot/attestation kaynaklı build hatalarında:

```bash
docker builder prune -af
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker compose up -d --build
```

- Eski compose sürümlerinde `docker compose` yerine `docker-compose` kullanın.

