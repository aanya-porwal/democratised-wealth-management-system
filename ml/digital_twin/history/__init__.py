"""History store for digital twins.

Persists the event timeline and periodic snapshots to disk (parquet +
JSON) so a large population of twins can be stored and replayed without
holding everything in memory. The store is append-friendly and never
overwrites history.
"""

from ml.digital_twin.history.store import HistoryStore  # noqa: F401

__all__ = ["HistoryStore"]
