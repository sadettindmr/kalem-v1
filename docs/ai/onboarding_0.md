<!--
FILE: docs/ai/onboarding_0.md
PURPOSE: AI assistant onboarding checklist (Part 1/2)
MAX_SIZE: 200 lines

CONTINUATION:
Next file: docs/ai/onboarding_1.md
Last Updated: 2026-03-28
-->

# AI Assistant Onboarding Guide (Part 1/2)

**Last Updated:** 2026-03-28

---

## 🎓 Welcome to Kalem!

This guide will help you get up to speed with the **Kalem** (Kasghar) project - an academic paper research and library management system.

---

## ✅ Onboarding Checklist

### Phase 1: Essential Reading (15 minutes)

- [ ] **Read this file** - Onboarding guide (you are here!)
- [ ] **Read** `docs/CLAUDE_0.md` and `docs/CLAUDE_1.md` - Main navigation hub
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
  # Expected: 6 services running
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

- [ ] **Read** `docs/ai/conventions_0.md` and `docs/ai/conventions_1.md` - Code style and standards
  - Focus on: Non-negotiable rules, commit message format

- [ ] **Review** active sprint docs
  - [ ] `docs/sprints/sprint12.md` - Advanced export features
  - [ ] `docs/sprints/sprint13.md` - Configuration center & FTS

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

**Goal:** Gain hands-on experience with the development workflow.

---

## ➡️ Continue Reading

**Next:** See `docs/ai/onboarding_1.md` for First Task Recommendations, Key Concepts, FAQ, and Final Checklist.

---

_Last Updated: 2026-03-28_
_Continuation: docs/ai/onboarding_1.md_
