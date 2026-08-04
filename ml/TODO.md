# Intelligent Learning & Simulation Platform — TODO

Tracking file for the build of the `ml/` platform.

## Phase A — Foundation
- [x] `ml/__init__.py` — package docstring + version
- [x] `ml/config/config.yaml` — all tunable constants
- [x] `ml/config/config.py` — typed dataclass loader (mirrors security_selection pattern)
- [x] `ml/config/__init__.py`
- [x] `ml/utils/` — seeding, logging, io, correlation copula sampler
- [x] `ml/models/` — shared dataclasses (FinancialTwinProfile, Persona, BehaviourTraits)

## Phase B — Digital Twin Engine (PART 0)
- [x] `ml/digital_twin/events/` — EventType + ImmutableFinancialEvent
- [x] `ml/digital_twin/models/` — Twin, LifeSnapshot, PortfolioState, GoalState
- [x] `ml/digital_twin/timeline/` — TimelineRepository, ReplayEngine
- [x] `ml/digital_twin/portfolio/` — twin portfolio evolution
- [x] `ml/digital_twin/behaviour/` — behaviour drift model
- [x] `ml/digital_twin/analytics/` — net worth, health, ratios over time
- [x] `ml/digital_twin/services/` — DigitalTwinService orchestrator
- [x] `ml/digital_twin/history/` — HistoryStore (parquet/JSON) + replay
- [x] `ml/digital_twin/simulation/` — TwinSimulationEngine

## Phase C — Synthetic Data Stack (PARTS 1–6)
- [x] `ml/synthetic_population/` — 100k+ Indian household profiles (personas + generator)
- [x] `ml/behaviour/` — persona archetypes + bias-driven decision model
- [x] `ml/life_events/` — probabilistic life event simulator
- [x] `ml/market_simulation/` — real historical market data + regime detection + return sampler
- [x] `ml/recommendation/` — recommendation simulation (accepted/rejected/ignored/modified)

## Phase D — ML Stack (PARTS 7–16)
- [ ] `ml/feature_engineering/` — automated feature builder
- [ ] `ml/datasets/` — time-aware dataset builder (train/val/test, CSV/Parquet/DB)
- [ ] `ml/training/` — supervised learners (RF, XGB, LGBM, CatBoost, LR, GB)
- [ ] `ml/evaluation/` — metrics + SHAP explainability + model selection
- [ ] `ml/experiments/` — MLflow tracker (13.5) + local JSON fallback
- [ ] `ml/models/model_registry.py` — (14.5)
- [ ] `ml/reinforcement_learning/` — env/state/action/reward + PPO/DQN/SAC

## Phase E — Deployment & Ops (PARTS 15–18)
- [ ] `ml/deployment/` — replaceable model API + shadow deployment (15.5)
- [ ] `ml/monitoring/` — drift, performance, data quality, model health

## Phase F — Orchestration & Tests
- [ ] `ml/ml_platform/` — one-call pipeline facade + CLI
- [ ] `ml/tests/` — population, life events, behaviour, dataset, training, evaluation, deployment, digital twin replay
- [ ] `requirements-ml.txt` — optional heavy deps
- [ ] Compile check + test suite + smoke end-to-end run

## Verification
- [ ] `python -m compileall ml`
- [ ] `python -m pytest ml/tests -q`
- [ ] `python -m ml_platform.cli run --users 2000 --demographics dev`
