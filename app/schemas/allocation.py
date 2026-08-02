"""Allocation schemas — strategic target allocation outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BucketOut(BaseModel):
    """One strategic bucket's target weight and suggested instruments."""

    bucket: str
    weight: float = Field(..., ge=0, le=1)
    instruments: list[str] = []


class AllocationRequest(BaseModel):
    """Optional overrides for the allocation engine."""

    model_config = {"json_schema_extra": {
        "example": {"risk_score": None, "horizon_years": 15, "liquidity_need": "low"}
    }}

    risk_score: int | None = Field(None, ge=0, le=100, description="Override risk score 0-100")
    horizon_years: float | None = Field(None, gt=0, description="Investment horizon in years")
    liquidity_need: str | None = Field(
        None, pattern="very_high|high|medium|low",
        description="Liquidity preference override",
    )
    monthly_investment: float | None = Field(None, ge=0)


class AllocationOut(BaseModel):
    """Strategic allocation response."""

    buckets: list[BucketOut]
    risk_score: int
    risk_category: str
    explanation: str

