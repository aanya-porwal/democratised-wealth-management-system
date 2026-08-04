"""Deterministic analytics over a digital twin's financial state.

These are lightweight summary metrics used to feed the ML layer and
monitoring. They never replace the authoritative deterministic engine
calculations (``wealth_management_system`` / ``engine``); they only
*derive* convenient aggregates from a twin's current state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ml.digital_twin.models.twin import DigitalTwin, LifeSnapshot


def compute_financial_ratios(twin: DigitalTwin) -> Dict[str, float]:
    """Compute a set of standard financial ratios for a twin.

    Returns a dict of ratios (all deterministic, guarded against
    division by zero).
    """
    profile = twin.profile
    income = profile.monthly_income
    expenses = profile.monthly_expenses
    savings = profile.monthly_savings
    debt = twin.total_debt
    emi = profile.monthly_emi_total
    portfolio = twin.portfolio.total_value
    net_worth = twin.net_worth

    def _ratio(numerator: float, denominator: float) -> float:
        return numerator / denominator if denominator else 0.0

    return {
        "savings_rate": _ratio(savings, income) if income else 0.0,
        "expense_to_income": _ratio(expenses, income),
        "debt_to_income": _ratio(emi, income),
        "debt_to_net_worth": _ratio(debt, net_worth) if net_worth else 0.0,
        "portfolio_to_net_worth": _ratio(portfolio, net_worth) if net_worth else 0.0,
        "emergency_fund_months": twin.emergency_fund_months,
        "liquidity_ratio": _ratio(profile.emergency_fund_months * expenses, expenses),
        "net_worth": net_worth,
    }


def compute_financial_health(twin: DigitalTwin) -> float:
    """Compute a 0..100 financial health score for a twin.

    A simple, transparent composite of savings rate, debt load and
    emergency fund adequacy. This is a *summary* metric for ML/monitoring,
    not a replacement for the engine's ``HealthScoreEngine``.
    """
    ratios = compute_financial_ratios(twin)
    savings_rate = min(ratios["savings_rate"] / 0.30, 1.0)  # 30% target
    debt_ok = max(0.0, 1.0 - ratios["debt_to_income"] / 0.50)  # 50% cap
    emergency_ok = min(ratios["emergency_fund_months"] / 6.0, 1.0)  # 6 months target
    score = 100.0 * (0.4 * savings_rate + 0.35 * debt_ok + 0.25 * emergency_ok)
    return round(max(0.0, min(100.0, score)), 2)


def build_snapshot(twin: DigitalTwin, as_of: datetime) -> LifeSnapshot:
    """Build a :class:`LifeSnapshot` reflecting a twin's state at a time."""
    health = compute_financial_health(twin)
    return LifeSnapshot(
        twin_id=twin.twin_id,
        timestamp=as_of,
        age=twin.profile.age,
        monthly_income=twin.profile.monthly_income,
        monthly_expenses=twin.profile.monthly_expenses,
        monthly_savings=twin.profile.monthly_savings,
        net_worth=twin.net_worth,
        portfolio=twin.portfolio,
        goals=list(twin.goals),
        total_debt=twin.total_debt,
        emergency_fund_months=twin.emergency_fund_months,
        risk_profile=twin.risk_profile,
        behaviour=twin.behaviour,
        financial_health_score=health,
    )


def net_worth_series(twin: DigitalTwin) -> List[Dict[str, object]]:
    """Return the net worth history as a list of {timestamp, net_worth}."""
    return list(twin.net_worth_history)

def health_series(twin: DigitalTwin) -> List[Dict[str, object]]:
    """Return the financial health history as a list of {timestamp, score}."""
    return list(twin.financial_health_history)
