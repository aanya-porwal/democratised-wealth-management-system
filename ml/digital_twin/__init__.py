"""Digital Twin Engine — event-sourced foundation package.

Every change to a person's financial life is recorded as an immutable,
timestamped event. The Digital Twin never overwrites history; it
appends. This makes the entire financial life of a person replayable
from any point in time, which is the foundation for the RL environment
and for time-aware ML datasets.
"""

from ml.digital_twin.events.event import EventType, FinancialEvent, ImmutableFinancialEvent  # noqa: F401
from ml.digital_twin.models.twin import DigitalTwin, LifeSnapshot, PortfolioState, GoalState  # noqa: F401

__all__ = [
    "EventType",
    "FinancialEvent",
    "ImmutableFinancialEvent",
    "DigitalTwin",
    "LifeSnapshot",
    "PortfolioState",
    "GoalState",
]
