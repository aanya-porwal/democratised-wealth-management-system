"""Goal planning engine.

Provides a production-grade :class:`GoalEngine` that produces a complete
analytical picture for every goal:

* future value / present value / inflation-adjusted target
* required SIP and remaining gap
* current progress
* expected corpus (median from Monte Carlo)
* probability of success

The engine reuses the deterministic FV/PV math from the legacy
``goal_engine`` module (backward compatible) and the seeded Monte Carlo
from ``probability_engine`` for the success probability.
"""

from wealth_management_system.goals.engine import GoalEngine

__all__ = ["GoalEngine"]
