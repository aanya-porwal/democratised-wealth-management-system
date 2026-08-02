"""Portfolio snapshot generation task.

Wraps ``app.services.background.generate_portfolio_snapshots`` for the
APScheduler job in ``app.main``.
"""

from __future__ import annotations

from app.services.background import generate_portfolio_snapshots

__all__ = ["run"]


def run() -> None:
    """Generate portfolio snapshots for all active portfolios."""
    generate_portfolio_snapshots()
