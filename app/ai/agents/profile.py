"""ProfileAgent — understands user information, updates profile, detects missing info."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult
from app.ai.tools.registry import ToolRegistry


class ProfileAgent(BaseAgent):
    """Manages user profiles — demographic, financial, behavioral."""

    name: AgentName = AgentName.PROFILE
    description: str = "Understand user info, update profile, detect missing information"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        user_id = ctx.get("user_id", "")
        if not user_id:
            return AgentResult(
                agent=self.name, status="needs_followup",
                message="I need to know who you are. Please provide your user ID.",
                followup_questions=["What is your user ID?"],
            )
        tool_results = []
        try:
            result = ToolRegistry.execute("profile_tool", action="get_user_profile", user_id=user_id)
            tool_results.append(result)
        except Exception as exc:
            return AgentResult(
                agent=self.name, status="failed",
                message=f"Could not retrieve profile: {exc}",
            )
        return AgentResult(
            agent=self.name, status="success",
            message="Profile retrieved successfully.",
            output={"profile": tool_results},
            tool_results=[],
        )
