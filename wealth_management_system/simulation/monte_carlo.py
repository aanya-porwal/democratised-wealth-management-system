"""Monte Carlo simulation engine.

Simulates thousands of possible futures for a growing investment
portfolio using geometric Brownian motion (lognormal returns) with
monthly contributions growing with inflation.

The engine is pure logic — it returns a :class:`SimulationResult`
containing the raw terminal values, percentile data and statistics.
Plotting is deliberately NOT here (see ``utilities.plotting``).

Vectorised with numpy: 10,000 paths × 240 months runs in well under a
second.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from wealth_management_system.config import SimulationConfig, get_config
from wealth_management_system.exceptions import SimulationError
from wealth_management_system.models.simulation import (
    SimulationResult,
    SimulationStatistics,
)
from wealth_management_system.utilities import get_logger

logger: logging.Logger = get_logger(__name__)


class MonteCarloEngine:
    """Vectorised Monte Carlo portfolio simulation.

    Parameters
    ----------
    simulations:
        Number of independent paths to simulate. Defaults to the value
        in config (10,000).
    seed:
        Random seed for reproducibility. Defaults to the config seed.
    config:
        Optional ``SimulationConfig``. Defaults to the process config.
    """

    def __init__(
        self,
        *,
        simulations: Optional[int] = None,
        seed: Optional[int] = None,
        config: Optional[SimulationConfig] = None,
    ) -> None:
        self._config = config or get_config().simulation
        self._simulations = simulations or self._config.default_simulations
        self._seed = seed if seed is not None else self._config.rng_seed

    # ── public API ──────────────────────────────────────────────────

    def run(
        self,
        *,
        expected_return: float,
        volatility: float,
        monthly_investment: float,
        inflation: float,
        horizon_years: float,
        initial_corpus: float = 0.0,
        target_amount: Optional[float] = None,
    ) -> SimulationResult:
        """Run the Monte Carlo simulation.

        Parameters
        ----------
        expected_return:
            Nominal expected annual return (e.g. 0.12 for 12%).
        volatility:
            Annualised volatility (e.g. 0.18 for 18%).
        monthly_investment:
            Monthly contribution, growing at ``inflation`` each month.
        inflation:
            Annual inflation rate used to grow the monthly contribution
            (rupees today lose purchasing power, but contributions rise
            with income).
        horizon_years:
            Investment horizon in years.
        initial_corpus:
            Starting lump sum.
        target_amount:
            Optional goal target. When provided the result includes the
            probability of reaching it.

        Returns
        -------
        SimulationResult
            Terminal values, percentile data and statistics.

        Raises
        ------
        SimulationError
            If inputs are invalid (negative volatility, no horizon, etc.)
        """
        self._validate(expected_return, volatility, monthly_investment, horizon_years)

        months = max(1, round(horizon_years * 12))
        monthly_rate = (1 + expected_return) ** (1 / 12) - 1
        monthly_vol = volatility / (12**0.5)
        monthly_inflation = (1 + inflation) ** (1 / 12) - 1

        rng = np.random.default_rng(self._seed)

        # one lognormal return per path per month
        returns = rng.lognormal(
            mean=np.log1p(monthly_rate) - 0.5 * monthly_vol**2,
            sigma=monthly_vol,
            size=(self._simulations, months),
        )

        # initial corpus grows for the full period
        lump_growth = returns.prod(axis=1)
        corpus = initial_corpus * lump_growth

        # monthly contributions, growing with inflation, deposited at end
        # of month. The contribution at month m grows for (months-m-1) months.
        contribution_growth = np.cumprod(
            np.full(months, 1 + monthly_inflation)
        ) / (1 + monthly_inflation)
        contribution_series = monthly_investment * contribution_growth

        # reverse cumulative product for per-deposit growth weights
        reversed_prod = np.flip(np.cumprod(np.flip(returns, axis=1), axis=1), axis=1)
        weights = np.ones_like(returns)
        weights[:, :-1] = reversed_prod[:, 1:]
        weights[:, -1] = 1.0

        contribution_fv = (contribution_series * weights).sum(axis=1)
        terminal = corpus + contribution_fv

        return self._build_result(
            terminal,
            target_amount=target_amount,
            expected_return=expected_return,
            volatility=volatility,
            monthly_investment=monthly_investment,
            inflation=inflation,
            horizon_years=horizon_years,
            initial_corpus=initial_corpus,
        )

    # ── internals ───────────────────────────────────────────────────

    def _validate(
        self,
        expected_return: float,
        volatility: float,
        monthly_investment: float,
        horizon_years: float,
    ) -> None:
        """Sanity-check simulation inputs."""
        if volatility < 0:
            raise SimulationError(
                "volatility cannot be negative",
                code="invalid_volatility",
                details={"volatility": volatility},
            )
        if expected_return <= -1:
            raise SimulationError(
                "expected_return must be greater than -100%",
                code="invalid_return",
                details={"expected_return": expected_return},
            )
        if horizon_years <= 0:
            raise SimulationError(
                "horizon_years must be positive",
                code="invalid_horizon",
                details={"horizon_years": horizon_years},
            )
        if monthly_investment < 0:
            raise SimulationError(
                "monthly_investment cannot be negative",
                code="invalid_investment",
                details={"monthly_investment": monthly_investment},
            )

    def _build_result(
        self,
        terminal: np.ndarray,
        *,
        target_amount: Optional[float],
        expected_return: float,
        volatility: float,
        monthly_investment: float,
        inflation: float,
        horizon_years: float,
        initial_corpus: float,
    ) -> SimulationResult:
        """Assemble the result object from raw terminal values."""
        probability = (
            float(np.mean(terminal >= target_amount))
            if target_amount is not None
            else 0.0
        )

        statistics = SimulationStatistics(
            median=float(np.median(terminal)),
            percentile_5=float(np.percentile(terminal, 5)),
            percentile_25=float(np.percentile(terminal, 25)),
            percentile_75=float(np.percentile(terminal, 75)),
            percentile_95=float(np.percentile(terminal, 95)),
            worst_case=float(terminal.min()),
            best_case=float(terminal.max()),
            mean=float(terminal.mean()),
            std_dev=float(terminal.std()),
            probability_of_success=probability,
        )

        return SimulationResult(
            statistics=statistics,
            terminal_values=terminal,
            target_amount=target_amount if target_amount is not None else 0.0,
            monthly_investment=monthly_investment,
            years=horizon_years,
            mean_return=expected_return,
            volatility=volatility,
            inflation=inflation,
        )
