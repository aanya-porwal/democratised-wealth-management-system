# Build TODO — goal-based wealth management platform

- [ ] Rename package to `wealth_management_system/` (valid python package) + `__init__.py`
- [ ] Convert internal imports to package-absolute imports; verify baseline `python -m wealth_management_system.main`
- [ ] Extend `models.py` (insurance cover, existing SIP, goal current contribution)
- [ ] Create `sample_users.py` (ravi, meena + archetypes: student, retiree, high-debt, family, HNW)
- [ ] Build `cashflow_engine.py` (surplus, savings rate, emergency fund gap, runway)
- [ ] Build `health_engine.py` (6-dimension health score + plain-language signals)
- [ ] Build `goal_engine.py` (priority ordering, required contribution, feasibility, surplus waterfall)
- [ ] Build `probability_engine.py` (Monte Carlo goal success probability)
- [ ] Build `portfolio_engine.py` (risk → target allocation + concrete instruments)
- [ ] Build `planner.py` (orchestrates engines → explained financial plan)
- [ ] Rewrite `main.py` as full end-to-end plan demo
- [ ] Create `tests/` assertion suite (all archetypes + edge cases); update `tests.py` demo
- [ ] Create canonical notebook `wealth_management_system.ipynb`; retire old notebooks
- [ ] Update `README.md`, `requirements.txt`, add `.gitignore`
- [ ] Run full suite, commit per engine, push to github

