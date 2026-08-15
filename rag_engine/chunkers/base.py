from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class Chunk:
    """A semantic chunk with metadata."""
    text: str
    index: int
    token_count: int = 0
    char_count: int = 0
    metadata: dict = None
    parent_chunk_id: str = None  # For hierarchical chunking
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.char_count = len(self.text)


class BaseChunker(ABC):
    """Abstract base for all chunkers."""
    
    def __init__(self, min_size: int = 100, max_size: int = 512):
        self.min_size = min_size
        self.max_size = max_size
    
    @abstractmethod
    def chunk(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Split text into chunks."""
        pass