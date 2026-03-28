<!--
FILE: docs/release-procedure.md
PURPOSE: Step-by-step procedures for creating releases
MAX_SIZE: 250 lines
-->

# Release Procedure - Step-by-Step Guide

**Last Updated:** 2026-03-28

---

## 📋 Pre-Release Checklist

Before starting the release process, ensure:

- [ ] All planned features merged to main
- [ ] All tests passing
- [ ] Code review completed
- [ ] Release notes prepared
- [ ] Version number decided
- [ ] Docker services tested

---

## 🚀 Feature Release (MINOR bump)

**Scenario:** Adding new features (e.g., v1.0 → v1.1)

### Step 1: Prepare Release Branch

```bash
# Create feature branch name based on sprint
git checkout -b feature/sprint-14-annotations

# Develop features, make commits
git commit -m "feat(annotations): add paper annotation model"
git commit -m "feat(annotations): add API endpoints"
git commit -m "feat(annotations): add frontend UI"

# Push to remote
git push -u origin feature/sprint-14-annotations
```

### Step 2: Create Pull Request

- Create PR on GitHub: `feature/sprint-14-annotations` → `main`
- Add description: Features added, tests added, migrations run
- Request reviewers
- Ensure CI/CD checks pass

### Step 3: Code Review

- Address review comments
- Request re-review after changes
- Approve and merge when ready

### Step 4: Prepare Release Notes

Update `docs/release_notes.md`:

```markdown
## v1.1.0 - 2026-03-29

### New Features

- Add paper annotation system
- Implement keyword management
- Support multiple annotation types

### Bug Fixes

- Fix search timeout issues

### Breaking Changes

None

### Migration Instructions

1. `poetry run alembic upgrade head`
2. `npm run build`
3. Restart services
```

### Step 5: Create Release Tag

```bash
git checkout main
git pull
git tag -a v1.1.0 -m "feat: Add paper annotation system"
git push origin v1.1.0
```

### Step 6: Update App Version

```bash
# Edit frontend version constant
# frontend/src/constants/app.ts
export const APP_VERSION = 'v1.1.0';

git add frontend/src/constants/app.ts
git commit -m "chore: bump version to v1.1.0"
git push
```

---

## 🔧 Patch Release (PATCH bump)

**Scenario:** Bug fixes (e.g., v1.0.2 → v1.0.3)

### Step 1: Create Fix Branch

```bash
git checkout main
git pull
git checkout -b fix/search-timeout-error

# Fix the bug
# Add tests for the fix
git commit -m "fix(search): improve timeout handling"
git push -u origin fix/search-timeout-error
```

### Step 2: Create and Merge PR

- Create PR: `fix/search-timeout-error` → `main`
- Add description: Issue #123, symptoms, root cause, fix
- After merge (CI/CD passes), continue

### Step 3: Release Tag

```bash
git checkout main
git pull
git tag -a v1.0.3 -m "fix: Improve search timeout handling"
git push origin v1.0.3
```

### Step 4: Update Release Notes

Append to `docs/release_notes.md`:

```markdown
## v1.0.3 - 2026-03-29

### Bug Fixes

- Fix search timeout on large datasets

### Migration Instructions

None required. Restart backend service.
```

---

## 🚀 Major Release (MAJOR bump)

**Scenario:** Major version with breaking changes (e.g., v1.0 → v2.0)

### Step 1: Create Major Version Branch

```bash
git checkout main
git pull
git checkout -b release/v2.0
git push -u origin release/v2.0
```

### Step 2: Protect Branch

On GitHub:

- Settings → Branches → Add branch protection rule
- Branch pattern: `release/v*`
- Require PR reviews: Yes
- Require CI passing: Yes

### Step 3: Development (Long-running)

```bash
# Team members work on feature branches off release/v2.0
git checkout release/v2.0
git checkout -b feature/v2-new-architecture

# Develop for weeks/months...
git commit -m "feat: New modular architecture"
git push origin feature/v2-new-architecture

# Create PR: feature/v2-* → release/v2.0 (NOT main)
```

### Step 4: Prepare for Release

When v2.0 is feature-complete:

```bash
# Update release notes with all changes
# docs/release_notes.md

## v2.0.0 - 2026-06-01

### Major Changes
- Complete architectural redesign
- Microservices architecture
- New API schema

### Breaking Changes
- API endpoints changed from /api/v1 to /api/v2
- Database schema migration required
- Authentication token format changed

### Migration Instructions
1. Backup database: `pg_dump ...`
2. Run migrations: `poetry run alembic upgrade head`
3. Update clients to use new API
4. Restart all services
```

### Step 5: Merge to Main

```bash
git checkout main
git pull
git merge --no-ff release/v2.0 -m "Merge v2.0.0 major release"
git push origin main
```

### Step 6: Tag Release

```bash
git tag -a v2.0.0 -m "Major release: Complete redesign with microservices"
git push origin v2.0.0
```

### Step 7: Retire Old Version

```bash
# Keep release/v1.0 for critical hotfixes
# Archive release/v1.0 if no longer needed
git branch -m release/v1.0 archive/release-v1.0
git push origin archive/release-v1.0 :release/v1.0
```

---

## 🐛 Hotfix for Released Version

**Scenario:** Critical bug in production, needs immediate patch

### Step 1: Create Hotfix Branch

```bash
# If bug in current main (v1.2.3)
git checkout main
git pull
git checkout -b hotfix/security-vulnerability

# If bug in old release (v1.0.x)
git checkout v1.0.3  # Check out from tag
git checkout -b hotfix/security-vulnerability-1.0
```

### Step 2: Fix and Test

```bash
# Make minimal fix for critical issue only
git commit -m "fix: Critical security vulnerability CVE-2024-1234"

# Test thoroughly
cd backend && poetry run pytest
cd frontend && npm run build
```

### Step 3: Merge and Tag

```bash
git checkout main
git merge --no-ff hotfix/security-vulnerability
git push origin main

# Tag patch version
git tag -a v1.2.4 -m "fix: Critical security patch"
git push origin v1.2.4
```

### Step 4: Backport if Needed

If hotfix applies to older versions:

```bash
git checkout v1.0.3
git checkout -b hotfix/security-vulnerability-1.0
git cherry-pick <commit-hash-of-fix>
git tag -a v1.0.4 -m "fix: Critical security patch"
git push origin v1.0.4
```

---

## ✅ Post-Release

After release is tagged and deployed:

1. **Monitor:** Watch error logs for 24 hours
2. **Notify:** Announce release to team
3. **Document:** Add release notes and communicate changes
4. **Backup:** Keep backup of database/data
5. **Archive:** Archive release branch if major version

---

## 🆘 Rollback Procedure

If critical bug found immediately after release:

```bash
# Identify the bug and previous good version
# e.g., v1.2.2 was good, v1.2.3 has the bug

git checkout main
git pull

# Create revert commit
git revert v1.2.3

# Fix message appears as new commit that undoes v1.2.3
git push origin main

# Tag new patch version
git tag -a v1.2.4 -m "fix: Rollback and fix critical bug from v1.2.3"
git push origin v1.2.4

# Deploy v1.2.4
```

---

## 📚 Related Documentation

- `docs/release-management.md` - Release strategy overview
- `docs/CLAUDE.md` - Main AI assistant guide
- `docs/ai/conventions.md` - Commit and version conventions
- `docs/release_notes.md` - Historical releases

---

_Last Updated: 2026-03-28_
