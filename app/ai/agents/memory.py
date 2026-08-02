"""MemoryAgent — stores and retrieves conversation history, preferences, and recommendations."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult


class MemoryAgent(BaseAgent):
    """Store/retrieve conversation history, preferences, recommendations, long-term context."""

    name: AgentName = AgentName.MEMORY
    description: str = "Store and retrieve conversation history, preferences, recommendations"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        return AgentResult(
            agent=self.name, status="success",
            message="Memory operations available via the memory store.",
            output={"memory_action": user_input, "context": ctx},
        )
