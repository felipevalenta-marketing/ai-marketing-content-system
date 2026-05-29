# CI/CD

This repository uses GitHub Actions as a validation pipeline for MVP release readiness.

## Workflows

### `ci.yml`

Runs on:
- pushes to `main`
- pull requests targeting `main`

Jobs:
- backend validation
- frontend validation
- Docker validation
- security validation
- smoke validation
- pipeline health

### `release-readiness.yml`

Runs manually with `workflow_dispatch`.

Jobs:
- backend validation
- frontend validation
- Docker validation
- security validation
- pipeline health
- release check

Both workflows use concurrency control so stale runs are cancelled when a newer push arrives on the same ref.

## Quality Gates

The pipeline now evaluates explicit quality gates before a release is considered ready:

- `backend_compile`
- `backend_tests`
- `frontend_build`
- `docker_validation`
- `security_scan`
- `smoke_tests`
- `release_validation`

Pipeline health also includes:

- dependency validation
- documentation validation
- project structure validation
- artifact safety
- observability compatibility

## What runs in CI

- `python -m compileall src tests scripts`
- `python -m pytest -p no:cacheprovider`
- `python scripts/production_smoke.py`
- `python scripts/ci_pipeline_health.py`
- `python scripts/ci_quality_gates.py`
- `python scripts/ci_dependency_check.py`
- `python scripts/ci_docs_check.py`
- `python scripts/ci_structure_check.py`
- `python scripts/ci_release_check.py`
- frontend TypeScript build
- Docker Compose syntax validation
- Docker image build
- repository secret scan
- release readiness file checks

## Local equivalents

Backend:

```bash
python -m compileall src tests scripts
python -m pytest -p no:cacheprovider
python scripts/production_smoke.py
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

Docker:

```bash
docker compose config
docker build -t ai-marketing-content-system:test .
```

Security:

```bash
python scripts/ci_security_check.py
```

Pipeline health:

```bash
python scripts/ci_pipeline_health.py
```

Dependencies:

```bash
python scripts/ci_dependency_check.py
```

Docs:

```bash
python scripts/ci_docs_check.py
```

Structure:

```bash
python scripts/ci_structure_check.py
```

Release readiness:

```bash
python scripts/ci_release_check.py
python scripts/release_readiness.py
python scripts/mvp_acceptance_check.py
python scripts/generate_release_report.py
```

The release readiness layer documents the final MVP acceptance report and does not introduce new product features.
The final release artifact set also includes `docs/MVP_EXECUTIVE_SUMMARY.md` and `docs/RELEASE_ARTIFACTS.md`.

## Environment variables used in CI

- `APP_ENV=ci`
- `API_DEBUG=false`
- `OPENAI_API_KEY=dummy_ci_key_do_not_use`
- `JWT_SECRET_KEY=dummy_ci_jwt_secret_for_tests_only`
- `ENABLE_AUTHENTICATION=true`
- `ENABLE_RBAC=true`
- `ENABLE_ANALYTICS=true`
- `ENABLE_OBSERVABILITY=true`
- `ENABLE_SECURITY_HARDENING=true`
- `ENABLE_SECURITY_HEADERS=true`
- `ENABLE_RATE_LIMITING=true`
- `ENABLE_SECRET_SCANNING=true`
- `ENABLE_DEPENDENCY_VALIDATION=true`
- `ENABLE_INPUT_SANITIZATION=true`
- `ENABLE_OUTPUT_SANITIZATION=true`
- `ENABLE_PERSISTENCE=false`
- `STORAGE_ROOT=data`
- `VITE_API_BASE_URL=http://localhost:8000`
- `ENABLE_CI_SECURITY_CHECKS=true`
- `ENABLE_RELEASE_VALIDATION=true`
- `ENABLE_DOCKER_VALIDATION=true`

These values are dummy-only and do not need production credentials.

## Troubleshooting

- If backend tests fail, confirm the virtual environment is active and dependencies are installed.
- If the frontend build fails, check `frontend/package.json` and `frontend/tsconfig.json`.
- If Docker validation fails, verify Docker Desktop or the Docker engine is available locally.
- If the security check fails, inspect the file and remove any real secrets or committed `.env` files.
- If the release check fails, verify the required deployment docs and project directories exist.
- If pipeline health reports a warning, inspect the quality gate summary and the supporting dependency/docs/structure checks.
