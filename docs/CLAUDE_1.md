<!--
FILE: docs/CLAUDE_1.md
PURPOSE: Main navigation hub for AI assistants (Part 2/2)
MAX_SIZE: 150 lines

CONTINUATION:
Previous file: docs/CLAUDE_0.md
Last Updated: 2026-03-28
-->

# Kalem - Kasghar AI Assistant Guide (Continued)

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
│   ├── ai/                  # AI assistant documentation
│   ├── release-management.md   # Release strategy
│   ├── release-procedure.md    # Release steps
│   ├── CLAUDE_0.md         # Navigation (part 1)
│   └── CLAUDE_1.md         # Navigation (part 2)
│
├── backend/                # FastAPI + Python
│   ├── athena/             # Main package
│   └── migrations/         # Database migrations
│
└── frontend/               # React + TypeScript
    └── src/                # Source code
```

**Full structure:** See `docs/ai/architecture.md`

---

## 🛠️ Technology Stack

| Layer    | Tech                          | Version          |
| -------- | ----------------------------- | ---------------- |
| Backend  | FastAPI + Python              | 3.11             |
| Database | PostgreSQL (async SQLAlchemy) | 16-alpine        |
| Tasks    | Celery + RabbitMQ             | 5.3.0            |
| Frontend | React + TypeScript + Vite     | 19.x / 5.x / 7.x |
| Cache    | Redis                         | 7-alpine         |

---

## 📊 Current Sprint Status

**Active Sprints:** Sprint 16 (API Documentation) + Sprint 15 (Collections) + Sprint 14 (QA/CI)

**Status:** ✅ Sprint 12-16 completed

**Details:** See `docs/ai/tasks.md` for full checklist

---

## 📞 Need Help?

| Question                 | Where to Look                |
| ------------------------ | ---------------------------- |
| "How do I start?"        | `docs/ai/onboarding.md`      |
| "What are we building?"  | `docs/ai/tasks.md`           |
| "How do I add X?"        | `docs/ai/quick-start.md`     |
| "How does Y work?"       | `docs/ai/architecture.md`    |
| "Why did we do Z?"       | `docs/ai/decisions.md`       |
| "What's the code style?" | `docs/ai/conventions.md`     |
| "I have an error!"       | `docs/ai/troubleshooting.md` |
| "Release procedures?"    | `docs/release-management.md` |

---

## 🎓 First Steps

- [ ] Read `docs/ai/onboarding.md` (15-30 min)
- [ ] Check `docs/ai/tasks.md` (current sprint status)
- [ ] Skim `docs/ai/architecture.md` (system overview)
- [ ] Review `docs/ai/conventions.md` (critical rules)
- [ ] Verify services: `docker-compose ps` (all 6 services)
- [ ] Test API: `curl http://localhost:8000/api/v2/health`

**You're ready to code!** 🚀

---

**Start from:** See `docs/CLAUDE_0.md` for full navigation table and quick start guide.

---

_Last Updated: 2026-03-28_
_Previous file: docs/CLAUDE_0.md_
