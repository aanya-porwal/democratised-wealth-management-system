"""Tests for the Monte Carlo simulation engine (PART 5)."""

import numpy as np
import pytest

from wealth_management_system.exceptions import SimulationError
from wealth_management_system.simulation import MonteCarloEngine



def test_run_returns_result():
    """A basic run must produce a SimulationResult."""
    result = MonteCarloEngine(simulations=2000, seed=7).run(
        expected_return=0.12,
        volatility=0.18,
        monthly_investment=10000,
        inflation=0.06,
        horizon_years=10,
        initial_corpus=100000,
        target_amount=3000000,
    )
    assert result.statistics is not None
    assert len(result.terminal_values) == 2000
    assert result.statistics.probability_of_success >= 0.0
    assert result.statistics.probability_of_success <= 1.0


def test_percentile_data():
    """percentile_data() must return the five documented keys."""
    result = MonteCarloEngine(simulations=1000, seed=1).run(
        expected_return=0.10,
        volatility=0.15,
        monthly_investment=5000,
        inflation=0.05,
        horizon_years=5,
    )
    data = result.percentile_data()
    assert set(data.keys()) == {
        "5th",
        "25th",
        "50th (median)",
        "75th",
        "95th",
    }
    assert data["5th"] <= data["50th (median)"] <= data["95th"]


def test_statistics_as_dict():
    """as_dict() on statistics renders every field."""
    result = MonteCarloEngine(simulations=800, seed=3).run(
        expected_return=0.11,
        volatility=0.20,
        monthly_investment=8000,
        inflation=0.06,
        horizon_years=8,
    )
    snapshot = result.statistics.as_dict()
    for key in (
        "median",
        "percentile_5",
        "percentile_25",
        "percentile_75",
        "percentile_95",
        "worst_case",
        "best_case",
        "mean",
        "std_dev",
        "probability_of_success",
    ):
        assert key in snapshot
    assert snapshot["worst_case"] <= snapshot["median"] <= snapshot["best_case"]


def test_probability_tracks_target():
    """A small target must raise success probability vs a huge target."""
    engine = MonteCarloEngine(simulations=4000, seed=11)
    easy = engine.run(
        expected_return=0.12,
        volatility=0.18,
        monthly_investment=50000,
        inflation=0.06,
        horizon_years=10,
        target_amount=100000,  # trivially reachable
    )
    hard = engine.run(
        expected_return=0.12,
        volatility=0.18,
        monthly_investment=50000,
        inflation=0.06,
        horizon_years=10,
        target_amount=10_000_000_000,  # unreachable
    )
    assert easy.statistics.probability_of_success > hard.statistics.probability_of_success


def test_negative_volatility_raises():
    """Negative volatility must raise SimulationError."""
    engine = MonteCarloEngine(simulations=500, seed=1)
    with pytest.raises(SimulationError):
        engine.run(
            expected_return=0.10,
            volatility=-0.05,
            monthly_investment=1000,
            inflation=0.06,
            horizon_years=10,
        )


def test_zero_horizon_raises():
    """A zero horizon must raise SimulationError."""
    engine = MonteCarloEngine(simulations=500, seed=1)
    with pytest.raises(SimulationError):
        engine.run(
            expected_return=0.10,
            volatility=0.15,
            monthly_investment=1000,
            inflation=0.06,
            horizon_years=0,
        )


def test_long_horizon_grows_corpus():
    """Median corpus must grow with the investment amount."""
    engine = MonteCarloEngine(simulations=2000, seed=5)
    low = engine.run(
        expected_return=0.12, volatility=0.18, monthly_investment=5000,
        inflation=0.06, horizon_years=10,
    ).statistics.median
    high = engine.run(
        expected_return=0.12, volatility=0.18, monthly_investment=50000,
        inflation=0.06, horizon_years=10,
    ).statistics.median
    assert high > low


def test_10000_simulations_supported():
    """The default config supports 10k+ paths (performance smoke test)."""
    result = MonteCarloEngine(simulations=10000, seed=42).run(
        expected_return=0.10,
        volatility=0.15,
        monthly_investment=10000,
        inflation=0.06,
        horizon_years=15,
    )
    assert len(result.terminal_values) == 10000
    assert result.statistics.mean > 0

