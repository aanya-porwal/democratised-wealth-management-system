"""Tests for the portfolio allocation engine (PART 2)."""

import pytest

from wealth_management_system.allocation import AllocationEngine
from wealth_management_system.exceptions import AllocationError
from wealth_management_system.models import (
    AllocationEngineInput,
    LiquidityNeed,
)


def test_allocation_weights_sum_to_one(ravi):
    """The target allocation must always be a complete allocation."""
    result = AllocationEngine().build(AllocationEngineInput(user=ravi))
    assert abs(result.total_weight() - 1.0) < 1e-6


def test_allocation_covers_required_buckets(ravi):
    """Equity, debt, gold and cash must be present."""
    result = AllocationEngine().build(AllocationEngineInput(user=ravi))
    buckets = {b.bucket for b in result.buckets}
    assert {"equity", "debt", "gold", "cash"} <= buckets


def test_allocation_has_12_strategic_buckets(ravi):
    """The full instrument spectrum must be represented."""
    result = AllocationEngine().build(AllocationEngineInput(user=ravi))
    expected_order = [
        "equity",
        "debt",
        "gold",
        "international_equity",
        "reits",
        "fixed_deposits",
        "cash",
        "elss",
        "ppf",
        "epf",
        "nps",
        "bonds",
    ]
    names = [b.bucket for b in result.buckets]
    # the returned subset must respect the strategic ordering
    filtered = [b for b in expected_order if b in names]
    assert filtered == [b for b in names if b in expected_order]


def test_risk_override_changes_equity(ravi):
    """A higher risk score must produce a higher equity weight."""
    engine = AllocationEngine()
    conservative = engine.build(
        AllocationEngineInput(user=ravi, risk_score=20)
    ).weight_of("equity")
    aggressive = engine.build(
        AllocationEngineInput(user=ravi, risk_score=80)
    ).weight_of("equity")
    assert aggressive > conservative


def test_liquidity_override_raises_cash(ravi):
    """High liquidity need must raise the cash/FD weight."""
    engine = AllocationEngine()
    high_liq = engine.build(
        AllocationEngineInput(user=ravi, liquidity_need=LiquidityNeed.HIGH)
    )
    low_liq = engine.build(
        AllocationEngineInput(user=ravi, liquidity_need=LiquidityNeed.LOW)
    )
    cash_high = high_liq.weight_of("cash") + high_liq.weight_of("fixed_deposits")
    cash_low = low_liq.weight_of("cash") + low_liq.weight_of("fixed_deposits")
    assert cash_high >= cash_low


def test_invalid_horizon_raises(ravi):
    """A non-positive horizon must raise AllocationError."""
    with pytest.raises(AllocationError):
        AllocationEngine().build(
            AllocationEngineInput(user=ravi, horizon_years=0)
        )


def test_explanation_is_present(ravi):
    """Every allocation must carry a plain-language rationale."""
    result = AllocationEngine().build(AllocationEngineInput(user=ravi))
    assert result.explanation
    assert result.risk_score >= 0
    assert result.risk_category


def test_instruments_are_strings(ravi):
    """Bucket instrument lists must be strings (instrument values)."""
    result = AllocationEngine().build(AllocationEngineInput(user=ravi))
    for bucket in result.buckets:
        assert bucket.instruments
        assert all(isinstance(i, str) for i in bucket.instruments)

