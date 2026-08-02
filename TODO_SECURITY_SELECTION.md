# Security Selection & Investment Research Platform — Task TODO

## Phase 5 — Evaluators (plugin architecture) ✅ DONE
- [x] `evaluators/_common.py` — shared mixin (discover/fetch/validate/metrics/normalize)
- [x] `evaluators/mutual_fund.py`, `etf.py`, `stock.py`
- [x] `evaluators/gold_etf.py`, `sgb.py`, `international_etf.py`, `international_fund.py`
- [x] `evaluators/corporate_bond.py`, `government_bond.py`
- [x] `evaluators/reit.py`, `invit.py`, `fixed_deposit.py`, `ppf.py`, `nps.py`
- [x] `evaluators/__init__.py` — exports + `build_default_registry()`
- [x] `models/enums.py` — add `TargetAssetClass.STOCKS`
- [x] `config/config.yaml` — add stocks + populate corporate/government bond universes
- [x] `providers/static_provider.py` — expand SGB + GSEC static catalogs
- [x] `filters/standard.py` — MinAUMFilter not applicable for non-fund instruments

## Phase 6 — Domain Services
- [ ] `services/__init__.py`
- [ ] `services/selection_service.py` — orchestrates registry → evaluators
- [ ] `services/search_service.py`
- [ ] `services/comparison_service.py`
- [ ] `services/report_service.py`

## Phase 7 — Backend Integration
- [ ] `app/models/security.py` — 11 tables
- [ ] `app/models/__init__.py` — register models
- [ ] `migrations/versions/0002_security_selection.py`
- [ ] `app/repositories/security_repository.py`
- [ ] `app/services/security_service.py` — engine bridge + persistence
- [ ] `app/schemas/security.py`
- [ ] `app/api/routes/security.py` — 8 endpoints
- [ ] `app/api/__init__.py` — mount router
- [ ] `app/tasks/security.py` — background jobs
- [ ] `app/main.py` — register scheduler jobs
- [ ] `requirements.txt` — add requests + yfinance

## Phase 8 — Tests
- [ ] `security_selection/tests/conftest.py` — mock providers
- [ ] test_metrics.py, test_ranking.py, test_filters.py, test_cache.py, test_factors.py
- [ ] test_portfolio_construction.py, test_comparison.py, test_explainability.py, test_evaluators.py

## Phase 9 — Verification
- [ ] `python -m compileall security_selection app`
- [ ] Run pytest suite (offline-safe)
- [ ] Update TODO.md

