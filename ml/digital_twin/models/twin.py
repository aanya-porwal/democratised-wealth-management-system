"""Digital Twin core models.

A :class:`DigitalTwin` is a persistent, evolving representation of a
person's *entire* financial life. It maintains the current state
(demographics, finances, portfolio, goals, behaviour, risk, etc.) along
with a reference to the event timeline that produced that state.

The twin is intentionally a *mutable* current-state view, but the
underlying history is immutable: every change is appended as an event
and the twin state is re-derived from the timeline. This means the twin
can be replayed to any point in time without ever losing history.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ml.digital_twin.events.event import EventType, FinancialEvent
from ml.models import (
    BehaviourTraits,
    CityTier,
    EducationLevel,
    FinancialTwinProfile,
    Gender,
    Industry,
    Occupation,
    RiskTolerance,
)


def _default_profile() -> FinancialTwinProfile:
    """Create a minimal empty profile for a yet-uninitialised twin."""
    return FinancialTwinProfile(
        person_id="",
        age=0,
        gender=Gender.MALE,
        city_tier=CityTier.TIER1,
        occupation=Occupation.OTHER,
        industry=Industry.OTHER,
        education=EducationLevel.HIGH_SCHOOL,
    )


@dataclass
class PortfolioState:
    """Current allocation of a twin's investment portfolio.

    ``holdings`` maps asset_class -> market value. ``weights`` maps
    asset_class -> fraction of total (0..1). These are derived from the
    deterministic engine's allocation logic; the twin only records the
    outcome.
    """

    total_value: float = 0.0
    holdings: Dict[str, float] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)
    cash: float = 0.0
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_value": self.total_value,
            "holdings": self.holdings,
            "weights": self.weights,
            "cash": self.cash,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class GoalState:
    """A single goal and its current funding progress."""

    goal_id: str
    goal_type: str
    priority: str
    target_amount: float
    target_date: Optional[datetime]
    current_savings: float = 0.0
    monthly_contribution: float = 0.0
    on_track: bool = True

    @property
    def progress_percent(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        return min(100.0, self.current_savings / self.target_amount * 100.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_type": self.goal_type,
            "priority": self.priority,
            "target_amount": self.target_amount,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "current_savings": self.current_savings,
            "monthly_contribution": self.monthly_contribution,
            "on_track": self.on_track,
            "progress_percent": self.progress_percent,
        }


@dataclass
class LifeSnapshot:
    """A point-in-time snapshot of a twin's complete financial state.

    Snapshots are emitted periodically (e.g. yearly) and on significant
    events. They give the ML layer and the analytics engine a clean,
    denormalised view of the twin at a moment in time.
    """

    twin_id: str
    timestamp: datetime
    age: int
    monthly_income: float
    monthly_expenses: float
    monthly_savings: float
    net_worth: float
    portfolio: PortfolioState = field(default_factory=PortfolioState)
    goals: List[GoalState] = field(default_factory=list)
    total_debt: float = 0.0
    emergency_fund_months: float = 0.0
    risk_profile: RiskTolerance = RiskTolerance.MODERATE
    behaviour: BehaviourTraits = field(default_factory=BehaviourTraits)
    financial_health_score: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "timestamp": self.timestamp.isoformat(),
            "age": self.age,
            "monthly_income": self.monthly_income,
            "monthly_expenses": self.monthly_expenses,
            "monthly_savings": self.monthly_savings,
            "net_worth": self.net_worth,
            "portfolio": self.portfolio.to_dict(),
            "goals": [g.to_dict() for g in self.goals],
            "total_debt": self.total_debt,
            "emergency_fund_months": self.emergency_fund_months,
            "risk_profile": self.risk_profile.value,
            "behaviour": self.behaviour.to_dict(),
            "financial_health_score": self.financial_health_score,
            "extra": self.extra,
        }


@dataclass
class DigitalTwin:
    """A persistent, evolving financial twin.

    The twin holds the *current* state as well as the identity and
    metadata. The full history lives in the timeline (see
    :mod:`ml.digital_twin.timeline`); the twin itself is the projected
    "latest" state.

    Attributes
    ----------
    twin_id:
        Unique identifier for the twin.
    profile:
        The base :class:`FinancialTwinProfile` (demographics + finances).
    behaviour:
        Current behavioural traits (may drift over time).
    risk_profile:
        Current risk profile.
    portfolio:
        Current portfolio state.
    goals:
        Current goals.
    net_worth_history:
        In-memory cache of net worth over time (used by analytics).
    financial_health_history:
        In-memory cache of financial health scores over time.
    """

    twin_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    profile: FinancialTwinProfile = field(default_factory=_default_profile)
    behaviour: BehaviourTraits = field(default_factory=BehaviourTraits.default)
    risk_profile: RiskTolerance = RiskTolerance.MODERATE
    portfolio: PortfolioState = field(default_factory=PortfolioState)
    goals: List[GoalState] = field(default_factory=list)
    total_debt: float = 0.0
    emergency_fund_months: float = 0.0
    financial_health_score: float = 0.0
    is_alive: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # History caches (kept in sync by the service layer)
    net_worth_history: List[Dict[str, Any]] = field(default_factory=list)
    financial_health_history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def age(self) -> int:
        return self.profile.age

    @property
    def net_worth(self) -> float:
        return self.profile.net_worth

    def apply_event(self, event: FinancialEvent) -> None:
        """Apply a single event to update the twin's current state.

        This is the *projection* step. The event has already been
        appended to the timeline; this method replays its effect onto
        the mutable current state. Deterministic calculations are never
        performed here - only state bookkeeping.
        """
        self.last_updated = event.timestamp
        payload = event.payload

        if event.event_type == EventType.PROFILE_CREATED:
            if "profile" in payload:
                self.profile = payload["profile"]
        elif event.event_type == EventType.SALARY_CHANGE:
            if "monthly_income" in payload:
                self.profile.monthly_income = payload["monthly_income"]
        elif event.event_type == EventType.PROMOTION:
            if "monthly_income" in payload:
                self.profile.monthly_income = payload["monthly_income"]
            if "salary_growth_rate" in payload:
                self.profile.salary_growth_rate = payload["salary_growth_rate"]
        elif event.event_type == EventType.JOB_LOSS:
            self.profile.monthly_income = 0.0
        elif event.event_type == EventType.CAREER_SWITCH:
            if "occupation" in payload:
                self.profile.occupation = payload["occupation"]
            if "monthly_income" in payload:
                self.profile.monthly_income = payload["monthly_income"]
        elif event.event_type == EventType.RETIREMENT:
            self.is_alive = True
            if "monthly_income" in payload:
                self.profile.monthly_income = payload["monthly_income"]
        elif event.event_type == EventType.MARRIAGE:
            if "marital_status" in payload:
                self.profile.marital_status = payload["marital_status"]
        elif event.event_type == EventType.CHILD_BIRTH:
            self.profile.dependents += 1
        elif event.event_type == EventType.DEPENDENT_CHANGE:
            if "dependents" in payload:
                self.profile.dependents = payload["dependents"]
        elif event.event_type == EventType.INHERITANCE:
            if "amount" in payload:
                self.profile.existing_investments += payload["amount"]
        elif event.event_type == EventType.HOUSE_PURCHASE:
            if "debt" in payload:
                self.total_debt += payload["debt"]
            if "emi" in payload:
                self.profile.monthly_emi_total += payload["emi"]
        elif event.event_type == EventType.VEHICLE_PURCHASE:
            if "debt" in payload:
                self.total_debt += payload["debt"]
            if "emi" in payload:
                self.profile.monthly_emi_total += payload["emi"]
        elif event.event_type == EventType.LOAN_TAKEN:
            if "debt" in payload:
                self.total_debt += payload["debt"]
            if "emi" in payload:
                self.profile.monthly_emi_total += payload["emi"]
        elif event.event_type == EventType.LOAN_REPAID:
            if "debt" in payload:
                self.total_debt = max(0.0, self.total_debt - payload["debt"])
            if "emi" in payload:
                self.profile.monthly_emi_total = max(
                    0.0, self.profile.monthly_emi_total - payload["emi"]
                )
        elif event.event_type == EventType.MEDICAL_EMERGENCY:
            if "cost" in payload:
                self.profile.existing_investments = max(
                    0.0, self.profile.existing_investments - payload["cost"]
                )
        elif event.event_type == EventType.PORTFOLIO_CHANGE:
            if "holdings" in payload:
                self.portfolio.holdings = payload["holdings"]
                self.portfolio.total_value = sum(payload["holdings"].values())
            if "cash" in payload:
                self.portfolio.cash = payload["cash"]
            if "weights" in payload:
                self.portfolio.weights = payload["weights"]
            self.portfolio.updated_at = event.timestamp
        elif event.event_type == EventType.MARKET_MOVEMENT:
            # Revalue existing holdings by market returns
            if "returns" in payload:
                for asset, ret in payload["returns"].items():
                    if asset in self.portfolio.holdings:
                        self.portfolio.holdings[asset] *= (1.0 + ret)
                self.portfolio.total_value = sum(self.portfolio.holdings.values())
                self.portfolio.updated_at = event.timestamp
        elif event.event_type == EventType.INVESTMENT_ADDED:
            if "asset" in payload and "amount" in payload:
                asset = payload["asset"]
                self.portfolio.holdings[asset] = (
                    self.portfolio.holdings.get(asset, 0.0) + payload["amount"]
                )
                self.portfolio.total_value = sum(self.portfolio.holdings.values())
                self.portfolio.updated_at = event.timestamp
        elif event.event_type == EventType.INSURANCE_ADDED:
            if "term_life" in payload:
                self.profile.has_term_life_insurance = payload["term_life"]
            if "health" in payload:
                self.profile.has_health_insurance = payload["health"]
        elif event.event_type == EventType.BEHAVIOUR_CHANGE:
            if "behaviour" in payload:
                self.behaviour = payload["behaviour"]
        elif event.event_type == EventType.RISK_PROFILE_CHANGE:
            if "risk_profile" in payload:
                self.risk_profile = payload["risk_profile"]
                self.profile.risk_profile = payload["risk_profile"]
        elif event.event_type == EventType.DEATH:
            self.is_alive = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "profile": self.profile.to_dict(),
            "behaviour": self.behaviour.to_dict(),
            "risk_profile": self.risk_profile.value,
            "portfolio": self.portfolio.to_dict(),
            "goals": [g.to_dict() for g in self.goals],
            "total_debt": self.total_debt,
            "emergency_fund_months": self.emergency_fund_months,
            "financial_health_score": self.financial_health_score,
            "is_alive": self.is_alive,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "net_worth": self.net_worth,
        }
