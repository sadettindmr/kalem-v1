<!--
FILE: CLAUDE.md
PURPOSE: Main navigation hub for AI assistants
MAX_SIZE: 150 lines

SPLIT_STRATEGY:
- This file should ONLY contain:
  1. Project metadata (name, version, architecture)
  2. Documentation navigation table
  3. Quick reference links
  4. Onboarding entry point
- NEVER add detailed content here - refer to modular docs instead
- If this file exceeds 150 lines, remove redundant sections and delegate to:
  - docs/ai/quick-start.md (workflows, commands)
  - docs/ai/conventions.md (rules, standards)
  - docs/ai/troubleshooting.md (issues, debugging)
  - docs/ai/onboarding.md (learning path)
-->

# Kalem - Kasghar AI Assistant Guide

**Project:** Academic Paper Research & Library Management System
**Version:** v2.0.0-develop (main branch: v1.3.0)
**Architecture:** Modular Monolith (FastAPI + React)

---

## 📚 Documentation Map

This project uses a **modular documentation approach**. Start with the reference most relevant to your task:

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[docs/ai/onboarding.md](docs/ai/onboarding.md)** | 🎓 AI assistant onboarding checklist | First time working on this project |
| **[docs/ai/tasks.md](docs/ai/tasks.md)** | 📋 Current sprint tasks & status | Before starting any work |
| **[docs/ai/quick-start.md](docs/ai/quick-start.md)** | 🚀 Development workflows & guides | Adding features, debugging, testing |
| **[docs/ai/architecture.md](docs/ai/architecture.md)** | 🏗️ System design & tech stack | Understanding module structure |
| **[docs/ai/conventions.md](docs/ai/conventions.md)** | 📐 Code style & standards | Writing code, commits, versioning |
| **[docs/ai/decisions.md](docs/ai/decisions.md)** | 🤔 Architectural Decision Records | Why we made specific choices |
| **[docs/ai/troubleshooting.md](docs/ai/troubleshooting.md)** | 🐛 Known issues & debugging | Fixing errors, debugging |
| **[docs/ai/context.md](docs/ai/context.md)** | 📖 Full project reference | Comprehensive details (large file) |
| **[docs/sprints/](docs/sprints/)** | 📁 Sprint documentation | Historical context, feature specs |

---

## 🎯 Quick Start

### New to this project?
1. Read `docs/ai/onboarding.md` (complete the checklist)
2. Check `docs/ai/tasks.md` (see current sprint status)
3. Review `docs/ai/quick-start.md` (learn development workflow)

### Starting a task?
1. **Read** `docs/ai/tasks.md` → Current sprint status
2. **Check** `docs/ai/architecture.md` → Module structure
3. **Review** relevant sprint docs in `docs/sprints/` → Feature context
4. **Consult** `docs/ai/decisions.md` → Architectural constraints

### Common task routing:
- **Add API endpoint** → `docs/ai/quick-start.md` (Adding a New API Endpoint)
- **Add search provider** → `docs/ai/decisions.md` (ADR-011: Adapter Pattern)
- **Modify database** → `docs/ai/quick-start.md` (Adding a Database Migration)
- **Update frontend UI** → `docs/ai/architecture.md` (Frontend Modules)
- **Debug error** → `docs/ai/troubleshooting.md`
- **Code style question** → `docs/ai/conventions.md`

---

## 🔑 Critical Rules

These rules are **non-negotiable** (see `docs/ai/conventions.md` for details):

1. ✅ **Never skip migrations** - Always create Alembic migration for schema changes
2. ✅ **Preserve async patterns** - All database operations must use `async/await`
3. ✅ **Maintain adapter pattern** - New providers implement `BaseSearchProvider`
4. ✅ **Follow error hierarchy** - Use `AthenaError` subclasses, not bare exceptions
5. ✅ **Use structured logging** - Loguru with `request_id` correlation
6. ✅ **Test before commit** - Run `pytest` + `npm build` before pushing

---

## 🏗️ Project Structure (Quick Reference)

```
/
├── docs/
│   ├── ai/                  # AI assistant documentation (READ THIS)
│   │   ├── onboarding.md   # Start here for new assistants
│   │   ├── tasks.md        # Current sprint status
│   │   ├── quick-start.md  # Development workflows
│   │   ├── architecture.md # System design
│   │   ├── conventions.md  # Code style & standards
│   │   ├── decisions.md    # Architectural decisions (ADRs)
│   │   ├── troubleshooting.md # Debugging guide
│   │   └── context.md      # Full reference (large file)
│   │
│   └── sprints/            # Sprint-by-sprint documentation
│       ├── sprint12.md     # Advanced export features
│       └── sprint13.md     # Configuration center & FTS
│
├── backend/
│   ├── athena/
│   │   ├── api/v2/routers/ # REST endpoints
│   │   ├── services/       # Business logic
│   │   ├── adapters/       # External API integrations
│   │   ├── models/         # SQLAlchemy ORM
│   │   └── schemas/        # Pydantic DTOs
│   └── migrations/         # Alembic database migrations
│
└── frontend/
    └── src/
        ├── components/     # React components
        ├── stores/         # Zustand state management
        └── services/       # API client functions
```

**Full structure:** See `docs/ai/architecture.md`

---

## 🛠️ Technology Stack

| Layer | Tech | Version |
|-------|------|---------|
| Backend | FastAPI + Python | 3.11 |
| Database | PostgreSQL (async SQLAlchemy) | 16-alpine |
| Tasks | Celery + RabbitMQ | 5.3.0 |
| Frontend | React + TypeScript + Vite | 19.x / 5.x / 7.x |
| Cache | Redis | 7-alpine |

**Detailed stack:** See `docs/ai/architecture.md`

---

## 📊 Current Sprint Status

**Active Sprints:** Sprint 18 (Library Management) - ✅ Completed

**Status:** ✅ v1.3.0 released - Delete, Remove from Collection, Edit Tags

**Details:** See `docs/ai/tasks.md` for full checklist

---

## 📞 Need Help?

| Question | Where to Look |
|----------|---------------|
| "How do I start?" | `docs/ai/onboarding.md` |
| "What are we building?" | `docs/ai/tasks.md` |
| "How do I add X?" | `docs/ai/quick-start.md` |
| "How does Y work?" | `docs/ai/architecture.md` |
| "Why did we do Z?" | `docs/ai/decisions.md` |
| "What's the code style?" | `docs/ai/conventions.md` |
| "I have an error!" | `docs/ai/troubleshooting.md` |
| "I need ALL the details" | `docs/ai/context.md` |

---

## 🎓 First Steps for AI Assistants

**Complete this onboarding checklist:**

- [ ] Read `docs/ai/onboarding.md` (15-30 min)
- [ ] Check `docs/ai/tasks.md` (current sprint status)
- [ ] Skim `docs/ai/architecture.md` (system overview)
- [ ] Review `docs/ai/conventions.md` (critical rules)
- [ ] Verify services: `docker-compose ps` (all 6 services running)
- [ ] Test API: `curl http://localhost:8000/api/v2/health`

**You're ready to code!** 🚀

---

*Last Updated: 2026-03-28*
*Documentation Version: 2.0 (Modular Structure)*
