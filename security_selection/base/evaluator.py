"""Abstract evaluator — the plugin architecture core.

Every concrete evaluator (ETF, Mutual Fund, Bond, ...) subclasses
:class:`BaseEvaluator` and implements only the asset-class-specific
stages of the pipeline:

    discover  ->  fetch_data  ->  validate  ->  calculate_metrics
    ->  normalize

The generic stages (filter, score, rank, construct_portfolio, report,
recommend, explain) are provided once here and delegate to injected,
reusable engines — so there is ZERO duplicated logic across asset
classes, and the core engine never knows how an ETF or a Bond works.

Adding a new asset class = subclass + override the asset-specific stages
+ register it. No core code changes.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from security_selection.base.provider import BaseProviderSet
from security_selection.config import SecuritySelectionConfig
from security_selection.explainability.engine import ExplanationEngine
from security_selection.filters.pipeline import FilterPipeline
from security_selection.metrics.engine import MetricsEngine
from security_selection.models.data import ProviderPayload, QualityReport, SecurityIdentity
from security_selection.models.enums import (
    AssetClassBucket,
    Confidence,
    SecurityKind,
    TargetAssetClass,
)
from security_selection.models.pipeline import (
    CandidateSecurity,
    EvaluatorOutput,
    PortfolioConstruction,
    RankedSecurity,
    Recommendation,
    ResearchReport,
    SelectionInput,
    WeightedPosition,
)
from security_selection.optimization.engine import PortfolioOptimizer
from security_selection.quality.engine import DataQualityEngine
from security_selection.ranking.engine import RankingEngine
from security_selection.research.report import ResearchReportGenerator
from security_selection.scoring.engine import ScoringEngine

logger = logging.getLogger(__name__)


class BaseEvaluator(ABC):
    """Template-method evaluator for a specific asset class.

    Subclasses must set the class attributes ``kind``, ``target`` and
    ``bucket``, and implement the asset-specific stages.
    """

    # ── class metadata (override in subclasses) ─────────────────────
    kind: SecurityKind = SecurityKind.ETF
    target: TargetAssetClass = TargetAssetClass.LARGE_CAP_EQUITY
    bucket: AssetClassBucket = AssetClassBucket.EQUITY

    def __init__(
        self,
        providers: BaseProviderSet,
        *,
        target: TargetAssetClass | None = None,
    ) -> None:
        self._providers = providers
        self._config: SecuritySelectionConfig = providers.config
        self._data = providers.data
        self._cache = providers.cache
        # One evaluator class may serve several target asset classes
        # (e.g. MutualFundEvaluator serves large/mid/small/flexi/ELSS).
        # The service passes the concrete target at construction time.
        if target is not None:
            self.target = target

        # shared reusable engines (injected, replaceable in tests)
        self._metrics = MetricsEngine()
        self._quality = DataQualityEngine(self._config.quality)
        self._filters = FilterPipeline(self._config.filters)
        self._scoring = ScoringEngine(self._config.scoring)
        self._ranking = RankingEngine(self._config.ranking)
        self._optimizer = PortfolioOptimizer(self._config.optimization)
        self._explainer = ExplanationEngine(self._config)
        self._reporter = ResearchReportGenerator(self._config.report)

    # ════════════════════════════════════════════════════════════════
    # Template method — the full pipeline
    # ════════════════════════════════════════════════════════════════

    def run(self, selection_input: SelectionInput) -> EvaluatorOutput:
        """Execute the complete security-selection pipeline."""
        identities = self.discover(selection_input)
        payloads = self.fetch_data(identities, selection_input)
        payloads = self.validate(payloads, selection_input)
        candidates = self.calculate_metrics(payloads, selection_input)
        candidates = self.normalize(candidates, selection_input)
        candidates = self.filter(candidates, selection_input)
        candidates = self.score(candidates, selection_input)
        ranked = self.rank(candidates, selection_input)
        portfolio = self.construct_portfolio(ranked, selection_input)
        recommendation = self.recommend(ranked, portfolio, selection_input)
        recommendation = self.explain(recommendation, ranked, portfolio, selection_input)
        report = self.generate_report(
            ranked, portfolio, recommendation, selection_input
        )
        return EvaluatorOutput(
            asset_class=self.target,
            universe=[_as_candidate(i, self) for i in identities],
            filtered=candidates,
            ranked=ranked,
            portfolio=portfolio,
            recommendation=recommendation,
            report=report,
            confidence=recommendation.confidence,
        )

    # ════════════════════════════════════════════════════════════════
    # Asset-class-specific stages (must implement in subclasses)
    # ════════════════════════════════════════════════════════════════

    @abstractmethod
    def discover(self, selection_input: SelectionInput) -> List[SecurityIdentity]:
        """Discover the eligible securities for the target asset class."""

    @abstractmethod
    def fetch_data(
        self,
        identities: List[SecurityIdentity],
        selection_input: SelectionInput,
    ) -> List[ProviderPayload]:
        """Retrieve live/static data for each identity from the providers."""

    @abstractmethod
    def validate(
        self,
        payloads: List[ProviderPayload],
        selection_input: SelectionInput,
    ) -> List[ProviderPayload]:
        """Apply quality checks; drop or annotate failing payloads."""

    @abstractmethod
    def calculate_metrics(
        self,
        payloads: List[ProviderPayload],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        """Compute metrics and build candidate securities."""

    @abstractmethod
    def normalize(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        """Normalize each candidate to the common :class:`NormalizedProfile`."""

    # ════════════════════════════════════════════════════════════════
    # Shared stages — override only if the asset class genuinely differs
    # ════════════════════════════════════════════════════════════════

    def filter(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        """Apply configurable filters (overridable per request)."""
        return self._filters.apply(candidates, selection_input.filter_overrides)

    def score(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        """Score candidates using the configured factor model."""
        for candidate in candidates:
            factor_scores, overall = self._scoring.score(candidate)
            candidate.factor_scores = factor_scores
            candidate.overall_score = overall
        return candidates

    def rank(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput,
    ) -> List[RankedSecurity]:
        """Rank candidates (all + top tiers + confidence)."""
        return self._ranking.rank(candidates)

    def construct_portfolio(
        self,
        ranked: List[RankedSecurity],
        selection_input: SelectionInput,
    ) -> PortfolioConstruction:
        """Construct a single- or multi-security portfolio."""
        candidates = [r.security for r in ranked]
        return self._optimizer.optimize(candidates, selection_input)

    def recommend(
        self,
        ranked: List[RankedSecurity],
        portfolio: PortfolioConstruction,
        selection_input: SelectionInput,
    ) -> Recommendation:
        """Build the recommendation from ranked list + constructed portfolio.

        Uses the explainability engine to produce reasons; evaluators
        never hand-write explanations.
        """
        candidates = [r.security for r in ranked]
        selected = portfolio.positions if portfolio.positions else (
            [WeightedPosition(security=candidates[0], weight=1.0)]
            if candidates
            else []
        )
        alternatives = self._alternatives(ranked, selected)
        return self._explainer.recommend(
            selected=selected,
            alternatives=alternatives,
            all_candidates=candidates,
            target=self.target,
        )

    def explain(
        self,
        recommendation: Recommendation,
        ranked: List[RankedSecurity],
        portfolio: PortfolioConstruction,
        selection_input: SelectionInput,
    ) -> Recommendation:
        """Attach explanations via the central :class:`ExplanationEngine`."""
        return recommendation

    def generate_report(
        self,
        ranked: List[RankedSecurity],
        portfolio: PortfolioConstruction,
        recommendation: Recommendation,
        selection_input: SelectionInput,
    ) -> ResearchReport:
        """Generate the institutional research report."""
        return self._reporter.generate(
            asset_class=self.target,
            universe_size=len(ranked) if not ranked else max(
                len([r for r in ranked]), len(ranked)
            ),
            filtered_size=len(ranked),
            ranked=ranked,
            portfolio=portfolio,
            recommendation=recommendation,
            selection_input=selection_input,
        )

    # ── helpers ─────────────────────────────────────────────────────

    def _tax_status(self, payload: ProviderPayload) -> str:
        """Default tax-status for a payload (override per asset class)."""
        meta = payload.snapshot.extra if payload.snapshot else {}
        return str(meta.get("tax_treatment") or meta.get("tax_status") or "debt_slab")

    def _region(self, payload: ProviderPayload) -> str:
        """Default market region for a payload (override per asset class)."""
        return "india"

    def _alternatives(
        self, ranked: List[RankedSecurity], selected: List[Any]
    ) -> List[CandidateSecurity]:
        """Pick alternatives = top-ranked securities not in the selection."""
        selected_keys = {p.security.key for p in selected}
        alt = [
            r.security
            for r in ranked
            if r.security.key not in selected_keys
        ]
        count = self._config.ranking.alternative_count
        return alt[:count]

    def _quality_report(self, payload: ProviderPayload) -> QualityReport:
        return self._quality.validate_payload(payload)


def _as_candidate(identity: SecurityIdentity, evaluator: "BaseEvaluator") -> CandidateSecurity:
    """Build a minimal candidate for the universe listing."""
    return CandidateSecurity(
        identity=identity,
        kind=evaluator.kind,
        asset_class=evaluator.target,
        bucket=evaluator.bucket,
    )




