"""Mean-variance portfolio optimization engine.

Implements Markowitz mean-variance optimization with:

* a risk constraint (max portfolio volatility)
* minimum / maximum allocation bounds per asset
* an optional liquidity penalty so illiquid assets are down-weighted
* optional per-asset tax drag used to adjust expected returns

The solver uses ``scipy.optimize.minimize`` with an SLSQP/QP-style
objective — maximize Sharpe ratio (or minimize variance when a target
volatility cap is set) subject to the constraints.

Design notes
------------
* ``Optimizer`` is a thin dispatcher; ``MeanVarianceOptimizer`` is the
  concrete strategy. Future algorithms inherit/implement the same
  ``optimize`` signature so the public API never changes.
* The covariance matrix is assumed to be annualised and positive
  semi-definite; no estimation is done here — inputs come from the
  caller (or the assets database).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
from scipy.optimize import minimize

from wealth_management_system.config import OptimizationConfig, get_config
from wealth_management_system.exceptions import OptimizationError
from wealth_management_system.models import AssetClass, OptimizationInput, OptimizationResult
from wealth_management_system.utilities import get_logger

logger: logging.Logger = get_logger(__name__)


class Optimizer:
    """Dispatcher for portfolio optimization strategies.

    Parameters
    ----------
    method:
        Optimization method. Currently supports ``"mean_variance"``.
        Unknown methods raise :class:`OptimizationError`.
    config:
        Optional ``OptimizationConfig``. Defaults to the process-wide
        configuration.
    """

    def __init__(
        self,
        method: str = "mean_variance",
        config: Optional[OptimizationConfig] = None,
    ) -> None:
        self._method = method
        self._config = config or get_config().optimization
        self._strategies: Dict[str, "MeanVarianceOptimizer"] = {
            "mean_variance": MeanVarianceOptimizer(config=self._config),
        }

    def optimize(self, input_data: OptimizationInput) -> OptimizationResult:
        """Run the selected optimization strategy.

        Parameters
        ----------
        input_data:
            The optimization problem definition.

        Returns
        -------
        OptimizationResult
            The optimal allocation and diagnostics.

        Raises
        ------
        OptimizationError
            If the method is unsupported.
        """
        strategy = self._strategies.get(self._method)
        if strategy is None:
            raise OptimizationError(
                f"unsupported optimization method: {self._method}",
                code="unsupported_method",
                details={"method": self._method},
            )
        return strategy.optimize(input_data)


class MeanVarianceOptimizer:
    """Markowitz mean-variance optimizer.

    Parameters
    ----------
    config:
        Optional ``OptimizationConfig`` for defaults like the risk-free
        rate and default max-weight cap.
    """

    def __init__(self, config: Optional[OptimizationConfig] = None) -> None:
        self._config = config or get_config().optimization

    # ── public API ──────────────────────────────────────────────────

    def optimize(self, input_data: OptimizationInput) -> OptimizationResult:
        """Solve the mean-variance optimization problem.

        Parameters
        ----------
        input_data:
            Asset universe, expected returns, covariance, bounds and
            constraints.

        Returns
        -------
        OptimizationResult
            The optimal weights plus the return/risk/Sharpe diagnostics.

        Raises
        ------
        OptimizationError
            If inputs are inconsistent or the solver fails.
        """
        returns = np.asarray(input_data.expected_returns, dtype=float)
        cov = np.asarray(input_data.covariance, dtype=float)
        n = len(input_data.asset_classes)

        if cov.shape != (n, n):
            raise OptimizationError(
                "covariance must be n x n matching asset_classes",
                code="bad_covariance",
                details={"n": n, "cov_shape": cov.shape},
            )

        min_weight = np.asarray(
            input_data.min_weights
            if input_data.min_weights is not None
            else [0.0] * n,
            dtype=float,
        )
        max_weight = np.asarray(
            input_data.max_weights
            if input_data.max_weights is not None
            else [self._config.max_allocation] * n,
            dtype=float,
        )
        if len(min_weight) != n or len(max_weight) != n:
            raise OptimizationError(
                "min/max weight arrays must match asset count",
                code="bad_bounds",
                details={"n": n},
            )

        # Optional tax drag adjusts the expected return per asset
        if input_data.tax_penalties is not None:
            penalties = np.asarray(input_data.tax_penalties, dtype=float)
            returns = returns - penalties

        liquidity = input_data.liquidity_scores
        risk_free = input_data.risk_free_rate

        # objective: maximize Sharpe, or minimize variance if target vol set
        target_vol = input_data.target_volatility
        max_vol = input_data.max_volatility or self._config.max_volatility

        def objective(weights: np.ndarray) -> float:
            """Objective to minimize: negative Sharpe (or variance)."""
            port_ret = float(weights @ returns)
            port_var = float(weights @ cov @ weights)
            port_vol = np.sqrt(max(port_var, 0.0))
            if target_vol is not None and target_vol > 0:
                # minimize deviation from target volatility with return bonus
                return (port_vol - target_vol) ** 2 + 0.1 * max(0.0, 0.0 - port_ret)
            # maximize Sharpe ratio -> minimize -(Sharpe)
            if port_vol > 1e-12:
                return -(port_ret - risk_free) / port_vol
            return 0.0  # degenerate

        # liquidity penalty added to objective (small)
        def penalised_objective(weights: np.ndarray) -> float:
            base = objective(weights)
            if liquidity is None:
                return base
            liq = np.asarray(liquidity, dtype=float)
            penalty = 0.05 * float(np.sum((1.0 - liq) * weights))
            return base + penalty

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        ]
        if max_vol is not None and max_vol > 0:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: max_vol - np.sqrt(max(float(w @ cov @ w), 0.0)),
                }
            )

        bounds = [(lo, hi) for lo, hi in zip(min_weight, max_weight)]
        x0 = np.full(n, 1.0 / n)

        try:
            result = minimize(
                penalised_objective,
                x0,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 1000, "ftol": 1e-10},
            )
        except Exception as exc:  # scipy can raise on malformed input
            raise OptimizationError(
                f"solver failed: {exc}",
                code="solver_failure",
                details={"n": n},
            ) from exc

        if not result.success:
            logger.warning("Optimization did not fully converge: %s", result.message)
            # fall back to the best feasible point the solver found
            if not np.allclose(result.x, x0) and np.isclose(np.sum(result.x), 1.0, atol=0.05):
                feasible = True
            else:
                feasible = False
        else:
            feasible = True

        weights = np.clip(result.x, 0.0, None)
        # normalize to sum 1.0 for safety
        total = weights.sum()
        if total > 0:
            weights = weights / total

        port_ret = float(weights @ returns)
        port_var = float(weights @ cov @ weights)
        port_vol = np.sqrt(max(port_var, 0.0))
        if port_vol > 1e-12:
            sharpe = (port_ret - risk_free) / port_vol
        else:
            sharpe = 0.0

        return OptimizationResult(
            weights=[round(float(w), 6) for w in weights],
            expected_return=round(port_ret, 6),
            volatility=round(float(port_vol), 6),
            sharpe_ratio=round(float(sharpe), 6),
            feasible=feasible,
            method="mean_variance",
            message=str(result.message) if hasattr(result, "message") else "",
        )

