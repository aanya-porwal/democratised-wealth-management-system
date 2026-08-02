"""Optimization input/output models.

``OptimizationInput`` describes the optimisation problem (asset universe,
expected returns, covariance, constraints); ``OptimizationResult`` holds
the optimal weights and the diagnostics needed to explain them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from wealth_management_system.models import AssetClass


@dataclass
class OptimizationInput:
    """Definition of a mean-variance optimisation problem.

    Attributes
    ----------
    asset_classes:
        Ordered list of assets under consideration.
    expected_returns:
        Expected annual return per asset (same order as ``asset_classes``).
    covariance:
        Annualised covariance matrix (n x n), matching asset order.
    risk_free_rate:
        Risk-free rate used for the Sharpe-ratio objective.
    min_weights:
        Optional per-asset lower bounds. Defaults to 0.0.
    max_weights:
        Optional per-asset upper bounds. Defaults to 0.50.
    target_volatility:
        Optional target annual volatility for the portfolio.
    max_volatility:
        Hard constraint on annual portfolio volatility.
    liquidity_scores:
        Optional per-asset liquidity score (0..1) used in the penalty.
    tax_penalties:
        Optional per-asset tax drag used to steer the optimizer.
    """

    asset_classes: list[AssetClass]
    expected_returns: list[float]
    covariance: list[list[float]]
    risk_free_rate: float = 0.055
    min_weights: Optional[list[float]] = None
    max_weights: Optional[list[float]] = None
    target_volatility: Optional[float] = None
    max_volatility: float = 0.16
    liquidity_scores: Optional[list[float]] = None
    tax_penalties: Optional[list[float]] = None

    def __post_init__(self) -> None:
        """Validate dimension consistency."""
        n = len(self.asset_classes)
        if len(self.expected_returns) != n:
            raise ValueError("expected_returns must match asset_classes length")
        if len(self.covariance) != n or any(len(row) != n for row in self.covariance):
            raise ValueError("covariance must be a square matrix of size n x n")
        for field_name in ("min_weights", "max_weights", "liquidity_scores", "tax_penalties"):
            values = getattr(self, field_name)
            if values is not None and len(values) != n:
                raise ValueError(f"{field_name} must match asset_classes length")


@dataclass
class OptimizationResult:
    """Result of an optimization run.

    Attributes
    ----------
    weights:
        Optimal weight per asset (same order as input).
    expected_return:
        Expected annual return of the optimal portfolio.
    volatility:
        Annual volatility of the optimal portfolio.
    sharpe_ratio:
        Sharpe ratio of the optimal portfolio.
    feasible:
        Whether a feasible solution was found.
    method:
        Which optimizer produced the result (e.g. ``"mean_variance"``).
    message:
        Human-readable summary of the outcome.
    """

    weights: list[float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    feasible: bool
    method: str
    message: str = ""

    def as_dict(self) -> dict[str, float]:
        """Map asset index -> weight (convenience)."""
        return {f"asset_{i}": round(w, 6) for i, w in enumerate(self.weights)}
