# FIXES.md — Phase 1 backend repair

Branch: `fix-and-research`. Every row below is a defect found by the prior
audit, the root cause, the smallest fix applied, and the test/command that
was actually executed and observed to pass.

| defect | root cause | fix | test that proves it |
|---|---|---|---|
| B1 — ORM attribute `metadata` | SQLAlchemy reserves `metadata` on declarative models, so `UserMemory.metadata` / `KnowledgeDocument.metadata` raised `InvalidRequestError` at class definition — importing `app.models.ai` (and therefore `app.main`) failed. | Renamed the Python attribute to `meta` while keeping the DB column named `metadata`: `meta: Mapped[...] = mapped_column("metadata", JSON, nullable=True)` in `app/models/ai.py`. No ORM-level user of the old attribute exists outside the frozen `app/ai/` package (the `.metadata` there is Pydantic/dataclass, unrelated to B1). | `python -m pytest app/tests` now collects and runs (previously the whole suite errored during collection); `python -m compileall -q app wealth_management_system` succeeds. |
| B2 — dependency pins | `bcrypt>=4.1` is incompatible with the pinned `passlib`, and `pytest-asyncio`, `yfinance`, `requests` were absent from `requirements.txt`. | Pinned `bcrypt==4.0.1`; added `pytest-asyncio>=0.23` under Testing and a new "Market data" section with `yfinance>=0.2` and `requests>=2.31`. No unrelated dependency was upgraded. | `pytest-asyncio` is exercised by the async app tests (`python -m pytest app/tests -q`, green). `yfinance`/`requests` are declared market-data dependencies and are not exercised by the current suite. |
| B3 — `create_token_pair` callers | `create_token_pair` is keyword-only (`subject=`, `role=`) and returns a dict, but `auth_service` called it positionally and the tests/`conftest` read `.access_token` / `.refresh_token` attributes. | Passed `subject=`/`role=` at both call sites in `app/services/auth_service.py`; fixed `app/tests/conftest.py` (`auth_headers`, `admin_auth_headers`) and `app/tests/test_auth.py` (`test_refresh`, `test_logout`) to use `tokens["access_token"]` / `tokens["refresh_token"]`. | `app/tests/test_auth.py::test_refresh`, `::test_logout`, and every test using `auth_headers` / `admin_auth_headers`. |
| B4 — TrustedHost fed CORS origins | `app/main.py` passed `settings.CORS_ORIGINS` (full origins such as `http://localhost:3000`) to `TrustedHostMiddleware`, which expects bare host names — requests via `http://test` were rejected. | Added `ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "test", "testserver"]` (with a comma-string validator mirroring `CORS_ORIGINS`) in `app/config/settings.py`, documented it in `.env.example`, and pointed `TrustedHostMiddleware` at `settings.ALLOWED_HOSTS`. CORS still uses `settings.CORS_ORIGINS`. | `python -m pytest app/tests` (the async client uses base_url `http://test`) and `curl.exe -i http://127.0.0.1:8765/api/v1/system/health`. |
| B5 — pytest asyncio config | Async tests depended on `asyncio_mode`/`testpaths` that were never declared, so async handling was environment-dependent. | Added `pytest.ini` with `asyncio_mode = auto` and `testpaths` = `app/tests`, `wealth_management_system/tests`. No other pytest configuration file exists, so nothing conflicts. | `python -m pytest app/tests -q` and `python -m pytest wealth_management_system/tests -q` (106 passed). |
| B6 — migration `down_revision` | `migrations/versions/0002_ai_layer.py` declared `down_revision = "0001"`, but the initial revision id is `0001_initial`, so Alembic could not resolve the chain. | Changed `down_revision` to `"0001_initial"` (nothing else in the migration changed). | `$env:DATABASE_URL="sqlite:///./check.db"; alembic upgrade head; alembic downgrade base` (full output pasted in the final report). |
| B7 — refresh 500 `'str' object has no attribute 'hex'` | The JWT `sub` claim is a string, but `AuthService.refresh` passed it straight into `UserRepository.get`, which queries the `Uuid`-typed `users.id` column. SQLAlchemy's Uuid bind processor calls `value.hex` on the bound value, so a `str` raised `AttributeError` and the handler returned 500. | Converted the claim to the domain type at the point of use: `self.users.get(uuid.UUID(payload["sub"]))` — the same `str`-to-`uuid.UUID` conversion `app/auth/deps._load_user` already performs. The `jti`/refresh-token path was already consistently `str` (`RefreshToken.jti` is String(64)) and was left unchanged. | `app/tests/test_auth.py::test_refresh` (rotates a real refresh token via `POST /api/v1/auth/refresh` and asserts HTTP 200). |
| B8 — simulation POST 409 | `simulation_results` has NOT NULL `horizon_years`, `expected_return`, `volatility`, `inflation`, `monthly_investment` columns, but `SimulationRepository.create_simulation` never set them, so the INSERT violated the NOT NULL constraint. | `create_simulation` now accepts and persists `simulations`, `horizon_years`, `expected_return`, `volatility`, `inflation`, `monthly_investment`, `initial_corpus` and `target_amount`, and `SimulationService.run_simulation` passes the validated request values through. No default is invented — the values come from the request that ran the engine. | `app/tests/test_simulation.py::test_run_simulation` (asserts the persisted `SimulationResult.horizon_years == 20`). |
| B9 — missing profile crashed with AttributeError | `load_engine_parts` returned `None` for a missing financial/behavioral row and the engine then dereferenced them (`user.financial.emergency_fund_months`, `profile.behavioral.risk_tolerance`), yielding a 500. | `load_engine_parts` now raises `NotFoundError` (`financial_profile_not_found` / `behavioral_profile_not_found`) before the engine runs — the same 404 contract `ProfileService`'s getters already use. The `default_user` fixture now creates the user/financial/behavioral profiles so the success-path tests remain valid. | `app/tests/test_profiles.py::test_missing_profile_returns_clean_error` (404) plus the previously-failing `test_allocation`, `test_health`, `test_planner`, `test_recommendations`, `test_simulation::test_run_scenario` and the profile success tests. |
| B10.1 — password-reset route returned 404 but the test expects 200 | `AuthService.request_password_reset` raised `NotFoundError` for an unknown email, even though the route returns the deliberately generic "If the account exists, a reset link has been sent" and its own comment says not to reveal whether the account exists. The code contradicted the intended contract. | `request_password_reset` now returns `None` for an unknown email instead of raising, so `POST /api/v1/auth/password-reset/request` always answers 200. | `app/tests/test_auth.py::test_password_reset_request` (expects 200). |
| B10.2 — register response shape mismatch | `test_register`/`test_login` asserted a flat `access_token`, but the intended contract is the nested `LoginResponse` = `{tokens: {...}, user_id, role, full_name}`. The route declares `response_model=LoginResponse`, the frozen frontend consumes `response.tokens` (`web/components/providers/auth-provider.tsx`) and `web/types/api.ts` mirrors the schema ("Types mirroring the backend Pydantic schemas"). The tests were the inconsistent artefact, not the application. | Corrected the assertions to `data["tokens"]["access_token"]` / `["refresh_token"]` in `app/tests/test_auth.py` and to `result.model_dump()["tokens"]` in `app/tests/test_services.py`. No application change was made, because switching the response to flat would break the frozen frontend client. | `app/tests/test_auth.py::test_register`, `::test_login`, `app/tests/test_services.py::TestAuthService::test_register_and_login`. |

## B10 — reasoning for each case

### password-reset route mismatch (B10.1)

`app/api/routes/auth.py` documents `POST /password-reset/request` as returning
`MessageResponse(message="If the account exists, a reset link has been sent")`.
That wording only makes sense if the endpoint never discloses whether the
account exists, and `AuthService.request_password_reset` even carried the
comment "do not reveal whether the account exists" immediately before raising
`NotFoundError` — a direct contradiction. The route contract and its own
comment agree with the test (200); the `raise NotFoundError` line was the
defect, so the application was fixed, not the test.

### register response shape mismatch (B10.2)

Three independent, authoritative sources agree on the *nested* shape:

1. the API schema and route — `LoginResponse` (with a nested `tokens:
   TokenPair`) is the declared `response_model` for both `/register` and
   `/login`;
2. the frozen web client — `web/components/providers/auth-provider.tsx`
   reads `response.tokens`, and `web/types/api.ts` states the types "mirror
   the backend Pydantic schemas";
3. `AuthService.login` builds and returns a `LoginResponse`.

Only the test assertions disagreed, flattening the response. Because the
frontend is frozen and defines the client contract, aligning the backend to a
flat response would break it; the correct, smallest change is therefore to
correct the inconsistent test assertions to the real contract.

## Notes

* The local interpreter is Python 3.10.0 (`.venv`). No source change was
  needed for it; the code, tests and migrations all run cleanly on it.
* Frozen trees (`web/`, `app/ai/`, `security_selection/`, `ml/digital_twin/`)
  were not modified.
* The existing stash `blackbox-work-before-phase-1` was not popped, applied,
  dropped or otherwise touched.
