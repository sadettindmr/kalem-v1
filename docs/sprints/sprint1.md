# Sprint 1 - Veritabanı Modelleri ve Migration

## 📋 Sprint Özeti
**Amaç:** SQLAlchemy ORM modellerini tanımlamak ve Alembic ile veritabanı şemasını oluşturmak.

**Durum:** ✅ Tamamlandı

---

## 🎯 Tamamlanan Prompt'lar

### Prompt 1.1 - Alembic Kurulumu
- [x] Alembic bağımlılığı eklendi (`^1.13.0`)
- [x] Async migration yapısı oluşturuldu (`alembic init -t async migrations`)
- [x] `alembic.ini` yapılandırıldı (URL env.py'dan alınır)
- [x] `migrations/env.py` düzenlendi:
  - sys.path ayarlandı
  - Settings ve Base import edildi
  - `target_metadata = Base.metadata` ayarlandı

### Prompt 1.2 - SQLAlchemy Modelleri
- [x] `models/associations.py` - Association tables
- [x] `models/paper.py` - Paper modeli
- [x] `models/author.py` - Author modeli
- [x] `models/library.py` - LibraryEntry, SourceType, DownloadStatus
- [x] `models/tag.py` - Tag modeli
- [x] `models/__init__.py` - Export tanımları
- [x] `migrations/env.py` - Model importları eklendi

### Prompt 1.3 - Migration Uygulaması (DoD)
- [x] Migration oluşturuldu: `create_initial_tables`
- [x] Migration uygulandı: `alembic upgrade head`
- [x] Veritabanı tabloları doğrulandı

---

## 📊 Veritabanı Şeması

### Tablolar

| Tablo | Açıklama |
|-------|----------|
| `papers` | Akademik makale bilgileri |
| `authors` | Yazar bilgileri |
| `library_entries` | Kullanıcı kütüphanesi kayıtları |
| `tags` | Etiketler |
| `paper_authors` | Paper ↔ Author (M:N) |
| `library_tags` | LibraryEntry ↔ Tag (M:N) |

### Entity-Relationship

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────┐
│   authors   │◄─────►│  paper_authors   │◄─────►│   papers    │
└─────────────┘  M:N  └──────────────────┘  M:N  └──────┬──────┘
                                                       │ 1:1
                                                       ▼
                                               ┌───────────────┐
                                               │library_entries│
                                               └───────┬───────┘
                                                       │ M:N
                                                       ▼
                                               ┌──────────────┐
                                               │ library_tags │◄────►┌──────┐
                                               └──────────────┘ M:N  │ tags │
                                                                     └──────┘
```

### Enum Değerleri

**SourceType:**
- `semantic` - Semantic Scholar
- `openalex` - OpenAlex
- `manual` - Manuel ekleme

**DownloadStatus:**
- `pending` - Bekliyor
- `downloading` - İndiriliyor
- `completed` - Tamamlandı
- `failed` - Başarısız

---

## 🔧 Kullanılan Komutlar

```bash
# Migration oluştur
cd backend
poetry run alembic revision --autogenerate -m "create_initial_tables"

# Migration uygula
poetry run alembic upgrade head

# Durumu kontrol et
poetry run alembic current
poetry run alembic history

# Tabloları görüntüle
docker exec athena_postgres psql -U athena -d athena_core -c "\dt"
```

---

## 📁 Oluşturulan/Değiştirilen Dosyalar

```
backend/
├── athena/
│   └── models/
│       ├── __init__.py          (güncellendi)
│       ├── associations.py      (yeni)
│       ├── author.py            (yeni)
│       ├── library.py           (yeni)
│       ├── paper.py             (yeni)
│       └── tag.py               (yeni)
├── migrations/
│   ├── env.py                   (güncellendi)
│   └── versions/
│       ├── df9503a87ed7_initial.py
│       └── 74a35bd4d28c_create_initial_tables.py
├── alembic.ini                  (güncellendi)
└── pyproject.toml               (güncellendi - alembic eklendi)
```

---

## ✅ DoD Doğrulama

```bash
# Tabloların listesi
docker exec athena_postgres psql -U athena -d athena_core -c "\dt"

# Beklenen çıktı:
#  Schema |      Name       | Type  | Owner
# --------+-----------------+-------+--------
#  public | alembic_version | table | athena
#  public | authors         | table | athena
#  public | library_entries | table | athena
#  public | library_tags    | table | athena
#  public | paper_authors   | table | athena
#  public | papers          | table | athena
#  public | tags            | table | athena
```

---

*Sprint 1 Tamamlanma Tarihi: 2026-02-09*
