# Goal-based financial planning core — TODO

## Milestone: goal-based planning pipeline (complete)

- [x] Rename package to `wealth_management_system` (importable, pytest-friendly)
- [x] `models.py` — add insurance, sip, and goal-contribution fields
- [x] `sample_users.py` — ravi, meena + 5 life-stage archetypes
- [x] `cashflow_engine.py` — surplus, savings rate, emergency fund
- [x] `health_engine.py` — health score + signals; emergency fund caps grade
- [x] `goal_engine.py` — feasibility, priority, surplus allocation
- [x] `probability_engine.py` — monte carlo goal success probability
- [x] `portfolio_engine.py` — risk score → strategic allocation + instruments
- [x] `planner.py` — orchestrates all engines into an explained `FinancialPlan`
- [x] `main.py` — entry point runs the full pipeline for every sample user
- [x] `demo.py` — walkthrough of every public API (replaces legacy `tests.py`)
- [x] pytest suite (44 tests across all engines)
- [x] README rewritten for the new architecture
- [x] `.gitignore` updated (scratch notebooks, caches)
- [x] Run full test suite green
- [x] Run `main.py` and `demo.py` end-to-end

