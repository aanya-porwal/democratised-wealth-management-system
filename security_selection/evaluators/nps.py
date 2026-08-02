"""NPS evaluator — discovers, fetches and evaluates National Pension System.

NPS is a tax-advantaged retirement instrument with Tier 1 (locked till 60)
and Tier 2 (liquid) options. Uses the static data provider for scheme
metadata.
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


class NPSEvaluator(BaseEvaluator):
    """Evaluator for National Pension System (NPS) schemes.

    NPS is evaluated on expected return, expense ratio (lowest among
    retirement products), lock-in period, and tax benefits (80C + 80CCD).
    """

    kind: SecurityKind = SecurityKind.NPS
    target: TargetAssetClass = TargetAssetClass.NPS
    bucket: AssetClassBucket = AssetClassBucket.TAX_ADVANTAGED

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
        if not universe:
            return self._data.search("", kind=SecurityKind.NPS)
        identities: List[SecurityIdentity] = []
        for symbol in universe:
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    name=symbol,
                    currency=default_currency(self.target),
                    kind=SecurityKind.NPS,
                )
            )
        limit = self._eval_config.max_candidates if self._eval_config else 5
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
            history_years=None,
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
                    "NPS %s failed quality: %s",
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
            payloads, self.target, kind=SecurityKind.NPS
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
            profile = self._normalize_nps(candidate)
            candidate.profile = profile
        return candidates

    def _normalize_nps(self, candidate: CandidateSecurity) -> NormalizedProfile:
        m = candidate.metrics
        avail: Dict[NormalizationAxis, bool] = {}

        # Expected return
        rate = m.get("interest_rate") or m.get("expected_return")
        if rate is not None and isinstance(rate, (int, float)):
            expected_return = _minmax_scale(float(rate), 0.0, 0.15)
            avail[NormalizationAxis.EXPECTED_RETURN] = True
        else:
            expected_return = 0.5
            avail[NormalizationAxis.EXPECTED_RETURN] = False

        # Risk (moderate, fund manager dependent)
        risk = 0.6
        avail[NormalizationAxis.RISK] = True

        # Liquidity (Tier 1 locked, Tier 2 liquid)
        symbol = candidate.identity.symbol
        if "TIER2" in symbol.upper():
            liquidity = 0.7
        else:
            liquidity = 0.1
        avail[NormalizationAxis.LIQUIDITY] = True

        diversification = 0.5
        avail[NormalizationAxis.DIVERSIFICATION] = True

        # Tax efficiency (EET: deduction on entry, partial tax on exit)
        tax_efficiency = 0.8
        avail[NormalizationAxis.TAX_EFFICIENCY] = True

        # Cost (lowest expense ratio among all retirement products)
        cost = 0.9
        avail[NormalizationAxis.COST] = True

        tracking_quality = 0.5
        avail[NormalizationAxis.TRACKING_QUALITY] = False

        quality = 0.7
        avail[NormalizationAxis.QUALITY] = True

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


def _minmax_scale(value: float, min_val: float, max_val: float) -> float:
    if max_val <= min_val:
        return 0.5
    scaled = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, scaled))
