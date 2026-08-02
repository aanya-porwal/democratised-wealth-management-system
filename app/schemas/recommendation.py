"""Recommendation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecommendationOut(BaseModel):
    """A persisted recommendation response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recommendation_type: str
    title: str
    description: str
    confidence: str
    reasons: list | None = None
    action: str | None = None
    impact: str | None = None
    priority: float | None = None
    status: str
    created_at: datetime


class RecommendationActionUpdate(BaseModel):
    """Update a recommendation's status (e.g. dismissed/completed)."""

    status: str = Field(..., pattern="pending|accepted|dismissed|completed")

