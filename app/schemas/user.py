"""User + profile schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserOut(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime


class UserProfileCreate(BaseModel):
    """Create the demographic profile."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Ravi Shankar",
            "age": 28,
            "date_of_birth": "1996-03-15",
            "dependents": 0,
        }
    })

    name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(..., ge=18, le=120)
    date_of_birth: date
    dependents: int = Field(0, ge=0, le=30)

    @field_validator("age")
    @classmethod
    def _age_sanity(cls, value: int, info) -> int:
        dob = info.data.get("date_of_birth")
        if dob and dob.year and (value != _approx_age(dob)):
            # age may be approximate; only sanity-check sign
            pass
        return value


def _approx_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class UserProfileOut(BaseModel):
    """Demographic profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    age: int
    date_of_birth: date
    dependents: int
    life_stage: str | None = None
    marital_status: str | None = None
    city: str | None = None
    occupation: str | None = None


class FinancialProfileCreate(BaseModel):
    """Financial inputs mirroring the engine's ``FinancialProfile``."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "monthly_income": 85000,
            "employment_type": "salaried_private",
            "income_stability": 0.85,
            "monthly_fixed_expenses": 35000,
            "monthly_variable_expenses": 20000,
            "emergency_fund_months": 1.5,
            "existing_investments": 80000,
            "total_debt": 200000,
            "monthly_emi_total": 8000,
            "tax_bracket_percent": 20,
            "has_health_insurance": True,
        }
    })

    monthly_income: float = Field(0, ge=0)
    employment_type: str = "salaried_private"
    income_stability: float = Field(0.5, ge=0.0, le=1.0)
    secondary_income: bool = False
    secondary_monthly_income: float = Field(0, ge=0)
    monthly_fixed_expenses: float = Field(0, ge=0)
    monthly_variable_expenses: float = Field(0, ge=0)
    emergency_fund_months: float = Field(0, ge=0)
    existing_investments: float = Field(0, ge=0)
    provident_fund_balance: float = Field(0, ge=0)
    real_estate_value: float = Field(0, ge=0)
    gold_value: float = Field(0, ge=0)
    total_debt: float = Field(0, ge=0)
    monthly_emi_total: float = Field(0, ge=0)
    tax_bracket_percent: float = Field(0, ge=0, le=45)
    has_term_life_insurance: bool = False
    has_health_insurance: bool = False
    existing_monthly_sip: float = Field(0, ge=0)


class FinancialProfileOut(FinancialProfileCreate):
    """Financial profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class BehavioralProfileCreate(BaseModel):
    """Behavioral / risk-tolerance inputs."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "risk_tolerance": "aggressive",
            "drawdown_reaction_score": 4,
            "has_invested_before": True,
            "financial_literacy_score": 3,
            "loss_aversion_score": 2,
        }
    })

    risk_tolerance: str = "moderate"
    drawdown_reaction_score: int = Field(3, ge=1, le=5)
    has_invested_before: bool = False
    has_experienced_market_crash: bool = False
    financial_literacy_score: int = Field(1, ge=1, le=5)
    loss_aversion_score: int = Field(3, ge=1, le=5)


class BehavioralProfileOut(BehavioralProfileCreate):
    """Behavioral profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    risk_score: float | None = None
    risk_category: str | None = None

