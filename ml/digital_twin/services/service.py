"""Digital Twin Service — the primary orchestrator for twin lifecycle.

This is the main entry point for creating, evolving, replaying, and
analysing digital twins. It delegates to:

* :mod:`~ml.digital_twin.events` for event creation
* :mod:`~ml.digital_twin.timeline` for persistence and replay
* :mod:`~ml.digital_twin.portfolio` for portfolio evolution
* :mod:`~ml.digital_twin.behaviour` for behaviour drift
* :mod:`~ml.digital_twin.analytics` for financial health metrics
* :mod:`~ml.digital_twin.history` for disk persistence
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from ml.digital_twin.analytics.calculator import TwinAnalyticsCalculator
from ml.digital_twin.behaviour.drift import apply_behaviour_drift
from ml.digital_twin.events.event import EventType, FinancialEvent
from ml.digital_twin.history.store import HistoryStore
from ml.digital_twin.models.twin import DigitalTwin, LifeSnapshot, PortfolioState
from ml.digital_twin.portfolio.evolution import (
    add_investment,
    apply_market_returns,
    rebalance_to_weights,
    withdraw_investment,
)
from ml.digital_twin.timeline.replay import ReplayEngine
from ml.digital_twin.timeline.repository import TimelineRepository
from ml.models import BehaviourTraits
from ml.utils.logging import get_logger

logger = get_logger(__name__)


class DigitalTwinService:
    """Orchestrates creation, evolution, replay and analysis of digital twins.

    Parameters
    ----------
    store:
        Optional :class:`HistoryStore` for persistence.
    """

    def __init__(self, store: Optional[HistoryStore] = None) -> None:
        self.store = store
        self._analytics = TwinAnalyticsCalculator()
        self._replay = ReplayEngine(analytics=self._analytics)

    # ── creation ────────────────────────────────────────────────────
    def create_twin(
        self,
        twin_id: str,
        initial_profile: Dict[str, object],
        initial_behaviour: BehaviourTraits,
        initial_portfolio: Optional[PortfolioState] = None,
    ) -> DigitalTwin:
        """Create a new digital twin and record its birth event."""
        now = datetime.now(timezone.utc)
        twin = DigitalTwin(
            twin_id=twin_id,
            profile=initial_profile,
            behaviour=initial_behaviour,
            portfolio=initial_portfolio or PortfolioState(),
            created_at=now,
        )
        event = FinancialEvent.create(
            twin_id, EventType.USER_CREATED, {"profile": initial_profile}, timestamp=now
        )
        if self.store:
            self.store.save_events(TimelineRepository(twin_id).add_event(event))
        return twin

    # ── evolution ───────────────────────────────────────────────────
    def evolve_market(
        self, twin: DigitalTwin, returns: Dict[str, float], timestamp
    ) -> FinancialEvent:
        """Apply market returns to the twin's portfolio."""
        event = apply_market_returns(twin, returns, timestamp)
        self._append_event(twin.twin_id, event)
        return event

    def evolve_investment(
        self, twin: DigitalTwin, asset: str, amount: float, timestamp
    ) -> FinancialEvent:
        """Add an investment to the twin."""
        event = add_investment(twin, asset, amount, timestamp)
        self._append_event(twin.twin_id, event)
        return event

    def evolve_withdrawal(
        self, twin: DigitalTwin, asset: str, amount: float, timestamp
    ) -> FinancialEvent:
        """Withdraw from the twin's portfolio."""
        event = withdraw_investment(twin, asset, amount, timestamp)
        self._append_event(twin.twin_id, event)
        return event

    def evolve_rebalance(
        self, twin: DigitalTwin, target_weights: Dict[str, float], timestamp
    ) -> FinancialEvent:
        """Rebalance the twin's portfolio."""
        event = rebalance_to_weights(twin, target_weights, timestamp)
        self._append_event(twin.twin_id, event)
        return event

    def evolve_behaviour(
        self, twin: DigitalTwin, drift: Dict[str, float], timestamp
    ) -> FinancialEvent:
        """Apply behaviour drift to the twin."""
        event = apply_behaviour_drift(twin, drift, timestamp)
        self._append_event(twin.twin_id, event)
        return event

    def add_custom_event(
        self, twin: DigitalTwin, event_type: EventType, data: Dict[str, object], timestamp
    ) -> FinancialEvent:
        """Add an arbitrary event to the twin's timeline."""
        event = FinancialEvent.create(twin.twin_id, event_type, data, timestamp=timestamp)
        self._append_event(twin.twin_id, event)
        return event

    # ── replay ──────────────────────────────────────────────────────
    def replay_twin(
        self, timeline: TimelineRepository, target_time: Optional[datetime] = None
    ) -> DigitalTwin:
        """Replay a twin's timeline to reconstruct state at a point in time."""
        return self._replay.replay(timeline, target_time)

    def simulate_life(
        self,
        timeline: TimelineRepository,
        events: List[FinancialEvent],
        start_state: Optional[DigitalTwin] = None,
    ) -> DigitalTwin:
        """Simulate a series of events on top of an existing timeline."""
        return self._replay.simulate(timeline, events, start_state)

    # ── snapshots ───────────────────────────────────────────────────
    def snapshot(self, twin: DigitalTwin) -> LifeSnapshot:
        """Record a point-in-time snapshot of the twin."""
        snap = LifeSnapshot(
            twin_id=twin.twin_id,
            timestamp=datetime.now(timezone.utc),
            profile=dict(twin.profile),
            behaviour=twin.behaviour,
            portfolio=twin.portfolio,
            goals=twin.goals,
        )
        return snap

    # ── persistence ─────────────────────────────────────────────────
    def persist_timeline(self, timeline: TimelineRepository) -> None:
        """Save the timeline to the history store."""
        if self.store:
            self.store.save_events(timeline)

    def load_timeline(self, twin_id: str) -> TimelineRepository:
        """Load a twin's timeline from the history store."""
        timeline = TimelineRepository(twin_id)
        if self.store:
            self.store.load_events(timeline)
        return timeline

    # ── internals ───────────────────────────────────────────────────
    def _append_event(self, twin_id: str, event: FinancialEvent) -> None:
        """Append an event to the twin's timeline (event-sourcing)."""
        repo = TimelineRepository(twin_id)
        if self.store:
            self.store.load_events(repo)
        repo.add_event(event)
        if self.store:
            self.store.save_events(repo)
