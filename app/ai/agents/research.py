"""ResearchAgent — fund/ETF/stock/bond comparison and research reports."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult
from app.ai.tools.registry import ToolRegistry


class ResearchAgent(BaseAgent):
    """Research securities using the Security Selection Engine."""

    name: AgentName = AgentName.RESEARCH
    description: str = "Fund/ETF/stock/bond comparison, research reports, security rankings"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        try:
            result = ToolRegistry.execute("research_tool", query=user_input)
            return AgentResult(
                agent=self.name, status="success",
                message="Research completed.",
                output={"research": result},
            )
        except Exception as exc:
            return AgentResult(
                agent=self.name, status="failed",
                message=f"Research failed: {exc}",
            )
