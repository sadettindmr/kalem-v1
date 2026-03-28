<!--
FILE: docs/ai/troubleshooting_0.md
PURPOSE: Known issues and common infrastructure errors (Part 1/2)
MAX_SIZE: 300 lines

CONTINUATION:
Next file: docs/ai/troubleshooting_1.md
Last Updated: 2026-03-28
-->

# Troubleshooting Guide (Part 1/2)

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
Another service using the port

# Solution 1: Stop conflicting service
lsof -i :5432
kill -9 <PID>

# Solution 2: Change port in docker-compose.yml
services:
  postgres:
    ports:
      - "5433:5432"  # Change host port to 5433
```

#### Error: "No space left on device"

```bash
# Symptom
ERROR: failed to register layer: write /...: no space left on device

# Cause
Docker disk space full

# Solution
docker system prune -a --volumes
# WARNING: Removes all unused containers, images, networks, and volumes

# Check disk usage
docker system df
```

#### Error: "BuildKit attestation warnings"

```bash
# Symptom
WARN[0000] attestation warnings: missing provenance

# Solution
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
docker-compose down -v
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

---

## ➡️ Continue Reading

**Next:** See `docs/ai/troubleshooting_1.md` for Frontend Issues, API Integration Problems, Health Checks, and Emergency Procedures.

---

**Related Documentation:**

- `docs/ai/quick-start.md` - Development workflows
- `docs/ai/architecture.md` - System architecture
- `docs/ai/conventions.md` - Code standards

---

_Last Updated: 2026-03-28_
_Continuation: docs/ai/troubleshooting_1.md_
