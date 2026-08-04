"""Twin simulation engine.

Drives a twin through a sequence of life events and market returns over
time, producing an evolving timeline. This is the foundation for the
later reinforcement-learning environment: the simulated twin is the
"environment" the RL agent interacts with.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from ml.digital_twin.events.event import EventType, FinancialEvent
from ml.digital_twin.models.twin import DigitalTwin
from ml.digital_twin.services.service import DigitalTwinService
from ml.digital_twin.timeline.repository import TimelineRepository
from ml.utils.seeding import seeded_rng
from ml.utils.logging import get_logger

logger = get_logger(__name__)


class TwinSimulationEngine:
    """Simulate a twin's financial life over a sequence of steps.

    Parameters
    ----------
    service:
        The :class:`DigitalTwinService` used to evolve the twin.
    seed:
        Optional random seed for reproducible simulations.
    """

    def __init__(self, service: DigitalTwinService, seed: Optional[int] = None) -> None:
        self.service = service
        self.seed = seed

    def simulate(
        self,
        twin: DigitalTwin,
        steps: int,
        market_returns: List[Dict[str, float]],
        life_events: Optional[List[Dict[str, object]]] = None,
        start_date: Optional[datetime] = None,
    ) -> TimelineRepository:
        """Run a multi-step simulation of the twin's life.

        Parameters
        ----------
        twin:
            The twin to simulate.
        steps:
            Number of time steps to run.
        market_returns:
            One return map per step (``{asset: return}``).
        life_events:
            Optional list of life events to inject at each step. Each
            element is a dict with ``event_type`` and ``data``.
        start_date:
            Start date for the timeline (defaults to now).

        Returns
        -------
        TimelineRepository
            The assembled timeline of the twin's simulated life.
        """
        rng = seeded_rng(self.seed)
        timeline = TimelineRepository(twin.twin_id)
        current = start_date or datetime.now(timezone.utc)

        for step in range(steps):
            delta = timedelta(days=30)
            current = current + delta

            # 1. market returns
            returns = market_returns[step % len(market_returns)] if market_returns else {}
            self.service.evolve_market(twin, returns, current)
            timeline.add_event(
                FinancialEvent.create(
                    twin.twin_id, EventType.MARKET_MOVEMENT, {"returns": returns},
                    timestamp=current,
                )
            )

            # 2. optional life event
            if life_events and step < len(life_events):
                ev = life_events[step]
                et = EventType(ev["event_type"])
                self.service.add_custom_event(twin, et, ev.get("data", {}), current)
                timeline.add_event(
                    FinancialEvent.create(twin.twin_id, et, ev.get("data", {}), timestamp=current)
                )

            # 3. periodic snapshot
            snap = self.service.snapshot(twin)
            timeline.add_event(
                FinancialEvent.create(
                    twin.twin_id,
                    EventType.SNAPSHOT,
                    {"snapshot": snap.to_dict()}
                    if hasattr(snap, "to_dict")
                    else {"snapshot": str(snap)},
                    timestamp=current,
                )
            )

        return timeline
