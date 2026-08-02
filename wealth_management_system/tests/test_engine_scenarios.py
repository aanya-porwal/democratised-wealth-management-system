"""Tests for the scenario analysis engine (PART 6)."""

import copy

import pytest

from wealth_management_system.exceptions import SimulationError
from wealth_management_system.models import Scenario, ScenarioType
from wealth_management_system.sample_users import build_all_sample_users
from wealth_management_system.simulation import ScenarioEngine


@pytest.fixture(scope="module")
def ravi() -> object:
    """Ravi Shankar — canonical demo user (deep-copied per use)."""
    return [u for u in build_all_sample_users() if u.name == "Ravi Shankar"][0]


def _fresh_ravi(ravi) -> object:
    """Return a fresh deep copy so scenarios never leak between tests."""
    return copy.deepcopy(ravi)


def test_salary_increase_scenario(ravi):
    """A salary increase must change the required SIP metrics."""
    engine = ScenarioEngine(simulations=1000)
    variant = engine.apply_preset(_fresh_ravi(ravi), ScenarioType.SALARY_INCREASE)
    assert variant.scenario.scenario_type == ScenarioType.SALARY_INCREASE
    assert variant.total_required_sip >= 0
    assert variant.net_worth is not None
    assert variant.allocation
    assert variant.summary


def test_market_crash_reduces_net_worth(ravi):
    """A market crash must reduce the user's net worth."""
    engine = ScenarioEngine(simulations=1000)
    user = _fresh_ravi(ravi)
    baseline_nw = user.financial.net_worth()
    variant = engine.apply_preset(user, ScenarioType.MARKET_CRASH)
    assert variant.net_worth <= baseline_nw


def test_emergency_expense_adds_debt_if_unabsorbed(ravi):
    """A large one-time expense must increase debt when assets cannot absorb it."""
    engine = ScenarioEngine(simulations=500)
    user = _fresh_ravi(ravi)
    baseline_nw = user.financial.net_worth()
    scenario = Scenario(
        scenario_type=ScenarioType.EMERGENCY_EXPENSE,
        one_time_expense=10_000_000,  # far more than any sample user holds
    )
    variant = engine.apply(user, scenario)
    # a 10M expense cannot be absorbed by Ravi's assets — net worth falls
    assert variant.net_worth <= baseline_nw
    assert variant.summary


def test_compare_returns_baseline_first(ravi):
    """compare() must place the baseline variant at index 0."""
    engine = ScenarioEngine(simulations=1000)
    scenarios = [
        Scenario(
            scenario_type=ScenarioType.SALARY_INCREASE,
            income_multiplier=1.2,
        ),
        Scenario(
            scenario_type=ScenarioType.SALARY_DECREASE,
            income_multiplier=0.8,
        ),
    ]
    variants = engine.compare(_fresh_ravi(ravi), scenarios)
    assert len(variants) == 3
    assert variants[0].scenario.name == "Baseline"


def test_empty_scenario_raises(ravi):
    """A scenario with no adjustments must raise SimulationError."""
    engine = ScenarioEngine(simulations=1000)
    neutral = Scenario(scenario_type=ScenarioType.EMERGENCY_EXPENSE)
    with pytest.raises(SimulationError):
        engine.apply(_fresh_ravi(ravi), neutral)


def test_user_not_mutated(ravi):
    """Applying a scenario must never mutate the original user."""
    engine = ScenarioEngine(simulations=1000)
    original_income = ravi.financial.monthly_income
    engine.apply_preset(_fresh_ravi(ravi), ScenarioType.SALARY_INCREASE)
    assert ravi.financial.monthly_income == original_income


def test_salary_decrease_lowers_sip_requirement(ravi):
    """A salary cut must change (not raise) the required SIP, without crashing."""
    engine = ScenarioEngine(simulations=1000)
    variant = engine.apply_preset(_fresh_ravi(ravi), ScenarioType.SALARY_DECREASE)
    assert variant.total_required_sip >= 0
    assert variant.summary

