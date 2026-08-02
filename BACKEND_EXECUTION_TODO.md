# Backend Execution TODO — Track Progress

## Phase A — Infrastructure fixes (in progress)
- [x] A1. `auth/jwt.py` — `create_token_pair` exists (verified, returns dict with refresh_jti/access_jti/expires_in)
- [x] A2. `recommendation_repository.create` accepts `hours_valid`
- [x] A3. `simulation_service` imports resolve (`SimulationCreate`, `ScenarioCreate`)
- [x] A4. `engine_adapter.health_to_dict` implemented
- [x] A5. `models/user.py` — `last_login_at` is a real nullable UTCDateTime column
- [x] A6. Planner serializer verified against engine dataclasses (FinancialPlan/GoalPlan/GoalProbability/CashflowSnapshot)
- [x] A7. `engine/` shim re-exports all engine symbols used by services

### Remaining Phase A fixes
- [x] AUD-1: Add shared `load_engine_parts(session, user)` helper to `engine_adapter.py`
- [x] AUD-2: Fix `UserProfile` PK-vs-FK lookup in `profile_service` (get_user_profile/upsert_user_profile/_engine_user)
- [x] AUD-3: Fix `_engine_user()` in `planner_service` to use shared helper
- [x] AUD-4: Fix `_engine_user()` in `health_service` to use shared helper
- [x] AUD-5: Fix `_engine_user()` in `simulation_service` to use shared helper
- [x] AUD-6: Fix `_engine_user()` in `portfolio_service` to use shared helper
- [x] AUD-7: Fix `_engine_user()` in `recommendation_service` to use shared helper
- [x] AUD-8: Fix `user_repository.create_refresh_token` — add `session.add` + flush
- [x] AUD-9: Fix `audit_repository.record` — stringify UUIDs for String(36) columns
- [x] AUD-10: Verify `auth_service` token-pair dict access + refresh jti
- [x] AUD-11: Verify `core/cache.py` has `blacklist_access_jti` + correct logout args

## Phase B — Alembic
- [x] B1. `alembic.ini`, `migrations/env.py`, `script.py.mako`
- [x] B2. Initial migration

## Phase C — Routers + main
- [x] C1..C18. All routers + api shim + dependencies shim + main.py

## Phase D — Background tasks
- [x] D1. `app/tasks/*`
- [x] D2. APScheduler wiring

## Phase E — Docker + requirements
- [x] E1. `requirements.txt`
- [x] E2. `Dockerfile`
- [x] E3. `docker-compose.yml`
- [x] E4. `.env.example`

## Phase F — Backend tests
- [x] F1. `tests/conftest.py`
- [x] F2. test modules

## Phase G — Docs + verification
- [x] G1. `.gitignore`
- [x] G2. `README.md`
- [x] G3. Run suites
- [x] G4. Boot uvicorn

