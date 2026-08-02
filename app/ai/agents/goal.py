"""GoalAgent — understands, creates, modifies, and tracks goals via the Goal Engine."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult
from app.ai.tools.registry import ToolRegistry


class GoalAgent(BaseAgent):
    """Analyze, create, list, and track financial goals."""

    name: AgentName = AgentName.GOAL
    description: str = "Understand, create, modify, delete goals; invoke Goal Engine"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        user_id = ctx.get("user_id", "")
        if not user_id:
            return AgentResult(
                agent=self.name, status="needs_followup",
                message="I need your user ID to analyze your goals.",
                followup_questions=["What is your user ID?"],
            )
        try:
            result = ToolRegistry.execute("goal_tool", action="analyse_all", user_id=user_id)
            return AgentResult(
                agent=self.name, status="success",
                message="Goals analyzed successfully.",
                output={"goal_analysis": result},
            )
        except Exception as exc:
            return AgentResult(
                agent=self.name, status="failed",
                message=f"Could not analyze goals: {exc}",
            )
