"""Timeline repository — append-only event store for digital twins.

The repository owns the *ordered* list of events for each twin. It is
deliberately simple: it never mutates or deletes events. It supports
in-memory storage (the default) and optional JSON persistence so the
timeline of a large population can be stored on disk and replayed.

The next step up (parquet / columnar) lives in
``ml.digital_twin.history`` for larger workloads.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ml.digital_twin.events.event import FinancialEvent
from ml.utils.io import atomic_write, ensure_dir, load_json, save_json


class TimelineRepository:
    """Append-only, ordered event store keyed by twin id.

    Events are stored as a list per twin, **sorted by timestamp** so
    that replay is deterministic. Thread-safe for concurrent twins.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self._events: Dict[str, List[FinancialEvent]] = {}
        self._lock = threading.RLock()
        self._base_path = Path(base_path) if base_path else None

    # ── write path ──────────────────────────────────────────────────
    def append(self, event: FinancialEvent) -> FinancialEvent:
        """Append an event to the twin's timeline (idempotent by id)."""
        with self._lock:
            events = self._events.setdefault(event.twin_id, [])
            if any(e.event_id == event.event_id for e in events):
                return event
            events.append(event)
            events.sort(key=lambda e: e.timestamp)
            return event

    def extend(self, events: Iterable[FinancialEvent]) -> int:
        """Append many events; returns the number of new events added."""
        count = 0
        for event in events:
            if self.append(event) is not None:
                count += 1
        return count

    # ── read path ───────────────────────────────────────────────────
    def get(self, twin_id: str) -> List[FinancialEvent]:
        """Return the full timeline for a twin (sorted by timestamp)."""
        with self._lock:
            return list(self._events.get(twin_id, []))

    def events_before(self, twin_id: str, timestamp) -> List[FinancialEvent]:
        """Return events whose timestamp is <= the given timestamp."""
        with self._lock:
            return [e for e in self._events.get(twin_id, []) if e.timestamp <= timestamp]

    def events_by_type(self, twin_id: str, event_type) -> List[FinancialEvent]:
        """Return events of a specific type for a twin."""
        with self._lock:
            return [e for e in self._events.get(twin_id, []) if e.event_type == event_type]

    def count(self, twin_id: str) -> int:
        """Number of events stored for a twin."""
        with self._lock:
            return len(self._events.get(twin_id, []))

    def twin_ids(self) -> List[str]:
        """Return all twin ids that have a timeline."""
        with self._lock:
            return list(self._events.keys())

    def all_events(self) -> Iterable[FinancialEvent]:
        """Yield every event across all twins (sorted per twin)."""
        with self._lock:
            for twin_id in list(self._events.keys()):
                yield from self._events[twin_id]

    # ── persistence (JSON) ──────────────────────────────────────────
    def save(self, path: Optional[Path] = None) -> Path:
        """Persist the full timeline to a JSON file (atomic)."""
        dest = Path(path) if path else (self._base_path / "timeline.json")
        ensure_dir(dest.parent)
        payload = {
            twin_id: [e.to_dict() for e in events]
            for twin_id, events in self._events.items()
        }
        save_json(dest, payload)
        return dest

    def load(self, path: Optional[Path] = None) -> "TimelineRepository":
        """Load a timeline previously saved with :meth:`save`."""
        src = Path(path) if path else (self._base_path / "timeline.json")
        raw = load_json(src)
        for twin_id, events in raw.items():
            self._events[twin_id] = [
                FinancialEvent.from_dict(e) for e in events
            ]
            self._events[twin_id].sort(key=lambda e: e.timestamp)
        return self

    def clear(self) -> None:
        """Drop all events (mainly for tests)."""
        with self._lock:
            self._events.clear()
