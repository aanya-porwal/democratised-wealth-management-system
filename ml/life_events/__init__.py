"""Life Event Simulator (PART 3).

Simulates the probabilistic life events a synthetic person may
experience over their lifetime: promotions, salary growth, marriage,
children, house/vehicle purchase, inheritance, medical emergency, job
loss, career switch, business success/failure, retirement, death.

Events occur probabilistically with probabilities configurable in
``ml/config/config.yaml``. Each event is emitted as a
:class:`~ml.digital_twin.events.event.FinancialEvent` so it can be
appended to a Digital Twin's timeline.
"""

from ml.life_events.simulator import (  # noqa: F401
    LifeEventSimulator,
    simulate_life_timeline,
)

__all__ = [
    "LifeEventSimulator",
    "simulate_life_timeline",
]
