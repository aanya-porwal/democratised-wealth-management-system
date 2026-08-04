"""Behavioural Simulation (PART 4).

Creates behavioural profiles (loss aversion, discipline, financial
literacy, overconfidence, panic selling, long-term thinking, impulse
spending, investment consistency) and a bias-driven decision model that
influences how a synthetic user responds to recommendations and market
events.

The decision model is *statistical*: it combines a user's behavioural
traits, financial context and market conditions into a decision
probability. It never calls into the deterministic engine — it only
*modulates* the likelihood of acceptance/rejection etc.
"""

from ml.behaviour.decision import (  # noqa: F401
    BehaviouralDecisionModel,
    DecisionOutcome,
    decide_recommendation_acceptance,
    rerank_by_behavior,
)

__all__ = [
    "BehaviouralDecisionModel",
    "DecisionOutcome",
    "decide_recommendation_acceptance",
    "rerank_by_behavior",
]
