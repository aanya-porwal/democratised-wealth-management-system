"""Comparison engine — compares any two or more securities.

Produces a side-by-side comparison across returns, risk, expense,
liquidity, tracking, holdings, AUM, Sharpe, Sortino, drawdown and sector
allocation, then derives per-security advantages/disadvantages and a
winner.

The winner is determined by the configured ``winner_metric_priority``:
the first metric among the priority list that is not a tie decides.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from security_selection.config import ComparisonConfig, get_config
from security_selection.models.pipeline import CandidateSecurity, ComparisonResult
from security_selection.utils.math import safe_float

logger = logging.getLogger(__name__)

_COMPARISON_METRICS: List[str] = [
    "overall_score",
    "return_1y",
    "return_3y",
    "volatility",
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
    "expense_ratio",
    "liquidity_score",
    "tracking_error",
    "aum_crore",
    "average_volume",
    "yield",
]

_METRIC_LABELS: Dict[str, str] = {
    "overall_score": "Overall Score",
    "return_1y": "1Y Return",
    "return_3y": "3Y Return",
    "volatility": "Annualized Volatility",
    "sharpe_ratio": "Sharpe Ratio",
    "sortino_ratio": "Sortino Ratio",
    "max_drawdown": "Max Drawdown",
    "expense_ratio": "Expense Ratio",
    "liquidity_score": "Liquidity Score",
    "tracking_error": "Tracking Error",
    "aum_crore": "AUM (₹ Cr)",
    "average_volume": "Avg Daily Volume",
    "yield": "Yield",
}

# lower is better for these metrics
_LOWER_IS_BETTER = {"volatility", "max_drawdown", "expense_ratio", "tracking_error"}


class ComparisonEngine:
    """Compares securities side-by-side and picks a winner."""

    def __init__(self, config: Optional[ComparisonConfig] = None) -> None:
        self._config = config or get_config().comparison

    def compare(self, securities: List[CandidateSecurity]) -> ComparisonResult:
        if len(securities) < 2:
            raise ValueError("comparison requires at least two securities")
        securities = securities[: self._config.max_securities]

        table: Dict[str, Dict[str, Any]] = {}
        for sec in securities:
            table[sec.key] = self._row(sec)

        advantages: Dict[str, List[str]] = {s.key: [] for s in securities}
        disadvantages: Dict[str, List[str]] = {s.key: [] for s in securities}

        # pairwise: record which securities beat which on each metric
        for i, a in enumerate(securities):
            for j, b in enumerate(securities):
                if i == j:
                    continue
                better = self._metric_verdict(a, b)
                for metric in better:
                    advantages[a.key].append(
                        f"{_METRIC_LABELS.get(metric, metric)} better than {b.identity.symbol}"
                    )
                    disadvantages[b.key].append(
                        f"{_METRIC_LABELS.get(metric, metric)} worse than {a.identity.symbol}"
                    )

        winner = self._winner(securities, table)
        return ComparisonResult(
            securities=securities,
            winner=winner,
            advantages=advantages,
            disadvantages=disadvantages,
            comparison_table=table,
            metric_labels=dict(_METRIC_LABELS),
        )

    # ── helpers ─────────────────────────────────────────────────────

    def _row(self, sec: CandidateSecurity) -> Dict[str, Any]:
        m = sec.metrics
        row: Dict[str, Any] = {
            "symbol": sec.identity.symbol,
            "name": sec.identity.name,
            "kind": sec.kind.value,
            "overall_score": sec.overall_score,
        }
        for metric in _COMPARISON_METRICS[1:]:
            row[metric] = safe_float(m.get(metric))
        # holdings + sectors
        row["holdings_count"] = len(sec.holdings)
        row["sectors"] = dict(sec.sector_allocations)
        return row

    def _metric_verdict(self, a: CandidateSecurity, b: CandidateSecurity) -> List[str]:
        better: List[str] = []
        for metric in _COMPARISON_METRICS:
            va = a.metrics.get(metric)
            vb = b.metrics.get(metric)
            fa, fb = safe_float(va), safe_float(vb)
            if fa is None or fb is None:
                continue
            if abs(fa - fb) < 1e-9:
                continue
            if metric == "overall_score":
                # overall already captured separately
                pass
            if metric in _LOWER_IS_BETTER:
                if fa < fb:
                    better.append(metric)
            else:
                if fa > fb:
                    better.append(metric)
        return better

    def _winner(self, securities: List[CandidateSecurity], table: Dict[str, Any]) -> str:
        # Score each security by how often it wins the priority metrics.
        priority = list(self._config.winner_metric_priority)
        scores: Dict[str, float] = {}
        for sec in securities:
            row = table[sec.key]
            total = 0.0
            for metric in priority:
                val = row.get(metric)
                f = safe_float(val)
                if f is None:
                    continue
                if metric in _LOWER_IS_BETTER:
                    rank = _rank_better(securities, metric, lower=True)
                    total += rank.get(sec.key, 0.0)
                else:
                    rank = _rank_better(securities, metric, lower=False)
                    total += rank.get(sec.key, 0.0)
            scores[sec.key] = total
        # also consider overall_score (already part of priority in default)
        winner_key = max(scores, key=lambda k: scores[k])
        for sec in securities:
            if sec.key == winner_key:
                return sec.identity.symbol
        return securities[0].identity.symbol


def _rank_better(
    securities: List[CandidateSecurity], metric: str, lower: bool
) -> Dict[str, float]:
    """Rank securities by a metric; return per-key score (1=best)."""
    values: List[tuple[float, CandidateSecurity]] = []
    for sec in securities:
        f = safe_float(sec.metrics.get(metric))
        if f is not None:
            values.append((f, sec))
    if not values:
        return {}
    values.sort(key=lambda t: t[0], reverse=not lower)
    result: Dict[str, float] = {}
    n = len(values)
    for i, (_, sec) in enumerate(values):
        result[sec.key] = 1.0 - (i / max(1, n - 1))
    return result

