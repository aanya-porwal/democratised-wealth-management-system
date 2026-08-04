"""Portfolio evolution helpers for the Digital Twin Engine.

These functions mutate a twin's :class:`PortfolioState` and return the
matching immutable events so the caller (typically
:class:`DigitalTwinService`) can append them to the timeline. This keeps
the event-sourced invariant: state is always derived from events.
"""

from __future__ import annotations

from typing import Dict, Optional

from ml.digital_twin.events.event import EventType, FinancialEvent
from ml.digital_twin.models.twin import DigitalTwin, PortfolioState


def _sync_weights(state: PortfolioState) -> None:
    """Recompute asset weights from holdings (deterministic bookkeeping)."""
    total = sum(state.holdings.values())
    state.total_value = total
    if total > 0:
        state.weights = {k: v / total for k, v in state.holdings.items()}
    else:
        state.weights = {}


def apply_market_returns(
    twin: DigitalTwin,
    returns: Dict[str, float],
    timestamp,
) -> FinancialEvent:
    """Apply one-period market returns to existing holdings."""
    state = twin.portfolio
    for asset, ret in returns.items():
        if asset in state.holdings:
            state.holdings[asset] *= 1.0 + ret
    _sync_weights(state)
    state.updated_at = timestamp
    return FinancialEvent.create(
        twin.twin_id,
        EventType.MARKET_MOVEMENT,
        {"returns": returns},
        timestamp=timestamp,
    )


def add_investment(
    twin: DigitalTwin,
    asset: str,
    amount: float,
    timestamp,
) -> FinancialEvent:
    """Add a new or additional investment to the twin's portfolio."""
    state = twin.portfolio
    state.holdings[asset] = state.holdings.get(asset, 0.0) + amount
    _sync_weights(state)
    state.updated_at = timestamp
    return FinancialEvent.create(
        twin.twin_id,
        EventType.INVESTMENT_ADDED,
        {"asset": asset, "amount": amount},
        timestamp=timestamp,
    )


def withdraw_investment(
    twin: DigitalTwin,
    asset: str,
    amount: float,
    timestamp,
) -> FinancialEvent:
    """Withdraw from a holding (clamped at zero)."""
    state = twin.portfolio
    current = state.holdings.get(asset, 0.0)
    actual = min(current, amount)
    if current - actual <= 1e-9:
        state.holdings.pop(asset, None)
    else:
        state.holdings[asset] = current - actual
    _sync_weights(state)
    state.updated_at = timestamp
    return FinancialEvent.create(
        twin.twin_id,
        EventType.INVESTMENT_WITHDRAWN,
        {"asset": asset, "amount": actual},
        timestamp=timestamp,
    )


def rebalance_to_weights(
    twin: DigitalTwin,
    target_weights: Dict[str, float],
    timestamp,
) -> FinancialEvent:
    """Rebalance the portfolio to a target allocation.

    The actual rebalancing *math* (sell/buy amounts, rounding) is handled
    by the deterministic engine; here we only record the resulting
    holdings and emit a portfolio change event.
    """
    state = twin.portfolio
    total = state.total_value
    if total <= 0:
        return FinancialEvent.create(
            twin.twin_id,
            EventType.PORTFOLIO_CHANGE,
            {"holdings": {}, "weights": {}, "cash": state.cash},
            timestamp=timestamp,
        )
    new_holdings = {}
    for asset, w in target_weights.items():
        new_holdings[asset] = total * w
    state.holdings = new_holdings
    _sync_weights(state)
    state.updated_at = timestamp
    return FinancialEvent.create(
        twin.twin_id,
        EventType.PORTFOLIO_CHANGE,
        {
            "holdings": dict(state.holdings),
            "weights": dict(state.weights),
            "cash": state.cash,
        },
        timestamp=timestamp,
    )
