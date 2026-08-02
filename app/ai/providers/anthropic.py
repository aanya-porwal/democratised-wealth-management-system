"""Anthropic LLM provider — optional PAID plugin.

Uses the Anthropic Messages API via ``httpx`` (no SDK). Only used when
``AI_LLM_PROVIDER=anthropic`` and an API key is configured.
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


class AnthropicLLMProvider(BaseLLMProvider):
    """Chat-completion provider for Anthropic's Messages API."""

    name = LLMProviderName.ANTHROPIC
    model = "claude-3-5-haiku-latest"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = (self.base_url or "https://api.anthropic.com").rstrip("/")
        if not self.api_key:
            raise LLMProviderError("Anthropic provider requires an API key", provider="anthropic")

    def _client(self) -> Any:
        if self._client is None:
            import httpx

            self._client = httpx.Client(timeout=self.timeout_seconds)
        return self._client

    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMCompletion:
        client = self._client()
        system = "\n".join(m.content for m in messages if m.role == "system")
        user_messages = [
            {"role": "user" if m.role == "tool" else m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        if not user_messages:
            user_messages = [{"role": "user", "content": system or "..."}]
        payload: dict[str, Any] = {
            "model": kwargs.get("model") or self.model,
            "messages": user_messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        if system:
            payload["system"] = system
        try:
            response = client.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
        except Exception as exc:
            raise LLMProviderError(f"anthropic request failed: {exc}", provider="anthropic") from exc
        if response.status_code >= 400:
            raise LLMProviderError(
                f"anthropic HTTP {response.status_code}: {response.text[:500]}",
                provider="anthropic",
            )
        data = response.json()
        content = ""
        try:
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")
        except (TypeError, AttributeError):
            content = str(data)
        return LLMCompletion(
            text=content,
            provider=self.name.value,
            model=data.get("model", self.model),
            latency_ms=0.0,
            finish_reason="stop",
            usage=data.get("usage", {}),
            raw=data,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

