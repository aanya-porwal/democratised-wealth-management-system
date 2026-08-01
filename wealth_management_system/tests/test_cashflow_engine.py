"""tests for the cashflow engine."""

from wealth_management_system.cashflow_engine import (
    build_cashflow_snapshot,
    emergency_fund_allocation,
    emergency_fund_status,
    emergency_fund_target,
)
from wealth_management_system.sample_users import (
    build_all_sample_users,
    meena,
    ravi,
)


def test_monthly_surplus_matches_model():
    """surplus must equal income minus expenses."""
    cash = build_cashflow_snapshot(ravi)
    expected = ravi.financial.monthly_income - (
        ravi.financial.monthly_fixed_expenses + ravi.financial.monthly_variable_expenses
    )
    assert cash.monthly_surplus == expected


def test_discretionary_surplus_deducts_committed_sip():
    """discretionary surplus must not double-count money already committed."""
    cash = build_cashflow_snapshot(ravi)
    assert cash.discretionary_surplus == max(
        0, cash.monthly_surplus - ravi.financial.existing_monthly_sip
    )


def test_ravi_emergency_fund_is_building():
    """ravi has 1.5 months — classified as building, not ready."""
    cash = build_cashflow_snapshot(ravi)
    assert cash.emergency_fund_priority == "building"
    assert cash.emergency_fund_amount_needed > 0


def test_irregular_income_gets_bigger_buffer():
    """business owners need a thicker emergency cushion."""
    want_meena = emergency_fund_target(meena.financial)
    want_ravi = emergency_fund_target(ravi.financial)
    assert want_meena >= want_ravi


def test_emergency_fund_status_boundaries():
    """classify the three readiness states correctly."""
    assert emergency_fund_status(6, 6) == "ready"
    assert emergency_fund_status(5, 6) == "building"
    assert emergency_fund_status(0, 6) == "missing"
    assert emergency_fund_status(1, 6) == "building"


def test_emergency_fund_allocation_zero_when_ready():
    """once the fund is ready, no surplus is held back for it."""
    priya = [u for u in build_all_sample_users() if u.name == "Priya Parent"][0]
    snapshot = build_cashflow_snapshot(priya)
    assert snapshot.emergency_fund_priority == "ready"
    assert emergency_fund_allocation(priya, snapshot) == 0.0

