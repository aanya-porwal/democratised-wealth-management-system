# Backend completion plan

## Phase 1 — Infrastructure files
- [x] `requirements.txt`
- [x] `Dockerfile`
- [x] `docker-compose.yml`
- [x] `.env.example`
- [x] Root `README.md`

## Phase 2 — Alembic initial migration
- [x] `migrations/versions/0001_initial.py`
- [x] `migrations/versions/__init__.py`

## Phase 3 — Background task modules
- [x] `app/tasks/__init__.py`
- [x] `app/tasks/market_data.py`
- [x] `app/tasks/portfolio.py`
- [x] `app/tasks/goals.py`
- [x] `app/tasks/notifications.py`

## Phase 4 — Test suite
- [x] `app/tests/__init__.py`
- [x] `app/tests/conftest.py`
- [x] `app/tests/test_auth.py`
- [x] `app/tests/test_users.py`
- [x] `app/tests/test_profiles.py`
- [x] `app/tests/test_goals.py`
- [x] `app/tests/test_portfolio.py`
- [x] `app/tests/test_allocation.py`
- [x] `app/tests/test_recommendations.py`
- [x] `app/tests/test_simulation.py`
- [x] `app/tests/test_health.py`
- [x] `app/tests/test_planner.py`
- [x] `app/tests/test_repositories.py`
- [x] `app/tests/test_services.py`

## Phase 5 — Verification
- [x] `python -m compileall app` — **all files compiled without errors**
- [ ] `alembic upgrade head` (requires PostgreSQL)
- [ ] `python -m pytest app/tests -v --tb=short` (requires PostgreSQL + deps)
- [x] Updated `TODO.md` and `BACKEND_EXECUTION_TODO.md`
