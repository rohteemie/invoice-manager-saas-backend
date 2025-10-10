# Pre-release: v0.3.0 (Draft)

Date: 2025-10-11
Target branch: develop

## Summary

This pre-release focuses on strengthening code quality and CI/CD reliability for the multi-tenant SaaS backend. It introduces consistent formatting and linting enforcement, resolves CI blockers, and cleans up the codebase to prepare for future feature releases. It also documents the changes and provides guidance for local verification.

## Highlights

- CI/CD improvements: Lint-first workflow, formatting checks, and test environment services (Postgres, Redis)
- Code quality: Black formatting enforcement, flake8 fixes, pycodestyle checks
- Cleanup and stability: Removed unused imports/artifacts, fixed broken imports, clarified config
- Documentation: Added change log for this sweep and release notes for the upcoming tag

## Changes in Detail

### CI/CD Pipeline

- Lint job
  - Run pycodestyle with max line length 88
  - Run flake8 (configured to ignore E203/W503 and align with Black)
  - Enforce Black formatting with `black --check app/`
- Test job
  - Spins up Postgres 14 and Redis 7 services
  - Creates a minimal `.env` for CI
  - Optional Alembic check
  - Executes pytest with concise output
- Build job (main branch only)
  - Builds and pushes Docker image to GHCR with metadata and build cache

### Linting and Formatting

- `.flake8`
  - Fixed invalid inline comments in ignore list that broke flake8
  - Excluded `.ENV` (local virtualenv) to avoid linting third-party packages
  - Kept `max-line-length = 88` to match Black
- Black
  - Enforced in CI; developers should run `black app/` before pushing

### Code Cleanup and Fixes

- Analytics endpoint
  - Removed unused `invalidate_tenant_cache` import and corrected formatting
- Auth endpoint
  - Fixed broken import for `UserCreate`, `User`, `Token` from `app.schemas.user`
- Metrics
  - Cleaned imports; removed unused `time` artifact
- Logging
  - Ensured clean imports and removed artifact leftovers
- Rate limiting
  - Removed unused `Response` import; clarified Redis/in-memory logic
- Invoice model
  - Removed accidental `...existing code...` artifact; validated syntax
- Schemas
  - Removed unused imports in analytics schema
- Tests
  - Trimmed unused imports in several test modules; note follow-ups remain for whitespace cleanup

## Breaking Changes

- None. All changes are non-functional cleanup and pipeline configuration.

## Security

- No security-impacting changes in this iteration.

## Migration Notes

- No database schema changes in this pre-release.
- Developers should:
  - Install and run Black locally: `pip install black && black app/`
  - Use flake8 locally: `pip install flake8 && flake8 .`

## Known Issues / Follow-ups

- Some tests contain trailing whitespace and minor style warnings (e.g., `tests/test_integration.py`); scheduled for a subsequent cleanup.
- Consider adding `isort` to enforce import ordering consistently alongside Black.
- Optional: Add a `pre-commit` config to run Black/Flake8 automatically.

## Verification Steps

1. Pull latest develop.
2. Set up a virtual environment and install deps:

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install black flake8 pycodestyle
  ```

1. Verify formatting and linting:

  ```bash
  black --check app/
  flake8 .
  pycodestyle app/ --max-line-length=88
  ```

1. Run tests with local SQLite and Redis (optional):

  ```bash
  export DATABASE_URL=sqlite:///./test.db
  export REDIS_URL=redis://localhost:6379/0
  pytest tests/ -v --tb=short --maxfail=5
  ```

## Pre-release Tag Suggestion

- Tag: `v0.3.0-rc.1`
- Title: "Code Quality and CI Stabilization"
- Description (changelog excerpt):
  - Align CI with Black/flake8
  - Fix flake8 config and exclude `.ENV`
  - Clean imports and remove artifacts across core modules
  - Fix broken auth import
  - Document changes and verification steps

## Contributors

- @rohteemie
- Assistant-guided cleanup session
