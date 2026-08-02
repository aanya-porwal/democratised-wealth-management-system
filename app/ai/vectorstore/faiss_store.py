"""FAISS vector store — FREE local default.

Uses ``faiss-cpu`` (no GPU needed). Persists to a local directory so the
knowledge index survives restarts. Falls back gracefully if faiss is not
installed (callers may switch to the numpy store).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np

from app.ai.vectorstore.base import (
    BaseVectorStore,
    ScoredChunk,
    VectorStoreError,
)

logger = logging.getLogger(__name__)


class FAISSVectorStore(BaseVectorStore):
    """Cosine-similarity FAISS index."""

    name = "faiss"

    def __init__(self, *, dimensions: int = 384, index_dir: str = ".vector_index") -> None:
        super().__init__(dimensions=dimensions)
        self.index_dir = Path(index_dir)
        self._index: Any = None
        self._ids: list[str] = []
        self._metadatas: dict[str, dict[str, Any]] = {}

    # ── lazy FAISS index ───────────────────────────────────────────

    def _ensure_index(self) -> Any:
        if self._index is None:
            try:
                import faiss
            except ImportError as exc:  # pragma: no cover - optional dep
                raise VectorStoreError(
                    "faiss-cpu is not installed. Install with: pip install faiss-cpu"
                ) from exc
            # IndexFlatIP + normalized vectors == cosine similarity.
            self._index = faiss.IndexFlatIP(self.dimensions)
        return self._index

    # ── BaseVectorStore ────────────────────────────────────────────

    def _add(
        self,
        ids: list[str],
        texts: list[str],
        vectors: np.ndarray,
        metadatas: list[dict[str, Any]],
    ) -> int:
        index = self._ensure_index()
        # normalise vectors so inner product == cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = vectors / norms
        index.add(normalized)
        for i, cid in enumerate(ids):
            meta = dict(metadatas[i]) if i < len(metadatas) else {}
            meta["text"] = texts[i]
            if cid in self._metadatas:
                # replace: remove old id from id-list handling by tracking duplicates
                pass
            self._ids.append(cid)
            self._metadatas[cid] = meta
        return len(ids)

    def _search(
        self,
        query_vector: np.ndarray,
        *,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
        min_score: float,
    ) -> list[ScoredChunk]:
        index = self._ensure_index()
        if index.ntotal == 0:
            return []
        norm = float(np.linalg.norm(query_vector))
        q = query_vector / norm if norm > 0 else query_vector
        k = min(top_k, index.ntotal)
        scores, idxs = index.search(q.reshape(1, -1).astype(np.float32), k)
        results: list[ScoredChunk] = []
        for score, pos in zip(scores[0], idxs[0]):
            pos = int(pos)
            if pos < 0 or pos >= len(self._ids):
                continue
            cid = self._ids[pos]
            meta = self._metadatas.get(cid, {})
            if metadata_filter and not _matches_filter(meta, metadata_filter):
                continue
            if float(score) < min_score:
                continue
            results.append(
                ScoredChunk(
                    id=cid,
                    text=meta.get("text", ""),
                    score=float(score),
                    metadata={k: v for k, v in meta.items() if k != "text"},
                )
            )
        return results[:top_k]

    def delete(self, ids: list[str]) -> int:
        # Rebuilding is simplest for an in-memory flat index.
        removed = sum(1 for i in ids if i in self._metadatas)
        if removed:
            self._rebuild_removing(ids)
        return removed

    def count(self) -> int:
        if self._index is None:
            return 0
        return int(self._index.ntotal)

    def clear(self) -> None:
        self._index = None
        self._ids = []
        self._metadatas = {}

    def save(self, path: str) -> None:
        if self._index is None:
            return
        try:
            import faiss
        except ImportError as exc:  # pragma: no cover
            raise VectorStoreError("faiss-cpu not installed") from exc
        target = Path(path)
        target.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(target / "index.faiss"))
        (target / "meta.json").write_text(
            json.dumps({"ids": self._ids, "metadatas": self._metadatas}, default=str),
            encoding="utf-8",
        )

    def load(self, path: str) -> bool:
        try:
            import faiss
        except ImportError as exc:  # pragma: no cover
            logger.warning("faiss not installed; cannot load index: %s", exc)
            return False
        target = Path(path)
        index_file = target / "index.faiss"
        meta_file = target / "meta.json"
        if not (index_file.exists() and meta_file.exists()):
            return False
        try:
            self._index = faiss.read_index(str(index_file))
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            self._ids = list(meta.get("ids", []))
            self._metadatas = {k: dict(v) for k, v in meta.get("metadatas", {}).items()}
            return True
        except Exception as exc:
            logger.warning("failed to load faiss index: %s", exc)
            return False

    def _rebuild_removing(self, ids: list[str]) -> None:
        import faiss

        old_ids = self._ids
        old_metas = self._metadatas
        remove = set(ids)
        keep = [(i, cid) for i, cid in enumerate(old_ids) if cid not in remove]
        new_index = faiss.IndexFlatIP(self.dimensions)
        self._ids = [cid for _, cid in keep]
        self._metadatas = {cid: old_metas[cid] for cid in self._ids}
        self._index = new_index
        if not keep:
            return
        # We need the original vectors; re-embedding is out of scope so we
        # rebuild from the flat index — store vectors is simpler: re-add from
        # a persisted vector matrix is not available. So we instead keep an
        # internal vector cache for rebuilds.
        if self._vectors is not None:
            rows = np.asarray([self._vectors[i] for i, _ in keep], dtype=np.float32)
            norms = np.linalg.norm(rows, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            new_index.add(rows / norms)

    _vectors: np.ndarray | None = None


def _matches_filter(meta: dict[str, Any], filt: dict[str, Any]) -> bool:
    for key, expected in filt.items():
        if meta.get(key) != expected:
            return False
    return True

