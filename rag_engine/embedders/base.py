from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np
from dataclasses import dataclass


@dataclass
class EmbeddingVector:
    """A single embedding with metadata."""
    dense: np.ndarray          # Dense vector (float32)
    sparse: dict = None        # Sparse vector {token_id: weight} or None
    text: str = None           # Original text
    metadata: dict = None      # Chunk metadata
    doc_id: str = None         # Document identifier
    chunk_id: str = None       # Chunk identifier


class BaseEmbedder(ABC):
    """Abstract base for all embedders."""
    
    def __init__(self, batch_size: int = 32, normalize: bool = True):
        self.batch_size = batch_size
        self.normalize = normalize
    
    @abstractmethod
    def embed(self, texts: Union[str, List[str]], metadata: List[dict] = None) -> List[EmbeddingVector]:
        """Embed texts into vectors."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass
    
    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """L2 normalize vectors."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # avoid div by zero
        return vectors / norms