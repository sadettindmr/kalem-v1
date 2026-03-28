<!--
FILE: docs/ai/onboarding_1.md
PURPOSE: Learning path, task recommendations, and FAQ (Part 2/2)
MAX_SIZE: 200 lines

CONTINUATION:
Previous file: docs/ai/onboarding_0.md
Last Updated: 2026-03-28
-->

# AI Assistant Onboarding Guide (Part 2/2)

**Last Updated:** 2026-03-28

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

| Pattern                | Location                       | Why It Matters                   |
| ---------------------- | ------------------------------ | -------------------------------- |
| **Adapter Pattern**    | `backend/athena/adapters/`     | All external APIs use this       |
| **Service Layer**      | `backend/athena/services/`     | Business logic isolated here     |
| **Repository Pattern** | `backend/athena/repositories/` | Data access abstraction          |
| **Async/Await**        | Everywhere                     | Non-blocking I/O for scalability |

### Frontend Patterns

| Pattern            | Location                      | Why It Matters          |
| ------------------ | ----------------------------- | ----------------------- |
| **Zustand Stores** | `frontend/src/stores/`        | Global state management |
| **ShadCN/UI**      | `frontend/src/components/ui/` | Reusable UI components  |
| **Axios Client**   | `frontend/src/lib/axios.ts`   | Centralized API calls   |
| **Type Safety**    | `frontend/src/types/`         | TypeScript interfaces   |

---

## ❓ FAQ for AI Assistants

**Q: Where do I start if I'm given a task?**

A: Always read `docs/ai/tasks.md` first to see current sprint status. Then check the relevant section in `docs/ai/architecture.md` for module structure.

**Q: Can I use synchronous code in backend?**

A: No. All database operations must use `async/await`. This is non-negotiable.

**Q: Should I create a new file or modify existing?**

A: Prefer modifying existing files unless adding completely new module. Avoid file bloat.

**Q: Do I need tests for every change?**

A: For new features, yes. For bug fixes, add test if possible. Always run existing tests before committing.

**Q: Can I add npm packages or Poetry dependencies?**

A: Ask user first. Only add if they solve clear problem and don't duplicate existing functionality.

**Q: What if I get blocked?**

A: Check `docs/ai/troubleshooting_0.md` and `docs/ai/troubleshooting_1.md` first. If unresolved, ask user.

**Q: How do I know which version to tag?**

A: Follow SemVer in `docs/ai/conventions_1.md`:

- Breaking changes → MAJOR bump
- New features → MINOR bump
- Bug fixes → PATCH bump

See `docs/release-management.md` for detailed procedures.

---

## 🚀 You're Ready!

After completing this onboarding:

1. ✅ You understand the project structure
2. ✅ You know where to find documentation
3. ✅ You've verified the development environment
4. ✅ You're familiar with key patterns and conventions
5. ✅ You know how to debug common issues

**Next Steps:**

- Check `docs/ai/tasks.md` for current sprint status
- Pick a task or ask the user what to work on
- Follow the development workflow in `docs/ai/quick-start.md`

**Welcome aboard! Let's build something great.** 🎉

---

**Start from:** See `docs/ai/onboarding_0.md` for Full Onboarding Checklist.

---

_Last Updated: 2026-03-28_
_Previous file: docs/ai/onboarding_0.md_
