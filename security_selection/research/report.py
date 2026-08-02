"""Research report generator.

Produces the institutional-quality research report covering:
universe size, filtered universe, ranking, metrics table, factor scores,
strengths, weaknesses, recommendation, alternatives, risk summary,
confidence, timestamp, data sources, reasons for selection and reasons
against alternatives.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from security_selection.config import ReportConfig
from security_selection.models.enums import TargetAssetClass
from security_selection.models.pipeline import (
    PortfolioConstruction,
    RankedSecurity,
    Recommendation,
    ResearchReport,
    SelectionInput,
)


class ResearchReportGenerator:
    """Builds the institutional research report."""

    def __init__(self, config: ReportConfig) -> None:
        self._config = config
        self._model_version = _model_version()

    def generate(
        self,
        *,
        asset_class: TargetAssetClass,
        universe_size: int,
        filtered_size: int,
        ranked: List[RankedSecurity],
        portfolio: PortfolioConstruction,
        recommendation: Recommendation,
        selection_input: SelectionInput,
    ) -> ResearchReport:
        metrics_table = self._metrics_table(ranked) if self._config.include_metrics_table else {}
        factor_scores = self._factor_scores(ranked) if self._config.include_factor_scores else {}
        strengths = self._strengths(ranked)
        weaknesses = self._weaknesses(ranked)

        return ResearchReport(
            asset_class=asset_class,
            generated_at=datetime.now(timezone.utc),
            universe_size=universe_size,
            filtered_size=filtered_size,
            ranking=ranked,
            metrics_table=metrics_table,
            factor_scores=factor_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=self._recommendation_text(recommendation, portfolio),
            alternatives=[a.identity.symbol for a in recommendation.alternatives],
            risk_summary=recommendation.risk_summary,
            confidence=recommendation.confidence.value,
            data_sources_used=self._data_sources(ranked),
            reasons_for_selection=recommendation.explanation,
            reasons_against_alternatives=recommendation.reasons_against_alternatives,
            model_version=self._model_version,
        )

    # ── sections ────────────────────────────────────────────────────

    def _metrics_table(self, ranked: List[RankedSecurity]) -> Dict[str, Dict[str, Any]]:
        """Key metrics per ranked security (bounded by max_universe_display)."""
        out: Dict[str, Dict[str, Any]] = {}
        for r in ranked[: self._config.max_universe_display]:
            m = r.security.metrics
            row = {
                "symbol": r.security.identity.symbol,
                "rank": r.rank,
                "overall_score": r.overall_score,
                "return_1y": m.get("return_1y"),
                "return_3y": m.get("return_3y"),
                "volatility": m.get("volatility"),
                "sharpe_ratio": m.get("sharpe_ratio"),
                "sortino_ratio": m.get("sortino_ratio"),
                "max_drawdown": m.get("max_drawdown"),
                "tracking_error": m.get("tracking_error"),
                "expense_ratio": m.get("expense_ratio"),
                "aum_crore": m.get("aum_crore"),
            }
            out[r.security.key] = row
        return out

    def _factor_scores(self, ranked: List[RankedSecurity]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for r in ranked[: self._config.max_universe_display]:
            out[r.security.key] = {
                f.factor: f.score for f in r.factor_scores
            }
        return out

    def _strengths(self, ranked: List[RankedSecurity]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for r in ranked[:5]:
            top = sorted(r.factor_scores, key=lambda f: f.score, reverse=True)[:3]
            out[r.security.key] = [
                f"{f.factor}: {f.score:.0%}" for f in top
            ]
        return out

    def _weaknesses(self, ranked: List[RankedSecurity]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for r in ranked[:5]:
            bottom = sorted(r.factor_scores, key=lambda f: f.score)[:2]
            out[r.security.key] = [
                f"{f.factor}: {f.score:.0%}" for f in bottom
            ]
        return out

    def _recommendation_text(
        self, recommendation: Recommendation, portfolio: PortfolioConstruction
    ) -> str:
        positions = ", ".join(
            f"{int(round(p.weight * 100))}% {p.security.identity.symbol}"
            for p in portfolio.positions
        )
        return (
            f"{recommendation.action.value} — {positions} "
            f"(confidence: {recommendation.confidence.value})"
        )

    @staticmethod
    def _data_sources(ranked: List[RankedSecurity]) -> List[str]:
        sources: List[str] = []
        for r in ranked:
            for src in r.security.data_sources:
                if src not in sources:
                    sources.append(src)
        return sources or ["static"]


def _model_version() -> str:
    try:
        from security_selection import __version__

        return __version__
    except Exception:
        return "1.0.0"

