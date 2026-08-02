# Security Selection & Investment Research Platform — Implementation Checklist

## Phase 1 — Domain Engine Core
- [x] `config/` — config.yaml (weights, thresholds, providers, refresh schedules, filters, optimization constraints)
- [x] `models/` — enums, data models, pipeline models
- [x] `utils/` — math, returns, feature builder
- [x] `metrics/` — MetricsEngine (returns, risk, ratios, drawdowns, tracking)
- [x] `quality/` — DataQualityEngine (missing, duplicates, stale, outliers, invalid NAVs, API failures)
- [x] `cache/` — CacheLayer (provider-independent, timestamps, TTL, refresh schedule)

## Phase 2 — Providers
- [x] `providers/base.py` — BaseDataProvider
- [x] `providers/yfinance_provider.py` — stocks, ETFs, gold ETFs, international ETFs, REITs, InvITs
- [x] `providers/mfapi_provider.py` — Indian mutual fund schemes + NAV
- [x] `providers/rbi_provider.py` — SGB, government bond datasets
- [x] `providers/static_provider.py` — FD/PPF/NPS/SGB static rate tables
- [x] `providers/fallback_provider.py` — chaining with cache fallback
- [x] `providers/factory.py` — build providers from config

## Phase 3 — Base Engine & Pipeline
- [x] `base/evaluator.py` — BaseEvaluator template-method pipeline
- [x] `base/provider.py` — provider set abstraction
- [x] `base/registry.py` — EvaluatorRegistry (target class → evaluators)

## Phase 4 — Selection Pipeline Components
- [x] `filters/` — configurable filters (AUM, expense, liquidity, age, credit, region, tax, tracking)
- [x] `scoring/` — 10 independent factor classes + IScoringModel + WeightedScoreModel + Feature/Dataset builders
- [x] `ranking/` — RankingEngine (all / top20 / top10 / top5 / best / alternatives / confidence)
- [x] `optimization/` — PortfolioOptimizer (single vs multi-security, configurable constraints)
- [x] `comparison/` — ComparisonEngine (any securities)
- [x] `explainability/` — ExplanationEngine (centralised reasons + confidence)
- [x] `research/` — ResearchReport generator

## Phase 5 — Evaluators (14)
- [x] `_common.py` — shared evaluator helpers (fetch, merge, candidate build, default_normalize)
- [x] mutual_fund.py
- [x] etf.py
- [x] stock.py
- [x] corporate_bond.py
- [x] government_bond.py
- [x] gold_etf.py
- [x] sgb.py
- [x] reit.py
- [x] invit.py
- [x] fixed_deposit.py
- [x] ppf.py
- [x] nps.py
- [x] international_etf.py
- [x] international_fund.py
- [x] `__init__.py` — exports + `build_default_registry()`

## Phase 6 — Domain Services
- [ ] `services/` — selection, search, comparison, reporting orchestration

## Phase 7 — Backend Integration
- [ ] `app/models/security.py` — 11 tables (security_master, historical_prices, historical_nav, market_metrics, fund_holdings, sector_allocations, country_allocations, security_rankings, selection_history, market_refresh_logs, market_cache)
- [ ] `app/models/__init__.py` — register models
- [ ] `migrations/versions/0002_security_selection.py` — Alembic migration
- [ ] `app/repositories/security_repository.py`
- [ ] `app/services/security_service.py` — engine bridge + persistence
- [ ] `app/schemas/security.py`
- [ ] `app/api/routes/security.py` — /security/search|compare|rank|recommend|report|history|top|details
- [ ] `app/api/__init__.py` — mount router
- [ ] `app/tasks/security.py` — background jobs (refresh data, rankings, metrics, snapshots, holdings, cache clean)
- [ ] `app/main.py` — register scheduler jobs
- [ ] `requirements.txt` — add requests, yfinance

## Phase 8 — Tests
- [ ] `security_selection/tests/conftest.py` — mock providers + sample data
- [ ] test_metrics.py, test_ranking.py, test_filters.py, test_cache.py, test_factors.py
- [ ] test_portfolio_construction.py, test_comparison.py, test_explainability.py, test_evaluators.py

## Phase 9 — Verification
- [ ] `python -m compileall security_selection app`
- [ ] Run pytest suite (offline-safe, mocked providers)

