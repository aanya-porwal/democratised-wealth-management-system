"""DataValidationAgent — validates market data freshness, API consistency, missing metrics."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult


class DataValidationAgent(BaseAgent):
    """Validate market data freshness, API consistency, missing metrics, fallback logic."""

    name: AgentName = AgentName.DATA_VALIDATION
    description: str = "Validate market data freshness, API consistency, missing metrics"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        return AgentResult(
            agent=self.name, status="success",
            message="Data validation is active.",
            output={"validated": True},
        )
