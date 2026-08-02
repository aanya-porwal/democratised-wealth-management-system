"""Notification preparation task.

Wraps ``app.services.background.prepare_notifications`` for the
APScheduler job in ``app.main``.
"""

from __future__ import annotations

from app.services.background import prepare_notifications

__all__ = ["run"]


def run() -> None:
    """Prepare notifications for at-risk goals and expiring recommendations."""
    prepare_notifications()
