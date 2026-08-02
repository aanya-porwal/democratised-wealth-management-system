"""PlannerAgent — understands intent, decomposes into subtasks, selects agents."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentPlan, AgentResult, PlannerAction

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Plans the workflow by decomposing user requests into agent actions."""

    name: AgentName = AgentName.PLANNER
    description: str = "Plan workflow by decomposing requests into agent actions"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        plan = self._create_plan(user_input, ctx)
        return AgentResult(
            agent=self.name,
            status="success",
            message=plan.summary,
            output={"plan": plan.model_dump()},
        )

    def _create_plan(self, user_input: str, context: dict[str, Any]) -> AgentPlan:
        """Decompose a user request into a typed plan."""
        lower = user_input.lower()
        actions: list[PlannerAction] = []

        # Detect profile-related requests
        if any(word in lower for word in ["profile", "age", "income", "name", "risk tolerance"]):
            actions.append(PlannerAction(
                agent=AgentName.PROFILE, tool=None,
                input={"user_id": context.get("user_id", "")},
                description="Understand user profile and detect missing information",
            ))

        # Detect goal-related requests
        if any(word in lower for word in ["goal", "retire", "save", "target", "education", "marriage"]):
            actions.append(PlannerAction(
                agent=AgentName.GOAL, tool=None,
                input={"user_id": context.get("user_id", "")},
                description="Analyze financial goals using the Goal Engine",
            ))

        # Detect portfolio/risk/allocation requests
        if any(word in lower for word in ["portfolio", "invest", "allocate", "risk", "rebalance", "holding"]):
            actions.append(PlannerAction(
                agent=AgentName.PORTFOLIO, tool=None,
                input={"user_id": context.get("user_id", "")},
                description="Analyze portfolio, risk, and allocation using the engines",
            ))

        # Detect research requests
        if any(word in lower for word in ["research", "compare", "fund", "etf", "stock", "bond"]):
            actions.append(PlannerAction(
                agent=AgentName.RESEARCH, tool=None,
                input={"query": user_input},
                description="Research and compare securities",
            ))

        # Detect scenario requests
        if any(word in lower for word in ["scenario", "what if", "crash", "salary", "retire early"]):
            actions.append(PlannerAction(
                agent=AgentName.SCENARIO, tool=None,
                input={"user_id": context.get("user_id", "")},
                description="Run what-if scenario analysis",
            ))

        # Detect coaching requests
        if any(word in lower for word in ["advice", "guidance", "coach", "improve", "emergency fund"]):
            actions.append(PlannerAction(
                agent=AgentName.COACH, tool=None,
                input={"user_id": context.get("user_id", "")},
                description="Generate proactive financial guidance",
            ))

        # Detect memory/recall requests
        if any(word in lower for word in ["remember", "recall", "history", "previous"]):
            actions.append(PlannerAction(
                agent=AgentName.MEMORY, tool=None,
                input={"user_id": context.get("user_id", "")},
                description="Retrieve relevant conversation history",
            ))

        # Default: explain and educate
        if not actions:
            actions.append(PlannerAction(
                agent=AgentName.COACH, tool=None,
                input={},
                description="Provide financial education and guidance",
            ))

        return AgentPlan(
            intent=self._detect_intent(user_input),
            summary=f"Decomposed request into {len(actions)} actions",
            actions=actions,
            confidence=0.8 if actions else 0.5,
        )

    @staticmethod
    def _detect_intent(user_input: str) -> str:
        lower = user_input.lower()
        if "retire" in lower:
            return "retirement_planning"
        if "goal" in lower or "save" in lower:
            return "goal_planning"
        if "invest" in lower or "portfolio" in lower:
            return "portfolio_analysis"
        if "risk" in lower:
            return "risk_assessment"
        if "scenario" in lower or "what if" in lower:
            return "scenario_analysis"
        if "research" in lower or "compare" in lower:
            return "research"
        if "profile" in lower or "age" in lower or "income" in lower:
            return "profile_setup"
        return "general_financial_education"
