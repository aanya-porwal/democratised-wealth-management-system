"""sentence-transformers embedding model — FREE local default.

Uses the ``sentence-transformers`` library with a free local model such
as ``all-MiniLM-L6-v2`` (384 dims) or ``BAAI/bge-small-en-v1.5``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.ai.embeddings.base import BaseEmbeddingModel, EmbeddingError

# Default dimension per known model name (overridden by config anyway).
_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "BAAI/bge-large-en-v1.5": 1024,
    "nomic-ai/nomic-embed-text-v1.5": 768,
}


class SentenceTransformerEmbedding(BaseEmbeddingModel):
    """Local sentence-transformers embeddings (CPU, free)."""

    name = "sentence_transformers"

    def __init__(self, *, model: str | None = None, dimensions: int | None = None) -> None:
        model_name = model or "sentence-transformers/all-MiniLM-L6-v2"
        dims = dimensions or _DIMENSIONS.get(model_name.split("/")[-1], 384)
        super().__init__(model=model_name, dimensions=dims)
        self._encoder: Any = None

    def _load(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise EmbeddingError(
                "sentence-transformers is not installed. "
                "Install with: pip install sentence-transformers"
            ) from exc
        try:
            self._encoder = SentenceTransformer(self.model_name)
        except Exception as exc:
            raise EmbeddingError(f"failed to load embedding model: {exc}") from exc

    def _embed(self, texts: list[str]) -> np.ndarray:
        if self._encoder is None:
            raise EmbeddingError("embedding model not loaded")
        return np.asarray(self._encoder.encode(texts, normalize_embeddings=True), dtype=np.float32)

