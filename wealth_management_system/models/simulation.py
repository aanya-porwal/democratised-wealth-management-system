"""Monte Carlo simulation result models.

``SimulationResult`` carries the raw simulated paths and the derived
statistics; ``SimulationStatistics`` summarises the distribution for
reporting. Plotting is deliberately a separate concern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class SimulationStatistics:
    """Summary statistics of a simulated corpus distribution.

    Attributes
    ----------
    median:
        50th percentile corpus.
    percentile_5:
        Bad-case corpus (5th percentile).
    percentile_25:
        25th percentile corpus.
    percentile_75:
        75th percentile corpus.
    percentile_95:
        Good-case corpus (95th percentile).
    worst_case:
        Minimum simulated corpus.
    best_case:
        Maximum simulated corpus.
    mean:
        Arithmetic mean corpus.
    std_dev:
        Standard deviation of the corpus.
    probability_of_success:
        Fraction of paths that reached the target.
    """

    median: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    worst_case: float
    best_case: float
    mean: float
    std_dev: float
    probability_of_success: float

    def as_dict(self) -> dict[str, float]:
        """Machine-readable snapshot of every statistic."""
        return {
            "median": round(self.median, 2),
            "percentile_5": round(self.percentile_5, 2),
            "percentile_25": round(self.percentile_25, 2),
            "percentile_75": round(self.percentile_75, 2),
            "percentile_95": round(self.percentile_95, 2),
            "worst_case": round(self.worst_case, 2),
            "best_case": round(self.best_case, 2),
            "mean": round(self.mean, 2),
            "std_dev": round(self.std_dev, 2),
            "probability_of_success": round(self.probability_of_success, 4),
        }


@dataclass
class SimulationResult:
    """The complete output of a Monte Carlo run.

    Attributes
    ----------
    statistics:
        Summary statistics of the terminal distribution.
    terminal_values:
        Raw simulated terminal corpus values (one per path).
    target_amount:
        The goal target used to compute success probability.
    monthly_investment:
        Monthly contribution used in the simulation.
    years:
        Investment horizon in years.
    mean_return:
        Expected annual return assumption.
    volatility:
        Annual volatility assumption.
    inflation:
        Annual inflation assumption.
    probabilities:
        Optional finer-grained success probabilities per year.
    """

    statistics: SimulationStatistics
    terminal_values: np.ndarray
    target_amount: float = 0.0
    monthly_investment: float = 0.0
    years: float = 0.0
    mean_return: float = 0.0
    volatility: float = 0.0
    inflation: float = 0.0
    probabilities: Optional[np.ndarray] = None

    def percentile_data(self) -> dict[str, float]:
        """Percentile breakdown for reporting and plotting."""
        return {
            "5th": round(float(np.percentile(self.terminal_values, 5)), 2),
            "25th": round(float(np.percentile(self.terminal_values, 25)), 2),
            "50th (median)": round(float(np.percentile(self.terminal_values, 50)), 2),
            "75th": round(float(np.percentile(self.terminal_values, 75)), 2),
            "95th": round(float(np.percentile(self.terminal_values, 95)), 2),
        }
