"""Base embedding model contract."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Sequence

import numpy as np


class EmbeddingError(Exception):
    """Base error for embedding failures."""


class BaseEmbeddingModel(ABC):
    """Provider-agnostic text embedding interface.

    All embeddings are ``np.ndarray[float32]`` with ``dimensions`` length.
    Subclasses lazily initialise heavy models in :meth:`_load`.
    """

    name: str = "base"
    dimensions: int = 384

    def __init__(self, *, model: str | None = None, dimensions: int | None = None) -> None:
        self.model_name = model or ""
        if dimensions is not None:
            self.dimensions = dimensions
        self._loaded = False

    def embed(self, texts: str | Sequence[str]) -> np.ndarray:
        """Embed one string or a batch; returns shape (n, dimensions)."""
        if isinstance(texts, str):
            texts = [texts]
        texts = [t or "" for t in texts]
        start = time.perf_counter()
        self._ensure_loaded()
        vectors = self._embed(list(texts))
        elapsed = (time.perf_counter() - start) * 1000.0
        result = np.asarray(vectors, dtype=np.float32)
        if result.ndim == 1:
            result = result.reshape(1, -1)
        return result

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self._load()
            self._loaded = True

    @abstractmethod
    def _load(self) -> None:
        """Load the underlying model (called once, lazily)."""

    @abstractmethod
    def _embed(self, texts: list[str]) -> np.ndarray:
        """Return an (n, dimensions) float32 array."""

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors."""
        a = np.asarray(a, dtype=np.float32).ravel()
        b = np.asarray(b, dtype=np.float32).ravel()
        if a.size == 0 or b.size == 0:
            return 0.0
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<{type(self).__name__} name={self.name} dims={self.dimensions}>"

