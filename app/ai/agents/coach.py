"""FinancialCoachAgent — generates proactive guidance and financial education."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult
from app.ai.tools.registry import ToolRegistry


class CoachAgent(BaseAgent):
    """Generate proactive financial guidance and education."""

    name: AgentName = AgentName.COACH
    description: str = "Generate proactive guidance: emergency fund, portfolio drift, tax season, etc."

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        user_id = ctx.get("user_id", "")
        guidance = []
        if user_id:
            try:
                health = ToolRegistry.execute("health_score_tool", user_id=user_id)
                guidance.append(health)
            except Exception:
                pass
        return AgentResult(
            agent=self.name, status="success",
            message="Here's my financial guidance based on your situation.",
            output={"guidance": guidance, "user_input": user_input},
        )
