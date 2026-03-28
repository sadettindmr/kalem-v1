<!--
FILE: docs/release-management.md
PURPOSE: Overall release management strategy and version control
MAX_SIZE: 300 lines

SPLIT_STRATEGY:
- If file exceeds 300 lines, split into:
  - release-management.md (strategy, workflow overview)
  - release-procedure.md (step-by-step procedures)
  - Update CLAUDE.md navigation table with new files
-->

# Release Management Strategy

**Last Updated:** 2026-03-28

---

## 🎯 Overview

This document defines how we manage versions, releases, and deployment for the Kalem project. It covers:

- Version numbering (SemVer)
- Release branches and lifecycle
- Major version isolation strategy
- Pre-release validation

---

## 📊 Version Numbering (Semantic Versioning)

**Format:** `MAJOR.MINOR.PATCH`

### When to Increment Each Component

| Component         | When                                            | Examples                                                    | Release Type    |
| ----------------- | ----------------------------------------------- | ----------------------------------------------------------- | --------------- |
| **MAJOR** (X.0.0) | Breaking changes, major architecture shifts     | v1.0 → v2.0 (Modular Monolith), v2.0 → v3.0 (Microservices) | Major Release   |
| **MINOR** (1.X.0) | New features, backward-compatible enhancements  | v1.0 → v1.1 (Add FTS), v1.1 → v1.2 (Add export)             | Feature Release |
| **PATCH** (1.0.X) | Bug fixes, security patches, small improvements | v1.0.1 (Fix search), v1.0.2 (UI stability)                  | Hotfix Release  |

---

## 🌳 Branch Strategy

### Production Branch (main)

**Purpose:** Stable, production-ready code
**Base:** Latest released MAJOR.MINOR version (currently: v1.0.2)
**Protection Rules:**

- Requires PR approval (minimum 1 reviewer)
- Requires all CI/CD checks pass
- No direct commits allowed
- Auto-delete merged branches

### Feature/Bugfix Branches (temporary)

**For MINOR bumps (new features):**

```bash
git checkout -b feature/sprint-14-annotations
```

→ Merge to main → Tag v1.3.0

**For PATCH bumps (bug fixes):**

```bash
git checkout -b fix/search-timeout-error
```

→ Merge to main → Tag v1.0.3

### Major Version Branches (isolated)

**Purpose:** Develop next major version independently without affecting production

**Naming Convention:** `release/vX.0` (where X = next major version)

**Creating a major version branch:**

```bash
# When ready to start development for v2.0
git checkout main
git pull
git checkout -b release/v2.0
# Push and protect this branch
git push -u origin release/v2.0
```

**Working on major version:**

```bash
# Team members work on feature branches off release/v2.0
git checkout release/v2.0
git checkout -b feature/v2-new-architecture
# Develop, commit, push
git push origin feature/v2-new-architecture
# Create PR: feature/v2-new-architecture → release/v2.0
```

**Merging major version to production:**

```bash
# When v2.0 is stable and ready
git checkout main
git pull
git merge --no-ff release/v2.0
git tag -a v2.0.0 -m "Major release: Complete redesign"
git push origin main
git push origin v2.0.0
```

---

## 📋 Release Lifecycle

### Stage 1: Development

- Work happens on feature/fix branches
- Regular merges to main for v1.x releases
- Major version development on release/vX.0 branches

### Stage 2: RC (Release Candidate) - Optional

- Created when version is feature-complete but needs testing
- Tag format: `v1.2.0-rc.1`, `v1.2.0-rc.2`, etc.
- Only bugfixes and critical issues fixed
- No new features

### Stage 3: Release

- All tests passing
- Full QA/manual testing complete
- Tag format: `v1.2.0`
- Announced in release notes

### Stage 4: Post-Release

- Monitor for critical bugs
- Patch releases as needed
- Document any issues in release notes

---

## 🔄 Current Active Versions

| Version | Status            | Branch            | Notes                         |
| ------- | ----------------- | ----------------- | ----------------------------- |
| v1.0.2  | Stable/Production | main              | Current production release    |
| v1.1.0+ | In Development    | feature/sprint-\* | New features (MINOR bumps)    |
| v1.0.3+ | As Needed         | fix/\*            | Bug fixes (PATCH bumps)       |
| v2.0.0  | In Development    | release/v2.0      | Next major version (isolated) |

---

## 🏷️ Version Tagging Rules

### Tag Format

```bash
git tag -a v1.2.3 -m "Brief description of release"
```

### When to Tag

1. After merging to main
2. When version is ready for deployment
3. After release notes are created

### Tag Examples

**Feature Release (MINOR bump):**

```bash
git tag -a v1.3.0 -m "feat: Add paper annotations and keyword management"
```

**Patch Release (PATCH bump):**

```bash
git tag -a v1.0.3 -m "fix: Improve search relevance ranking algorithm"
```

**Major Release (MAJOR bump):**

```bash
git tag -a v2.0.0 -m "feat: Complete architectural redesign with microservices"
```

---

## 📝 Release Checklist

Before creating any release tag:

- [ ] All tests passing (`cd backend && poetry run pytest`)
- [ ] Frontend builds successfully (`cd frontend && npm run build`)
- [ ] All migrations applied (`poetry run alembic upgrade head`)
- [ ] Code reviewed and approved
- [ ] Changelog/release notes written
- [ ] Version number in frontend app constant updated
- [ ] Docker images tested
- [ ] Documentation updated (if needed)

---

## 📖 Release Notes Format

Create entry in `docs/release_notes.md`:

```markdown
## v1.3.0 - 2026-03-29

### New Features

- Add paper annotations feature (Sprint 14)
- Implement keyword management UI
- Support multiple annotation types

### Bug Fixes

- Fix search timeout on large datasets
- Improve pagination performance
- Fix UI responsive layout issues

### Breaking Changes

None

### Dependencies

- Updated React to 19.x
- Updated FastAPI to ^0.109.0

### Migration Instructions

1. Run: `poetry run alembic upgrade head`
2. Rebuild frontend: `npm run build`
3. Restart backend service

### Contributors

- @developer1 (Lead)
- @developer2 (Testing)
```

---

## 🚀 Deployment Process

1. **Pre-Deployment Validation**
   - Review release notes
   - Verify all CI/CD checks pass
   - Run smoke tests

2. **Deployment**
   - Tag the release: `git tag -a vX.Y.Z`
   - Push tag: `git push origin vX.Y.Z`
   - Trigger deployment pipeline (GitHub Actions/GitLab CI)
   - Monitor deployment logs

3. **Post-Deployment Verification**
   - Verify health check endpoint: `curl https://prod.kalem.ai/api/v2/health`
   - Test critical user flows
   - Monitor error logs for 1 hour
   - Confirm no degraded performance

---

## 🚨 Emergency Procedures

### Rollback to Previous Version

```bash
# If critical bug found after release
git checkout main
git pull
git revert v1.2.3  # Creates new commit undoing v1.2.3
git push origin main

# Tag new patch version
git tag -a v1.2.4 -m "fix: Rollback critical bug in v1.2.3"
git push origin v1.2.4
```

### Hotfix for Production Bug

```bash
# Create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/critical-security-issue

# Fix, test, commit
git add .
git commit -m "fix: Patch critical security vulnerability"

# Merge to main
git push origin hotfix/critical-security-issue
# Create PR → main

# After merge
git checkout main
git pull
git tag -a v1.2.4 -m "fix: Critical security patch"
git push origin v1.2.4
```

---

## 📚 Related Documentation

- `docs/release-procedure.md` - Step-by-step release guide
- `docs/CLAUDE.md` - Main AI assistant guide
- `docs/ai/conventions.md` - Version and branching conventions
- `docs/release_notes.md` - Historical release notes

---

_Last Updated: 2026-03-28_
