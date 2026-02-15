# Sprint 5 - Frontend Kurulumu

## Sprint Ozeti
**Amac:** React + Vite + TypeScript + ShadCN/UI ile modern frontend altyapisini kurmak.

**Durum:** ✅ Tamamlandi

---

## Tamamlanan Promptlar

### Prompt 5.1 - Proje Kurulumu
- [x] `frontend/` dizininde Vite + React + TypeScript projesi olusturuldu
- [x] Tailwind CSS v3, postcss, autoprefixer kuruldu ve yapilandirildi
- [x] `tsconfig.json` ve `vite.config.ts` dosyalarina `@/*` path alias'i eklendi
- [x] ShadCN/UI projesi baslatildi (Style: New York, Base Color: Slate, CSS Variables: Yes)
- [x] Temel bilesenleri eklendi: button, input, card, badge, separator, scroll-area, skeleton, sonner (toast)
- [x] Vite config'e `/api` icin proxy ayari eklendi (`http://localhost:8000`)
- [x] Lucide React ikonlari yuklendi

### Prompt 5.2 - State Management ve Routing
- [x] `@tanstack/react-query` eklendi (server state)
- [x] `zustand` eklendi (client state)
- [x] `react-router-dom` eklendi (routing)
- [x] Temel sayfa yonlendirmesi (`/` ve `/settings`) yapildi
- [x] QueryClient olusturuldu ve `main.tsx`'e eklendi
- [x] UI store olusturuldu (`isSidebarOpen`, `activeTab`)

### Prompt 5.3 - API Client ve Error Management (Axios Interceptor)
- [x] `axios` kurlumu ve yapilandirmasi
- [x] `src/lib/api.ts` - Axios instance olusturuldu (`baseURL: '/api/v2'`)
- [x] Response interceptor eklendi (error handling + toast notifications)
- [x] `src/types/api.ts` - TypeScript interface'leri (Backend Pydantic modelleri ile uyumlu)
- [x] `src/services/search.ts` - Search service fonksiyonu
- [x] `sonner.tsx` duzeltildi (next-themes bagimliligi kaldirildi)

### Prompt 5.4 - Zotero-Like Layout (3 Sutunlu Tasarim)
- [x] `src/layouts/DashboardLayout.tsx` olusturuldu
- [x] 3 sutunlu layout: Sidebar (240px) + Paper List (320px) + Detail Panel (flex)
- [x] Responsive tasarim (sidebar collapse destegi)
- [x] CSS class-based styling (min-h-screen, flex, overflow-hidden)

### Prompt 5.5 - Search ve Paper Listeleme
- [x] `src/components/SearchForm.tsx` - Arama formu (useMutation ile)
- [x] `src/components/PaperCard.tsx` - Paper kart bileseni
- [x] `src/components/PaperList.tsx` - Liste bileseni (Loading/Empty/Success states)
- [x] `src/components/PaperDetail.tsx` - Detail panel (secili makale goruntuleme)
- [x] `src/components/Sidebar.tsx` - Navigation + SearchForm entegrasyonu
- [x] UI Store guncellendi (`selectedPaperId`, `searchResults`, `isSearching`)
- [x] Docker container'lar (frontend + backend) olusturuldu ve test edildi

---

## Mimari

```
frontend/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── ui/                    # ShadCN/UI bileşenleri
│   │   │   ├── badge.tsx
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── skeleton.tsx
│   │   │   └── sonner.tsx
│   │   ├── PaperCard.tsx          # Paper kart bileşeni
│   │   ├── PaperDetail.tsx        # Detail panel
│   │   ├── PaperList.tsx          # Paper listesi
│   │   ├── SearchForm.tsx         # Arama formu
│   │   ├── Sidebar.tsx            # Sol panel navigasyonu
│   │   ├── dashboard.tsx
│   │   └── settings.tsx
│   ├── layouts/
│   │   └── DashboardLayout.tsx    # 3-sütunlu Zotero-like layout
│   ├── lib/
│   │   ├── api.ts                 # Axios client + interceptor
│   │   ├── react-query.ts         # QueryClient yapılandırması
│   │   └── utils.ts               # ShadCN cn() helper
│   ├── services/
│   │   └── search.ts              # Search API service
│   ├── stores/
│   │   └── ui-store.ts            # Zustand UI store
│   ├── types/
│   │   └── api.ts                 # TypeScript interfaces (API types)
│   ├── App.tsx                    # Router yapılandırması
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Tailwind + CSS Variables
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
└── components.json                # ShadCN yapılandırması
```

---

## Teknoloji Stack

| Kategori | Teknoloji | Versiyon |
|----------|-----------|----------|
| Framework | React | 19.x |
| Build Tool | Vite | 7.x |
| Dil | TypeScript | 5.x |
| UI Kit | ShadCN/UI | latest |
| Styling | Tailwind CSS | 3.x |
| Icons | Lucide React | latest |
| State (Server) | React Query | 5.x |
| State (Client) | Zustand | 5.x |
| Routing | React Router DOM | 7.x |

---

## Bagimlilıklar

### Production
```json
{
  "@tanstack/react-query": "^5.90.21",
  "@tanstack/react-query-devtools": "^5.91.3",
  "axios": "^1.13.5",
  "clsx": "^2.1.1",
  "lucide-react": "latest",
  "react": "^19.2.0",
  "react-dom": "^19.2.0",
  "react-router-dom": "^7.13.0",
  "tailwind-merge": "^3.4.0",
  "zustand": "^5.0.11"
}
```

### Development
```json
{
  "autoprefixer": "^10.4.24",
  "postcss": "^8.5.6",
  "tailwindcss": "^3.4.19",
  "typescript": "~5.9.3",
  "vite": "^7.3.1"
}
```

---

## Yapilandirma Dosyalari

### vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### tailwind.config.js
- `darkMode: ["class"]` - Class-based dark mode
- ShadCN CSS variables entegrasyonu
- Slate renk paleti

### components.json (ShadCN)
```json
{
  "style": "new-york",
  "tailwind": {
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  }
}
```

---

## Komutlar

```bash
cd frontend

# Bagimliliklari yukle
npm install

# Gelistirme sunucusunu baslat (port 5173)
npm run dev

# Production build olustur
npm run build

# Build onizleme
npm run preview

# Lint kontrolu
npm run lint
```

---

## State Management

### React Query (Server State)
```typescript
// src/lib/react-query.ts
import { QueryClient } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 dakika
      retry: 1,
    },
  },
})
```

### Zustand (Client State)
```typescript
// src/stores/ui-store.ts
interface UIState {
  isSidebarOpen: boolean
  activeTab: string
  toggleSidebar: () => void
  setActiveTab: (tab: string) => void
}

const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  activeTab: 'search',
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setActiveTab: (tab) => set({ activeTab: tab }),
}))
```

---

## API Proxy

Frontend gelistirme sunucusu, `/api` isteklerini otomatik olarak backend'e yonlendirir:

```
Frontend (5173) ---> /api/* ---> Backend (8000)
```

Ornek:
```javascript
// Frontend'de:
fetch('/api/v2/health')

// Gercekte gider:
// http://localhost:8000/api/v2/health
```

---

## API Client (Axios)

### Axios Instance
```typescript
// src/lib/api.ts
import axios from 'axios';
import { toast } from 'sonner';

const api = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Response Interceptor - Global Error Handling
api.interceptors.response.use(
  (response) => response.data,  // Otomatik .data unwrap
  (error) => {
    const errorMessage = error.response?.data?.error?.message || 'Bir hata oluştu';
    toast.error(errorMessage);
    return Promise.reject(error);
  }
);
```

### TypeScript Interfaces
```typescript
// src/types/api.ts
export interface SearchFilters {
  query: string;
  year_start?: number | null;
  year_end?: number | null;
  min_citations?: number | null;
}

export interface Author {
  name: string;
}

export interface PaperResponse {
  title: string;
  abstract: string | null;
  year: number | null;
  citation_count: number;
  venue: string | null;
  authors: Author[];
  source: 'semantic' | 'openalex' | 'manual';
  external_id: string | null;
  pdf_url: string | null;
}

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    suggestion?: string;
    details?: string;
    request_id?: string;
  };
}
```

### Service Layer
```typescript
// src/services/search.ts
import api from '@/lib/api';
import type { SearchFilters, PaperResponse } from '@/types/api';

export async function searchPapers(filters: SearchFilters): Promise<PaperResponse[]> {
  return api.post<never, PaperResponse[]>('/search', filters);
}
```

---

## Docker Configuration

### Dockerfile.backend
```dockerfile
FROM python:3.11-slim
ENV POETRY_VERSION=1.8.5
RUN apt-get install -y curl  # healthcheck için
RUN pip install "poetry==$POETRY_VERSION"
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root
COPY backend/ ./
EXPOSE 8000
CMD ["uvicorn", "athena.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.frontend
```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production (nginx ile serve)
FROM nginx:alpine
RUN apk add --no-cache curl  # healthcheck için
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### nginx.frontend.conf
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing - tüm istekleri index.html'e yönlendir
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API isteklerini backend'e proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Statik dosyalar için cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Docker Servisleri (docker-compose.yml)
| Servis | Image | Port | Açıklama |
|--------|-------|------|----------|
| `postgres_db` | postgres:16-alpine | 5433:5432 | PostgreSQL veritabanı |
| `redis_cache` | redis:7-alpine | 6379 | Redis cache |
| `rabbitmq_broker` | rabbitmq:3-management-alpine | 5672, 15672 | Message broker |
| `backend` | Dockerfile.backend | 8000 | FastAPI backend |
| `frontend` | Dockerfile.frontend | 3000:80 | React frontend (nginx) |

### Docker Komutları
```bash
# Tüm servisleri başlat (build dahil)
docker-compose up -d --build

# Orphan container'ları temizle
docker-compose up -d --remove-orphans

# Logları izle
docker-compose logs -f backend frontend

# Tek bir servisi yeniden başlat
docker-compose restart backend
```

---

## DoD Dogrulama

### Development Mode (Local)
```bash
# 1. Docker altyapi servislerini baslat
docker-compose up -d postgres_db redis_cache rabbitmq_broker

# 2. Backend'i baslat
cd backend
poetry run uvicorn athena.main:app --reload --port 8000

# 3. Frontend'i baslat
cd frontend
npm run dev

# 4. Tarayicida ac: http://localhost:5173

# 5. Health check (proxy testi)
curl http://localhost:5173/api/v2/health
```

### Docker Production Mode
```bash
# 1. Tüm servisleri başlat (build dahil)
docker-compose up -d --build --remove-orphans

# 2. Sağlık kontrolü
docker-compose ps
curl http://localhost:8000/api/v2/health  # Backend
curl http://localhost:3000                 # Frontend

# 3. Search testi
curl -X POST http://localhost:8000/api/v2/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning"}'

# 4. Frontend'den backend'e proxy testi
# http://localhost:3000 adresinde arama yapın
```

### Kontrol Listesi
- [ ] Sidebar ve SearchForm görünüyor
- [ ] Arama yapıldığında sonuçlar PaperList'te listeleniyor
- [ ] Loading durumu (skeleton) görünüyor
- [ ] Bir paper'a tıklandığında PaperDetail paneli güncelleniyor
- [ ] Toast bildirimleri çalışıyor (hata durumunda)
- [ ] Docker container'lar sağlıklı (docker-compose ps)

---

*Sprint 5 Tamamlanma Tarihi: 2026-02-12*
