# Sprint 17 - Enstitü Erişimi ve EZProxy Entegrasyonu

**Tarih:** 2026-03-30
**Durum:** ✅ Tamamlandı
**Versiyon:** v1.2.0

---

## 🎯 Hedef

Açık kaynaklardan (Open Access) indirilemeyen ücretli makaleleri, üniversitelerin sağladığı EZProxy sistemleri (örn: proxy.uskudar.edu.tr) üzerinden indirmeyi sağlayacak altyapıyı kurmak.

---

## 📋 Gereksinimler

### ADIM 1: Veritabanı ve Settings Modeli Güncellemesi

- [x] `UserSettings` modeline `ezproxy_prefix` alanı ekleme (str, nullable)
- [x] `UserSettings` modeline `ezproxy_cookie` alanı ekleme (str, nullable)
- [x] Alembic migration oluşturma (`7245dcd6adc4_add_ezproxy_settings.py`)
- [x] `schemas/settings.py` güncelleme
- [x] API router'ında yeni alanları expose etme

### ADIM 2: Downloader Servisi Entegrasyonu

- [x] `_download_file()` metoduna `headers_override` parametresi ekleme
- [x] `_load_ezproxy_settings()` helper fonksiyonu
- [x] `_should_try_ezproxy()` kontrol fonksiyonu
- [x] `_build_ezproxy_target()` URL oluşturucu
- [x] `_download_via_ezproxy()` fallback indirici
- [x] 401/402/403 hatalarında EZProxy fallback tetikleme

### ADIM 3: Frontend Arayüz Güncellemesi

- [x] `UserSettingsResponse` interface'ine EZProxy alanları ekleme
- [x] `UserSettingsUpdateRequest` interface'ine EZProxy alanları ekleme
- [x] `SettingsFormState` interface'ini genişletme
- [x] `toFormState()` mapping fonksiyonunu güncelleme
- [x] Settings Network tab'ında "Enstitü Erişimi (EZProxy)" bölümü
- [x] EZProxy Prefix URL input alanı
- [x] Aktif Oturum Çerezi input alanı
- [x] Bilgilendirme metni (Alert)

---

## 🔧 Teknik Detaylar

### Veritabanı Değişiklikleri

```python
# backend/athena/models/settings.py
class UserSettings(Base):
    # ... mevcut alanlar ...
    ezproxy_prefix: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    ezproxy_cookie: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
```

### Migration

```python
# 7245dcd6adc4_add_ezproxy_settings.py
def upgrade():
    op.add_column('user_settings', sa.Column('ezproxy_prefix', sa.String(1000), nullable=True))
    op.add_column('user_settings', sa.Column('ezproxy_cookie', sa.String(2000), nullable=True))
```

### EZProxy Fallback Akışı

```
1. Normal PDF indirme dene (pdf_url)
2. Başarısız olursa (401/402/403):
   a. EZProxy ayarları kontrol et
   b. ezproxy_prefix ve ezproxy_cookie ayarlıysa:
      - target_url = f"{ezproxy_prefix}{original_url}"
      - Cookie header'ı ekle
      - Yeniden indirmeyi dene
3. Hâlâ başarısızsa "failed" olarak işaretle
```

### API Değişiklikleri

**GET/PUT `/api/v2/system/settings`** yanıtına eklenen alanlar:

```json
{
  "ezproxy_prefix": "https://proxy.uskudar.edu.tr/login?url=",
  "ezproxy_cookie": "***" // Masked in response
}
```

---

## 🧪 Test Kriterleri (DoD)

| Test                          | Tip    | Beklenen Sonuç                    | Durum |
| ----------------------------- | ------ | --------------------------------- | ----- |
| Settings API ezproxy alanları | API    | GET/PUT yanıtlarında görünmeli    | ✅    |
| Frontend EZProxy bölümü       | UI     | Network tab'da görünmeli          | ✅    |
| EZProxy prefix kaydedebilme   | UI     | Değer veritabanına yazılmalı      | ✅    |
| EZProxy cookie maskeleme      | API    | Yanıtta `***` görünmeli           | ✅    |
| Downloader fallback log       | Worker | "EZProxy fallback attempted" logu | ⏳    |
| E2E EZProxy indirme           | Manuel | Ücretli makale indirilmeli        | ⏳    |

---

## 📁 Değiştirilen Dosyalar

### Backend

| Dosya                                   | Değişiklik                   |
| --------------------------------------- | ---------------------------- |
| `models/settings.py`                    | EZProxy alanları eklendi     |
| `schemas/settings.py`                   | Pydantic şeması güncellendi  |
| `services/settings.py`                  | Update logic genişletildi    |
| `api/v2/routers/settings.py`            | Maskeleme eklendi            |
| `tasks/downloader.py`                   | EZProxy fallback helper'ları |
| `migrations/versions/7245dcd6adc4_*.py` | Yeni migration               |

### Frontend

| Dosya                         | Değişiklik                 |
| ----------------------------- | -------------------------- |
| `src/types/api.ts`            | EZProxy interface alanları |
| `src/components/settings.tsx` | EZProxy UI bölümü          |

---

## 🐛 Karşılaşılan Sorunlar

### Issue #1: Migration Uygulanmadı

**Semptom:** Settings sayfası "Beklenmeyen hata" döngüsüne girdi.
**Neden:** Alembic migration dosyası container'a kopyalandı ama DDL çalışmadı.
**Çözüm:** Kolonlar manuel olarak `ALTER TABLE` ile eklendi.

```sql
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS ezproxy_prefix VARCHAR(1000);
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS ezproxy_cookie VARCHAR(2000);
```

---

## 📈 Sonraki Adımlar

- [ ] Celery worker'ı rebuild edip downloader değişikliklerini test et
- [ ] Gerçek bir EZProxy sistemi ile uçtan uca test
- [ ] Çerez süresinin dolması durumu için UI uyarısı (gelecek sprint)

---

_Sprint 17 - Tamamlandı: 2026-03-30_
