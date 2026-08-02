"""SGB evaluator — discovers, fetches and evaluates Sovereign Gold Bonds.

SGBs are government-issued gold-linked bonds with a fixed 2.5% interest
and zero capital gains tax at maturity. Uses the static data provider
for bond metadata and yfinance for gold price tracking.
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


class SGBEvaluator(BaseEvaluator):
    """Evaluator for Sovereign Gold Bonds.

    SGBs have a unique combination: 2.5% annual interest + gold price
    appreciation + zero capital gains tax at 8-year maturity.
    """

    kind: SecurityKind = SecurityKind.SGB
    target: TargetAssetClass = TargetAssetClass.SGB
    bucket: AssetClassBucket = AssetClassBucket.GOLD

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
            logger.warning("No SGB universe configured")
            return []
        identities: List[SecurityIdentity] = []
        for symbol in universe:
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    name=symbol,
                    currency=default_currency(self.target),
                    kind=SecurityKind.SGB,
                )
            )
        limit = self._eval_config.max_candidates if self._eval_config else 20
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
            history_years=None,  # SGBs use static data
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
                    "SGB %s failed quality: %s",
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
            payloads, self.target, kind=SecurityKind.SGB
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
            profile = self._normalize_sgb(candidate)
            candidate.profile = profile
        return candidates

    def _normalize_sgb(self, candidate: CandidateSecurity) -> NormalizedProfile:
        m = candidate.metrics
        avail: Dict[NormalizationAxis, bool] = {}

        # SGB return = gold price appreciation + 2.5% interest, tax-free at maturity
        if "expected_return_annual" in m:
            expected_return = _minmax_scale(
                float(m["expected_return_annual"]), 0.0, 0.20
            )
        else:
            expected_return = 0.6
        avail[NormalizationAxis.EXPECTED_RETURN] = True

        # Risk (very low for sovereign guaranteed)
        risk = 0.9
        avail[NormalizationAxis.RISK] = True

        # Liquidity (traded on exchanges but less liquid than ETFs)
        liquidity = 0.4
        avail[NormalizationAxis.LIQUIDITY] = True

        # Diversification (single issuer)
        diversification = 0.2
        avail[NormalizationAxis.DIVERSIFICATION] = True

        # Tax efficiency (best: zero CGT at 8yr maturity)
        tax_efficiency = 0.95
        avail[NormalizationAxis.TAX_EFFICIENCY] = True

        # Cost (no management fee, no brokerage on primary)
        cost = 0.9
        avail[NormalizationAxis.COST] = True

        tracking_quality = 0.5
        avail[NormalizationAxis.TRACKING_QUALITY] = False

        # Quality
        quality = 0.8
        avail[NormalizationAxis.QUALITY] = True

        # Market exposure
        market_exposure = 0.5
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
