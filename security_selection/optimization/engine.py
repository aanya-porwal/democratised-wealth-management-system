"""Portfolio optimizer — constructs single- or multi-security portfolios.

The engine does NOT assume the best answer is a single security. It
starts from the top-ranked candidates and decides whether diversification
improves the outcome under configurable constraints:

* if the best security already covers the target bucket weight with high
  confidence, recommend it alone;
* otherwise build an equal-risk-weighted basket of the top candidates
  that clears the minimum-liquidity floor and the min/max weight bounds.

The optimizer is deliberately lightweight (no scipy dependency at the
hot path): a transparent, explainable construction rule rather than a
black-box mean-variance solver. A pluggable ``constraint`` hook allows a
future full optimizer to be dropped in.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from security_selection.config import OptimizationConfig
from security_selection.models.pipeline import (
    CandidateSecurity,
    PortfolioConstruction,
    SelectionInput,
    WeightedPosition,
)
from security_selection.utils.math import clamp

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """Builds an explainable portfolio from ranked candidates."""

    def __init__(self, config: OptimizationConfig) -> None:
        self._config = config

    def optimize(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput | None = None,
    ) -> PortfolioConstruction:
        if not candidates:
            return PortfolioConstruction(
                strategy="single",
                positions=[],
                reason="no candidates available",
            )
        selection_input = selection_input or SelectionInput(
            target_asset_class=selection_input.target_asset_class
            if selection_input
            else _default_target()
        )
        cfg = self._config
        constraints: List[str] = [
            f"min_weight={cfg.min_weight}",
            f"max_weight={cfg.max_weight}",
            f"min_liquidity={cfg.min_liquidity_score}",
        ]

        # filter to candidates that clear the liquidity floor
        pool = [
            c for c in candidates
            if self._liquidity(c) >= cfg.min_liquidity_score
        ]
        pool = pool[: cfg.candidate_pool_size]
        if not pool:
            pool = candidates[:1]

        best = pool[0]
        best_coverage = self._coverage(best)

        # single-security path
        if (
            len(pool) == 1
            or best_coverage >= cfg.single_security_coverage_threshold
            or not self._diversification_benefit(pool)
        ):
            position = WeightedPosition(
                security=best,
                weight=1.0,
                rationale=[
                    "highest overall score in the target asset class",
                    f"covers {best_coverage:.0%} of the target bucket exposure",
                ],
            )
            return PortfolioConstruction(
                strategy="single",
                positions=[position],
                reason=self._single_reason(best, best_coverage),
                constraints_applied=constraints,
            )

        # diversified multi-security path
        positions = self._build_diversified(pool)
        weights = " + ".join(
            f"{int(round(p.weight * 100))}% {p.security.identity.symbol}"
            for p in positions
        )
        return PortfolioConstruction(
            strategy="diversified",
            positions=positions,
            reason=(
                "diversification across multiple securities improves liquidity "
                f"and reduces single-security concentration risk → {weights}"
            ),
            constraints_applied=constraints,
        )

    # ── helpers ─────────────────────────────────────────────────────

    def _liquidity(self, candidate: CandidateSecurity) -> float:
        if candidate.profile is not None:
            return candidate.profile.liquidity
        return float(candidate.metrics.get("liquidity_score", 0.0))

    def _coverage(self, candidate: CandidateSecurity) -> float:
        """Estimate how much of the target bucket the security covers."""
        # Approximation from data quality + score: a high-quality, highly
        # liquid, top-scoring security is treated as near-full coverage.
        quality = candidate.data_quality_score
        score = candidate.overall_score / 100.0 if candidate.overall_score else 0.5
        liquidity = self._liquidity(candidate)
        return clamp(0.4 + 0.3 * quality + 0.3 * liquidity + 0.2 * score, 0.0, 1.0)

    def _diversification_benefit(self, pool: List[CandidateSecurity]) -> bool:
        """Whether spreading across the pool meaningfully reduces risk."""
        if len(pool) < 2:
            return False
        vols = [
            float(c.metrics.get("volatility", 0.15) or 0.15) for c in pool[:2]
        ]
        # Correlation assumption: equity instruments are ~0.9 correlated;
        # the risk reduction from splitting is small unless volatility
        # differs materially.
        vol_a, vol_b = vols[0], vols[1]
        if vol_a <= 0 or vol_b <= 0:
            return True  # can't measure risk → prefer diversification
        combined = (vol_a + vol_b) / 2.0
        reduction = (combined - vol_a) / vol_a if vol_a > 0 else 0.0
        return reduction >= self._config.min_diversification_benefit or (
            abs(vol_a - vol_b) / max(vol_a, vol_b) > 0.3
        )

    def _build_diversified(self, pool: List[CandidateSecurity]) -> List[WeightedPosition]:
        cfg = self._config
        count = min(cfg.target_portfolio_count, len(pool))
        chosen = pool[:count]

        # inverse-volatility weights (simple, explainable risk parity)
        vols = []
        for c in chosen:
            v = float(c.metrics.get("volatility", 0.15) or 0.15)
            vols.append(max(v, 1e-6))
        inv = [1.0 / v for v in vols]
        total_inv = sum(inv)
        raw = [i / total_inv for i in inv]

        # enforce min/max weight bounds
        n = len(raw)
        raw = [clamp(w, cfg.min_weight, cfg.max_weight) for w in raw]
        total = sum(raw)
        raw = [w / total if total > 0 else 1.0 / n for w in raw]
        # re-clamp and renormalize once more
        raw = [clamp(w, cfg.min_weight, cfg.max_weight) for w in raw]
        total = sum(raw)
        raw = [w / total if total > 0 else 1.0 / n for w in raw]

        positions: List[WeightedPosition] = []
        for c, w in zip(chosen, raw):
            positions.append(
                WeightedPosition(
                    security=c,
                    weight=round(w, 4),
                    rationale=[
                        "risk-parity weighting (inverse volatility)",
                        f"weight {w:.0%} bounded by configured constraints",
                    ],
                )
            )
        return positions

    @staticmethod
    def _single_reason(candidate: CandidateSecurity, coverage: float) -> str:
        return (
            f"single-security recommendation: {candidate.identity.symbol} "
            f"ranks best with {coverage:.0%} target coverage; "
            "diversification would not materially improve risk-adjusted outcome"
        )


def _default_target():
    from security_selection.models.enums import TargetAssetClass

    return TargetAssetClass.LARGE_CAP_EQUITY

