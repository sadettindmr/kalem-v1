<!--
FILE: docs/ai/onboarding.md
PURPOSE: AI assistant onboarding checklist and learning path
MAX_SIZE: 200 lines

SPLIT_STRATEGY:
- If file exceeds 200 lines, split into:
  - onboarding.md (core checklist and first steps - first 100 lines)
  - learning-path.md (detailed tutorials and examples - remaining)
  - Update CLAUDE.md navigation table with new files
-->

# AI Assistant Onboarding Guide

**Last Updated:** 2026-03-30

---

## 🎓 Welcome to Kalem!

This guide will help you get up to speed with the **Kalem** (Kasghar) project - an academic paper research and library management system.

---

## 🚀 Current Release Snapshot

- **Version:** `v1.2.0` (Kasghar Release)
- **Release Date:** 2026-03-30
- **Highlights:** EZProxy enstitü erişimi desteği, ücretli makalelerin üniversite proxy'si üzerinden indirilmesi.
- **Reference:** See `docs/release_notes.md` for full changelog and deployment notes.

---

## ✅ Onboarding Checklist

### Phase 1: Essential Reading (15 minutes)

- [ ] **Read this file** - Onboarding guide (you are here!)
- [ ] **Read** `CLAUDE.md` - Main navigation hub
- [ ] **Read** `docs/ai/tasks.md` - Current sprint status and priorities
- [ ] **Skim** `docs/ai/architecture.md` - System architecture overview

**Goal:** Understand the project structure and current development status.

---

### Phase 2: System Verification (10 minutes)

- [ ] **Verify Docker is running**

  ```bash
  docker ps
  ```

- [ ] **Check all services are healthy**

  ```bash
  docker-compose ps
  # Expected: 6 services running (backend, frontend, postgres, redis, rabbitmq, celery_worker)
  ```

- [ ] **Test backend API**

  ```bash
  curl http://localhost:8000/api/v2/health
  # Expected: {"status":"healthy"}
  ```

- [ ] **Access frontend**
  ```bash
  open http://localhost:3000
  # Expected: React app loads in browser
  ```

**Goal:** Confirm the development environment is working.

---

### Phase 3: Deep Dive (30 minutes)

- [ ] **Read** `docs/ai/decisions.md` - Key architectural decisions (ADRs)
  - Focus on: ADR-001 (Framework), ADR-005 (Celery), ADR-011 (Adapters)

- [ ] **Read** `docs/ai/conventions.md` - Code style and standards
  - Focus on: Non-negotiable rules, commit message format

- [ ] **Review** active sprint docs
  - [ ] `docs/sprints/sprint18.md` - Library management (delete, remove, tags)
  - [ ] `docs/sprints/sprint17.md` - EZProxy institutional access
  - [ ] `docs/sprints/sprint15.md` - Collections / projects

**Goal:** Understand why we made specific design choices and what we're building.

---

### Phase 4: Code Exploration (30 minutes)

- [ ] **Backend structure**
  - [ ] Open `backend/athena/api/v2/routers/search.py` - API endpoint example
  - [ ] Open `backend/athena/services/search.py` - Business logic example
  - [ ] Open `backend/athena/adapters/arxiv.py` - Adapter pattern example
  - [ ] Open `backend/athena/models/library.py` - Database model example

- [ ] **Frontend structure**
  - [ ] Open `frontend/src/App.tsx` - Main app component
  - [ ] Open `frontend/src/components/SearchBar.tsx` - Component example
  - [ ] Open `frontend/src/stores/searchStore.ts` - State management example
  - [ ] Open `frontend/src/services/api.ts` - API client example

**Goal:** Familiarize yourself with the codebase structure and patterns.

---

### Phase 5: Hands-On Practice (Optional, 30 minutes)

- [ ] **Run backend tests**

  ```bash
  cd backend
  poetry run pytest
  ```

- [ ] **Run frontend build**

  ```bash
  cd frontend
  npm run build
  ```

- [ ] **Create a test migration** (optional)
  ```bash
  cd backend
  poetry run alembic revision -m "test migration"
  # Delete the generated file after: rm migrations/versions/xxxx_test_migration.py
  ```

**Goal:** Gain hands-on experience with the development workflow.

---

## 📚 Learning Path

### For Backend Tasks

**Priority:** High → Low

1. `docs/ai/architecture.md` → **API Layer** section
2. `docs/ai/conventions.md` → **Backend (Python)** section
3. `docs/ai/decisions.md` → **ADR-005 (Celery)**, **ADR-011 (Adapters)**
4. `docs/ai/quick-start.md` → **Adding a New API Endpoint** guide
5. `docs/ai/context.md` → **Module structure** (if needed)

### For Frontend Tasks

**Priority:** High → Low

1. `docs/ai/architecture.md` → **Frontend Modules** section
2. `docs/ai/conventions.md` → **Frontend (TypeScript/React)** section
3. `docs/ai/decisions.md` → **ADR-009 (ShadCN/UI)**
4. `docs/ai/quick-start.md` → **Common Tasks** → Frontend development
5. `frontend/src/` → Explore component structure

### For Database Tasks

**Priority:** High → Low

1. `docs/ai/architecture.md` → **Database Schema** section
2. `docs/ai/quick-start.md` → **Adding a Database Migration** guide
3. `docs/ai/conventions.md` → **Async Patterns** section
4. `backend/athena/models/` → Explore existing models
5. `backend/migrations/versions/` → Review migration examples

### For DevOps/Infrastructure Tasks

**Priority:** High → Low

1. `docs/ai/architecture.md` → **Infrastructure** section
2. `docs/ai/troubleshooting.md` → **Docker Issues** section
3. `docker-compose.yml` → Service definitions
4. `Dockerfile.backend` and `Dockerfile.frontend` → Build configurations

---

## 🎯 First Task Recommendations

### Easy Tasks (Good for beginners)

- Add a new field to an existing Pydantic schema
- Update frontend UI text or styling
- Add logging statements to track request flow
- Write unit tests for an existing function

### Medium Tasks (After completing onboarding)

- Add a new API endpoint with Pydantic validation
- Create a new React component
- Add a database migration for a new field
- Debug a Celery task issue

### Advanced Tasks (After understanding the codebase)

- Implement a new search provider adapter
- Add a new sprint feature (e.g., paper annotations)
- Refactor existing code to improve performance
- Design a new module architecture

---

## 🔑 Key Concepts to Understand

### Backend Patterns

| Pattern                | Location                       | Why It Matters                                       |
| ---------------------- | ------------------------------ | ---------------------------------------------------- |
| **Adapter Pattern**    | `backend/athena/adapters/`     | All external APIs (arXiv, Semantic Scholar) use this |
| **Service Layer**      | `backend/athena/services/`     | Business logic is isolated here                      |
| **Repository Pattern** | `backend/athena/repositories/` | Data access abstraction (planned)                    |
| **Async/Await**        | Everywhere                     | Non-blocking I/O for scalability                     |

### Frontend Patterns

| Pattern            | Location                      | Why It Matters                          |
| ------------------ | ----------------------------- | --------------------------------------- |
| **Zustand Stores** | `frontend/src/stores/`        | Global state management                 |
| **ShadCN/UI**      | `frontend/src/components/ui/` | Reusable UI components                  |
| **Axios Client**   | `frontend/src/lib/axios.ts`   | Centralized API calls                   |
| **Type Safety**    | `frontend/src/types/`         | TypeScript interfaces for API responses |

---

## ❓ FAQ for AI Assistants

### Q: Where do I start if I'm given a task?

**A:** Always start by reading `docs/ai/tasks.md` to see the current sprint status. Then check the relevant section in `docs/ai/architecture.md` for module structure.

### Q: Can I use synchronous code in the backend?

**A:** No. All database operations and I/O must use `async/await`. This is a non-negotiable rule.

### Q: Should I create a new file or modify an existing one?

**A:** Always prefer modifying existing files unless you're adding a completely new module. Avoid file bloat.

### Q: Do I need to create tests for every change?

**A:** For new features, yes. For bug fixes, add a test case if possible. Always run existing tests before committing.

### Q: Can I add npm packages or Poetry dependencies?

**A:** Ask the user first. Only add dependencies if they solve a clear problem and don't duplicate existing functionality.

### Q: What should I do if I encounter a blocking issue?

**A:** Check `docs/ai/troubleshooting.md` first. If not resolved, ask the user for guidance rather than making assumptions.

### Q: How do I know which version to tag?

**A:** Follow SemVer rules in `docs/ai/conventions.md`:

- Breaking changes → MAJOR bump
- New features → MINOR bump
- Bug fixes → PATCH bump

---

## 🚀 You're Ready!

After completing this onboarding:

1. ✅ You understand the project structure
2. ✅ You know where to find documentation
3. ✅ You've verified the development environment
4. ✅ You're familiar with key patterns and conventions
5. ✅ You know how to debug common issues

**Next Steps:**

- Check `docs/ai/tasks.md` for the current sprint status
- Pick a task or ask the user what to work on
- Follow the development workflow in `docs/ai/quick-start.md`

**Welcome aboard! Let's build something great.** 🎉

---

_Last Updated: 2026-03-30_
