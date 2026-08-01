"""tests for the portfolio engine."""

from wealth_management_system.portfolio_engine import (
    _equity_weight,
    build_portfolio,
)
from wealth_management_system.sample_users import (
    build_all_sample_users,
    ravi,
)


def test_weights_sum_to_one():
    """the strategic allocation must always be a full allocation."""
    for user in build_all_sample_users():
        portfolio = build_portfolio(user)
        total = sum(s.weight for s in portfolio.slices)
        assert abs(total - 1.0) < 0.01


def test_equity_weight_is_conservative():
    """even a maximum risk score must not produce 100% equity."""
    assert _equity_weight(100) <= 0.75
    assert _equity_weight(0) <= 0.10


def test_equity_weight_monotonic():
    """more risk capacity should never mean less equity."""
    weights = [_equity_weight(score) for score in (10, 40, 70, 100)]
    assert weights == sorted(weights)


def test_has_all_buckets():
    """every portfolio should have equity, debt, gold and cash buckets."""
    portfolio = build_portfolio(ravi)
    buckets = {s.bucket for s in portfolio.slices}
    assert {"equity", "debt", "gold", "cash"} <= buckets


def test_cash_bucket_is_liquid():
    """the cash bucket must only contain truly liquid instruments."""
    from wealth_management_system.assets import ASSET_PROFILES
    from wealth_management_system.models import AssetCategory

    portfolio = build_portfolio(ravi)
    cash = next(s for s in portfolio.slices if s.bucket == "cash")
    for ac in cash.instruments:
        assert ASSET_PROFILES[ac].category == AssetCategory.CASH_AND_LIQUID
        assert ASSET_PROFILES[ac].liquidity_score >= 0.9


def test_buckets_have_instruments():
    """every bucket must recommend at least one instrument."""
    portfolio = build_portfolio(ravi)
    for s in portfolio.slices:
        assert len(s.instruments) > 0

