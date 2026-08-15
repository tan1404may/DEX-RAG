from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from .base import BaseEmbedder, EmbeddingVector
from ..config import settings


class DenseEmbedder(BaseEmbedder):
    """
    Dense embeddings using sentence-transformers.
    Default: BAAI/bge-large-en-v1.5 (1024d, state-of-the-art for retrieval)
    """
    
    def __init__(
        self,
        model_name: str = None,
        device: str = None,
        batch_size: int = None,
        normalize: bool = None,
    ):
        super().__init__(
            batch_size=batch_size or settings.EMBEDDING_BATCH_SIZE,
            normalize=normalize if normalize is not None else settings.EMBEDDING_NORMALIZE,
        )
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model
    
    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
    
    def embed(self, texts: Union[str, List[str]], metadata: List[dict] = None) -> List[EmbeddingVector]:
        if isinstance(texts, str):
            texts = [texts]
        
        # BGE models expect "Represent this sentence for searching relevant passages: " prefix for queries
        # We handle this at query time, not indexing time
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        
        if self.normalize:
            embeddings = self._normalize(embeddings)
        
        results = []
        for i, emb in enumerate(embeddings):
            results.append(EmbeddingVector(
                dense=emb.astype(np.float32),
                text=texts[i],
                metadata=metadata[i] if metadata and i < len(metadata) else {},
            ))
        
        return results
    
    def embed_query(self, query: str) -> EmbeddingVector:
        """Embed a query with BGE prefix for better retrieval."""
        # BGE-specific query prefix
        prefixed = f"Represent this sentence for searching relevant passages: {query}"
        return self.embed(prefixed)[0]