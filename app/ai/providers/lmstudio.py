"""LM Studio LLM provider — optional local plugin (free).

LM Studio exposes a local OpenAI-compatible server. Configure with
``AI_LLM_PROVIDER=lmstudio`` and ``AI_LLM_BASE_URL=http://localhost:1234/v1``.
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


class LMStudioLLMProvider(BaseLLMProvider):
    """Chat-completion provider for a local LM Studio server."""

    name = LLMProviderName.LMSTUDIO
    model = "local-model"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = (self.base_url or "http://localhost:1234/v1").rstrip("/")

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
            "stream": False,
        }
        try:
            response = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        except Exception as exc:
            raise LLMProviderError(
                f"lmstudio request failed (is LM Studio running at {self.base_url}?): {exc}",
                provider="lmstudio",
            ) from exc
        if response.status_code >= 400:
            raise LLMProviderError(
                f"lmstudio HTTP {response.status_code}: {response.text[:500]}",
                provider="lmstudio",
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

