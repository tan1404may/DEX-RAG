from .base import BaseChunker
from .semantic import SemanticChunker
from .hierarchical import HierarchicalChunker


class ChunkerFactory:
    _chunkers = {
        "semantic": SemanticChunker,
        "hierarchical": HierarchicalChunker,
    }
    
    @classmethod
    def get_chunker(cls, chunker_type: str = "semantic", **kwargs) -> BaseChunker:
        chunker_class = cls._chunkers.get(chunker_type)
        if not chunker_class:
            raise ValueError(f"Unknown chunker: {chunker_type}")
        return chunker_class(**kwargs)