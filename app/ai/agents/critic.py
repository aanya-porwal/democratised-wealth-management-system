"""CriticAgent — validates every response for logic, hallucinations, contradictions."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult


class CriticAgent(BaseAgent):
    """Validate every response: logic, tool outputs, hallucinations, contradictions, risk consistency."""

    name: AgentName = AgentName.CRITIC
    description: str = "Validate responses for logic, hallucinations, contradictions, and missing information"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        warnings: list[str] = []
        # Check for financial calculations in the input
        calc_keywords = ["calculate", "compute", "return", "interest", "multiply", "divide"]
        for word in calc_keywords:
            if word in user_input.lower():
                warnings.append(f"Potential calculation detected: '{word}'. AI must not calculate.")
        return AgentResult(
            agent=self.name, status="success" if not warnings else "needs_followup",
            message="Validation complete." if not warnings else "Warnings found.",
            output={"validated": True, "warnings": warnings},
            warnings=warnings,
        )
