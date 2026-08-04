"""Market regime detection (PART 5 support).

Classifies historical return series into discrete market regimes:
bull, bear, sideways, or crisis. Regimes are used as features in the
ML pipeline, for scenario analysis and for recommendation timing.

The detector is intentionally simple and transparent: it uses rolling
mean returns and drawdown thresholds. It is a *feature* input, not a
deterministic trading signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence

import numpy as np
import pandas as pd


class MarketRegime(str, Enum):
    """Discrete market states."""

    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"


@dataclass
class RegimeDetector:
    """Detect market regimes from a return series.

    Parameters
    ----------
    rolling_window:
        Months used to compute the rolling mean return.
    bull_threshold:
        Annualised rolling return above this -> bull.
    bear_threshold:
        Annualised rolling return below this -> bear.
    crisis_drawdown:
        Drawdown below this (negative) -> crisis.
    """

    rolling_window: int = 12
    bull_threshold: float = 0.10
    bear_threshold: float = -0.05
    crisis_drawdown: float = -0.25

    def detect(self, monthly_returns: Sequence[float]) -> List[MarketRegime]:
        """Classify each month's trailing regime.

        Parameters
        ----------
        monthly_returns:
            Monthly returns (decimal, e.g. ``0.01`` for +1%).

        Returns
        -------
        List[MarketRegime]
            One regime per input month (first ``rolling_window - 1``
            months use a shorter window and are labelled sideways).
        """
        arr = np.asarray(monthly_returns, dtype=float)
        n = len(arr)
        if n == 0:
            return []
        # Cumulative wealth index for drawdowns.
        wealth = np.cumprod(1.0 + arr)
        running_max = np.maximum.accumulate(wealth)
        drawdown = wealth / running_max - 1.0

        regimes: List[MarketRegime] = []
        for i in range(n):
            window = arr[max(0, i - self.rolling_window + 1): i + 1]
            if len(window) < 3:
                regimes.append(MarketRegime.SIDEWAYS)
                continue
            annualised = float((1.0 + window.mean()) ** 12 - 1.0)
            if drawdown[i] < self.crisis_drawdown:
                regimes.append(MarketRegime.CRISIS)
            elif annualised >= self.bull_threshold:
                regimes.append(MarketRegime.BULL)
            elif annualised <= self.bear_threshold:
                regimes.append(MarketRegime.BEAR)
            else:
                regimes.append(MarketRegime.SIDEWAYS)
        return regimes

    def detect_dataframe(
        self, df: pd.DataFrame, return_col: str = "monthly_return"
    ) -> pd.DataFrame:
        """Add a ``regime`` column to a dataframe of monthly returns."""
        regimes = self.detect(df[return_col].dropna().tolist())
        out = df.copy()
        out["regime"] = regimes
        return out


def detect_regime(
    monthly_returns: Sequence[float],
    detector: Optional[RegimeDetector] = None,
) -> MarketRegime:
    """Return the *latest* regime for a return series."""
    det = detector or RegimeDetector()
    regimes = det.detect(monthly_returns)
    return regimes[-1] if regimes else MarketRegime.SIDEWAYS


def regime_from_return_series(
    monthly_returns: Sequence[float],
    detector: Optional[RegimeDetector] = None,
) -> List[str]:
    """Convenience: return regime labels as strings."""
    det = detector or RegimeDetector()
    return [r.value for r in det.detect(monthly_returns)]
