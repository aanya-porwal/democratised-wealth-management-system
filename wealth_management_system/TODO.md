# Wealth Management System — Production Engine Transformation

## Task
Transform the existing goal-based planning prototype into a production-quality
financial planning engine while preserving backward compatibility.

## Plan Steps

### Foundations
- [x] 1. Create `config/` package: `config.yaml` (all constants) + `config.py` (typed loader)
- [x] 2. Create `exceptions.py` — custom exception hierarchy
- [x] 3. Create `models/` package: converted root `models.py` → `models/base.py` + new engine models (backward compatible)
- [x] 4. Create `utilities/` package: logging setup + plotting helpers (matplotlib optional)

### Engines
- [x] 5. PART 1 — `goals/` goal planning engine (future value, present value, required SIP, inflation-adjusted target, expected corpus, progress, probability)
- [x] 6. PART 2 — `allocation/` portfolio allocation engine (12 buckets, varies by age/risk/horizon/EF/debt/goals)
- [x] 7. PART 3 — `rebalancing/` rebalancing engine (drift thresholds, trades, tax + transaction cost aware)
- [x] 8. PART 4 — `score/` financial health score engine (0-100, strengths/weaknesses/suggestions)
- [x] 9. PART 5 — `simulation/` Monte Carlo engine (10k+ sims, percentiles, stats) + plotting separated
- [x] 10. PART 6 — `simulation/scenarios.py` scenario analysis engine
- [x] 11. PART 7 — `optimization/` mean-variance optimizer + base Optimizer protocol
- [x] 12. PART 8 — `recommendation/` explainable recommendation engine (confidence + reasoning)
- [x] 13. Update package `__init__.py` public API facade

### Configuration & Quality
- [x] 14. Move constants into `config/config.yaml` (returns, inflation, risk thresholds, asset constraints, tax assumptions, simulation params)
- [x] 15. Add `pyproject.toml` (black, ruff, mypy) + update `requirements.txt` (scipy, pyyaml)

### Testing
- [x] 16. Tests: goal engine, allocation, rebalancing, health score, monte carlo, scenarios, optimization, recommendation, config
- [x] 17. Ensure all 44 existing tests still pass

### Verification
- [x] 18. Run full test suite green
- [x] 19. Run `main.py` and `demo.py` end-to-end
- [x] 20. Update README.md + root TODO.md

