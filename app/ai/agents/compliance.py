"""ComplianceAgent — checks SEBI wording, disclaimers, risk disclosures, etc."""

from __future__ import annotations

from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.schemas import AgentName, AgentResult


class ComplianceAgent(BaseAgent):
    """Check SEBI wording, financial disclaimers, risk disclosures, prevent misleading responses."""

    name: AgentName = AgentName.COMPLIANCE
    description: str = "Check SEBI wording, disclaimers, risk disclosures, prevent misleading responses"

    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        ctx = context or {}
        warnings: list[str] = []
        advice_keywords = ["buy", "sell", "recommend", "advise", "should invest", "best stock"]
        for word in advice_keywords:
            if word in user_input.lower():
                warnings.append(f"Potential investment advice detected: '{word}'. Must include SEBI disclaimer.")
        return AgentResult(
            agent=self.name, status="success" if not warnings else "needs_followup",
            message="Compliance check passed." if not warnings else "Compliance warnings found.",
            output={"compliant": len(warnings) == 0, "warnings": warnings},
            warnings=warnings,
        )
