"""Factor scoring subsystem.

Each factor is an independent class implementing :class:`BaseFactor`.
The overall score combines factor scores using configurable weights via
an :class:`IScoringModel` (default: :class:`WeightedScoreModel`). Future
ML models plug into the same interface.
"""

from security_selection.scoring.factors import (
    BaseFactor,
    CostFactor,
    CreditQualityFactor,
    DiversificationFactor,
    ExpectedReturnFactor,
    LiquidityFactor,
    MarketExposureFactor,
    QualityFactor,
    RiskFactor,
    TaxFactor,
    TrackingFactor,
    build_factors,
)
from security_selection.scoring.models import (
    IScoringModel,
    WeightedScoreModel,
    FeatureBuilder,
    DatasetBuilder,
)
from security_selection.scoring.engine import ScoringEngine

__all__ = [
    "BaseFactor",
    "ExpectedReturnFactor",
    "RiskFactor",
    "CostFactor",
    "LiquidityFactor",
    "QualityFactor",
    "DiversificationFactor",
    "TaxFactor",
    "TrackingFactor",
    "CreditQualityFactor",
    "MarketExposureFactor",
    "build_factors",
    "IScoringModel",
    "WeightedScoreModel",
    "FeatureBuilder",
    "DatasetBuilder",
    "ScoringEngine",
]

