# Sprint 9 - Docker Deployment Duzeltmeleri ve E2E Test

## Sprint Ozeti
**Amac:** Sprint 8'de eklenen coklu kaynak entegrasyonunun Docker ortaminda uretim kalitesinde calismasini saglamak, deployment sorunlarini cozmek ve uctan uca testlerle dogrulamak.

**Durum:** Tamamlandi

---

## Tamamlanan Isler

### 9.1 - Backend Image Guncelleme
- [x] Backend container'da `feedparser` modulu eksikti (`ModuleNotFoundError`)
- [x] Docker build credential sorunu (`docker-credential-desktop` not found) nedeniyle `docker compose build` calismiyor
- [x] Cozum: Gecici container ile `pip install feedparser` + guncel kod kopyalama + `docker commit` ile yeni image olusturma
- [x] `project-athena-backend:latest` image'i feedparser + tum Sprint 8 kodu ile guncellendi

### 9.2 - docker-compose.yml Duzeltmeleri
- [x] Backend servisine `command: uvicorn athena.main:app --host 0.0.0.0 --port 8000` eklendi
  - Sebep: `docker commit` ile olusturulan image'in CMD'si `sleep 3600` olarak kaliyordu
- [x] Celery worker servisi `image: project-athena-backend:latest` olarak degistirildi
  - Sebep: Eski image'da loguru, feedparser gibi bagimliliklar ve guncel task tanimlari yoktu
  - Eski image'daki task adi: `athena.tasks.download_paper` (uyumsuz)
  - Guncel task adi: `athena.tasks.downloader.download_paper_task` (dogru)

### 9.3 - Frontend DNS Cache Sorunu
- [x] Backend container yeniden olusturulunca IP adresi degisti (ornek: 172.18.0.5 -> 172.18.0.7)
- [x] Frontend nginx eski IP'yi cache'liyordu -> `502 Bad Gateway`
- [x] Cozum: `docker compose restart frontend` ile nginx DNS cache yenilendi

### 9.4 - Uctan Uca Test
- [x] 12 test senaryosu basariyla tamamlandi

---

## Test Sonuclari

| # | Test | Sonuc |
|---|------|-------|
| 1 | Health Check (`/api/v2/health`) | healthy, DB+Redis connected |
| 2 | Frontend HTML (`localhost:3000`) | 200 OK |
| 3 | Arama API - 5 kaynak (`deep learning`) | OA:1000, arXiv:500, CR:500, Toplam:1961 |
| 4 | Library Ingest | queued, entry_id:206 |
| 5 | Celery Worker task processing | Task received + PDF downloaded (0.63s) |
| 6 | Library status check | entry 206: completed, file_path set |
| 7 | Nis sorgu (`federated learning`) | SS:1000, OA:1000, arXiv:500, CR:500, dedup:593, Toplam:2407 |
| 8 | Yil filtresi (2023-2024) | Calisiyor, range disi yil: 0 |
| 9 | Library check endpoint | Kayitli DOI'ler dogru tespit edildi |
| 10 | Library export (CSV) | 200 OK, text/csv |
| 11 | Frontend API proxy | 200 OK (restart sonrasi) |
| 12 | Container durumlari | 6/6 container up & healthy |

### Semantic Scholar Gecici Hatasi
- `deep learning` sorgusunda SS API gecici 500 hatasi verdi
- Sonraki sorguda (`federated learning`) SS 1000 sonuc dondurdu
- Bu bir API tarafindaki gecici sorun, kodla ilgili degil

---

## Degisiklik Yapilan Dosyalar

| Dosya | Degisiklik |
|-------|-----------|
| `docker-compose.yml` | Backend: `command` eklendi. Celery worker: `build` -> `image` degistirildi |
| `project-athena-backend:latest` | Docker image: feedparser + guncel kod ile yeniden olusturuldu |

---

## Ogrenilenler / Notlar

1. **`docker commit` CMD sorunu:** Gecici container'dan commit yapildiginda, o anki CMD (ornek: `sleep 3600`) image'a yazilir. docker-compose.yml'da explicit `command` ile override edilmeli.

2. **Celery task adi uyumu:** Worker ve backend ayni task adini kullanmali. Farkli image'lardan calistirildiginda task registry uyumsuzlugu olusabilir.

3. **Nginx DNS cache:** Backend container yeniden olusturulunca nginx DNS cache'i gecersiz kalir. Frontend container'in da restart edilmesi gerekir.

4. **Docker credential sorunu:** macOS'ta `docker-credential-desktop` PATH'te bulunamadiginda `docker compose build` basarisiz olur. Workaround: Mevcut image'i `docker commit` ile guncellemek.
