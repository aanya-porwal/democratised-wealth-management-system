"""Explanation engine — the single place reasons are generated.

Produces:
* why a security was chosen (its strongest factor scores)
* why alternatives ranked lower (their weakest factor scores)
* risk summary from the candidate's risk metrics
* a confidence level derived from data completeness + score gap
"""

from __future__ import annotations

from typing import Dict, List, Optional

from security_selection.config import SecuritySelectionConfig
from security_selection.models.enums import Confidence, TargetAssetClass
from security_selection.models.pipeline import (
    CandidateSecurity,
    Recommendation,
    WeightedPosition,
)
from security_selection.utils.math import safe_float

# human labels for the factor names
_FACTOR_LABELS: Dict[str, str] = {
    "return_factor": "return profile",
    "risk_factor": "risk profile",
    "cost_factor": "cost efficiency",
    "liquidity_factor": "liquidity",
    "quality_factor": "data quality",
    "diversification_factor": "diversification",
    "tax_factor": "tax efficiency",
    "tracking_factor": "tracking quality",
    "credit_quality_factor": "credit quality",
    "market_exposure_factor": "market exposure",
}


class ExplanationEngine:
    """Generates all explanations for the platform."""

    def __init__(self, config: SecuritySelectionConfig) -> None:
        self._config = config

    def recommend(
        self,
        selected: List[WeightedPosition],
        alternatives: List[CandidateSecurity],
        all_candidates: List[CandidateSecurity],
        target: TargetAssetClass,
    ) -> Recommendation:
        reasons = self._selection_reasons(selected)
        risk_summary = self._risk_summary(selected)
        against = self._reasons_against(alternatives)
        confidence = self._confidence(selected, all_candidates)

        from security_selection.models.enums import RecommendationAction

        return Recommendation(
            action=RecommendationAction.INVEST,
            confidence=confidence,
            selected=selected,
            alternatives=alternatives,
            rejected=[c for c in all_candidates if c not in selected_candidates(selected)],
            explanation=reasons,
            reasons_against_alternatives=against,
            risk_summary=risk_summary,
        )

    # ── selection reasons ───────────────────────────────────────────

    def _selection_reasons(self, selected: List[WeightedPosition]) -> List[str]:
        reasons: List[str] = []
        for position in selected:
            sec = position.security
            factor_scores = sorted(
                sec.factor_scores, key=lambda f: f.score, reverse=True
            )
            top_factors = factor_scores[:3]
            reasons.append(
                f"Chosen: {sec.identity.symbol} ({sec.identity.name or sec.kind.value}) "
                f"— overall score {sec.overall_score:.1f}/100, weight {position.weight:.0%}"
            )
            for factor in top_factors:
                label = _FACTOR_LABELS.get(factor.factor, factor.factor)
                reasons.append(
                    f"  strong {label} ({factor.score:.0%})"
                )
            if position.rationale:
                reasons.extend(f"  {r}" for r in position.rationale)
        return reasons

    def _reasons_against(self, alternatives: List[CandidateSecurity]) -> List[str]:
        out: List[str] = []
        for sec in alternatives:
            factor_scores = sorted(
                sec.factor_scores, key=lambda f: f.score
            )
            weak = factor_scores[:2]
            detail = "; ".join(
                f"{_FACTOR_LABELS.get(f.factor, f.factor)} {f.score:.0%}"
                for f in weak
            )
            out.append(
                f"{sec.identity.symbol} ranked lower — weaker {detail or 'scores'}, "
                f"overall {sec.overall_score:.1f}/100"
            )
        return out

    def _risk_summary(self, selected: List[WeightedPosition]) -> List[str]:
        out: List[str] = []
        for position in selected:
            m = position.security.metrics
            vol = safe_float(m.get("volatility"))
            mdd = safe_float(m.get("max_drawdown"))
            sharpe = safe_float(m.get("sharpe_ratio"))
            parts = [f"{position.security.identity.symbol}:"]
            if vol is not None:
                parts.append(f"annualized volatility {vol:.1%}")
            if mdd is not None:
                parts.append(f"max drawdown {mdd:.1%}")
            if sharpe is not None:
                parts.append(f"Sharpe {sharpe:.2f}")
            out.append(" ".join(parts) if len(parts) > 1 else f"{position.security.identity.symbol}: risk metrics unavailable")
        return out

    def _confidence(
        self,
        selected: List[WeightedPosition],
        all_candidates: List[CandidateSecurity],
    ) -> Confidence:
        if not selected:
            return Confidence.LOW
        best = selected[0].security
        completeness = self._completeness(best)
        # score gap between best and runner-up
        gap = 0.0
        if len(all_candidates) > 1:
            second = max(
                (c.overall_score for c in all_candidates if c.key != best.key),
                default=0.0,
            )
            gap = best.overall_score - second
        if completeness >= 0.8 and gap >= 5.0:
            return Confidence.HIGH
        if completeness >= 0.5:
            return Confidence.MEDIUM
        return Confidence.LOW

    def _completeness(self, candidate: CandidateSecurity) -> float:
        expected = {
            "return_1y", "return_3y", "volatility", "sharpe_ratio",
            "max_drawdown", "expense_ratio", "aum_crore", "age_years",
        }
        present = sum(1 for m in expected if candidate.metrics.get(m) is not None)
        return present / len(expected)


def selected_candidates(selected: List[WeightedPosition]) -> List[CandidateSecurity]:
    return [p.security for p in selected]

