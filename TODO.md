# Goal-based financial planning core — TODO

## Milestone: goal-based planning pipeline (complete)
- [x] All legacy engines

## Milestone: production engine transformation (complete)
- [x] Config, exceptions, models, engines, tests

## Milestone: FastAPI backend (complete)
- [x] `app/` — FastAPI application layer (14 routes, 9 services, 7 repos, 20 models, auth, cache, middleware, core)
- [x] `engine/` — re-export shim (engine untouched)
- [x] `migrations/` — Alembic + initial migration (20 tables)
- [x] `requirements.txt`
- [x] `Dockerfile` + `docker-compose.yml` (backend + postgres + redis + pgadmin)
- [x] `.env.example`
- [x] `app/tasks/` — background task modules
- [x] `app/tests/` — pytest suite (12 modules, 30+ tests)
- [x] Root `README.md` — architecture, setup, API docs, deployment

## Verification
- [ ] Compile-check: `python -m compileall app`
- [ ] Alembic dry-run: `alembic upgrade head`
- [ ] Test suite: `python -m pytest app/tests -v --tb=short`
- [ ] Engine test suite: `python -m pytest wealth_management_system/tests -q`
