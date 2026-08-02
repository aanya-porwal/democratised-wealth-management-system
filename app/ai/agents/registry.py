"""Agent registry — maps agent names to agent instances."""

from __future__ import annotations

import logging
from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry of available agents, keyed by AgentName."""

    _agents: dict[AgentName, BaseAgent] = {}
    _initialized = False

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        cls._agents[agent.name] = agent
        logger.debug("registered agent: %s", agent.name.value)

    @classmethod
    def get(cls, name: AgentName) -> BaseAgent:
        if name not in cls._agents:
            raise ValueError(f"agent not found: {name.value}")
        return cls._agents[name]

    @classmethod
    def list_agents(cls) -> list[dict[str, Any]]:
        return [
            {"name": agent.name.value, "description": agent.description}
            for agent in cls._agents.values()
        ]

    @classmethod
    def run(cls, name: AgentName, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        agent = cls.get(name)
        return agent.run(user_input, context)

    @classmethod
    def initialize_defaults(cls) -> None:
        if cls._initialized:
            return
        from app.ai.agents.planner import PlannerAgent
        from app.ai.agents.profile import ProfileAgent
        from app.ai.agents.goal import GoalAgent
        from app.ai.agents.portfolio import PortfolioAgent
        from app.ai.agents.research import ResearchAgent
        from app.ai.agents.scenario import ScenarioAgent
        from app.ai.agents.coach import CoachAgent
        from app.ai.agents.memory import MemoryAgent
        from app.ai.agents.explainability import ExplainabilityAgent
        from app.ai.agents.critic import CriticAgent
        from app.ai.agents.compliance import ComplianceAgent
        from app.ai.agents.data_validation import DataValidationAgent
        cls.register(PlannerAgent())
        cls.register(ProfileAgent())
        cls.register(GoalAgent())
        cls.register(PortfolioAgent())
        cls.register(ResearchAgent())
        cls.register(ScenarioAgent())
        cls.register(CoachAgent())
        cls.register(MemoryAgent())
        cls.register(ExplainabilityAgent())
        cls.register(CriticAgent())
        cls.register(ComplianceAgent())
        cls.register(DataValidationAgent())
        cls._initialized = True
        logger.info("registered %d agents", len(cls._agents))


def get_agent_registry() -> AgentRegistry:
    AgentRegistry.initialize_defaults()
    return AgentRegistry
