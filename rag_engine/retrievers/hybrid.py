from typing import List
import numpy as np

from .base import BaseRetriever
from ..vector_store.base import SearchResult
from ..vector_store.qdrant_store import QdrantStore
from ..embedders.hybrid import HybridEmbedder


class HybridRetriever(BaseRetriever):
    """
    Hybrid retrieval: Dense vector search + optional sparse reweighting.
    """
    
    def __init__(
        self,
        vector_store: QdrantStore = None,
        embedder: HybridEmbedder = None,
    ):
        self.store = vector_store or QdrantStore()
        self.embedder = embedder or HybridEmbedder()
    
    def retrieve(
        self,
        query_embedding: np.ndarray,
        user_id: str = "default",
        doc_id: str = None,
        limit: int = 20,          # Retrieve more for reranking
        score_threshold: float = None,
        **kwargs
    ) -> List[SearchResult]:
        """Retrieve top-k chunks from vector store."""
        return self.store.search(
            query_vector=query_embedding,
            user_id=user_id,
            doc_id=doc_id,
            limit=limit,
            score_threshold=score_threshold,
        )