<!--
FILE: docs/ai/troubleshooting_1.md
PURPOSE: Frontend, API integration, health checks, and emergency procedures (Part 2/2)
MAX_SIZE: 250 lines

CONTINUATION:
Previous file: docs/ai/troubleshooting_0.md
Last Updated: 2026-03-28
-->

# Troubleshooting Guide (Part 2/2)

**Last Updated:** 2026-03-28

---

### Frontend Issues

#### Error: "npm install fails"

```bash
# Symptom
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree

# Cause
Dependency conflict

# Solution 1: Clean install
cd frontend
rm -rf node_modules package-lock.json
npm install

# Solution 2: Force install (use with caution)
npm install --force

# Solution 3: Use legacy peer deps
npm install --legacy-peer-deps
```

#### Error: "Module not found: Can't resolve '@/...'"

```bash
# Symptom
Module not found: Error: Can't resolve '@/components/SearchBar'

# Cause
TypeScript path alias not configured

# Solution
# Check vite.config.ts has path alias
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

# Check tsconfig.json has paths
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

#### Error: "TypeScript errors in production build"

```bash
# Symptom
npm run build
> tsc && vite build
src/components/SearchBar.tsx:12:5 - error TS2322

# Cause
Type mismatch in code

# Solution
# Fix TypeScript errors at the indicated file and line
# Example:
interface Props {
  limit: number;  # Type is number
}

// Good:
<Component limit={10} />  # ✅ Number

// Bad:
<Component limit="10" />  # ❌ String
```

---

### API Integration Issues

#### Error: "Rate limit exceeded"

```bash
# Symptom
429 Too Many Requests from external API

# Cause
Exceeded provider rate limit

# Solution
# Implement exponential backoff (already done in v1.0.1+)
import asyncio
await asyncio.sleep(5)  # Wait 5 seconds before retry

# Check provider rate limits in docs/ai/architecture.md
```

#### Error: "Invalid API key"

```bash
# Symptom
401 Unauthorized from Semantic Scholar API

# Cause
Missing or invalid API key in .env

# Solution
# Check .env file
SEMANTIC_SCHOLAR_API_KEY=your_actual_api_key_here

# Restart backend to reload environment
docker-compose restart backend
```

---

## 📊 Health Checks

### System Health Verification

```bash
# 1. Check all services are running
docker-compose ps

# 2. Verify backend API
curl http://localhost:8000/api/v2/health
# Expected: {"status":"healthy"}

# 3. Verify frontend
curl http://localhost:3000
# Expected: HTML response

# 4. Verify database connectivity
docker-compose exec postgres pg_isready -U athena_user
# Expected: /var/run/postgresql:5432 - accepting connections

# 5. Check Redis
docker-compose exec redis redis-cli ping
# Expected: PONG

# 6. Check RabbitMQ
curl http://localhost:15672
# Expected: RabbitMQ Management UI (login: guest/guest)
```

---

## 🆘 Emergency Procedures

### Complete System Reset

**WARNING:** This deletes all data, including the database and Docker volumes.

```bash
# 1. Stop all services
docker-compose down -v

# 2. Remove all Docker resources (optional, for deep clean)
docker system prune -a --volumes

# 3. Rebuild and start
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build

# 4. Wait for services to be ready (30 seconds)
sleep 30

# 5. Run migrations
cd backend
poetry run alembic upgrade head

# 6. Verify system health
curl http://localhost:8000/api/v2/health
```

### Backup Database Before Reset

```bash
# Export database to SQL file
docker exec kalem-v1-kasghar-postgres-1 pg_dump -U athena_user athena_db > backup.sql

# Restore after reset
cat backup.sql | docker exec -i kalem-v1-kasghar-postgres-1 psql -U athena_user -d athena_db
```

---

## ➡️ Previous Section

**Start from:** See `docs/ai/troubleshooting_0.md` for Known Issues and Docker/Database/Backend Errors.

---

**Related Documentation:**

- `docs/ai/quick-start.md` - Development workflows
- `docs/ai/architecture.md` - System architecture
- `docs/ai/conventions.md` - Best practices
- `docs/release-management.md` - Release procedures

---

_Last Updated: 2026-03-28_
_Previous file: docs/ai/troubleshooting_0.md_
