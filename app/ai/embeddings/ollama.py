"""Ollama embedding model — FREE local alternative.

Talks to a local Ollama server's ``/api/embed`` endpoint via ``httpx``.
Models like ``nomic-embed-text`` or ``mxbai-embed-large`` run locally.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.ai.embeddings.base import BaseEmbeddingModel, EmbeddingError


class OllamaEmbedding(BaseEmbeddingModel):
    """Local Ollama embeddings via httpx."""

    name = "ollama"

    def __init__(
        self,
        *,
        model: str | None = None,
        dimensions: int | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(model=model or "nomic-embed-text", dimensions=dimensions or 768)
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self._client: Any = None

    def _load(self) -> None:
        import httpx

        self._client = httpx.Client(timeout=60.0)

    def _embed(self, texts: list[str]) -> np.ndarray:
        if self._client is None:
            raise EmbeddingError("ollama embedding client not loaded")
        out: list[list[float]] = []
        for text in texts:
            try:
                response = self._client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model_name, "input": text},
                )
            except Exception as exc:
                raise EmbeddingError(
                    f"ollama embed failed (is Ollama running at {self.base_url}?): {exc}"
                ) from exc
            if response.status_code >= 400:
                raise EmbeddingError(
                    f"ollama embed HTTP {response.status_code}: {response.text[:300]}"
                )
            data = response.json()
            embeddings = data.get("embeddings", [])
            if embeddings:
                out.append(embeddings[0])
            else:
                out.append([0.0] * self.dimensions)
        arr = np.asarray(out, dtype=np.float32)
        # normalise rows
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return arr / norms

