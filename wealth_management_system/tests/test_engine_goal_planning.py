"""Tests for the production goal planning engine (PART 1)."""

from datetime import date, timedelta

import pytest

from wealth_management_system.exceptions import GoalError
from wealth_management_system.goals import GoalEngine
from wealth_management_system.models import (
    Goal,
    GoalPriority,
    GoalType,
    GoalVerdict,
)


def _make_goal(**kwargs):
    return Goal(
        goal_type=kwargs.pop("goal_type", GoalType.WEALTH_CREATION),
        priority=kwargs.pop("priority", GoalPriority.HIGH),
        target_amount=kwargs.pop("target_amount", 1000000),
        target_date=kwargs.pop("target_date", date.today() + timedelta(days=10 * 365)),
        current_savings_for_goal=kwargs.pop("current_savings_for_goal", 0.0),
        current_monthly_contribution=kwargs.pop("current_monthly_contribution", 0.0),
        notes=kwargs.pop("notes", ""),
        **kwargs,
    )


def test_goal_analysis_has_all_required_fields(ravi):
    """Every business field must be present on the analysis."""
    engine = GoalEngine(simulations=1000)
    analysis = engine.analyse(ravi.goals[0])

    assert analysis.name
    assert analysis.goal_type
    assert analysis.priority
    assert analysis.current_amount >= 0
    assert analysis.target_amount > 0
    assert analysis.target_date is not None
    assert analysis.years_remaining > 0
    assert analysis.inflation_rate >= 0
    assert analysis.expected_return >= 0
    assert analysis.inflation_adjusted_target > 0
    assert analysis.future_value >= 0
    assert analysis.required_sip >= 0
    assert analysis.remaining_gap >= 0
    assert analysis.probability_of_success is not None


def test_goal_progress_under_control():
    """Progress must be a fraction between 0 and 1."""
    goal = _make_goal(current_savings_for_goal=500000)
    analysis = GoalEngine(simulations=1000).analyse(goal)
    assert 0.0 <= analysis.current_progress <= 1.0


def test_inflation_adjusts_target():
    """An inflation-linked goal must have a higher future target."""
    goal = _make_goal(
        goal_type=GoalType.EDUCATION_CHILD,
        target_amount=1000000,
        target_date=date.today() + timedelta(days=10 * 365),
    )
    analysis = GoalEngine(simulations=1000).analyse(goal)
    assert analysis.inflation_adjusted_target >= analysis.target_amount


def test_required_sip_rises_with_target():
    """A bigger target needs a bigger SIP."""
    engine = GoalEngine(simulations=1000)
    small = engine.analyse(_make_goal(target_amount=500000))
    big = engine.analyse(_make_goal(target_amount=5000000))
    assert big.required_sip > small.required_sip


def test_analyse_all_covers_every_goal(ravi):
    """analyse_all must return one result per goal."""
    result = GoalEngine(simulations=1000).analyse_all(ravi)
    assert len(result.goals) == len(ravi.goals)
    assert result.total_required_sip() >= 0
    assert result.total_remaining_gap() >= 0


def test_goal_without_date_raises():
    """A goal without a target date is invalid."""
    goal = _make_goal(target_date=None)
    with pytest.raises(GoalError):
        GoalEngine(simulations=1000).analyse(goal)


def test_goal_zero_target_raises():
    """A goal with a non-positive target is invalid."""
    goal = _make_goal(target_amount=0)
    with pytest.raises(GoalError):
        GoalEngine(simulations=1000).analyse(goal)


def test_verdict_is_enum():
    """The verdict must be one of the GoalVerdict values."""
    engine = GoalEngine(simulations=1000)
    analysis = engine.analyse(
        _make_goal(
            goal_type=GoalType.EMERGENCY_FUND,
            current_savings_for_goal=10000,
            current_monthly_contribution=5000,
            target_amount=50000,
            target_date=date.today() + timedelta(days=2 * 365),
        )
    )
    assert isinstance(analysis.verdict, GoalVerdict)

