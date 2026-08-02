"""Deterministic rule-based LLM provider — works with NO LLM running.

This provider keeps the multi-agent system fully functional when Ollama
is not installed/running (e.g. CI, tests, low-resource environments). It
does not generate free-form text; instead it:

* understands a small, explicit command grammar for tool planning,
* responds with canned, education-only explanations,
* always returns JSON-safe structured output so the planner stays typed.

The fallback NEVER fabricates financial numbers.
"""

from __future__ import annotations

import re
from typing import Any

from app.ai.config import LLMProviderName
from app.ai.providers.base import BaseLLMProvider, LLMCompletion, LLMMessage

# A tiny intent→agent keyword map used by the fallback planner.
_INTENT_KEYWORDS: dict[str, tuple[str, list[str]]] = {
    "profile": (
        "profile",
        ["my income", "salary", "expense", "age", "profile", "dependent", "emergency fund"],
    ),
    "goal": (
        "goal",
        ["goal", "retire", "retirement", "education", "house", "marriage", "target", "sip"],
    ),
    "risk": (
        "risk",
        ["risk", "tolerance", "aggressive", "conservative", "moderate"],
    ),
    "portfolio": (
        "portfolio",
        ["portfolio", "allocation", "invest", "holdings", "rebalance", "drift"],
    ),
    "research": (
        "research",
        ["research", "compare", "fund", "etf", "stock", "bond", "security", "report"],
    ),
    "scenario": (
        "scenario",
        ["scenario", "what if", "salary increase", "salary decrease", "market crash",
         "marriage", "children", "job loss", "house purchase"],
    ),
    "health": (
        "health",
        ["health", "score", "emergency fund complete", "financial health"],
    ),
    "simulation": (
        "simulation",
        ["simulate", "monte carlo", "probability", "simulation", "forecast"],
    ),
}

_FOLLOWUP_TRIGGERS = [
    "what is my",
    "how much",
    "should i invest",
    "is my",
    "can i",
    "will i",
    "calculate",
]


class FallbackLLMProvider(BaseLLMProvider):
    """Deterministic rule-based provider (no network, no SDK)."""

    name = LLMProviderName.FALLBACK
    model = "rule-based-v1"

    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMCompletion:
        # The planner agent asks for a JSON plan; detect that by content.
        user_text = self._last_user_text(messages)
        system_text = "\n".join(m.content for m in messages if m.role == "system")
        lower = user_text.lower()

        if "json" in system_text.lower() or "plan" in system_text.lower() or _looks_like_json_request(system_text):
            plan = self._build_plan(lower)
            return self._completion(_json(plan), kwargs)

        if any(keyword in lower for keyword in ["hello", "hi", "hey"]):
            return self._completion(
                "Hello! I'm your AI financial advisor. I can help you plan your goals, "
                "understand your risk profile, build a portfolio, or research investments. "
                "What would you like to explore?",
                kwargs,
            )

        if any(t in lower for t in _FOLLOWUP_TRIGGERS):
            return self._completion(
                "To give you an accurate answer, I need your financial profile and goals. "
                "Could you share your monthly income, expenses, age, and any financial goals "
                "you're planning for?",
                kwargs,
            )

        intent = self._detect_intent(lower)
        if intent:
            return self._completion(
                f"I can help with your {intent}. Let me pull your latest financial data and "
                "run the appropriate analysis through our planning engines. This may take a "
                "moment.",
                kwargs,
            )

        return self._completion(
            "I can help you with goal planning, portfolio allocation, risk assessment, "
            "investment research, and financial education. Could you tell me a little more "
            "about what you'd like to do?",
            kwargs,
        )

    # ── helpers ────────────────────────────────────────────────────

    def _build_plan(self, lower: str) -> dict[str, Any]:
        intent = self._detect_intent(lower)
        if intent is None:
            return {
                "intent": "clarification",
                "summary": "Need more information to plan the request.",
                "requires_followup": True,
                "followup_questions": [
                    "What are you trying to achieve financially?",
                    "Do you have a goal amount and target date in mind?",
                    "What is your current monthly income and savings?",
                ],
                "actions": [],
                "confidence": 0.4,
            }
        return {
            "intent": intent,
            "summary": f"Plan for {intent} request.",
            "actions": self._actions_for(intent),
            "confidence": 0.7,
            "requires_followup": False,
            "followup_questions": [],
        }

    def _actions_for(self, intent: str) -> list[dict[str, Any]]:
        mapping: dict[str, list[dict[str, Any]]] = {
            "profile": [
                {"agent": "profile", "tool": "profile_tool",
                 "input": {"action": "get"}, "description": "Load the user profile."},
            ],
            "goal": [
                {"agent": "goal", "tool": "goal_tool",
                 "input": {"action": "list"}, "description": "List the user's goals."},
            ],
            "risk": [
                {"agent": "portfolio", "tool": "risk_tool",
                 "input": {}, "description": "Assess the user's risk profile."},
            ],
            "portfolio": [
                {"agent": "portfolio", "tool": "allocation_tool",
                 "input": {}, "description": "Compute the strategic allocation."},
            ],
            "research": [
                {"agent": "research", "tool": "research_tool",
                 "input": {"query": "research"}, "description": "Run security research."},
            ],
            "scenario": [
                {"agent": "scenario", "tool": "scenario_tool",
                 "input": {"scenario_type": "salary_increase"},
                 "description": "Run a what-if scenario."},
            ],
            "health": [
                {"agent": "coach", "tool": "health_score_tool",
                 "input": {}, "description": "Compute the financial health score."},
            ],
            "simulation": [
                {"agent": "portfolio", "tool": "simulation_tool",
                 "input": {}, "description": "Run a Monte Carlo simulation."},
            ],
        }
        return mapping.get(intent, [])

    def _detect_intent(self, lower: str) -> str | None:
        for intent, (name, keywords) in _INTENT_KEYWORDS.items():
            if any(k in lower for k in keywords):
                return name
        return None

    @staticmethod
    def _last_user_text(messages: list[LLMMessage]) -> str:
        for m in reversed(messages):
            if m.role in ("user", "tool"):
                return m.content
        return ""

    def _completion(self, text: str, kwargs: dict[str, Any]) -> LLMCompletion:
        return LLMCompletion(
            text=text,
            provider=self.name.value,
            model=self.model,
            latency_ms=0.0,
            finish_reason="stop",
            usage={},
        )


def _json(data: dict[str, Any]) -> str:
    import json

    return json.dumps(data, default=str)


def _looks_like_json_request(system_text: str) -> bool:
    return any(
        marker in system_text.lower()
        for marker in ["agentplan", "planneraction", "followup_questions", "actions"]
    )

