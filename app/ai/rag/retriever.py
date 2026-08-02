"""RAG retriever — retrieves relevant knowledge documents for AI context."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.ai.config import ai_settings
from app.ai.embeddings.base import BaseEmbeddingModel
from app.ai.embeddings.factory import get_embedding_model
from app.ai.rag.knowledge import KnowledgeCorpus, KnowledgeDocument
from app.ai.schemas import RetrievedDocument
from app.ai.vectorstore.base import BaseVectorStore
from app.ai.vectorstore.factory import get_vector_store

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieves relevant knowledge documents for a given query.

    Embeds the query, searches the vector store, and returns the top-K
    matching documents. Also seeds the vector store on first use.
    """

    _seeded = False

    def __init__(
        self,
        embedding: BaseEmbeddingModel | None = None,
        vector_store: BaseVectorStore | None = None,
    ) -> None:
        self._embedding = embedding or get_embedding_model()
        self._vector_store = vector_store or get_vector_store()
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        if RAGRetriever._seeded:
            return
        try:
            if self._vector_store.count() == 0:
                self._seed_corpus()
            RAGRetriever._seeded = True
        except Exception as exc:
            logger.warning("RAG seeding failed (%s); continuing without corpus", exc)

    def _seed_corpus(self) -> None:
        """Embed all knowledge documents and store them."""
        docs = KnowledgeCorpus.documents()
        if not docs:
            logger.info("no knowledge documents to seed")
            return
        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[dict[str, Any]] = []
        for doc in docs:
            cid = f"knowledge:{doc.category}:{doc.title}"
            ids.append(cid)
            texts.append(doc.content)
            metadatas.append({
                "title": doc.title,
                "source": doc.source,
                "category": doc.category,
                **doc.metadata,
            })
        vectors = self._embedding.embed(texts)
        self._vector_store.add(ids, texts, vectors, metadatas)
        self._vector_store.save(ai_settings.vector_index_dir)
        logger.info("seeded %d knowledge documents into vector store", len(docs))

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        """Retrieve the top-K most relevant documents for a query."""
        if not ai_settings.rag_enabled:
            return []
        k = top_k or ai_settings.rag_top_k
        query_vec = self._embedding.embed(query)
        chunks = self._vector_store.search(
            query_vec,
            top_k=k,
            min_score=ai_settings.rag_min_score,
        )
        results: list[RetrievedDocument] = []
        for chunk in chunks:
            results.append(
                RetrievedDocument(
                    id=chunk.id,
                    title=chunk.metadata.get("title", ""),
                    content=chunk.text,
                    source=chunk.metadata.get("source", ""),
                    category=chunk.metadata.get("category", ""),
                    score=chunk.score,
                )
            )
        return results

    def reindex(self) -> int:
        """Clear and re-seed the knowledge corpus."""
        self._vector_store.clear()
        self._seed_corpus()
        return KnowledgeCorpus.count()

    def add_document(self, doc: KnowledgeDocument) -> str:
        """Add a single document to the vector store."""
        cid = f"knowledge:{doc.category}:{doc.title}"
        vec = self._embedding.embed(doc.content)
        self._vector_store.add(
            [cid],
            [doc.content],
            vec,
            [{"title": doc.title, "source": doc.source, "category": doc.category, **doc.metadata}],
        )
        self._vector_store.save(ai_settings.vector_index_dir)
        return cid

    @classmethod
    def reset_seeded(cls) -> None:
        cls._seeded = False
