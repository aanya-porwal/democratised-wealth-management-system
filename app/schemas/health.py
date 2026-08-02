"""Financial health score schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthFactorOut(BaseModel):
    """One factor's contribution to the health score."""

    name: str
    score: float
    max_points: float
    severity: str
    message: str
    percentage: float


class HealthScoreOut(BaseModel):
    """Health score response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    scored_at: datetime | None = None
    score: int
    grade: str
    factors: list[HealthFactorOut] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []

