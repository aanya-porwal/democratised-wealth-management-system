# Wealth Management System

A goal-based, AI-assisted financial planning platform for India.

This is not a "pick mutual funds" tool. It reasons like a financial
planner: it understands your cashflow and financial health before it
ever suggests an investment. It prioritises your goals, checks whether
they are realistic, measures how much risk you can actually take, builds
a strategic portfolio, and — most importantly — explains every
recommendation in plain language.

Built for users across the economic spectrum: students, young
professionals, families, business owners, retirees, low income, high
income, high debt, and high net worth.

---

## The philosophy

- cashflow always comes before investing
- emergency fund always comes before wealth creation
- goal priority always comes before return optimisation
- risk capacity always overrides risk tolerance
- liquidity is never ignored
- tax is never an afterthought
- a recommendation that cannot be explained should not exist

The system is built around **engines**, each solving one real problem,
orchestrated by a **planner** that runs the full planning flow.

---

## Architecture

```
wealth_management_system/
├── models.py                 # data models: enums + dataclasses (no logic)
├── sample_users.py           # ravi, meena + 5 life-stage archetypes
├── utils.py                  # formatting + IRR helpers
├── risk_engine.py            # risk capacity + tolerance → RiskAssessment
├── cashflow_engine.py        # surplus, savings rate, emergency fund
├── health_engine.py          # financial health score + explainable signals
├── goal_engine.py            # goal feasibility, priority, surplus allocation
├── probability_engine.py     # monte carlo goal success probability
├── portfolio_engine.py       # risk score → strategic allocation + instruments
├── recommendation_engine.py  # tax-aware instrument selection
├── planner.py                # orchestrates all engines → FinancialPlan
├── main.py                   # entry point: runs the pipeline, prints plans
├── demo.py                   # full walkthrough of every public API
└── tests/                    # pytest suite (44 tests across all engines)
```

### The planning flow

The planner runs these steps in exactly this order — the way a certified
planner would:

1. **cashflow** — how much money exists each month after expenses
2. **health** — how solid the foundations are (savings rate, emergency
   fund, debt, surplus, protection)
3. **goals** — what the money is for, and whether each goal is realistic
4. **risk** — how much risk the user can *actually* take (capacity is a
   ceiling)
5. **portfolio** — the strategic allocation and concrete instruments
6. **probability** — monte carlo success probability for each goal
7. **actions** — explained recommendations, ordered by priority

The system never skips straight to recommending investments.

---

## Quick start

```bash
# 1. (recommended) create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the full planning pipeline for every sample user
python -m wealth_management_system.main

# 4. walk every public API (risk, assets, recommendations, diagnostics)
python -m wealth_management_system.demo

# 5. run the test suite
python -m pytest wealth_management_system/tests -q
```

### Sample output (`python -m wealth_management_system.main`)

```
=====================================================================
FINANCIAL PLAN — Ravi Shankar
=====================================================================
Ravi Shankar's foundations are good (health 69/100). Risk capacity: aggressive (69/100). Goal outlook: 2 goal(s) unlikely on the current path.

Health: good (69/100)
Risk capacity: Aggressive (69/100)

Portfolio allocation (strategic target):
  equity   65.0%  →  equity elss, equity small cap, equity mid cap
  debt     28.0%  →  balanced advantage, nps tier2, epf
  gold      3.5%  →  sovereign gold bond, gold etf
  cash      3.5%  →  savings account, liquid fund

Recommended actions:
  [now ] top up the emergency fund to 6 months (₹247,500 more)
        ↳ the buffer is partial; finish it before heavy long-term investing
  [next] revisit the wealth creation goal — increase the monthly contribution or extend the date
        ↳ only a 0% chance of success on the current path (median shortfall ₹10,000,000)

Goal outlook:
  emergency fund          0%  median ₹      44,359 (unlikely)
  wealth creation         0%  median ₹           0 (unlikely)
```

---

## Engines in detail

### risk_engine

- **capacity** — weighted blend of emergency fund readiness (30%),
  income stability (25%), debt burden (20%), investable surplus (15%),
  dependents (10%).
- **tolerance** — behavioural: stated tolerance, drawdown reaction,
  experience, financial literacy, loss aversion.
- **final score** = `min(0.45 * tolerance + 0.55 * capacity, capacity)`.
  Capacity is a hard ceiling — you can never take more risk than you can
  financially absorb.

### cashflow_engine

Computes true monthly surplus, savings rate, and emergency fund
readiness. The emergency fund is the foundation — irregular earners get
a thicker recommended buffer (9 months vs 6).

### health_engine

Scores 0–100 across five foundations and returns plain-language signals
explaining the score. The emergency fund **caps the grade**: a user with
no buffer can never score "excellent". Foundations always come first.

### goal_engine

For every goal: projected value on the current savings path, required
monthly contribution to hit the target, and feasibility. Then allocates
surplus to goals in strict priority order (critical → high →
aspirational), after holding back the emergency fund share.

### probability_engine

Monte Carlo simulation (lognormal returns, seeded and deterministic).
Returns a success probability plus 5th/25th/50th/75th/95th percentile
outcomes, so the plan talks in ranges rather than false precision.

### portfolio_engine

Maps the risk score to a strategic asset allocation via a conservative
glidepath (even maximum risk never exceeds 75% equity). Each bucket is
filled with tax-aware instruments from the curated asset database. The
cash bucket is strictly cash-and-liquid products.

### recommendation_engine

Tax-aware instrument selection across the full asset universe, ranked by
after-tax return. ELSS is handled specially via an IRR calculation that
correctly models the one-time 80C entry benefit.

### planner

Orchestrates everything. Produces a `FinancialPlan` with a plain-language
summary, the strategic allocation, goal outlook, and ordered explained
actions.

---

## Sample users & archetypes

`sample_users.py` provides:

| user | profile | what the planner detects |
|------|---------|--------------------------|
| Ravi | 28, software engineer, Mumbai | thin emergency fund → build it first |
| Meena | 44, business owner, tier 3 | irregular income → thicker buffer + term cover |
| Aarav | 21, student | negative cashflow → fix the budget, don't invest |
| Sharma | 65, retiree | complete foundations → protect capital |
| Karan | 31, high-debt professional | over-leveraged → debt + emergency fund first |
| Priya | 38, working parent | strong foundations → invest toward goals |
| Vikram | 45, HNW | idle cash + under-insured → get cover, deploy surplus |

---

## Testing

44 pytest tests cover every engine:

- cashflow surplus and emergency fund logic
- health score bounds and the emergency-fund grade ceiling
- goal priority, feasibility and allocation ordering
- probability determinism and boundary behaviour
- portfolio weight conservation and liquidity of the cash bucket
- risk capacity as a ceiling
- the planner's action ordering and "foundations first" rule
- asset-universe consistency and tax treatment

---

## Roadmap

- replace fixed-return assumptions with calibrated Monte Carlo
- monitor a portfolio over time and suggest rebalancing
- tax-loss harvesting and instrument-level tax optimisation
- conversational financial advice (the recommendation layer explains
  *why this, why now, why not something else*)
- automated detection of the financial-intelligence patterns
  (over-insured, under-insured, idle money, unrealistic goals, ...)

---

## License

Educational prototype. Not investment advice.

