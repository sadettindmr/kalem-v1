<!--
FILE: docs/ai/conventions_1.md
PURPOSE: Versioning, branching, commits, testing, and security (Part 2/2)
MAX_SIZE: 300 lines

CONTINUATION:
Previous file: docs/ai/conventions_0.md
Last Updated: 2026-03-28
-->

# Development Conventions & Standards (Part 2/2)

**Last Updated:** 2026-03-28

---

## 🏷️ Versioning & Branching Strategy

### Semantic Versioning (SemVer)

**Format:** `MAJOR.MINOR.PATCH`

| Component         | When to Increment                               | Examples                 |
| ----------------- | ----------------------------------------------- | ------------------------ |
| **MAJOR** (X.0.0) | Breaking changes, major architecture shifts     | v1.0 → v2.0, v2.0 → v3.0 |
| **MINOR** (1.X.0) | New features, backward-compatible enhancements  | v1.0 → v1.1, v1.1 → v1.2 |
| **PATCH** (1.0.X) | Bug fixes, security patches, small improvements | v1.0.1, v1.0.2           |

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
  └─ release/v2.0       # Next major version (isolated)
      └─ merged → main when stable → tag v2.0.0
```

**For detailed release procedures see:** `docs/release-management.md` and `docs/release-procedure.md`

### Branch Naming

```bash
# Features (Sprint-based)
feature/sprint-14-annotations
feature/add-pdf-viewer

# Bug fixes
fix/search-timeout-error
fix/ui-responsive-layout

# Major versions (isolated)
release/v2.0
release/v3.0

# Hotfixes (critical production bugs)
hotfix/security-patch-cve-2024-1234

# Experimental (not merged to main)
experiment/ml-ranking-algorithm
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

### Good vs Bad Commit Messages

✅ **Good:**

```
feat(search): add OpenAlex provider adapter
fix(library): prevent duplicate entries on concurrent saves
docs(architecture): document adapter pattern
refactor(api): extract validation middleware
test(search): add integration tests for semantic scholar
perf(db): add index on library_entries.paper_id
```

❌ **Bad:**

```
update code
fix bug
WIP
asdf
Final commit before deadline
```

---

## 🧪 Testing Standards

### Backend Testing (pytest)

```python
@pytest.mark.asyncio
async def test_search_returns_results():
    service = SearchService()
    results = await service.search("ml", providers=["arxiv"], limit=10)
    assert len(results) > 0

@pytest.mark.asyncio
async def test_search_handles_invalid_provider():
    service = SearchService()
    with pytest.raises(ValidationError):
        await service.search("test", providers=["invalid"])
```

### Frontend Testing (Vitest)

```typescript
test('calls onSearch when form submitted', () => {
  const handleSearch = vi.fn();
  render(<SearchBar onSearch={handleSearch} />);

  const input = screen.getByRole('textbox');
  fireEvent.change(input, { target: { value: 'test' } });
  fireEvent.submit(input.form!);

  expect(handleSearch).toHaveBeenCalledWith('test');
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

## ➡️ Previous Section

**Start from:** See `docs/ai/conventions_0.md` for Key Principles and Code Style Guides.

---

**Related Documentation:**

- `docs/release-management.md` - Release strategy overview
- `docs/release-procedure.md` - Step-by-step release guide
- `docs/ai/quick-start.md` - Development workflows
- `docs/ai/decisions.md` - Architectural decisions

---

_Last Updated: 2026-03-28_
_Previous file: docs/ai/conventions_0.md_
