"""SQLAlchemy ORM models package.

Each table is a SQLAlchemy 2.0 ``Mapped`` class with UUID primary keys,
``created_at`` / ``updated_at`` / ``deleted_at``, explicit foreign keys
and indexes. These are persistence models only — request/response
validation lives in :mod:`app.schemas` (Pydantic v2).
"""

from app.models.user import Role, User
from app.models.user_profile import UserProfile
from app.models.financial_profile import FinancialProfile
from app.models.behavioral_profile import BehavioralProfile
from app.models.goal import Goal, GoalProgress
from app.models.portfolio import Portfolio, PortfolioHolding, PortfolioSnapshot
from app.models.recommendation import Recommendation
from app.models.health import FinancialHealthScore
from app.models.simulation import SimulationResult, ScenarioAnalysis
from app.models.audit import AuditLog
from app.models.system import ChatSession, MarketDataCache, SystemSetting
from app.models.auth_token import EmailVerificationToken, PasswordResetToken, RefreshToken

__all__ = [
    "Role",
    "User",
    "UserProfile",
    "FinancialProfile",
    "BehavioralProfile",
    "Goal",
    "GoalProgress",
    "Portfolio",
    "PortfolioHolding",
    "PortfolioSnapshot",
    "Recommendation",
    "FinancialHealthScore",
    "SimulationResult",
    "ScenarioAnalysis",
    "AuditLog",
    "ChatSession",
    "MarketDataCache",
    "SystemSetting",
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
]

