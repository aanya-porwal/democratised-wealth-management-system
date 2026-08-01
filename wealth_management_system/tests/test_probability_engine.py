"""tests for the monte carlo probability engine."""

import numpy as np

from wealth_management_system.probability_engine import (
    DEFAULT_SIMULATIONS,
    RNG_SEED,
    _simulate_paths,
    project_future_value,
    simulate_goal_probability,
)
from wealth_management_system.sample_users import ravi


def test_probability_between_zero_and_one():
    """a probability must always be a valid fraction."""
    for goal in ravi.goals:
        p = simulate_goal_probability(goal)
        assert 0.0 <= p.probability <= 1.0


def test_probability_is_deterministic():
    """same seed must give the same result every run."""
    a = simulate_goal_probability(ravi.goals[0])
    b = simulate_goal_probability(ravi.goals[0])
    assert a.probability == b.probability
    assert a.median_outcome == b.median_outcome


def test_large_contribution_hits_target():
    """a very large monthly contribution should make a small goal almost certain."""
    # build a goal we can meet easily
    from datetime import date, timedelta

    from wealth_management_system.models import (
        Goal,
        GoalPriority,
        GoalType,
    )

    easy = Goal(
        goal_type=GoalType.WEALTH_CREATION,
        priority=GoalPriority.HIGH,
        target_amount=100000,  # 1L
        target_date=date.today() + timedelta(days=5 * 365),
        current_savings_for_goal=0,
        current_monthly_contribution=50000,  # 50K/mo for 5 years = 30L
    )
    p = simulate_goal_probability(easy)
    assert p.probability > 0.9


def test_zero_contribution_zero_savings_means_failure():
    """no money in, no money out — a big goal must be nearly impossible."""
    from datetime import date, timedelta

    from wealth_management_system.models import (
        Goal,
        GoalPriority,
        GoalType,
    )

    impossible = Goal(
        goal_type=GoalType.WEALTH_CREATION,
        priority=GoalPriority.HIGH,
        target_amount=50000000,  # 5 crore
        target_date=date.today() + timedelta(days=10 * 365),
        current_savings_for_goal=0,
        current_monthly_contribution=0,
    )
    p = simulate_goal_probability(impossible)
    assert p.probability < 0.05


def test_simulated_paths_shape():
    """must produce one terminal value per simulation."""
    paths = _simulate_paths(0, 1000, 10, 0.07, 0.12, 100)
    assert paths.shape == (100,)


def test_projection_grows_with_time():
    """future value must be higher for a longer horizon."""
    short = project_future_value(100000, 5000, 5)
    long = project_future_value(100000, 5000, 15)
    assert long > short

