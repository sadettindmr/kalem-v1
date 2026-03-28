# Sprint 14 - Butunlesik QA ve CI/CD

## Sprint Ozeti
**Amac:** Projenin frontend birim test altyapisini kurmak, Playwright ile E2E test yazmak ve GitHub Actions ile CI/CD pipeline'i olusturmak.

**Durum:** Tamamlandi
**Tarih:** 2026-03-29

---

## 14.1 - Frontend Birim Test Altyapisi (Vitest)

### Kurulan Bagimliliklar
- `vitest` - Test runner (Vite-native)
- `@testing-library/react` - React component test utilities
- `@testing-library/jest-dom` - DOM matchers (toBeInTheDocument, toBeDisabled, etc.)
- `@testing-library/user-event` - User interaction simulation
- `jsdom` - Browser environment for Node.js

### Konfigürasyon Degisiklikleri

#### `frontend/vite.config.ts`
- `test` blogu eklendi: `environment: 'jsdom'`, `globals: true`, `setupFiles: './src/test/setup.ts'`
- `exclude: ['tests/**', 'node_modules/**']` ile Playwright testleri Vitest'ten ayrildi

#### `frontend/tsconfig.app.json`
- `types` dizisine `vitest/globals` eklendi (describe, it, expect global tanimlar)

#### `frontend/tsconfig.node.json`
- `types` dizisine `vitest/config` eklendi (vite.config.ts icindeki `test` blogunun tip hatasi giderildi)

#### `frontend/src/test/setup.ts`
- `@testing-library/jest-dom` import ediyor (DOM matcher'lari aktif eder)

### Yazilan Testler

#### `frontend/src/components/SearchForm.test.tsx` (6 test)
1. **renders the form** - Form elemanlarinin (input, button, labels) render edildigini dogrular
2. **allows typing** - Arama kutusuna yazi yazilabildigini dogrular
3. **disables button when empty** - Bos sorguda butonun disabled oldugunu dogrular
4. **enables button when text** - Metin girildiginde butonun aktif oldugunu dogrular
5. **submits and calls searchPapers** - Form submit'te searchPapers service'inin dogru parametrelerle cagirildigini dogrular
6. **allows year range filters** - Yil araligi inputlarinin calistigini dogrular

### Calistirma
```bash
cd frontend
npm run test         # Tek seferlik calistirma
npm run test:watch   # Watch modunda calistirma
```

---

## 14.2 - E2E Testing (Playwright)

### Kurulum
- `@playwright/test` dev dependency olarak eklendi
- Chromium headless browser kuruldu

### Konfigürasyon

#### `frontend/playwright.config.ts`
- `testDir: './tests'`
- `baseURL`: Env variable `BASE_URL` veya varsayilan `http://localhost:3000` (Docker)
- Sadece Chromium projesi (hafif ve hizli)
- CI'da retry: 2, worker: 1

#### `frontend/tests/main-flow.spec.ts`
Ana kullanici akisini test eder:
1. Uygulamanin ana sayfasina gider
2. Arama kutusuna "Machine Learning" yazar
3. "Ara" butonuna tiklar
4. Sonuclarin yuklenmesini bekler (90s timeout - 5 provider paralel calisir)
5. Ilk sonucun "Kutuphaneme Ekle" butonuna tiklar
6. "Makale kutuphaneme eklendi" toast bildirimini dogrular

**Not:** Bu test canli backend gerektirir (Docker servisleri calisir durumda olmali).

### Calistirma
```bash
cd frontend
npm run test:e2e                  # Headless calistir
npx playwright test --ui          # UI modunda calistir
npx playwright show-report        # Son raporu goruntule
BASE_URL=http://localhost:5173 npm run test:e2e  # Dev server'a karsi calistir
```

---

## 14.3 - CI/CD Pipeline (GitHub Actions)

### Dosya: `.github/workflows/ci.yml`

### Trigger'lar
- `push` to `main`
- `pull_request` to `main`

### Job 1: Backend Tests
- **Runner:** ubuntu-latest
- **Python:** 3.11
- **Dependency Manager:** Poetry (cached .venv)
- **Steps:**
  1. Checkout
  2. Setup Python 3.11
  3. Install Poetry
  4. Cache dependencies
  5. `poetry install`
  6. `poetry run black --check athena/ tests/` (format lint)
  7. `poetry run isort --check-only athena/ tests/` (import sort lint)
  8. `poetry run pytest tests/ -v`

### Job 2: Frontend Tests
- **Runner:** ubuntu-latest
- **Node:** 20
- **Steps:**
  1. Checkout
  2. Setup Node.js 20 (npm cache)
  3. `npm ci`
  4. `npx tsc -b` (TypeScript compile check)
  5. `npm run test` (Vitest unit tests)

**Not:** E2E testler CI'da calistirilmaz (canli backend gerektirir). Ileride Docker Compose ile CI'da E2E eklenebilir.

---

## Test Sonuclari

| Test Suite | Sonuc | Sure |
|-----------|-------|------|
| Backend pytest | 17/17 passed | ~1.8s |
| Frontend Vitest | 6/6 passed | ~1.4s |
| Playwright E2E | 1/1 passed | ~40s |
| TypeScript build | Success | ~4.6s |

---

## Dosya Listesi

### Yeni Dosyalar
- `frontend/src/test/setup.ts` - Vitest setup
- `frontend/src/components/SearchForm.test.tsx` - Birim testleri
- `frontend/playwright.config.ts` - Playwright konfigurasyonu
- `frontend/tests/main-flow.spec.ts` - E2E test
- `.github/workflows/ci.yml` - CI/CD pipeline

### Degisiklik Yapilan Dosyalar
- `frontend/vite.config.ts` - test konfigurasyonu eklendi
- `frontend/tsconfig.app.json` - vitest/globals tipi eklendi
- `frontend/tsconfig.node.json` - vitest/config tipi eklendi
- `frontend/package.json` - test dependencies ve scripts eklendi
