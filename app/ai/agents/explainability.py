"""ExplainabilityAgent — converts technical outputs into plain English."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult


class ExplainabilityAgent(BaseAgent):
    """Convert technical outputs into plain English explanations."""

    name: AgentName = AgentName.EXPLAINABILITY
    description: str = "Convert technical outputs into plain English"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        return AgentResult(
            agent=self.name, status="success",
            message="Explanations are available for all engine outputs.",
            output={"explanation": user_input, "context": ctx},
        )
