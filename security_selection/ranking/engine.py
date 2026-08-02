"""Ranking engine.

Ranks all scored candidates and produces the tiers required by the
specification:

* all securities ranked
* Top 20 / Top 10 / Top 5
* Best Overall
* Alternative Recommendations
* Confidence Score

Confidence blends data completeness and the score gap between the top
security and its runner-up.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from security_selection.config import RankingConfig
from security_selection.models.pipeline import CandidateSecurity, RankedSecurity

logger = logging.getLogger(__name__)


class RankingEngine:
    """Sorts candidates by overall score and builds ranking tiers."""

    def __init__(self, config: RankingConfig) -> None:
        self._config = config

    def rank(self, candidates: List[CandidateSecurity]) -> List[RankedSecurity]:
        """Rank candidates descending by overall score."""
        scored = [c for c in candidates if c.overall_score > 0]
        scored.sort(key=lambda c: c.overall_score, reverse=True)
        ranked: List[RankedSecurity] = []
        for idx, candidate in enumerate(scored, start=1):
            confidence = self._confidence(candidate, scored, idx)
            ranked.append(
                RankedSecurity(
                    security=candidate,
                    rank=idx,
                    overall_score=candidate.overall_score,
                    confidence=confidence,
                    factor_scores=list(candidate.factor_scores),
                )
            )
        return ranked

    # ── tier accessors ──────────────────────────────────────────────

    def top_n(self, ranked: List[RankedSecurity], n: int) -> List[RankedSecurity]:
        return ranked[:n]

    def best(self, ranked: List[RankedSecurity]) -> RankedSecurity | None:
        return ranked[0] if ranked else None

    def alternatives(
        self, ranked: List[RankedSecurity], exclude_first: bool = True
    ) -> List[RankedSecurity]:
        """Return the top alternatives after the best pick."""
        skip = 1 if exclude_first else 0
        return ranked[skip : skip + self._config.alternative_count]

    def as_dict(self, ranked: List[RankedSecurity]) -> Dict[str, object]:
        """Structured ranking output for the API."""
        return {
            "all": [self._row(r) for r in ranked],
            "top_20": [self._row(r) for r in self.top_n(ranked, self._config.top_n)],
            "top_10": [self._row(r) for r in self.top_n(ranked, self._config.top_n_10)],
            "top_5": [self._row(r) for r in self.top_n(ranked, self._config.top_n_5)],
            "best_overall": self._row(ranked[0]) if ranked else None,
            "alternatives": [self._row(r) for r in self.alternatives(ranked)],
        }

    # ── helpers ─────────────────────────────────────────────────────

    def _confidence(
        self,
        candidate: CandidateSecurity,
        scored: List[CandidateSecurity],
        rank: int,
    ) -> float:
        """Confidence from data completeness and score gap."""
        completeness = self._completeness(candidate)
        score_gap = 0.5
        if rank == 1 and len(scored) > 1:
            top = scored[0].overall_score
            second = scored[1].overall_score
            gap = top - second
            # bigger gap → higher confidence
            score_gap = clamp_0_1(0.5 + gap / 20.0)
        w = self._config
        return round(
            w.completeness_weight * completeness + w.score_gap_weight * score_gap,
            4,
        )

    def _completeness(self, candidate: CandidateSecurity) -> float:
        """Fraction of expected metrics actually present."""
        expected = {
            "return_1y", "return_3y", "volatility", "sharpe_ratio",
            "max_drawdown", "expense_ratio", "aum_crore", "age_years",
        }
        present = sum(1 for m in expected if candidate.metrics.get(m) is not None)
        return present / len(expected)

    @staticmethod
    def _row(r: RankedSecurity) -> Dict[str, object]:
        return {
            "rank": r.rank,
            "symbol": r.security.identity.symbol,
            "name": r.security.identity.name,
            "kind": r.security.kind.value,
            "overall_score": r.overall_score,
            "confidence": r.confidence,
            "factor_scores": {
                f.factor: f.score for f in r.factor_scores
            },
        }


def clamp_0_1(value: float) -> float:
    return max(0.0, min(1.0, value))

