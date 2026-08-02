"""Agent implementations for the Multi-Agent AI Financial Advisor."""

from __future__ import annotations

from app.ai.agents.base import BaseAgent
from app.ai.agents.registry import AgentRegistry
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

__all__ = [
    "BaseAgent",
    "AgentRegistry",
    "PlannerAgent",
    "ProfileAgent",
    "GoalAgent",
    "PortfolioAgent",
    "ResearchAgent",
    "ScenarioAgent",
    "CoachAgent",
    "MemoryAgent",
    "ExplainabilityAgent",
    "CriticAgent",
    "ComplianceAgent",
    "DataValidationAgent",
]
