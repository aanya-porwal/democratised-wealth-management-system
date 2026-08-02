"""Data models for the wealth management system.

This package is the home of every data definition in the system.

* ``base`` — the original data models (``UserProfile``, ``FinancialProfile``,
  ``BehavioralProfile``, ``Goal``, ``RiskAssessment``, ``AssetClassProfile``
  and the enums). Everything from ``base`` is re-exported here so the
  legacy import ``from wealth_management_system.models import Goal`` keeps
  working exactly as before.
* ``allocation``, ``goal``, ``health``, ``optimization``, ``portfolio``,
  ``rebalancing``, ``recommendation``, ``scenario``, ``simulation`` —
  engine I/O models added by the production transformation.

The package deliberately contains no business logic; engines implement it.
"""

from wealth_management_system.models.base import (
    AssetCategory,
    AssetClass,
    AssetClassProfile,
    BehavioralProfile,
    DeductionBenefit,
    EmploymentType,
    FinancialProfile,
    Goal,
    GoalPriority,
    GoalType,
    RiskAssessment,
    RiskToleranceLevel,
    TaxTreatment,
    UserProfile,
)

from wealth_management_system.models.allocation import (
    AllocationEngineInput,
    AllocationResult,
    BucketAllocation,
    LiquidityNeed,
)
from wealth_management_system.models.goal import (
    GoalAnalysis,
    GoalAnalysisResult,
    GoalVerdict,
)
from wealth_management_system.models.health import (
    HealthFactorScore,
    HealthScoreResult,
)
from wealth_management_system.models.optimization import OptimizationInput, OptimizationResult
from wealth_management_system.models.portfolio import (
    Holding,
    PortfolioHoldings,
    Trade,
)
from wealth_management_system.models.rebalancing import (
    RebalanceAction,
    RebalanceDirection,
    RebalanceResult,
)
from wealth_management_system.models.recommendation import (
    ConfidenceLevel,
    Recommendation,
    RecommendationReason,
    RecommendationType,
)
from wealth_management_system.models.scenario import (
    Scenario,
    ScenarioType,
    ScenarioVariant,
)
from wealth_management_system.models.simulation import (
    SimulationResult,
    SimulationStatistics,
)

__all__ = [
    # legacy base models (backward-compatible)
    "AssetCategory",
    "AssetClass",
    "AssetClassProfile",
    "BehavioralProfile",
    "DeductionBenefit",
    "EmploymentType",
    "FinancialProfile",
    "Goal",
    "GoalPriority",
    "GoalType",
    "RiskAssessment",
    "RiskToleranceLevel",
    "TaxTreatment",
    "UserProfile",
    # new engine models
    "AllocationEngineInput",
    "AllocationResult",
    "BucketAllocation",
    "LiquidityNeed",
    "GoalAnalysis",
    "GoalAnalysisResult",
    "GoalVerdict",
    "HealthFactorScore",
    "HealthScoreResult",
    "OptimizationInput",
    "OptimizationResult",
    "Holding",
    "PortfolioHoldings",
    "Trade",
    "RebalanceAction",
    "RebalanceDirection",
    "RebalanceResult",
    "ConfidenceLevel",
    "Recommendation",
    "RecommendationReason",
    "RecommendationType",
    "Scenario",
    "ScenarioType",
    "ScenarioVariant",
    "SimulationResult",
    "SimulationStatistics",
]
