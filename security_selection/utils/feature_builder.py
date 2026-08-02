"""Feature engineering for the ML-ready prediction interface.

The platform deliberately does NOT train models. Instead it builds a
flat feature matrix (the same one a supervised model would consume) so
future ML models can plug into the existing ``IScoringModel`` interface
without changing the pipeline.

``FeatureBuilder`` extracts a stable, typed feature vector from a
:class:`CandidateSecurity` and its metrics.
"""

from __future__ import annotations

from typing import Any, Dict, List

from security_selection.models.pipeline import CandidateSecurity

# The canonical feature order. Keep it stable so persisted datasets stay
# compatible across versions.
FEATURE_COLUMNS: List[str] = [
    "return_1y",
    "return_3y",
    "return_5y",
    "volatility",
    "sharpe",
    "sortino",
    "max_drawdown",
    "expense_ratio",
    "aum_crore",
    "avg_volume",
    "liquidity_score",
    "tracking_error",
    "dividend_yield",
    "quality_score",
    "diversification",
    "tax_efficiency",
    "age_years",
]


class FeatureBuilder:
    """Build flat feature vectors and datasets from candidates."""

    @staticmethod
    def build(candidate: CandidateSecurity) -> Dict[str, float]:
        """Extract a feature dict for a single candidate."""
        m = candidate.metrics
        p = candidate.profile

        def metric(name: str, default: float = 0.0) -> float:
            value = m.get(name)
            if value is None:
                return default
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        return {
            "return_1y": metric("return_1y"),
            "return_3y": metric("return_3y"),
            "return_5y": metric("return_5y"),
            "volatility": metric("volatility"),
            "sharpe": metric("sharpe_ratio"),
            "sortino": metric("sortino_ratio"),
            "max_drawdown": metric("max_drawdown"),
            "expense_ratio": metric("expense_ratio"),
            "aum_crore": metric("aum_crore"),
            "avg_volume": metric("average_volume"),
            "liquidity_score": p.liquidity if p else 0.0,
            "tracking_error": metric("tracking_error"),
            "dividend_yield": metric("dividend_yield"),
            "quality_score": p.quality if p else 0.0,
            "diversification": p.diversification if p else 0.0,
            "tax_efficiency": p.tax_efficiency if p else 0.0,
            "age_years": metric("age_years"),
        }

    @staticmethod
    def build_matrix(candidates: List[CandidateSecurity]) -> List[Dict[str, Any]]:
        """Build a row-per-candidate feature matrix (ML dataset)."""
        return [
            {
                "security_key": c.key,
                "symbol": c.identity.symbol,
                "name": c.identity.name,
                "kind": c.kind.value,
                "target_asset_class": c.asset_class.value,
                "overall_score": c.overall_score,
                **FeatureBuilder.build(c),
            }
            for c in candidates
        ]

