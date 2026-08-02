"""Corporate bond evaluator — discovers, fetches and evaluates corporate bonds.

Uses the static data provider for bond metadata (interest rates, credit
ratings, maturity). Corporate bonds are fixed-income securities issued
by companies.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from security_selection.base.evaluator import BaseEvaluator
from security_selection.base.provider import BaseProviderSet
from security_selection.evaluators._common import (
    build_candidates_from_payloads,
    default_benchmark_symbol,
    default_currency,
    enrich_candidate_from_metrics,
)
from security_selection.models.data import ProviderPayload, SecurityIdentity
from security_selection.models.enums import (
    AssetClassBucket,
    NormalizationAxis,
    SecurityKind,
    TargetAssetClass,
)
from security_selection.models.pipeline import (
    CandidateSecurity,
    NormalizedProfile,
    SelectionInput,
)

logger = logging.getLogger(__name__)


class CorporateBondEvaluator(BaseEvaluator):
    """Evaluator for corporate bonds (listed debt securities).

    Corporate bonds are evaluated on yield, credit rating, maturity,
    and liquidity. The config universe is populated from the static
    provider's CORPORATE_BOND_STATIC catalog.
    """

    kind: SecurityKind = SecurityKind.CORPORATE_BOND
    target: TargetAssetClass = TargetAssetClass.CORPORATE_BONDS
    bucket: AssetClassBucket = AssetClassBucket.DEBT

    def __init__(
        self,
        providers: BaseProviderSet,
        *,
        target: TargetAssetClass | None = None,
    ) -> None:
        super().__init__(providers, target=target)
        self._eval_config = self._config.evaluator_config(self.target)

    def discover(self, selection_input: SelectionInput) -> List[SecurityIdentity]:
        universe = self._eval_config.universe if self._eval_config else []
        # Fall back to static provider search if universe is empty
        if not universe:
            return self._data.search("", kind=SecurityKind.CORPORATE_BOND)
        identities: List[SecurityIdentity] = []
        for symbol in universe:
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    name=symbol,
                    currency=default_currency(self.target),
                    kind=SecurityKind.CORPORATE_BOND,
                )
            )
        limit = self._eval_config.max_candidates if self._eval_config else 30
        if selection_input.candidate_limit:
            limit = min(limit, selection_input.candidate_limit)
        return identities[:limit]

    def fetch_data(
        self,
        identities: List[SecurityIdentity],
        selection_input: SelectionInput,
    ) -> List[ProviderPayload]:
        return self._data.fetch_multi(
            identities=identities,
            history_years=None,  # Static data
            use_cache=selection_input.use_cache,
        )

    def validate(
        self,
        payloads: List[ProviderPayload],
        selection_input: SelectionInput,
    ) -> List[ProviderPayload]:
        valid: List[ProviderPayload] = []
        for payload in payloads:
            report = self._quality.validate_payload(payload)
            if report.is_usable:
                valid.append(payload)
            else:
                logger.warning(
                    "Corporate bond %s failed quality: %s",
                    payload.identity.symbol,
                    report.summary(),
                )
        return valid

    def calculate_metrics(
        self,
        payloads: List[ProviderPayload],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        candidates = build_candidates_from_payloads(
            payloads, self.target, kind=SecurityKind.CORPORATE_BOND
        )
        for candidate in candidates:
            enrich_candidate_from_metrics(candidate, self._metrics, self._config)
        return candidates

    def normalize(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        for candidate in candidates:
            profile = self._normalize_corporate_bond(candidate)
            candidate.profile = profile
        return candidates

    def _normalize_corporate_bond(self, candidate: CandidateSecurity) -> NormalizedProfile:
        m = candidate.metrics
        avail: Dict[NormalizationAxis, bool] = {}

        # Expected return = yield to maturity
        ytm = m.get("interest_rate") or m.get("yield_to_maturity")
        if ytm is not None and isinstance(ytm, (int, float)):
            expected_return = _minmax_scale(float(ytm), 0.0, 0.15)
            avail[NormalizationAxis.EXPECTED_RETURN] = True
        else:
            expected_return = 0.5
            avail[NormalizationAxis.EXPECTED_RETURN] = False

        # Risk (inverse of credit rating)
        credit_rating = str(m.get("credit_rating", "BBB"))
        risk = _rating_to_risk_score(credit_rating)
        avail[NormalizationAxis.RISK] = True

        # Liquidity (bonds are less liquid than equities)
        liquidity = 0.3
        avail[NormalizationAxis.LIQUIDITY] = True

        # Diversification (single issuer)
        diversification = 0.2
        avail[NormalizationAxis.DIVERSIFICATION] = True

        # Tax efficiency (debt slab)
        tax_efficiency = 0.3
        avail[NormalizationAxis.TAX_EFFICIENCY] = True

        # Cost (no expense ratio, but bid-ask spread)
        cost = 0.6
        avail[NormalizationAxis.COST] = True

        tracking_quality = 0.5
        avail[NormalizationAxis.TRACKING_QUALITY] = False

        # Quality (credit rating proxy)
        quality = risk  # higher risk = lower quality
        avail[NormalizationAxis.QUALITY] = True

        # Market exposure
        market_exposure = 0.4
        avail[NormalizationAxis.MARKET_EXPOSURE] = True

        available_count = sum(1 for v in avail.values() if v)
        confidence = available_count / len(NormalizationAxis)

        return NormalizedProfile(
            security_key=candidate.key,
            expected_return=expected_return,
            risk=risk,
            liquidity=liquidity,
            diversification=diversification,
            tax_efficiency=tax_efficiency,
            cost=cost,
            tracking_quality=tracking_quality,
            quality=quality,
            market_exposure=market_exposure,
            confidence=confidence,
            available=avail,
        )


def _rating_to_risk_score(rating: str) -> float:
    """Convert a credit rating string to a risk score (0 = risky, 1 = safe)."""
    rating_map = {
        "AAA": 0.95,
        "AA": 0.85,
        "A": 0.75,
        "BBB": 0.60,
        "BB": 0.40,
        "B": 0.25,
        "CCC": 0.10,
    }
    for key, score in rating_map.items():
        if key in rating.upper():
            return score
    return 0.5


def _minmax_scale(value: float, min_val: float, max_val: float) -> float:
    if max_val <= min_val:
        return 0.5
    scaled = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, scaled))
