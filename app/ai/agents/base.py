"""Base agent class — every agent inherits from BaseAgent."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from app.ai.schemas import AgentName, AgentResult, ToolResult


class BaseAgent(ABC):
    """Abstract agent that processes tasks using tools."""

    name: AgentName
    description: str = ""

    def __init__(self) -> None:
        self._last_result: AgentResult | None = None

    @abstractmethod
    def process(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Process user input and return a result."""

    def run(self, user_input: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Full lifecycle with timing."""
        start = time.perf_counter()
        result = self.process(user_input, context)
        result.latency_ms = (time.perf_counter() - start) * 1000.0
        self._last_result = result
        return result
