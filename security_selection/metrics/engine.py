"""Metrics engine.

Computes every derivable statistic from a security's historical series
and snapshot. The engine is asset-class agnostic: it operates on price
or NAV series plus optional benchmark series.

Design rules
------------
* Derive from available history whenever mathematically possible.
* If a metric cannot be derived reliably, return it in the ``unavailable``
  dict with a human-readable reason — never fabricate a value.
* All numbers are plain floats; pandas/numpy stay inside this module.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from security_selection.models.data import HistoricalSeries, MetricValue, SecurityIdentity
from security_selection.utils.returns import (
    annualized_return,
    information_ratio,
    max_drawdown,
    rolling_returns,
    sharpe_ratio,
    sortino_ratio,
    tracking_error,
    treynor_ratio,
)

logger = logging.getLogger(__name__)

# metrics every evaluator can produce; derived where possible
COMMON_METRICS = [
    "return_1m",
    "return_3m",
    "return_6m",
    "return_1y",
    "return_3y",
    "return_5y",
    "return_inception",
    "cagr",
    "rolling_return_1y",
    "volatility",
    "sharpe_ratio",
    "sortino_ratio",
    "treynor_ratio",
    "information_ratio",
    "max_drawdown",
    "tracking_error",
    "tracking_difference",
    "current_price",
    "nav",
    "expense_ratio",
    "exit_load",
    "aum_crore",
    "average_volume",
    "market_cap",
    "dividend_yield",
    "yield",
    "modified_duration",
    "maturity_years",
    "credit_rating",
    "benchmark",
    "fund_house",
    "inception_date",
    "age_years",
    "pe_ratio",
    "pb_ratio",
    "return_on_equity",
    "debt_to_equity",
]


class MetricsEngine:
    """Computes the metric dictionary for a candidate security."""

    def __init__(self, risk_free_rate: float = 0.055) -> None:
        self._rf = risk_free_rate

    # ── public API ──────────────────────────────────────────────────

    def compute(
        self,
        identity: SecurityIdentity,
        history: HistoricalSeries | None,
        snapshot: Any | None = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> tuple[Dict[str, Any], Dict[str, str]]:
        """Compute metrics and a map of unavailable metrics -> reasons.

        Returns
        -------
        (metrics, unavailable)
        """
        extra = extra or {}
        metrics: Dict[str, Any] = {}
        unavailable: Dict[str, str] = {}

        series = [p.value for p in history.points] if history and history.points else []
        bench = [p.value for p in history.benchmark] if history and history.benchmark else []

        # ── returns ────────────────────────────────────────────────
        if len(series) >= 2:
            n = len(series)
            self._period_returns(series, n, metrics, unavailable)
            metrics["return_inception"] = annualized_return(series)
            metrics["cagr"] = annualized_return(series)
        else:
            for name in ("return_1m", "return_3m", "return_6m", "return_1y",
                         "return_3y", "return_5y", "return_inception", "cagr"):
                unavailable[name] = "insufficient history (fewer than 2 points)"

        # ── risk metrics ───────────────────────────────────────────
        if len(series) >= 10:
            metrics["volatility"] = annualized_volatility(series)
            metrics["sharpe_ratio"] = sharpe_ratio(series, self._rf)
            metrics["sortino_ratio"] = sortino_ratio(series, self._rf)
            metrics["max_drawdown"] = max_drawdown(series)
            if len(bench) >= 10:
                metrics["treynor_ratio"] = treynor_ratio(series, bench, self._rf)
                metrics["tracking_error"] = tracking_error(series, bench)
                metrics["information_ratio"] = information_ratio(series, bench)
                metrics["tracking_difference"] = tracking_difference(series, bench)
            else:
                for name in ("treynor_ratio", "tracking_error",
                             "information_ratio", "tracking_difference"):
                    unavailable[name] = "no benchmark series available"
            r1y = rolling_returns(series, 252)
            metrics["rolling_return_1y"] = r1y[-1] if r1y else None
            if not r1y:
                unavailable["rolling_return_1y"] = "insufficient history for 1y rolling window"
        else:
            for name in ("volatility", "sharpe_ratio", "sortino_ratio",
                         "max_drawdown", "treynor_ratio", "tracking_error",
                         "information_ratio", "tracking_difference", "rolling_return_1y"):
                unavailable[name] = "insufficient history (fewer than 10 points)"

        # ── snapshot metrics ───────────────────────────────────────
        if snapshot is not None:
            price = getattr(snapshot, "price", None)
            metrics["current_price"] = price
            metrics["nav"] = getattr(snapshot, "nav", None)
            metrics["average_volume"] = getattr(snapshot, "average_volume", None)
            metrics["market_cap"] = getattr(snapshot, "market_cap", None)
            metrics["aum_crore"] = getattr(snapshot, "aum", None)
            if getattr(snapshot, "volume", None) is not None and \
                    getattr(snapshot, "average_volume", None) is None:
                metrics["average_volume"] = snapshot.volume
        else:
            unavailable["current_price"] = "no market snapshot"
            unavailable["nav"] = "no market snapshot"

        # ── provider-supplied extra metrics ────────────────────────
        for name, value in extra.items():
            if name in metrics:
                continue  # derived value wins
            metrics[name] = value

        # ── consistency / derived age ──────────────────────────────
        if history and history.points:
            first = history.points[0].date
            metrics["inception_date"] = first.isoformat()
            metrics["age_years"] = round((date.today() - first).days / 365.25, 2)
        else:
            unavailable["inception_date"] = "no history for inception date"
            unavailable["age_years"] = "no history for age"

        return metrics, unavailable

    # ── helpers ────────────────────────────────────────────────────

    def _period_returns(
        self,
        series: List[float],
        n: int,
        metrics: Dict[str, Any],
        unavailable: Dict[str, str],
    ) -> None:
        """Compute trailing-period annualized returns."""
        periods = {
            "return_1m": 21,
            "return_3m": 63,
            "return_6m": 126,
            "return_1y": 252,
            "return_3y": 756,
            "return_5y": 1260,
        }
        for name, window in periods.items():
            if n >= window + 1:
                sub = series[-window - 1:]
                metrics[name] = annualized_return(sub, years=window / 252)
            else:
                unavailable[name] = f"insufficient history for {name} window"


def annualized_volatility(series: List[float]) -> float | None:
    """Annualized volatility from daily returns."""
    import math

    from security_selection.utils.returns import to_returns

    rets = to_returns(series)
    if len(rets) < 2:
        return None
    std = rets.std(ddof=1)
    if math.isnan(std):
        return None
    return float(std * math.sqrt(252))


def tracking_difference(series: List[float], bench: List[float]) -> float | None:
    """Annualized return difference vs benchmark (simple TD)."""
    n = min(len(series), len(bench))
    if n < 2:
        return None
    sr = annualized_return(series[-n:])
    br = annualized_return(bench[-n:])
    if sr is None or br is None:
        return None
    return sr - br


# convenience helpers for evaluators
def metric_row(metrics: Dict[str, Any], unavailable: Dict[str, str]) -> List[MetricValue]:
    """Flatten metrics + unavailable into ``MetricValue`` rows."""
    rows: List[MetricValue] = []
    for name in COMMON_METRICS:
        if name in metrics:
            value = metrics[name]
            if value is None:
                rows.append(MetricValue.unavailable(name, "metric value is null"))
            else:
                rows.append(MetricValue(name=name, value=float(value) if isinstance(value, (int, float)) else value))
        elif name in unavailable:
            rows.append(MetricValue.unavailable(name, unavailable[name]))
    return rows

