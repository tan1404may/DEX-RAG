from typing import List, Union
import numpy as np

from .base import BaseEmbedder, EmbeddingVector
from .dense import DenseEmbedder
from .sparse import SparseEmbedder
from ..config import settings


class HybridEmbedder(BaseEmbedder):
    """
    Combines dense + sparse embeddings.
    Dense: semantic meaning
    Sparse: lexical matching (exact word hits)
    """
    
    def __init__(
        self,
        dense_embedder: DenseEmbedder = None,
        sparse_embedder: SparseEmbedder = None,
        use_sparse: bool = None,
    ):
        super().__init__()
        self.dense = dense_embedder or DenseEmbedder()
        self.sparse = sparse_embedder or SparseEmbedder()
        self.use_sparse = use_sparse if use_sparse is not None else settings.SPARSE_USE
    
    @property
    def dimension(self) -> int:
        return self.dense.dimension
    
    def embed(self, texts: Union[str, List[str]], metadata: List[dict] = None) -> List[EmbeddingVector]:
        # Dense embeddings
        dense_results = self.dense.embed(texts, metadata)
        
        if not self.use_sparse:
            return dense_results
        
        # Sparse embeddings
        sparse_results = self.sparse.embed(texts, metadata)
        
        # Merge
        for i, dense_vec in enumerate(dense_results):
            dense_vec.sparse = sparse_results[i].sparse
        
        return dense_results
    
    def embed_query(self, query: str) -> EmbeddingVector:
        """Embed query with both dense and sparse."""
        dense_vec = self.dense.embed_query(query)
        
        if self.use_sparse:
            sparse_vec = self.sparse.embed([query])[0]
            dense_vec.sparse = sparse_vec.sparse
        
        return dense_vec