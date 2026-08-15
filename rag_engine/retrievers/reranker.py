from typing import List
import numpy as np
from sentence_transformers import CrossEncoder

from ..vector_store.base import SearchResult
from ..config import settings


class CrossEncoderReranker:
    """
    Re-rank retrieved results using a cross-encoder.
    Much more accurate than bi-encoder (embedding) similarity.
    """
    
    def __init__(self, model_name: str = None):
        # Default: small but effective cross-encoder
        self.model_name = model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            self._model = CrossEncoder(self.model_name, device=settings.EMBEDDING_DEVICE)
        return self._model
    
    def rerank(self, query: str, results: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        """Re-rank and return top-k."""
        if not results:
            return []
        
        pairs = [(query, r.text) for r in results]
        scores = self.model.predict(pairs)
        
        # Attach new scores and sort
        for r, score in zip(results, scores):
            r.score = float(score)
        
        ranked = sorted(results, key=lambda x: x.score, reverse=True)
        return ranked[:top_k]