"""Pipeline models — the objects that flow through the selection pipeline.

These models form the common interface between every evaluator and the
core engine. Evaluators translate provider-specific data into these
generic containers; the pipeline stages (scoring, ranking, optimization,
reporting, explanation) operate only on these containers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from security_selection.models.data import (
    AvailableMetric,
    HistoricalSeries,
    MarketSnapshot,
    SecurityIdentity,
)
from security_selection.models.enums import (
    AssetClassBucket,
    Confidence,
    NormalizationAxis,
    RecommendationAction,
    SecurityKind,
    TargetAssetClass,
    TaxStatus,
)


@dataclass(frozen=True)
class NormalizedProfile:
    """The normalized 0..1 profile produced by every evaluator.

    Each axis is a 0..1 score (higher = better). ``confidence`` is 0..1
    and reflects how much source data supported the score. ``available``
    is False when the axis could not be computed.
    """

    security_key: str
    expected_return: float = 0.0
    risk: float = 0.0
    liquidity: float = 0.0
    diversification: float = 0.0
    tax_efficiency: float = 0.0
    cost: float = 0.0
    tracking_quality: float = 0.0
    quality: float = 0.0
    market_exposure: float = 0.0
    confidence: float = 0.5
    available: Dict[NormalizationAxis, bool] = field(default_factory=dict)

    def axis(self, name: NormalizationAxis) -> float:
        return getattr(self, name.value)

    def as_dict(self) -> Dict[str, float]:
        return {
            "expected_return": self.expected_return,
            "risk": self.risk,
            "liquidity": self.liquidity,
            "diversification": self.diversification,
            "tax_efficiency": self.tax_efficiency,
            "cost": self.cost,
            "tracking_quality": self.tracking_quality,
            "quality": self.quality,
            "market_exposure": self.market_exposure,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class FactorScore:
    """One factor's contribution to the overall score."""

    factor: str
    score: float  # 0..1
    weight: float  # configured weight
    weighted: float  # score * weight
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateSecurity:
    """A security that survived discovery & data quality checks.

    This is the mutable working object throughout the pipeline; the final
    outputs are derived immutable views.
    """

    identity: SecurityIdentity
    kind: SecurityKind
    asset_class: TargetAssetClass
    bucket: AssetClassBucket
    profile: NormalizedProfile | None = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    unavailable: Dict[str, str] = field(default_factory=dict)
    snapshot: MarketSnapshot | None = None
    history: HistoricalSeries | None = None
    holdings: List[Dict[str, Any]] = field(default_factory=list)
    sector_allocations: Dict[str, float] = field(default_factory=dict)
    country_allocations: Dict[str, float] = field(default_factory=dict)
    factor_scores: List[FactorScore] = field(default_factory=list)
    overall_score: float = 0.0
    data_quality_score: float = 1.0
    data_sources: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return self.identity.key


@dataclass(frozen=True)
class RankedSecurity:
    """An immutable ranked security row."""

    security: CandidateSecurity
    rank: int
    overall_score: float
    confidence: float
    factor_scores: List[FactorScore] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.security.key

    @property
    def identity(self) -> SecurityIdentity:
        return self.security.identity

    @property
    def metrics(self) -> Dict[str, Any]:
        return self.security.metrics


@dataclass(frozen=True)
class WeightedPosition:
    """A security with an assigned portfolio weight."""

    security: CandidateSecurity
    weight: float  # 0..1, sum of all positions = 1
    rationale: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PortfolioConstruction:
    """Result of the portfolio construction step."""

    strategy: str  # "single" | "diversified"
    positions: List[WeightedPosition] = field(default_factory=list)
    reason: str = ""
    constraints_applied: List[str] = field(default_factory=list)

    def total_weight(self) -> float:
        return round(sum(p.weight for p in self.positions), 6)


@dataclass(frozen=True)
class Recommendation:
    """The final investment recommendation."""

    action: RecommendationAction
    confidence: Confidence
    selected: List[WeightedPosition]
    alternatives: List[CandidateSecurity]
    rejected: List[CandidateSecurity]
    explanation: List[str]
    reasons_against_alternatives: List[str] = field(default_factory=list)
    risk_summary: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SecurityDecision:
    """The persisted Investment-Committee-Log entry."""

    user_id: str
    inputs: Dict[str, Any]
    risk_profile: Dict[str, Any]
    allocation: Dict[str, float]
    available_securities: List[str]
    scores: Dict[str, float]
    chosen: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    explanation: List[str]
    model_version: str
    weights_used: Dict[str, float]
    confidence: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class EvaluatorOutput:
    """The complete output of one evaluator run."""

    asset_class: TargetAssetClass
    universe: List[CandidateSecurity]
    filtered: List[CandidateSecurity]
    ranked: List[RankedSecurity]
    portfolio: PortfolioConstruction
    recommendation: Recommendation
    report: "ResearchReport"
    confidence: Confidence


@dataclass(frozen=True)
class SelectionResult:
    """The aggregate outcome of a full selection run across evaluators.

    A single request may target one asset class (one evaluator) or the
    whole book of asset classes (several evaluators). This container
    bundles every evaluator output plus the ordered, deduplicated union
    of all recommendations so the service layer can present them
    uniformly to the API.
    """

    outputs: List[EvaluatorOutput] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def asset_classes(self) -> List[TargetAssetClass]:
        return [o.asset_class for o in self.outputs]

    @property
    def all_ranked(self) -> List[RankedSecurity]:
        out: List[RankedSecurity] = []
        seen: set[str] = set()
        for output in self.outputs:
            for ranked in output.ranked:
                if ranked.key not in seen:
                    out.append(ranked)
                    seen.add(ranked.key)
        return out

    @property
    def all_recommendations(self) -> List[Recommendation]:
        return [o.recommendation for o in self.outputs]


@dataclass(frozen=True)
class ComparisonResult:
    """Result of comparing two or more securities."""

    securities: List[CandidateSecurity]
    winner: str
    advantages: Dict[str, List[str]]
    disadvantages: Dict[str, List[str]]
    comparison_table: Dict[str, Dict[str, Any]]
    metric_labels: Dict[str, str]


@dataclass(frozen=True)
class ResearchReport:
    """Institutional-quality research report."""

    asset_class: TargetAssetClass
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    universe_size: int = 0
    filtered_size: int = 0
    ranking: List[RankedSecurity] = field(default_factory=list)
    metrics_table: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    factor_scores: Dict[str, Dict[str, float]] = field(default_factory=dict)
    strengths: Dict[str, List[str]] = field(default_factory=dict)
    weaknesses: Dict[str, List[str]] = field(default_factory=dict)
    recommendation: str = ""
    alternatives: List[str] = field(default_factory=list)
    risk_summary: List[str] = field(default_factory=list)
    confidence: str = ""
    data_sources_used: List[str] = field(default_factory=list)
    reasons_for_selection: List[str] = field(default_factory=list)
    reasons_against_alternatives: List[str] = field(default_factory=list)
    model_version: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SelectionInput:
    """Everything the selection pipeline needs about a selection request."""

    target_asset_class: TargetAssetClass
    user_id: str | None = None
    risk_profile: Dict[str, Any] = field(default_factory=dict)
    allocation: Dict[str, float] = field(default_factory=dict)
    horizon_years: float | None = None
    monthly_investment: float | None = None
    filter_overrides: Dict[str, Any] = field(default_factory=dict)
    use_cache: bool = True
    candidate_limit: int | None = None

