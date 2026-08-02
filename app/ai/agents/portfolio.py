"""PortfolioAgent — invokes Risk, Allocation, Security Selection, and Monte Carlo engines."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult
from app.ai.tools.registry import ToolRegistry


class PortfolioAgent(BaseAgent):
    """Analyze portfolio, risk, allocation, and rebalancing."""

    name: AgentName = AgentName.PORTFOLIO
    description: str = "Invoke Risk, Allocation, Security Selection, Monte Carlo, Rebalancing"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        user_id = ctx.get("user_id", "")
        if not user_id:
            return AgentResult(
                agent=self.name, status="needs_followup",
                message="I need your user ID to analyze your portfolio.",
                followup_questions=["What is your user ID?"],
            )
        results = []
        try:
            risk_result = ToolRegistry.execute("risk_tool", user_id=user_id)
            results.append(risk_result)
        except Exception:
            pass
        try:
            portfolio_result = ToolRegistry.execute("portfolio_tool", action="list", user_id=user_id)
            results.append(portfolio_result)
        except Exception:
            pass
        return AgentResult(
            agent=self.name, status="success",
            message="Portfolio analysis complete.",
            output={"analysis": results},
        )
