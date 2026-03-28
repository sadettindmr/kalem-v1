<!--
FILE: docs/ai/quick-start.md
PURPOSE: Quick start guide for AI assistants
MAX_SIZE: 400 lines

SPLIT_STRATEGY:
- If file exceeds 400 lines, split into:
  - quick-start.md (core workflow, first 200 lines)
  - common-tasks.md (task-specific guides, remaining content)
  - Update CLAUDE.md navigation table with new files
-->

# Quick Start Guide for AI Assistants

**Last Updated:** 2026-03-28

---

## 🎯 Before Any Code Changes

Follow this workflow for every task:

1. **Read** `docs/ai/tasks.md` → Current sprint status and priorities
2. **Check** `docs/ai/architecture.md` → Module structure and patterns
3. **Review** relevant sprint docs in `docs/sprints/` → Feature context
4. **Consult** `docs/ai/decisions.md` → Architectural constraints

**Golden Rule:** Never guess at architecture. Always read the relevant documentation first.

---

## 🔍 Common Tasks

### Task Routing Table

| Task                      | Primary Reference                                 | Secondary Reference                          |
| ------------------------- | ------------------------------------------------- | -------------------------------------------- |
| **Backend Development**   |
| Add a new API endpoint    | `docs/ai/architecture.md` (API Layer)             | `docs/ai/context.md` (Module structure)      |
| Add a new search provider | `docs/ai/decisions.md` (ADR-011: Adapter Pattern) | `backend/athena/adapters/base.py`            |
| Modify database schema    | `docs/ai/architecture.md` (Database Schema)       | `docs/ai/context.md` (Alembic workflow)      |
| Debug a Celery task       | `docs/ai/decisions.md` (ADR-005: Celery)          | `docs/ai/context.md` (Tasks module)          |
| Change configuration      | `docs/ai/decisions.md` (ADR-008: Runtime Config)  | `backend/athena/core/config.py`              |
| **Frontend Development**  |
| Update frontend UI        | `docs/ai/architecture.md` (Frontend Modules)      | `docs/ai/context.md` (ShadCN/UI)             |
| Add a new page/route      | `frontend/src/App.tsx`                            | `docs/ai/architecture.md` (Routing)          |
| Create Zustand store      | `frontend/src/stores/`                            | `docs/ai/architecture.md` (State Management) |
| **DevOps**                |
| Docker configuration      | `docker-compose.yml`, `Dockerfile.*`              | `docs/ai/architecture.md` (Infrastructure)   |
| Database migrations       | `backend/migrations/`                             | `docs/ai/context.md` (Alembic workflow)      |

---

## 🚀 Development Workflow

### 1. Starting the Application

```bash
# Start all services (PostgreSQL, Redis, RabbitMQ, backend, frontend, Celery)
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build

# Check service health
docker-compose ps

# Verify backend API
curl http://localhost:8000/api/v2/health

# Access frontend
open http://localhost:3000
```

### 2. Running Tests

```bash
# Backend tests (pytest)
cd backend
poetry run pytest

# Frontend build check
cd frontend
npm run build

# Database migrations (apply all pending)
cd backend
poetry run alembic upgrade head
```

### 3. Development Cycle

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes
# - Edit code
# - Create migration if needed: poetry run alembic revision --autogenerate -m "description"
# - Run tests

# 3. Commit with conventional commits
git add .
git commit -m "feat: add new feature description"

# 4. Push and create PR
git push origin feature/your-feature-name
# Create PR via GitHub UI
```

---

## 📝 Step-by-Step Guides

### Adding a New API Endpoint

1. **Define the Pydantic schema** (`backend/athena/schemas/`)

   ```python
   # schemas/your_module.py
   from pydantic import BaseModel

   class YourRequest(BaseModel):
       field: str

   class YourResponse(BaseModel):
       result: str
   ```

2. **Create the service logic** (`backend/athena/services/`)

   ```python
   # services/your_service.py
   from athena.core.exceptions import AthenaError

   async def process_request(data: YourRequest) -> YourResponse:
       # Business logic here
       return YourResponse(result="...")
   ```

3. **Add the router endpoint** (`backend/athena/api/v2/routers/`)

   ```python
   # api/v2/routers/your_router.py
   from fastapi import APIRouter
   from athena.schemas.your_module import YourRequest, YourResponse
   from athena.services.your_service import process_request

   router = APIRouter(prefix="/your-endpoint", tags=["Your Tag"])

   @router.post("/", response_model=YourResponse)
   async def endpoint(request: YourRequest):
       return await process_request(request)
   ```

4. **Register the router** (`backend/athena/api/v2/router.py`)

   ```python
   from athena.api.v2.routers import your_router

   api_router.include_router(your_router.router)
   ```

5. **Test the endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/v2/your-endpoint/ \
     -H "Content-Type: application/json" \
     -d '{"field": "value"}'
   ```

### Adding a Database Migration

1. **Modify the model** (`backend/athena/models/`)

   ```python
   # models/your_model.py
   from sqlalchemy import Column, String
   from athena.models.base import Base

   class YourModel(Base):
       __tablename__ = "your_table"
       new_field = Column(String, nullable=True)  # Add this field
   ```

2. **Generate migration**

   ```bash
   cd backend
   poetry run alembic revision --autogenerate -m "add new_field to your_table"
   ```

3. **Review migration file** (`backend/migrations/versions/xxxx_*.py`)
   - Check upgrade() and downgrade() functions
   - Verify column types and constraints

4. **Apply migration**

   ```bash
   poetry run alembic upgrade head
   ```

5. **Verify in database**
   ```bash
   docker exec -it kalem-v1-kasghar-postgres-1 psql -U athena_user -d athena_db
   \d your_table
   \q
   ```

### Adding a New Search Provider

1. **Create adapter class** (`backend/athena/adapters/`)

   ```python
   # adapters/your_provider.py
   from athena.adapters.base import BaseSearchProvider
   from athena.schemas.search import SearchResult

   class YourProviderAdapter(BaseSearchProvider):
       provider_name = "your_provider"

       async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
           # Implementation
           pass
   ```

2. **Register in SearchService** (`backend/athena/services/search.py`)

   ```python
   from athena.adapters.your_provider import YourProviderAdapter

   self.adapters = {
       # ...existing adapters...
       "your_provider": YourProviderAdapter(),
   }
   ```

3. **Test the adapter**
   ```bash
   curl -X POST http://localhost:8000/api/v2/search/ \
     -H "Content-Type: application/json" \
     -d '{
       "query": "test",
       "providers": ["your_provider"],
       "limit": 10
     }'
   ```

---

## 🔧 Troubleshooting

### Common Issues

#### Docker Build Failures

```bash
# Clear Docker cache and rebuild
docker-compose down -v
docker system prune -a
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker-compose up -d --build
```

#### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

#### Migration Conflicts

```bash
# Check migration history
cd backend
poetry run alembic history

# Downgrade one revision
poetry run alembic downgrade -1

# Reapply migration
poetry run alembic upgrade head
```

#### Frontend Build Errors

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build
```

---

## 📋 Pre-Commit Checklist

Before creating a PR, verify:

- [ ] **Tests pass:** `cd backend && poetry run pytest`
- [ ] **Frontend builds:** `cd frontend && npm run build`
- [ ] **Migrations applied:** `poetry run alembic upgrade head`
- [ ] **Docker services healthy:** `docker-compose ps`
- [ ] **API responds:** `curl http://localhost:8000/api/v2/health`
- [ ] **Conventional commit message:** `feat: description` or `fix: description`
- [ ] **No secrets in code:** Check for API keys, passwords
- [ ] **Code formatted:** Black (backend), Prettier (frontend)

---

## 🎓 Learning Resources

### Understanding the Codebase

1. **Start here:** `docs/ai/architecture.md`
   - System overview
   - Module responsibilities
   - Data flow diagrams

2. **Then read:** `docs/ai/decisions.md`
   - Why we chose FastAPI
   - Why async SQLAlchemy
   - Why adapter pattern

3. **Finally explore:** `docs/ai/context.md`
   - Full reference documentation
   - Historical context
   - Detailed configurations

### Key Patterns to Learn

| Pattern            | Location                            | Why It Matters                    |
| ------------------ | ----------------------------------- | --------------------------------- |
| Adapter Pattern    | `backend/athena/adapters/`          | All external APIs use this        |
| Repository Pattern | `backend/athena/repositories/`      | Data access abstraction (planned) |
| Service Layer      | `backend/athena/services/`          | Business logic isolation          |
| Error Hierarchy    | `backend/athena/core/exceptions.py` | Structured error handling         |
| Async/Await        | Everywhere in backend               | Non-blocking I/O                  |

---

**Next Steps:**

- Review `docs/ai/conventions.md` for coding standards
- Check `docs/ai/tasks.md` for current sprint status
- Explore `docs/sprints/` for feature implementation details

---

_Last Updated: 2026-03-28_
