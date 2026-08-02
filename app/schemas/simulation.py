"""Simulation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SimulationCreate(BaseModel):
    """Create a Monte Carlo simulation run (service input)."""

    model_config = {"json_schema_extra": {
        "example": {
            "expected_return": 0.12,
            "volatility": 0.18,
            "monthly_investment": 15000,
            "inflation": 0.06,
            "horizon_years": 20,
            "initial_corpus": 500000,
            "target_amount": 20000000,
            "simulations": 10000,
        }
    }}

    expected_return: float = Field(..., gt=-1)
    volatility: float = Field(..., ge=0)
    monthly_investment: float = Field(0, ge=0)
    inflation: float = Field(0.06, ge=0)
    horizon_years: float = Field(..., gt=0)
    initial_corpus: float = Field(0, ge=0)
    target_amount: float | None = Field(None, gt=0)
    simulations: int = Field(10000, ge=100, le=100000)
    goal_id: uuid.UUID | None = None
    simulation_type: str = Field("monte_carlo", pattern="monte_carlo")


class ScenarioCreate(BaseModel):
    """Create a scenario analysis run (service input)."""

    scenario_type: str = Field(..., pattern="salary_increase|salary_decrease|market_crash|early_retirement|delayed_retirement|house_purchase|child_education|marriage|emergency_expense")
    name: str | None = None
    description: str | None = None
    income_multiplier: float | None = None
    expense_multiplier: float | None = None
    portfolio_drawdown: float | None = None
    one_time_expense: float | None = None
    monthly_contribution_adjustment: float | None = None
    emergency_fund_months: float | None = None
    retirement_age: int | None = None
    target_date_shift_years: float | None = None
    simulations: int = Field(10000, ge=100, le=100000)


class SimulationRequest(BaseModel):
    """Parameters for a Monte Carlo simulation."""

    model_config = {"json_schema_extra": {
        "example": {
            "expected_return": 0.12,
            "volatility": 0.18,
            "monthly_investment": 15000,
            "inflation": 0.06,
            "horizon_years": 20,
            "initial_corpus": 500000,
            "target_amount": 20000000,
            "simulations": 10000,
        }
    }}

    expected_return: float = Field(..., gt=-1)
    volatility: float = Field(..., ge=0)
    monthly_investment: float = Field(0, ge=0)
    inflation: float = Field(0.06, ge=0)
    horizon_years: float = Field(..., gt=0)
    initial_corpus: float = Field(0, ge=0)
    target_amount: float | None = Field(None, gt=0)
    simulations: int = Field(10000, ge=100, le=100000)
    goal_id: uuid.UUID | None = None


class SimulationStatisticsOut(BaseModel):
    """Summary statistics of a simulated corpus distribution."""

    median: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    worst_case: float
    best_case: float
    mean: float
    std_dev: float
    probability_of_success: float


class SimulationOut(BaseModel):
    """Simulation result response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    goal_id: uuid.UUID | None = None
    run_at: datetime
    simulations: int
    horizon_years: float
    expected_return: float
    volatility: float
    inflation: float
    monthly_investment: float
    initial_corpus: float
    target_amount: float | None = None
    statistics: SimulationStatisticsOut | None = None
    percentiles: dict | None = None


class ScenarioRequest(BaseModel):
    """A what-if scenario to apply."""

    scenario_type: str = Field(..., pattern="salary_increase|salary_decrease|market_crash|early_retirement|delayed_retirement|house_purchase|child_education|marriage|emergency_expense")
    name: str | None = None
    description: str | None = None
    income_multiplier: float | None = None
    expense_multiplier: float | None = None
    portfolio_drawdown: float | None = None
    one_time_expense: float | None = None
    monthly_contribution_adjustment: float | None = None
    emergency_fund_months: float | None = None
    retirement_age: int | None = None
    target_date_shift_years: float | None = None


class ScenarioOut(BaseModel):
    """Scenario analysis response."""

    id: uuid.UUID | None = None
    run_at: datetime | None = None
    scenario_type: str
    name: str
    description: str | None = None
    goal_probabilities: dict[str, float] = {}
    total_required_sip: float | None = None
    net_worth: float | None = None
    allocation: dict[str, float] = {}
    summary: str = ""

