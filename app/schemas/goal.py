"""Goal + goal-progress schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Valid engine goal types (from wealth_management_system.models.base.GoalType)
GOAL_TYPES = {
    "emergency_fund", "home_purchase", "vehicle", "education_self",
    "education_child", "wedding", "travel", "retirement",
    "wealth_creation", "other",
}
GOAL_PRIORITIES = {"critical", "high", "aspirational"}


class GoalCreate(BaseModel):
    """Create a financial goal."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Retirement corpus",
            "goal_type": "retirement",
            "priority": "high",
            "target_amount": 15000000,
            "target_date": "2045-01-01",
            "current_savings_for_goal": 500000,
            "current_monthly_contribution": 15000,
        }
    })

    name: str = Field("", max_length=255)
    goal_type: str = Field(..., pattern="|".join(sorted(GOAL_TYPES)))
    priority: str = Field("high", pattern="|".join(sorted(GOAL_PRIORITIES)))
    target_amount: float = Field(..., gt=0)
    target_date: date
    current_savings_for_goal: float = Field(0, ge=0)
    current_monthly_contribution: float = Field(0, ge=0)
    notes: str = Field("", max_length=2000)

    @field_validator("target_date")
    @classmethod
    def _target_not_in_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("target_date cannot be in the past")
        return value


class GoalUpdate(BaseModel):
    """Partial update of a goal."""

    name: str | None = Field(None, max_length=255)
    goal_type: str | None = Field(None, pattern="|".join(sorted(GOAL_TYPES)))
    priority: str | None = Field(None, pattern="|".join(sorted(GOAL_PRIORITIES)))
    target_amount: float | None = Field(None, gt=0)
    target_date: date | None = None
    current_savings_for_goal: float | None = Field(None, ge=0)
    current_monthly_contribution: float | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)


class GoalOut(BaseModel):
    """Goal response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    goal_type: str
    priority: str
    target_amount: float
    target_date: date
    current_savings_for_goal: float
    current_monthly_contribution: float
    notes: str
    created_at: datetime
    updated_at: datetime


class GoalProgressOut(BaseModel):
    """Goal progress snapshot response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    recorded_at: datetime
    current_savings: float
    progress_percent: float
    probability_of_success: float | None = None
    required_sip: float | None = None
    remaining_gap: float | None = None


class GoalAnalysisOut(BaseModel):
    """Engine goal analysis response (from GoalEngine.analyse)."""

    name: str
    goal_type: str
    priority: str
    current_amount: float
    target_amount: float
    current_progress: float
    target_date: date
    years_remaining: float
    inflation_rate: float
    expected_return: float
    inflation_adjusted_target: float
    future_value: float
    present_value: float
    required_sip: float
    remaining_gap: float
    expected_corpus: float | None = None
    probability_of_success: float | None = None
    verdict: str = "not_applicable"
    notes: list[str] = []

