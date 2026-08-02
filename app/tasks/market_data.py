"""Market data refresh task.

Wraps ``app.services.background.refresh_market_data_cache`` for the
APScheduler job in ``app.main``.
"""

from __future__ import annotations

from app.services.background import refresh_market_data_cache

__all__ = ["run"]


def run() -> None:
    """Refresh the market-data cache."""
    refresh_market_data_cache()
