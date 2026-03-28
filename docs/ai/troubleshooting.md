<!--
FILE: docs/ai/troubleshooting.md
PURPOSE: Known issues, common errors, and debugging guides
MAX_SIZE: 300 lines

SPLIT_STRATEGY:
- If file exceeds 300 lines, split by category:
  - troubleshooting.md (infrastructure, Docker, database - first 150 lines)
  - debugging-backend.md (Python, FastAPI, Celery issues)
  - debugging-frontend.md (React, TypeScript, build issues)
  - Update CLAUDE.md navigation table with new files
-->

# Troubleshooting Guide

**Last Updated:** 2026-03-28

---

## 🐛 Known Issues

### Current Production Issues

| Issue                         | Impact | Status    | Workaround                                       |
| ----------------------------- | ------ | --------- | ------------------------------------------------ |
| npm vulnerabilities (6 total) | Low    | Deferred  | Development dependencies only, not in production |
| Docker BuildKit warnings      | Low    | Mitigated | Use `BUILDX_NO_DEFAULT_ATTESTATIONS=1` flag      |

### Resolved Issues

| Issue                      | Resolution                      | Version |
| -------------------------- | ------------------------------- | ------- |
| arXiv low-result anomalies | Added stability checks          | v1.0.2  |
| Search timeout errors      | Implemented exponential backoff | v1.0.1  |

---

## 🚨 Common Errors & Solutions

### Docker Issues

#### Error: "Cannot connect to the Docker daemon"

```bash
# Symptom
ERROR: Cannot connect to the Docker daemon at unix:///var/run/docker.sock

# Cause
Docker Desktop not running

# Solution
# Start Docker Desktop application
open -a Docker

# Verify Docker is running
docker ps
```

#### Error: "Port already in use"

```bash
# Symptom
ERROR: for postgres  Cannot start service postgres:
Ports are not available: listen tcp 0.0.0.0:5432: bind: address already in use

# Cause
Another service is using the port (PostgreSQL, Redis, RabbitMQ, etc.)

# Solution 1: Stop conflicting service
# Find process using port 5432
lsof -i :5432
kill -9 <PID>

# Solution 2: Change port in docker-compose.yml
# Edit docker-compose.yml
services:
  postgres:
    ports:
      - "5433:5432"  # Change host port to 5433
```

#### Error: "No space left on device"

```bash
# Symptom
ERROR: failed to register layer: Error processing tar file: write /...: no space left on device

# Cause
Docker disk space full

# Solution
# Clean up Docker resources
docker system prune -a --volumes
# WARNING: This removes all unused containers, images, networks, and volumes

# Check disk usage
docker system df
```

#### Error: "BuildKit attestation warnings"

```bash
# Symptom
WARN[0000] attestation warnings: missing provenance

# Solution
# Use environment variable to disable BuildKit attestations
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build
```

---

### Database Issues

#### Error: "Connection refused (PostgreSQL)"

```bash
# Symptom
sqlalchemy.exc.OperationalError: could not connect to server: Connection refused

# Cause
PostgreSQL container not running or not ready

# Solution
# Check PostgreSQL status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U athena_user
```

#### Error: "Database does not exist"

```bash
# Symptom
sqlalchemy.exc.OperationalError: database "athena_db" does not exist

# Cause
Database not initialized

# Solution
# Recreate database
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d postgres
# Wait 10 seconds for PostgreSQL to be ready
docker-compose exec postgres createdb -U athena_user athena_db

# Run migrations
cd backend
poetry run alembic upgrade head
```

#### Error: "Migration conflict"

```bash
# Symptom
alembic.util.exc.CommandError: Can't locate revision identified by 'xxxx'

# Cause
Migration history mismatch

# Solution
# Check current migration
cd backend
poetry run alembic current

# Check migration history
poetry run alembic history

# Downgrade to base and reapply
poetry run alembic downgrade base
poetry run alembic upgrade head

# If that fails, reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d postgres
# Wait 10 seconds, then:
poetry run alembic upgrade head
```

---

### Backend Issues

#### Error: "ModuleNotFoundError: No module named 'athena'"

```bash
# Symptom
ModuleNotFoundError: No module named 'athena'

# Cause
Dependencies not installed or Poetry environment not activated

# Solution
cd backend
poetry install
poetry shell  # Activate virtual environment
```

#### Error: "Celery worker not processing tasks"

```bash
# Symptom
Tasks stuck in PENDING state

# Cause
Celery worker not running or RabbitMQ connection issue

# Solution
# Check Celery worker status
docker-compose ps celery_worker

# View Celery logs
docker-compose logs celery_worker

# Restart Celery worker
docker-compose restart celery_worker

# Check RabbitMQ status
docker-compose ps rabbitmq
```

#### Error: "422 Unprocessable Entity (Pydantic validation)"

```bash
# Symptom
fastapi.exceptions.RequestValidationError: validation error for Request

# Cause
Request body doesn't match Pydantic schema

# Solution
# Check API request in FastAPI docs
open http://localhost:8000/docs

# Example: Missing required field
# Bad request:
{
  "query": "machine learning"
  # Missing "providers" field
}

# Good request:
{
  "query": "machine learning",
  "providers": ["arxiv", "semantic_scholar"],
  "limit": 10
}
```

#### Error: "Timeout waiting for response"

```bash
# Symptom
httpx.TimeoutException: Request timeout

# Cause
External API slow or unresponsive

# Solution
# Check provider status in logs
docker-compose logs backend | grep "provider"

# Increase timeout in adapters (temporary fix)
# backend/athena/adapters/arxiv.py
async with httpx.AsyncClient(timeout=60.0) as client:  # Increase from 30.0
    ...
```

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
src/components/SearchBar.tsx:12:5 - error TS2322: Type 'string' is not assignable to type 'number'

# Cause
Type mismatch in code

# Solution
# Fix TypeScript errors
# Check the file and line number indicated
# Example:
interface Props {
  limit: number;  // Type is number
}

// Bad:
<Component limit="10" />  // ❌ String

// Good:
<Component limit={10} />  // ✅ Number
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
# backend/athena/adapters/base.py

# Wait before retrying
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

## 🔍 Debugging Tools

### Backend Debugging

```bash
# View live backend logs
docker-compose logs -f backend

# Filter logs by level
docker-compose logs backend | grep ERROR

# Access backend container shell
docker-compose exec backend bash

# Check Python environment
docker-compose exec backend poetry run python --version
docker-compose exec backend poetry run pip list
```

### Database Debugging

```bash
# Access PostgreSQL shell
docker exec -it kalem-v1-kasghar-postgres-1 psql -U athena_user -d athena_db

# Useful SQL queries
\dt                           # List tables
\d library_entries            # Describe table
SELECT COUNT(*) FROM library_entries;  # Count rows
\q                            # Quit
```

### Frontend Debugging

```bash
# View live frontend logs
docker-compose logs -f frontend

# Check frontend build output
cd frontend
npm run build

# Test production build locally
npm run preview
open http://localhost:4173
```

---

## 📊 Health Checks

### System Health Verification

```bash
# 1. Check all services are running
docker-compose ps

# Expected output:
# NAME                           STATUS
# kalem-v1-kasghar-backend-1     Up
# kalem-v1-kasghar-celery_worker-1    Up
# kalem-v1-kasghar-frontend-1    Up
# kalem-v1-kasghar-postgres-1    Up
# kalem-v1-kasghar-rabbitmq-1    Up
# kalem-v1-kasghar-redis-1       Up

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

**Related Documentation:**

- `docs/ai/quick-start.md` - Development workflows
- `docs/ai/architecture.md` - System architecture
- `docs/ai/conventions.md` - Best practices

---

_Last Updated: 2026-03-28_
