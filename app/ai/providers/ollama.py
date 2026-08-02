"""Ollama LLM provider — the FREE default.

Talks to a local Ollama server (``http://localhost:11434`` by default)
over its OpenAI-compatible ``/v1/chat/completions`` endpoint using only
``httpx`` — no vendor SDK required. Works fully offline.
"""

from __future__ import annotations

from typing import Any

from app.ai.config import LLMProviderName
from app.ai.providers.base import (
    BaseLLMProvider,
    LLMCompletion,
    LLMMessage,
    LLMProviderError,
)


class OllamaLLMProvider(BaseLLMProvider):
    """Chat-completion provider backed by a local Ollama server."""

    name = LLMProviderName.OLLAMA
    model = "llama3"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = (self.base_url or "http://localhost:11434").rstrip("/")

    def _client(self) -> Any:
        """Lazily create the shared httpx client."""
        if self._client is None:
            import httpx

            self._client = httpx.Client(timeout=self.timeout_seconds)
        return self._client

    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMCompletion:
        client = self._client()
        payload: dict[str, Any] = {
            "model": kwargs.get("model") or self.model,
            "messages": [
                {"role": m.role, "content": m.content, **({"name": m.name} if m.name else {})}
                for m in messages
            ],
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
            },
        }
        try:
            response = client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        except Exception as exc:
            raise LLMProviderError(
                f"ollama request failed (is Ollama running at {self.base_url}?): {exc}",
                provider="ollama",
            ) from exc

        if response.status_code >= 400:
            raise LLMProviderError(
                f"ollama HTTP {response.status_code}: {response.text[:500]}",
                provider="ollama",
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise LLMProviderError(
                f"ollama returned non-JSON response: {exc}", provider="ollama"
            ) from exc

        content = ""
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = str(data)

        usage = data.get("usage", {})
        finish_reason = ""
        try:
            finish_reason = data["choices"][0].get("finish_reason", "stop") or "stop"
        except (KeyError, IndexError, TypeError):
            finish_reason = "stop"

        return LLMCompletion(
            text=content or "",
            provider=self.name.value,
            model=data.get("model", self.model),
            latency_ms=0.0,
            finish_reason=finish_reason,
            usage=usage,
            raw=data,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

