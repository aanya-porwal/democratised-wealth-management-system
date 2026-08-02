"""Groq LLM provider — optional plugin (free tier available).

Uses Groq's OpenAI-compatible endpoint via ``httpx``. Configure with
``AI_LLM_PROVIDER=groq`` and an API key.
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


class GroqLLMProvider(BaseLLMProvider):
    """Chat-completion provider for Groq (OpenAI-compatible API)."""

    name = LLMProviderName.GROQ
    model = "llama-3.3-70b-versatile"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = (self.base_url or "https://api.groq.com/openai/v1").rstrip("/")
        if not self.api_key:
            raise LLMProviderError("Groq provider requires an API key", provider="groq")

    def _client(self) -> Any:
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
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        try:
            response = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
        except Exception as exc:
            raise LLMProviderError(f"groq request failed: {exc}", provider="groq") from exc
        if response.status_code >= 400:
            raise LLMProviderError(
                f"groq HTTP {response.status_code}: {response.text[:500]}", provider="groq"
            )
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = str(data)
        finish_reason = "stop"
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
            usage=data.get("usage", {}),
            raw=data,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

