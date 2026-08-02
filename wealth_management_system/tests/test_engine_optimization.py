"""Tests for the optimization engine (PART 7)."""

import pytest

from wealth_management_system.exceptions import OptimizationError
from wealth_management_system.models import AssetClass, OptimizationInput
from wealth_management_system.optimization import Optimizer


@pytest.fixture
def sample_input():
    """A small 3-asset optimization problem."""
    return OptimizationInput(
        asset_classes=[
            AssetClass.EQUITY_INDEX_LARGECAP,
            AssetClass.CORPORATE_BOND_FUND,
            AssetClass.GOLD_ETF,
        ],
        expected_returns=[0.12, 0.08, 0.09],
        covariance=[
            [0.0324, 0.005, 0.002],
            [0.005, 0.0064, 0.001],
            [0.002, 0.001, 0.0225],
        ],
        risk_free_rate=0.055,
        min_weights=[0.0, 0.0, 0.0],
        max_weights=[0.60, 0.60, 0.40],
        max_volatility=0.18,
    )


def test_mean_variance_weights_sum_to_one(sample_input):
    """Optimal weights must sum to 1.0 (fully invested)."""
    result = Optimizer(method="mean_variance").optimize(sample_input)
    assert abs(sum(result.weights) - 1.0) < 1e-6
    assert result.feasible is True


def test_weights_respect_bounds(sample_input):
    """Every weight must respect the min/max bounds."""
    result = Optimizer(method="mean_variance").optimize(sample_input)
    for w, lo, hi in zip(result.weights, sample_input.min_weights, sample_input.max_weights):
        assert lo - 1e-9 <= w <= hi + 1e-9


def test_volatility_constraint_respected(sample_input):
    """Portfolio volatility must not exceed the configured cap."""
    result = Optimizer(method="mean_variance").optimize(sample_input)
    assert result.volatility <= 0.18 + 1e-6


def test_returns_positive_diagnostics(sample_input):
    """Expected return, volatility and Sharpe must be present."""
    result = Optimizer(method="mean_variance").optimize(sample_input)
    assert result.expected_return > 0
    assert result.volatility > 0
    assert isinstance(result.sharpe_ratio, float)
    assert result.method == "mean_variance"


def test_unsupported_method_raises(sample_input):
    """An unknown optimization method must raise OptimizationError."""
    with pytest.raises(OptimizationError) as excinfo:
        Optimizer(method="blackbox_quantum").optimize(sample_input)
    assert excinfo.value.code == "unsupported_method"


def test_bad_covariance_raises():
    """A non-square covariance matrix must be rejected at input validation."""
    from wealth_management_system.models import AssetClass

    with pytest.raises(ValueError):
        OptimizationInput(
            asset_classes=[AssetClass.GOLD_ETF, AssetClass.PPF],
            expected_returns=[0.09, 0.071],
            covariance=[[0.0225]],
        )

