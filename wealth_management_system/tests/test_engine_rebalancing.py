"""Tests for the rebalancing engine (PART 3)."""

import pytest

from wealth_management_system.exceptions import RebalancingError
from wealth_management_system.models import (
    AssetClass,
    Holding,
    PortfolioHoldings,
    RebalanceDirection,
)
from wealth_management_system.rebalancing import RebalancingEngine

# A simple bucket map covering the buckets we test.
_TARGET = {
    "equity": 0.60,
    "debt": 0.30,
    "cash": 0.10,
}


def _holdings(overrides: dict | None = None) -> PortfolioHoldings:
    """Build a small portfolio of known holdings."""
    defaults: dict = {
        AssetClass.EQUITY_INDEX_LARGECAP: (60000, 50000),
        AssetClass.CORPORATE_BOND_FUND: (30000, 30000),
        AssetClass.LIQUID_FUND: (10000, 10000),
    }
    if overrides:
        defaults.update(overrides)
    holdings = PortfolioHoldings()
    for ac, (mv, cb) in defaults.items():
        holdings.add(Holding(asset_class=ac, market_value=mv, cost_basis=cb))
    return holdings


def test_no_drift_no_rebalance():
    """A portfolio already at target must not require rebalancing."""
    result = RebalancingEngine().analyse(_holdings(), _TARGET)
    assert result.rebalance_required is False
    assert result.actions == []


def test_large_drift_triggers_rebalance():
    """A portfolio far from target must require rebalancing."""
    # equity is only 10% vs 60% target
    holdings = _holdings(
        {
            AssetClass.EQUITY_INDEX_LARGECAP: (10000, 10000),
            AssetClass.CORPORATE_BOND_FUND: (70000, 70000),
            AssetClass.LIQUID_FUND: (20000, 20000),
        }
    )
    result = RebalancingEngine().analyse(holdings, _TARGET)
    assert result.rebalance_required is True
    # the equity bucket must be bought
    equity_actions = [a for a in result.actions if a.bucket == "equity"]
    assert equity_actions
    assert equity_actions[0].direction == RebalanceDirection.BUY


def test_trades_have_tax_and_cost():
    """Sell trades must estimate capital-gains tax; every trade carries cost."""
    holdings = _holdings(
        {
            AssetClass.EQUITY_INDEX_LARGECAP: (90000, 40000),  # large gain
            AssetClass.CORPORATE_BOND_FUND: (10000, 10000),
            AssetClass.LIQUID_FUND: (20000, 20000),
        }
    )
    result = RebalancingEngine().analyse(holdings, _TARGET)
    assert result.trades
    for trade in result.trades:
        assert trade.estimated_transaction_cost >= 0
        assert trade.estimated_tax_impact >= 0
    assert result.total_transaction_cost >= 0
    assert result.total_tax_impact >= 0


def test_small_drift_ignored():
    """Small drifts within thresholds must not trigger trades."""
    # debt 32% vs 30% target: within 5% absolute threshold
    holdings = _holdings(
        {
            AssetClass.EQUITY_INDEX_LARGECAP: (58000, 50000),
            AssetClass.CORPORATE_BOND_FUND: (32000, 30000),
            AssetClass.LIQUID_FUND: (10000, 10000),
        }
    )
    result = RebalancingEngine().analyse(holdings, _TARGET)
    assert result.rebalance_required is False


def test_empty_target_raises():
    """An empty target allocation must raise RebalancingError."""
    with pytest.raises(RebalancingError):
        RebalancingEngine().analyse(_holdings(), {})


def test_zero_portfolio_no_rebalance():
    """A zero-value portfolio must be flagged as requiring no trades."""
    holdings = PortfolioHoldings()
    result = RebalancingEngine().analyse(holdings, _TARGET)
    assert result.rebalance_required is False


def test_total_trade_notional():
    """total_trade_notional() must be the sum of absolute amounts."""
    holdings = _holdings(
        {
            AssetClass.EQUITY_INDEX_LARGECAP: (10000, 10000),
            AssetClass.CORPORATE_BOND_FUND: (70000, 70000),
            AssetClass.LIQUID_FUND: (20000, 20000),
        }
    )
    result = RebalancingEngine().analyse(holdings, _TARGET)
    total = result.total_trade_notional()
    manual = sum(abs(t.amount) for t in result.trades)
    assert abs(total - manual) < 0.01

