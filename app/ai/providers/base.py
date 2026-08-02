"""Base LLM provider contract.

The whole AI layer depends only on this interface. Concrete providers
(Ollama, OpenAI, Anthropic, Gemini, Groq, LM Studio, fallback) implement
:meth:`complete` and :meth:`stream_complete`; callers never touch vendor
SDKs or HTTP details.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator

from app.ai.config import LLMProviderName


class LLMError(Exception):
    """Base error for LLM provider failures."""

    def __init__(self, message: str, *, provider: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider


class LLMProviderError(LLMError):
    """A provider was unavailable / returned an error."""


class LLMValidationError(LLMError):
    """The provider input or output failed validation."""


@dataclass(frozen=True)
class LLMMessage:
    """A single chat message in the LLM request."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class LLMCompletion:
    """A completed LLM generation."""

    text: str
    provider: str
    model: str
    latency_ms: float
    finish_reason: str = "stop"
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def empty(self) -> bool:
        return not self.text.strip()


class BaseLLMProvider(ABC):
    """Provider-agnostic chat-completion interface.

    Subclasses should be cheap to construct; any heavy client (HTTP
    session, API key validation) is lazily initialised in :meth:`_client`.
    """

    name: LLMProviderName = LLMProviderName.FALLBACK
    model: str = "llama3"

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 120.0,
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> None:
        self.model = model or self.model
        self.base_url = base_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client: Any = None

    # ── public API ─────────────────────────────────────────────────

    def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMCompletion:
        """Generate a completion for ``messages`` synchronously.

        Subclasses implement :meth:`_complete`; this wrapper adds timing
        and basic empty-output validation.
        """
        start = time.perf_counter()
        try:
            result = self._complete(messages, **kwargs)
        except LLMError:
            raise
        except Exception as exc:  # defensive: vendor SDKs throw anything
            raise LLMProviderError(
                f"{self.name.value} provider error: {exc}", provider=self.name.value
            ) from exc
        latency = (time.perf_counter() - start) * 1000.0
        completion = result if isinstance(result, LLMCompletion) else self._to_completion(
            text=str(result), latency_ms=latency, kwargs=kwargs
        )
        if completion.latency_ms <= 0:
            completion = LLMCompletion(
                text=completion.text,
                provider=completion.provider,
                model=completion.model,
                latency_ms=latency,
                finish_reason=completion.finish_reason,
                usage=completion.usage,
                raw=completion.raw,
            )
        return completion

    def stream_complete(self, messages: list[LLMMessage], **kwargs: Any) -> Iterator[str]:
        """Stream a completion token-by-token (optional override)."""
        yield self.complete(messages, **kwargs).text

    # ── template / JSON helpers ────────────────────────────────────

    def json_complete(self, messages: list[LLMMessage], **kwargs: Any) -> dict[str, Any]:
        """Ask the model for a JSON object and parse it.

        The prompt is expected to instruct JSON output; the provider may
        relax temperature for determinism.
        """
        import json

        kwargs.setdefault("temperature", min(self.temperature, 0.1))
        completion = self.complete(messages, **kwargs)
        text = completion.text.strip()
        # strip code fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMValidationError(
                f"provider returned invalid JSON: {exc}", provider=self.name.value
            ) from exc

    # ── internals ──────────────────────────────────────────────────

    @abstractmethod
    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMCompletion:
        """Provider-specific completion implementation."""

    def _to_completion(
        self, *, text: str, latency_ms: float, kwargs: dict[str, Any]
    ) -> LLMCompletion:
        return LLMCompletion(
            text=text,
            provider=self.name.value,
            model=self.model,
            latency_ms=latency_ms,
            usage={},
        )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<{type(self).__name__} provider={self.name.value} model={self.model}>"

