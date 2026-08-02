"""Return and risk statistics derived from historical price/NAV series.

Every function derives its statistic from the supplied series using
numpy/pandas. When a statistic cannot be derived reliably, the caller
decides whether to surface ``None`` with an explanation — these functions
never fabricate values.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
import pandas as pd

TRADING_DAYS = 252

__all__ = [
    "TRADING_DAYS",
    "to_returns",
    "total_return",
    "cagr",
    "annualized_return",
    "daily_to_annual_volatility",
    "rolling_returns",
    "max_drawdown",
    "sharpe_ratio",
    "sortino_ratio",
    "treynor_ratio",
    "tracking_error",
    "information_ratio",
]


def to_returns(values: Sequence[float]) -> np.ndarray:
    """Daily simple returns as a numpy array (drops the first NaN)."""
    arr = np.asarray(values, dtype=float)
    if len(arr) < 2:
        return np.array([], dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rets = np.diff(arr) / arr[:-1]
    return rets[~np.isnan(rets)]


def total_return(values: Sequence[float]) -> float | None:
    """Total simple return over the full series."""
    if not values or len(values) < 2:
        return None
    first, last = values[0], values[-1]
    if first == 0:
        return None
    return last / first - 1.0


def annualized_return(values: Sequence[float], years: float | None = None) -> float | None:
    """Annualized return (CAGR) over the series.

    ``years`` may be supplied directly; otherwise derived from the number
    of trading points.
    """
    total = total_return(values)
    if total is None:
        return None
    if years is None:
        years = len(values) / TRADING_DAYS
    if years <= 0:
        return None
    return (1.0 + total) ** (1.0 / years) - 1.0


def cagr(values: Sequence[float], years: float | None = None) -> float | None:
    """Alias for :func:`annualized_return`."""
    return annualized_return(values, years)


def daily_to_annual_volatility(daily_std: float, periods: int = TRADING_DAYS) -> float | None:
    """Scale daily volatility to annualized volatility."""
    if daily_std is None or math.isnan(daily_std):
        return None
    return float(daily_std * math.sqrt(periods))


def rolling_returns(values: Sequence[float], window: int) -> list[float] | None:
    """Rolling (overlapping) period returns for the given window (in points)."""
    if not values or len(values) < window + 1:
        return None
    series = pd.Series(values, dtype=float)
    rolled = series.pct_change(window)
    out = [v for v in rolled.tolist() if v == v and v is not None]
    return out if out else None


def max_drawdown(values: Sequence[float]) -> float | None:
    """Maximum peak-to-trough drawdown as a negative fraction."""
    if not values or len(values) < 2:
        return None
    series = pd.Series(values, dtype=float)
    running_max = series.cummax()
    drawdowns = series / running_max - 1.0
    mdd = float(drawdowns.min())
    return mdd if mdd == mdd else None


def sharpe_ratio(
    values: Sequence[float],
    risk_free_rate: float = 0.055,
    periods: int = TRADING_DAYS,
) -> float | None:
    """Annualized Sharpe ratio from daily returns."""
    rets = to_returns(values)
    if len(rets) < 2:
        return None
    std = rets.std(ddof=1)
    if std == 0 or math.isnan(std):
        return None
    daily_rf = risk_free_rate / periods
    excess = rets.mean() - daily_rf
    return float(excess / std * math.sqrt(periods))


def sortino_ratio(
    values: Sequence[float],
    risk_free_rate: float = 0.055,
    periods: int = TRADING_DAYS,
) -> float | None:
    """Annualized Sortino ratio (downside deviation denominator)."""
    rets = to_returns(values)
    if len(rets) < 2:
        return None
    downside = rets[rets < 0]
    if len(downside) == 0:
        return None
    downside_std = downside.std(ddof=1)
    if downside_std == 0 or math.isnan(downside_std):
        return None
    daily_rf = risk_free_rate / periods
    excess = rets.mean() - daily_rf
    return float(excess / downside_std * math.sqrt(periods))


def treynor_ratio(
    values: Sequence[float],
    benchmark_values: Sequence[float] | None,
    risk_free_rate: float = 0.055,
    periods: int = TRADING_DAYS,
) -> float | None:
    """Annualized Treynor ratio = excess return / beta.

    Beta is computed against the benchmark series when available; without
    a benchmark the ratio cannot be derived (returns ``None``).
    """
    if benchmark_values is None or len(benchmark_values) < 2:
        return None
    rets = to_returns(values)
    bench_rets = to_returns(benchmark_values)
    n = min(len(rets), len(bench_rets))
    if n < 2:
        return None
    rets, bench = rets[:n], bench_rets[:n]
    var_bench = bench.var(ddof=1)
    if var_bench == 0 or math.isnan(var_bench):
        return None
    beta = float(np.cov(rets, bench, ddof=1)[0, 1] / var_bench)
    if beta == 0:
        return None
    daily_rf = risk_free_rate / periods
    excess = rets.mean() - daily_rf
    return float(excess / beta * math.sqrt(periods))


def tracking_error(
    values: Sequence[float],
    benchmark_values: Sequence[float],
    periods: int = TRADING_DAYS,
) -> float | None:
    """Annualized tracking error vs a benchmark series."""
    if benchmark_values is None or len(benchmark_values) < 2:
        return None
    rets = to_returns(values)
    bench_rets = to_returns(benchmark_values)
    n = min(len(rets), len(bench_rets))
    if n < 2:
        return None
    diff = rets[:n] - bench_rets[:n]
    std = diff.std(ddof=1)
    if math.isnan(std):
        return None
    return float(std * math.sqrt(periods))


def information_ratio(
    values: Sequence[float],
    benchmark_values: Sequence[float],
    periods: int = TRADING_DAYS,
) -> float | None:
    """Annualized information ratio = active return / tracking error."""
    te = tracking_error(values, benchmark_values, periods)
    if te is None or te == 0:
        return None
    rets = to_returns(values)
    bench_rets = to_returns(benchmark_values)
    n = min(len(rets), len(bench_rets))
    if n < 2:
        return None
    active = (rets[:n] - bench_rets[:n]).mean()
    return float(active / te * math.sqrt(periods))

