"""Goal progress update task.

Wraps ``app.services.background.update_goal_progress`` for the
APScheduler job in ``app.main``.
"""

from __future__ import annotations

from app.services.background import update_goal_progress

__all__ = ["run"]


def run() -> None:
    """Recompute goal-progress snapshots for all active users."""
    update_goal_progress()
