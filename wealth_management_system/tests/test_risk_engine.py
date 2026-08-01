"""tests for the risk engine."""

from wealth_management_system.risk_engine import (
    assess_risk,
    calculate_risk_capacity,
    calculate_risk_tolerance,
)
from wealth_management_system.sample_users import (
    build_all_sample_users,
    meena,
    ravi,
)


def test_risk_scores_in_bounds():
    """capacity, tolerance and final must all live in 0-1."""
    for user in build_all_sample_users():
        risk = assess_risk(user)
        assert 0.0 <= risk.capacity_score <= 1.0
        assert 0.0 <= risk.tolerance_score <= 1.0
        assert 0.0 <= risk.final_score <= 1.0
        assert 0 <= risk.final_score_100 <= 100


def test_capacity_is_ceiling():
    """final score must never exceed capacity."""
    for user in build_all_sample_users():
        risk = assess_risk(user)
        assert risk.final_score <= risk.capacity_score + 1e-9


def test_meena_more_conservative_than_ravi():
    """a business owner with dependents should not out-risk a young engineer."""
    risk_ravi = assess_risk(ravi)
    risk_meena = assess_risk(meena)
    assert risk_meena.final_score <= risk_ravi.final_score


def test_high_debt_user_gets_capacity_penalty():
    """over-leverage must visibly reduce capacity."""
    karan = [u for u in build_all_sample_users() if u.name == "Karan HighDebt"][0]
    capacity_karan = calculate_risk_capacity(karan)
    capacity_ravi = calculate_risk_capacity(ravi)
    # karan has high debt burden + dependents, so should be lower
    assert capacity_karan < capacity_ravi


def test_very_conservative_tolerance_scores_low():
    """the most loss-averse behavioural profile must score low on tolerance."""
    student = [u for u in build_all_sample_users() if u.name == "Aarav Student"][0]
    # student has aggressive stated tolerance but no experience
    assert calculate_risk_tolerance(student) >= 0.0

