"""tests for the financial health engine."""

from wealth_management_system.health_engine import (
    EF_BUILDING_CAP,
    EF_MISSING_CAP,
    assess_health,
)
from wealth_management_system.sample_users import (
    build_all_sample_users,
    ravi,
)

# user with a complete emergency fund
PRIYA = [u for u in build_all_sample_users() if u.name == "Priya Parent"][0]


def test_health_score_in_range():
    """score must always be within 0-100."""
    for user in build_all_sample_users():
        health = assess_health(user)
        assert 0 <= health.score <= 100


def test_emergency_fund_acts_as_grade_ceiling():
    """a user with a partial buffer cannot score above the building cap."""
    health = assess_health(ravi)
    assert health.score <= EF_BUILDING_CAP
    assert health.grade in ("good", "fair", "poor", "critical")


def test_missing_emergency_fund_caps_at_poor():
    """no buffer means the grade can never reach excellent/good."""
    # high-debt user has only 0.5 months
    karan = [u for u in build_all_sample_users() if u.name == "Karan HighDebt"][0]
    health = assess_health(karan)
    assert health.score <= EF_MISSING_CAP
    assert health.grade in ("poor", "critical")


def test_complete_emergency_fund_allows_excellent():
    """a user with a full buffer can reach the top grade."""
    health = assess_health(PRIYA)
    assert health.grade == "excellent"
    assert health.score >= 80


def test_signals_are_plain_language():
    """every signal must read like a person, not a dataframe."""
    health = assess_health(ravi)
    for s in health.signals:
        assert len(s.message) > 10  # no empty or one-word messages
        assert s.severity in ("critical", "warning", "good")


def test_critical_signals_only_returns_critical():
    """helper must filter the list to critical severities."""
    health = assess_health(ravi)
    assert all(s.severity == "critical" for s in health.critical_signals())

