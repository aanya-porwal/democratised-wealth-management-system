"""History store for digital twins.

Persists the event timeline and periodic snapshots to disk (parquet +
JSON) so a large population of twins can be stored and replayed without
holding everything in memory. The store is append-only and never
overwrites history.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from ml.digital_twin.events.event import FinancialEvent
from ml.digital_twin.timeline.repository import TimelineRepository
from ml.utils.io import ensure_dir, load_dataframe, save_dataframe


class HistoryStore:
    """File-backed store for events and snapshots of a twin population.

    Parameters
    ----------
    base_path:
        Directory where history is persisted. Created if missing.
    """

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = ensure_dir(base_path)
        self.events_dir = ensure_dir(self.base_path / "events")
        self.snapshots_dir = ensure_dir(self.base_path / "snapshots")

    # ── events ─────────────────────────────────────────────────────
    def save_events(self, timeline: TimelineRepository) -> Path:
        """Persist the full timeline to a single JSON file."""
        return timeline.save(self.events_dir / "timeline.json")

    def load_events(self, timeline: TimelineRepository) -> TimelineRepository:
        """Load a timeline previously saved by :meth:`save_events`."""
        return timeline.load(self.events_dir / "timeline.json")

    # ── snapshots (parquet) ─────────────────────────────────────────
    def save_snapshots(
        self, snapshots: List[Dict[str, object]], shard: str = "all"
    ) -> Path:
        """Persist a list of snapshot dicts as a parquet shard."""
        df = pd.DataFrame(snapshots)
        return save_dataframe(df, self.snapshots_dir / f"snapshots_{shard}.parquet")

    def load_snapshots(self, shard: str = "all") -> pd.DataFrame:
        """Load a snapshot shard as a DataFrame."""
        return load_dataframe(self.snapshots_dir / f"snapshots_{shard}.parquet")

    def list_snapshots(self) -> List[str]:
        """Return the names of available snapshot shards."""
        return [p.name for p in self.snapshots_dir.glob("snapshots_*.parquet")]

    # ── events per twin (parquet) ───────────────────────────────────
    def save_events_frame(self, events: List[FinancialEvent]) -> Path:
        """Persist a list of events as a parquet frame (for analytics)."""
        rows = [e.to_dict() for e in events]
        df = pd.DataFrame(rows)
        return save_dataframe(df, self.events_dir / "events_frame.parquet")

    def load_events_frame(self) -> pd.DataFrame:
        """Load the events frame as a DataFrame."""
        return load_dataframe(self.events_dir / "events_frame.parquet")
