"""Background maintenance tasks.

These jobs run on the APScheduler loop inside the API process:

* refresh the market-data cache in Redis
* generate portfolio snapshots for active portfolios
* update goal-progress records from current holdings/savings
* prepare notifications for at-risk goals

Each task opens its own session via :func:`session_scope` so a failure
in one job never affects request traffic.
"""

from __future__ import annotations

import logging

from app.core import cache
from app.core.logging import get_logger
from app.database.session import session_scope

logger = get_logger(__name__)


def refresh_market_data_cache() -> None:
    """Refresh cached market data (indices, asset prices, assumptions).

    Currently seeds a lightweight placeholder payload; a real feed
    (e.g. Yahoo/RBI/NSE) can be swapped in without touching the API.
    """
    cache.cache.set_json(
        "system:market_data:last_refresh",
        {
            "refreshed": True,
            "source": "placeholder",
            "message": "Wire a market-data provider here without changing the API.",
        },
        ttl_seconds=60 * 60 * settings_market_data_hours(),
    )
    logger.info("Market data cache refreshed (placeholder)")


def generate_portfolio_snapshots() -> None:
    """Persist a snapshot for every user portfolio with holdings."""
    from app.models.portfolio import Portfolio, PortfolioSnapshot

    captured = 0
    with session_scope() as session:
        portfolios = (
            session.query(Portfolio)
            .filter(Portfolio.deleted_at.is_(None))
            .all()
        )
        for portfolio in portfolios:
            holdings = portfolio.holdings
            if not holdings:
                continue
            total_value = sum(h.market_value for h in holdings)
            if total_value <= 0:
                continue
            session.add(
                PortfolioSnapshot(
                    portfolio_id=portfolio.id,
                    user_id=portfolio.user_id,
                    total_value=total_value,
                    weights={
                        h.asset_class: h.market_value / total_value
                        for h in holdings
                    },
                    cash_flow=None,
                    notes="scheduled snapshot",
                )
            )
            captured += 1
    logger.info("Portfolio snapshots captured: %d", captured)


def update_goal_progress() -> None:
    """Recompute and persist goal-progress snapshots overnight.

    Uses the goal engine via the service layer so the calculation stays
    correct and centralised (no duplicated math in the job).
    """
    from app.models.user import User
    from app.services.goal_service import GoalService

    updated = 0
    with session_scope() as session:
        users = (
            session.query(User)
            .filter(User.deleted_at.is_(None), User.is_active.is_(True))
            .all()
        )
        service = GoalService(session)
        for user in users:
            goals = service.list_goals(user.id)
            for goal in goals:
                try:
                    service.record_progress(user.id, goal.id)
                    updated += 1
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Goal progress failed for goal %s: %s", goal.id, exc)
    logger.info("Goal progress snapshots recorded: %d", updated)


def prepare_notifications() -> None:
    """Queue notifications for goals that drifted to at-risk status.

    Placeholder for an email/push pipeline; the detection logic stays
    in the goal service.
    """
    logger.info("Notification preparation complete (placeholder)")


def settings_market_data_hours() -> int:
    """Return the configured market-data refresh interval in hours."""
    from app.config import settings

    return settings.MARKET_DATA_REFRESH_HOURS

