"""ScenarioAgent — what-if scenario analysis using the engine."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult
from app.ai.tools.registry import ToolRegistry


class ScenarioAgent(BaseAgent):
    """Run what-if scenario analyses."""

    name: AgentName = AgentName.SCENARIO
    description: str = "Support salary change, marriage, children, job loss, market crash, etc."

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        user_id = ctx.get("user_id", "")
        scenario_type = ctx.get("scenario_type", "market_crash")
        if not user_id:
            return AgentResult(
                agent=self.name, status="needs_followup",
                message="I need your user ID to run scenario analysis.",
                followup_questions=["What is your user ID?"],
            )
        try:
            result = ToolRegistry.execute(
                "scenario_tool", user_id=user_id, scenario_type=scenario_type,
            )
            return AgentResult(
                agent=self.name, status="success",
                message="Scenario analysis complete.",
                output={"scenario": result},
            )
        except Exception as exc:
            return AgentResult(
                agent=self.name, status="failed",
                message=f"Scenario analysis failed: {exc}",
            )
