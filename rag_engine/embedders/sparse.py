from typing import List, Union
import numpy as np

from .base import BaseEmbedder, EmbeddingVector
from ..config import settings


class SparseEmbedder(BaseEmbedder):
    """
    Sparse embeddings using SPLADE or BM25.
    For now: simple TF-IDF style as fallback. 
    Production: Use SPLADE via transformers (heavy) or PyTerrier.
    """
    
    def __init__(self, use_bm25: bool = True):
        super().__init__(batch_size=64, normalize=False)
        self.use_bm25 = use_bm25
        self.vocab = {}
        self.idf = {}
        self._fitted = False
    
    @property
    def dimension(self) -> int:
        return len(self.vocab) if self.vocab else 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization. Production: use proper tokenizer."""
        import re
        return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    
    def fit(self, texts: List[str]):
        """Build vocabulary and IDF from corpus."""
        from collections import Counter
        import math
        
        # Term frequency per doc
        doc_freq = Counter()
        total_docs = len(texts)
        
        for text in texts:
            tokens = set(self._tokenize(text))
            for token in tokens:
                doc_freq[token] += 1
        
        # IDF calculation
        self.vocab = {token: idx for idx, token in enumerate(doc_freq.keys())}
        self.idf = {
            token: math.log((total_docs + 1) / (freq + 1) + 1)
            for token, freq in doc_freq.items()
        }
        self._fitted = True
    
    def embed(self, texts: Union[str, List[str]], metadata: List[dict] = None) -> List[EmbeddingVector]:
        if isinstance(texts, str):
            texts = [texts]
        
        if not self._fitted:
            # Fit on the fly if not pre-fitted (not ideal but works for single batch)
            self.fit(texts)
        
        results = []
        for i, text in enumerate(texts):
            tokens = self._tokenize(text)
            from collections import Counter
            tf = Counter(tokens)
            
            sparse = {}
            for token, count in tf.items():
                if token in self.vocab:
                    idx = self.vocab[token]
                    weight = count * self.idf.get(token, 1.0)
                    sparse[idx] = float(weight)
            
            results.append(EmbeddingVector(
                dense=np.array([]),  # No dense for sparse
                sparse=sparse,
                text=text,
                metadata=metadata[i] if metadata and i < len(metadata) else {},
            ))
        
        return results