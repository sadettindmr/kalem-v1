<!--
FILE: docs/ai/conventions.md
PURPOSE: Code style, conventions, and development standards
MAX_SIZE: 400 lines

SPLIT_STRATEGY:
- If file exceeds 400 lines, split into:
  - conventions.md (core rules, versioning, commits - first 200 lines)
  - code-style.md (language-specific formatting rules - remaining)
  - Update CLAUDE.md navigation table with new files
-->

# Development Conventions & Standards

**Last Updated:** 2026-03-28

---

## 🔑 Key Principles

### Non-Negotiable Rules

These rules are **mandatory** and breaking them will cause issues:

1. **Never skip migrations**
   - Always create an Alembic migration for schema changes
   - Never modify the database manually
   - Test migrations in both directions (upgrade + downgrade)

2. **Preserve async patterns**
   - All database operations must use `async/await`
   - Never use synchronous SQLAlchemy methods
   - Use `async with` for async context managers

3. **Maintain adapter pattern**
   - New external API providers must implement `BaseSearchProvider`
   - Never call external APIs directly from services
   - Keep adapters stateless and testable

4. **Follow error hierarchy**
   - Use `AthenaError` subclasses, not bare exceptions
   - Never raise generic `Exception` or `RuntimeError`
   - Always provide context in error messages

5. **Use structured logging**
   - Use Loguru with `request_id` correlation
   - Never use `print()` statements
   - Log errors with full context (exception, request_id, user_id)

6. **Test before commit**
   - Run `pytest` for backend changes
   - Run `npm run build` for frontend changes
   - Verify Docker services are healthy

---

## 📐 Code Style

### Backend (Python)

#### Formatting Tools

- **Black:** Code formatter (line length: 88)
- **isort:** Import sorter (profile: black)
- **mypy:** Type checker (strict mode)

```bash
# Auto-format code
cd backend
poetry run black athena/
poetry run isort athena/

# Type checking
poetry run mypy athena/
```

#### Naming Conventions

```python
# Classes: PascalCase
class SearchService:
    pass

# Functions/Methods: snake_case
async def fetch_paper_details(paper_id: str) -> PaperDetail:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# Private methods: _leading_underscore
def _internal_helper(self):
    pass

# Async functions: always prefix with "async"
async def get_database_session():  # Good
    pass

def fetch_data():  # Bad - should be async if it does I/O
    pass
```

#### Type Hints

**Always use type hints** for function signatures:

```python
# Good
async def search_papers(
    query: str,
    providers: list[str],
    limit: int = 10
) -> list[SearchResult]:
    pass

# Bad
async def search_papers(query, providers, limit=10):
    pass
```

#### Import Organization

```python
# 1. Standard library
import asyncio
from datetime import datetime
from typing import Optional

# 2. Third-party packages
from fastapi import APIRouter, Depends
from sqlalchemy import select
from pydantic import BaseModel

# 3. Local imports (absolute paths)
from athena.core.database import get_db
from athena.models.library import LibraryEntry
from athena.schemas.search import SearchRequest
```

#### Error Handling

```python
# Good: Use custom exceptions
from athena.core.exceptions import ValidationError, NotFoundError

if not paper_id:
    raise ValidationError("paper_id is required")

paper = await db.get(Paper, paper_id)
if not paper:
    raise NotFoundError(f"Paper {paper_id} not found")

# Bad: Generic exceptions
raise ValueError("Invalid input")  # ❌
raise Exception("Something went wrong")  # ❌
```

#### Async Patterns

```python
# Good: Proper async/await
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Bad: Blocking I/O in async function
async def fetch_data():
    response = requests.get(url)  # ❌ Blocks event loop
    return response.json()
```

---

### Frontend (TypeScript/React)

#### Formatting Tools

- **Prettier:** Code formatter (via Vite)
- **ESLint:** Linter (extends: react, typescript)

```bash
# Auto-format code
cd frontend
npm run lint
npm run format
```

#### Naming Conventions

```typescript
// Components: PascalCase
export function SearchBar() {
  return <div>...</div>;
}

// Hooks: use* prefix
function useSearchQuery() {
  return useState(...);
}

// Functions: camelCase
function formatDate(date: Date): string {
  return date.toISOString();
}

// Constants: UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8000';
const MAX_RESULTS = 100;

// Interfaces/Types: PascalCase
interface SearchResult {
  title: string;
  authors: string[];
}

type PaperId = string;
```

#### Component Structure

```tsx
// Good: Functional component with types
interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

export function SearchBar({
  onSearch,
  placeholder = "Search...",
}: SearchBarProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
    </form>
  );
}

// Bad: Untyped props
export function SearchBar({ onSearch, placeholder }) {
  // ❌
  // ...
}
```

#### State Management (Zustand)

```typescript
// stores/searchStore.ts
import { create } from "zustand";

interface SearchState {
  query: string;
  results: SearchResult[];
  isLoading: boolean;
  setQuery: (query: string) => void;
  setResults: (results: SearchResult[]) => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  results: [],
  isLoading: false,
  setQuery: (query) => set({ query }),
  setResults: (results) => set({ results }),
}));
```

#### API Client Patterns

```typescript
// Good: Typed API client
import axios from "@/lib/axios";

export async function searchPapers(
  query: string,
  providers: string[],
): Promise<SearchResult[]> {
  const { data } = await axios.post<{ results: SearchResult[] }>(
    "/api/v2/search/",
    { query, providers },
  );
  return data.results;
}

// Bad: Untyped responses
export async function searchPapers(query, providers) {
  // ❌
  const response = await fetch("/api/v2/search/", {
    method: "POST",
    body: JSON.stringify({ query, providers }),
  });
  return response.json(); // Unknown type
}
```

---

## 🏷️ Versioning & Branching Strategy

### Semantic Versioning (SemVer)

**Format:** `MAJOR.MINOR.PATCH`

| Component         | When to Increment                               | Examples                                                    |
| ----------------- | ----------------------------------------------- | ----------------------------------------------------------- |
| **MAJOR** (X.0.0) | Breaking changes, major architecture shifts     | v1.0 → v2.0 (Modular Monolith), v2.0 → v3.0 (Microservices) |
| **MINOR** (1.X.0) | New features, backward-compatible enhancements  | v1.0 → v1.1 (Add FTS), v1.1 → v1.2 (Add export)             |
| **PATCH** (1.0.X) | Bug fixes, security patches, small improvements | v1.0.1 (Fix search), v1.0.2 (UI stability)                  |

### Branching Model

```
main                    # Production-ready (v1.0.2)
  │
  ├─ feature/sprint-X   # New features (minor bump)
  │   └─ merged → main → tag vX.Y.0
  │
  ├─ fix/issue-name     # Bug fixes (patch bump)
  │   └─ merged → main → tag vX.Y.Z
  │
  └─ v2.0.0-develop     # Next major version (isolated)
      └─ merged → main when stable → tag v2.0.0
```

### Branch Naming

```bash
# Features (Sprint-based)
feature/sprint-14-annotations
feature/add-pdf-viewer

# Bug fixes
fix/search-timeout-error
fix/ui-responsive-layout

# Hotfixes (critical production bugs)
hotfix/security-patch-cve-2024-1234

# Experimental (not merged to main)
experiment/ml-ranking-algorithm
```

### Workflow Examples

#### 1. Feature Development

```bash
# Start feature branch
git checkout main
git pull
git checkout -b feature/sprint-14-annotations

# Develop and commit
git add .
git commit -m "feat(annotations): add paper annotation model"
git commit -m "feat(annotations): add API endpoints"
git commit -m "feat(annotations): add frontend UI"

# Push and create PR
git push origin feature/sprint-14-annotations
# Create PR via GitHub → main

# After merge: Tag new version
git checkout main
git pull
git tag -a v1.3.0 -m "feat: Add paper annotations (Sprint 14)"
git push origin v1.3.0

# Update app version
# Edit frontend/src/constants/app.ts → APP_VERSION = 'v1.3.0'
git add frontend/src/constants/app.ts
git commit -m "chore: bump version to v1.3.0"
git push
```

#### 2. Bug Fix

```bash
# Start fix branch
git checkout -b fix/search-relevance-ranking

# Fix and commit
git add .
git commit -m "fix(search): improve relevance ranking algorithm"

# Push and create PR
git push origin fix/search-relevance-ranking
# Create PR via GitHub → main

# After merge: Tag patch version
git checkout main
git pull
git tag -a v1.0.3 -m "fix: Improve search relevance ranking"
git push origin v1.0.3
```

### Branch Protection Rules

- **main branch:**
  - Requires PR approval
  - Requires passing CI/CD tests
  - No direct commits allowed
  - Auto-delete head branches after merge

---

## 📝 Commit Message Convention

**Format:** Conventional Commits (https://www.conventionalcommits.org/)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Commit Types

| Type       | Purpose                    | Example                                        |
| ---------- | -------------------------- | ---------------------------------------------- |
| `feat`     | New feature                | `feat(search): add semantic scholar provider`  |
| `fix`      | Bug fix                    | `fix(api): resolve timeout in paper fetch`     |
| `docs`     | Documentation              | `docs: update architecture.md with new module` |
| `style`    | Formatting, no code change | `style: format code with black`                |
| `refactor` | Code restructuring         | `refactor(services): extract caching logic`    |
| `test`     | Add/update tests           | `test(search): add unit tests for adapter`     |
| `chore`    | Maintenance                | `chore: update dependencies`                   |
| `perf`     | Performance improvement    | `perf(db): optimize query with index`          |

### Scope Examples

- `search` - Search module
- `library` - Library management
- `api` - API endpoints
- `ui` - Frontend UI
- `db` - Database operations
- `celery` - Background tasks
- `config` - Configuration
- `docker` - Docker/infrastructure

### Good Commit Messages

```bash
✅ feat(search): add OpenAlex provider adapter
✅ fix(library): prevent duplicate entries on concurrent saves
✅ docs(architecture): document adapter pattern
✅ refactor(api): extract validation middleware
✅ test(search): add integration tests for semantic scholar
✅ perf(db): add index on library_entries.paper_id
```

### Bad Commit Messages

```bash
❌ "update code"
❌ "fix bug"
❌ "WIP"
❌ "asdf"
❌ "Final commit before deadline"
```

---

## 🧪 Testing Standards

### Backend Testing (pytest)

```python
# tests/test_search_service.py
import pytest
from athena.services.search import SearchService

@pytest.mark.asyncio
async def test_search_returns_results():
    service = SearchService()
    results = await service.search("machine learning", providers=["arxiv"], limit=10)

    assert len(results) > 0
    assert all(r.title for r in results)

@pytest.mark.asyncio
async def test_search_handles_invalid_provider():
    service = SearchService()

    with pytest.raises(ValidationError, match="Invalid provider"):
        await service.search("test", providers=["invalid_provider"])
```

### Frontend Testing (Vitest - optional)

```typescript
// __tests__/SearchBar.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchBar } from '@/components/SearchBar';

test('calls onSearch when form is submitted', () => {
  const handleSearch = vi.fn();
  render(<SearchBar onSearch={handleSearch} />);

  const input = screen.getByRole('textbox');
  fireEvent.change(input, { target: { value: 'test query' } });
  fireEvent.submit(input.form!);

  expect(handleSearch).toHaveBeenCalledWith('test query');
});
```

---

## 🔒 Security Best Practices

1. **Never commit secrets**
   - Use `.env` for sensitive data
   - Never hardcode API keys in code
   - Use environment variables for credentials

2. **Input validation**
   - Validate all user inputs with Pydantic
   - Sanitize query parameters
   - Use parameterized SQL queries (SQLAlchemy ORM)

3. **Rate limiting**
   - Respect external API rate limits
   - Implement client-side throttling
   - Use exponential backoff for retries

4. **Error messages**
   - Don't expose stack traces to users
   - Log detailed errors server-side
   - Return generic error messages to clients

---

**Related Documentation:**

- `docs/ai/quick-start.md` - Development workflows
- `docs/ai/architecture.md` - System design patterns
- `docs/ai/decisions.md` - Why we chose these conventions

---

_Last Updated: 2026-03-28_
