# Democratised Wealth Management System

An AI-powered wealth management prototype that combines **risk assessment**,
**tax-aware asset allocation** and **investment recommendations** for the
Indian market. Built for users across the economic spectrum — from tier-2/3
first-time investors to sophisticated high-earners.

This project is a clean, modular refactor of the original Jupyter prototype
(`notebooks/prototype.ipynb`), preserving all business logic and outputs while
removing duplication and enforcing PEP 8 + type hints.

---

## Features

| Module | Responsibility |
|--------|----------------|
| `models.py` | Pure data models — enums, dataclasses, user/goal/risk/asset definitions. No calculations. |
| `risk_engine.py` | Risk capacity (income stability, emergency fund, debt, surplus, dependents) & risk tolerance (behavioural), combined into a final `RiskAssessment` where **capacity acts as a ceiling**. |
| `assets.py` | The curated `ASSET_PROFILES` database — 44+ Indian investment instruments with returns, volatility, liquidity, lock-in, tax treatment and 80C eligibility. |
| `recommendation_engine.py` | Tax-optimised instrument selection: within-category alternatives and cross-category `best_instruments_for_need`. |
| `utils.py` | Shared helpers: INR formatting and an IRR-based `elss_irr` for correctly modelling the ELSS 80C entry benefit. |
| `tests.py` | Demo users (`ravi`, `meena`) and runnable sanity checks for every public API. |
| `main.py` | Thin orchestration entry point (risk + recommendations for a demo user). |

---

## Quick Start

```bash
# 1. (Recommended) create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the end-to-end demo
python main.py

# 4. run all sanity checks / demo users
python tests.py
```

### Sample output (`python main.py`)

```
=== Risk Assessment: Ravi Shankar ===
Capacity Score:  0.63 / 1.0
Tolerance Score: 0.76 / 1.0
Final Score:     63 / 100
Risk Category:   Aggressive
Capacity binding: True

=== Recommendations: Ravi Shankar ===
         instrument      category gross_return effective_return projected_1L  risk_level  lock_in_yrs deduction
...
```

---

## How it works

### 1. Risk Assessment (`risk_engine.py`)

- **Capacity** — a weighted blend of:
  - Emergency fund readiness (30%)
  - Income stability (25%)
  - Debt burden (20%)
  - Investable surplus ratio (15%)
  - Dependents (10%)
- **Tolerance** — from the user's stated risk tolerance, drawdown reaction,
  experience, financial literacy and loss aversion.
- **Final score** = `min(0.45*tolerance + 0.55*capacity, capacity)`.
  Capacity is a hard ceiling — a user can never take more risk than they can
  absorb.

### 2. Asset Universe (`assets.py`)

Every instrument is described by an `AssetClassProfile`: expected return,
volatility, horizon, liquidity, lock-in, risk level (1–10), tax treatment
(`EEE` / `EET` / equity LTCG / debt slab / SGB / ...), 80C deduction benefit,
minimum investment and SIP eligibility.

### 3. Recommendations (`recommendation_engine.py`)

- `get_tax_optimised_alternatives(...)` — ranks every instrument *within a
  category* by after-tax return for the user's bracket.
- `best_instruments_for_need(...)` — the core function. Maps a generic need
  (`"safe"`, `"debt"`, `"growth"`, `"gold"`, `"real_assets"`, `"all"`) to the
  top instruments *across all categories*, filtered by horizon, monthly
  investment, risk ceiling and then ranked by effective (after-tax) return.

### 4. ELSS special-case (`utils.py`)

ELSS gets a one-time 80C entry benefit. A naive rate adjustment overstates
this, so the engine builds the actual monthly cash flows (SIP outflows, annual
tax refunds, terminal redemption net of LTCG) and solves for the **IRR** to
derive the true effective after-tax return.

---

## Project Structure

```
democratised-wealth-management-system/
├── README.md
├── requirements.txt
├── main.py                  # orchestration only
├── models.py                # enums + dataclasses (no calculations)
├── risk_engine.py           # risk scoring & assessment
├── assets.py                # investment product database
├── recommendation_engine.py # tax-aware recommendations
├── utils.py                 # shared helpers (formatting, IRR)
├── tests.py                 # demo users + sanity checks
└── notebooks/
    └── prototype.ipynb      # original notebook (archival)
```

---

## Refactor summary

### Cell → file mapping

| Notebook cell(s) | Moved to |
|------------------|----------|
| 0, 6, 7, 8 | `models.py` |
| 1, 2, 3, 4 | **duplicates of cell 0 — removed** |
| 9 | `tests.py` (`ravi` + sanity prints) |
| 10 | (imports only — removed, merged into modules) |
| 11, 12, 13, 14 | `risk_engine.py` |
| 15 | `tests.py` (`ravi` risk print) |
| 16 | `tests.py` (`meena` + risk print) |
| 17 | (section comment — dropped) |
| 18 | `models.py` (asset enums) + `assets.py` imports |
| 19 | `assets.py` + `models.py` (AssetClassProfile dataclass) |
| 20 | `assets.py` (`ASSET_PROFILES`) |
| 21 | `tests.py` (asset universe verification) |
| 22 | `recommendation_engine.py` |
| 23 | `recommendation_engine.py` |
| 24 | `tests.py` (recommendation demos) |
| 25 | `tests.py` (diagnostics) |
| 26 | malformed cell — ignored |

### Duplicated code removed

- `EmploymentType`, `GoalType`, `GoalPriority`, `Goal` were defined twice
  (cell 0 and again in cells 1–4) → kept once in `models.py`.
- `import numpy as np` / `from dataclasses import ...` / `from enum import
  Enum` repeated in cells 10 and 18 → consolidated into per-module imports.
- `pd.set_option(...)` display options repeated → applied once in `tests.py`
  and `main.py`.

### Assumptions made

1. `models.ipynb` is an empty/broken stub (single malformed cell) → ignored.
2. `elss_irr` was **referenced but never defined** in the notebook. Implemented
   a correct IRR-based version in `utils.py` to make the ELSS code path run.
3. `numpy.irr`/`numpy.npv` are deprecated/removed in numpy 2.x, so `utils.py`
   implements its own bisection IRR (no extra dependency).
4. `has_nps_headroom` is accepted for API compatibility but does not currently
   change any ranking (as in the original notebook).
5. Tax brackets/rates and SGB interest are kept at the notebook's values; the
   comment about "update as per 2026" is left as a TODO in `FinancialProfile`.

### TODOs / known limitations

- **2026 tax-slab update**: `FinancialProfile.tax_bracket_percent` docstring
  notes the brackets may need updating for FY 2026-27 (surcharges etc.).
- **Onboarding questionnaire** referenced in `BehavioralProfile` does not yet
  exist — scores are currently supplied directly.
- `elss_irr` uses a deterministic bisection fallback when no exact root exists;
  behaviour is stable but slightly approximate for pathological inputs.
- No tests yet for the risk/asset modules beyond the `tests.py` demo runs.

---

## License

Educational prototype. Not investment advice.

