"""Replay engine — reconstruct a twin's state at any point in time.

Replay is the read-side of the event-sourced digital twin. Given a
timeline of immutable events, we project them onto a fresh :class:`DigitalTwin`
to recreate its state exactly as it was at a given time. This is what
makes the twin "replayable from any point in time":
``DigitalTwinService`` persists the current state, while ``ReplayEngine``
can rebuild any historical state from the event log alone.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from ml.digital_twin.events.event import EventType, FinancialEvent
from ml.digital_twin.models.twin import DigitalTwin, LifeSnapshot
from ml.digital_twin.timeline.repository import TimelineRepository


class ReplayEngine:
    """Projects event streams onto fresh twins to reconstruct state.

    Parameters
    ----------
    timeline:
        The repository to read events from.
    """

    def __init__(self, timeline: TimelineRepository) -> None:
        self._timeline = timeline

    def replay(
        self,
        twin_id: str,
        as_of: Optional[datetime] = None,
        include_types: Optional[Iterable[EventType]] = None,
        exclude_types: Optional[Iterable[EventType]] = None,
    ) -> DigitalTwin:
        """Rebuild a twin's state from its event timeline.

        Parameters
        ----------
        twin_id:
            The twin to rebuild.
        as_of:
            Only replay events up to this timestamp (inclusive). If
            ``None``, the entire timeline is replayed.
        include_types:
            If given, only these event types are applied.
        exclude_types:
            If given, these event types are skipped.

        Returns
        -------
        DigitalTwin
            A fresh twin with state equal to the projected timeline.
        """
        twin = DigitalTwin(twin_id=twin_id)
        if tuple(twin.profile.to_dict().keys()):
            # Reset the default profile; we'll let PROFILE_CREATED fill it.
            pass
        for event in self._iter_events(twin_id, as_of):
            if include_types and event.event_type not in set(include_types):
                continue
            if exclude_types and event.event_type in set(exclude_types):
                continue
            twin.apply_event(event)
        return twin

    def snapshot_at(
        self, twin_id: str, as_of: datetime
    ) -> Optional[LifeSnapshot]:
        """Return a :class:`LifeSnapshot` of the twin's state at a time."""
        twin = self.replay(twin_id, as_of=as_of)
        if not twin.profile.person_id:
            return None
        # Build a snapshot from the replayed state. The analytics module
        # provides the richer builder; here we emit a minimal one.
        from ml.digital_twin.analytics.calculator import build_snapshot

        return build_snapshot(twin, as_of)

    def _iter_events(
        self, twin_id: str, as_of: Optional[datetime]
    ) -> Iterable[FinancialEvent]:
        events = self._timeline.get(twin_id)
        if as_of is not None:
            events = [e for e in events if e.timestamp <= as_of]
        return events

    def replay_between(
        self,
        twin_id: str,
        start: datetime,
        end: datetime,
    ) -> List[FinancialEvent]:
        """Return the ordered events that occurred in ``[start, end]``."""
        events = self._timeline.get(twin_id)
        return [e for e in events if start <= e.timestamp <= end]
