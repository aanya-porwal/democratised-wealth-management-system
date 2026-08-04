"""Recommendation Simulation (PART 6).

Every synthetic user receives recommendations. This module:

* Generates recommendation records (category, title, priority, etc.)
* Simulates the user's interaction outcome (accepted / rejected /
  ignored / modified) using the behaviour-driven decision model.
* Logs the full interaction history for downstream ML training.

The recommendation engine itself (deterministic) is never touched — the
ML layer only *simulates* how a user *responds* to recommendations.
"""

from ml.recommendation.simulator import (  # noqa: F401
    RecommendationSimulator,
    RecommendationRecord,
    simulate_recommendation_interaction,
)

__all__ = [
    "RecommendationSimulator",
    "RecommendationRecord",
    "simulate_recommendation_interaction",
]
