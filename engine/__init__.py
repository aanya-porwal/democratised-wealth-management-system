"""Thin re-export shim over the real financial engine.

The actual engine lives at ``wealth_management_system/`` and is kept
100% untouched so its existing test suite remains green. This ``engine/``
package exists only because the target project layout calls the engine
folder ``engine/``; it forwards every public symbol without adding or
duplicating any business logic.
"""

from wealth_management_system.config import (  # noqa: F401
    AssetConfig,
    GoalConfig,
    HealthConfig,
    InflationConfig,
    OptimizationConfig,
    RebalancingConfig,
    RiskConfig,
    ScenarioConfig,
    SimulationConfig,
    TaxConfig,
    WealthConfig,
    get_config,
    load_config,
    reset_config_cache,
)
from wealth_management_system.exceptions import (  # noqa: F401
    AllocationError,
    ConfigurationError,
    GoalError,
    OptimizationError,
    RebalancingError,
    SimulationError,
    ValidationError,
    WealthManagementError,
)
from wealth_management_system.allocation import AllocationEngine  # noqa: F401
from wealth_management_system.goals import GoalEngine  # noqa: F401
from wealth_management_system.optimization import Optimizer  # noqa: F401
from wealth_management_system.rebalancing import RebalancingEngine  # noqa: F401
from wealth_management_system.recommendation import RecommendationEngine  # noqa: F401
from wealth_management_system.score import HealthScoreEngine  # noqa: F401
from wealth_management_system.simulation import MonteCarloEngine, ScenarioEngine  # noqa: F401

# additional engine functions/models used by services
from wealth_management_system.risk_engine import assess_risk  # noqa: F401
from wealth_management_system.planner import build_plan, FinancialPlan  # noqa: F401
from wealth_management_system.models import (  # noqa: F401
    AllocationEngineInput,
    AllocationResult,
    AssetClass,
    BehavioralProfile as EngineBehavioralProfile,
    FinancialProfile as EngineFinancialProfile,
    Goal as EngineGoal,
    GoalAnalysis,
    GoalAnalysisResult,
    GoalPriority,
    GoalType,
    HealthFactorScore,
    HealthScoreResult,
    Holding,
    LiquidityNeed,
    PortfolioHoldings,
    RebalanceResult,
    Recommendation,
    Scenario,
    ScenarioType,
    SimulationResult,
    SimulationStatistics,
    UserProfile,
)

__all__ = [
    "get_config",
    "load_config",
    "reset_config_cache",
    "WealthManagementError",
    "ValidationError",
    "GoalError",
    "SimulationError",
    "OptimizationError",
    "AllocationError",
    "RebalancingError",
    "ConfigurationError",
    "GoalEngine",
    "AllocationEngine",
    "HealthScoreEngine",
    "RecommendationEngine",
    "RebalancingEngine",
    "MonteCarloEngine",
    "ScenarioEngine",
    "Optimizer",
    "assess_risk",
    "build_plan",
    "FinancialPlan",
    "AllocationEngineInput",
    "AllocationResult",
    "AssetClass",
    "EngineBehavioralProfile",
    "EngineFinancialProfile",
    "EngineGoal",
    "GoalAnalysis",
    "GoalAnalysisResult",
    "GoalPriority",
    "GoalType",
    "HealthFactorScore",
    "HealthScoreResult",
    "Holding",
    "LiquidityNeed",
    "PortfolioHoldings",
    "RebalanceResult",
    "Recommendation",
    "Scenario",
    "ScenarioType",
    "SimulationResult",
    "SimulationStatistics",
    "UserProfile",
]

