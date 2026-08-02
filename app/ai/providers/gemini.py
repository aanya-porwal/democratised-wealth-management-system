"""Gemini LLM provider — optional PAID plugin.

Uses the Google Generative Language API via ``httpx`` (no SDK). Only used
when ``AI_LLM_PROVIDER=gemini`` and an API key is configured.
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


class GeminiLLMProvider(BaseLLMProvider):
    """Chat-completion provider for Google Gemini."""

    name = LLMProviderName.GEMINI
    model = "gemini-1.5-flash"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = (
            self.base_url or "https://generativelanguage.googleapis.com/v1beta"
        ).rstrip("/")
        if not self.api_key:
            raise LLMProviderError("Gemini provider requires an API key", provider="gemini")

    def _client(self) -> Any:
        if self._client is None:
            import httpx

            self._client = httpx.Client(timeout=self.timeout_seconds)
        return self._client

    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMCompletion:
        client = self._client()
        model = kwargs.get("model") or self.model
        # Map roles to Gemini's API roles.
        contents: list[dict[str, Any]] = []
        for m in messages:
            if m.role in ("system", "tool"):
                continue  # Gemini has no system/tool message; injected via systemInstruction
            role = "model" if m.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.content}]})
        if not contents:
            contents = [{"role": "user", "parts": [{"text": "..."}]}]
        system_text = "\n".join(m.content for m in messages if m.role == "system")
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
            },
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        try:
            response = client.post(url, json=payload)
        except Exception as exc:
            raise LLMProviderError(f"gemini request failed: {exc}", provider="gemini") from exc
        if response.status_code >= 400:
            raise LLMProviderError(
                f"gemini HTTP {response.status_code}: {response.text[:500]}",
                provider="gemini",
            )
        data = response.json()
        text = ""
        try:
            for part in data["candidates"][0]["content"]["parts"]:
                text += part.get("text", "")
        except (KeyError, IndexError, TypeError):
            text = str(data)
        return LLMCompletion(
            text=text,
            provider=self.name.value,
            model=model,
            latency_ms=0.0,
            finish_reason="stop",
            usage={},
            raw=data,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

