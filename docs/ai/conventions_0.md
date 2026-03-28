<!--
FILE: docs/ai/conventions_0.md
PURPOSE: Code style conventions (Part 1/2) - Backend and Frontend code standards
MAX_SIZE: 400 lines

CONTINUATION:
Next file: docs/ai/conventions_1.md
Last Updated: 2026-03-28
-->

# Development Conventions & Standards (Part 1/2)

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

## ➡️ Continue Reading

**Next:** See `docs/ai/conventions_1.md` for Versioning & Branching, Commit Message Convention, Testing Standards, and Security Best Practices.

---

**Related Documentation:**

- `docs/ai/quick-start.md` - Development workflows
- `docs/ai/architecture.md` - System design patterns
- `docs/ai/decisions.md` - Why we chose these conventions

---

_Last Updated: 2026-03-28_
_Continuation: docs/ai/conventions_1.md_
