from typing import List
from .base import BaseChunker, Chunk
from .semantic import SemanticChunker


class HierarchicalChunker(BaseChunker):
    """
    Parent-child chunking: large parent chunks with smaller child chunks.
    Retrieval hits child chunks, but we send the parent context to LLM.
    """
    
    def __init__(
        self,
        parent_chunker: BaseChunker = None,
        child_chunker: BaseChunker = None,
    ):
        # Parent: larger semantic chunks (e.g., 1024 chars)
        self.parent_chunker = parent_chunker or SemanticChunker(
            min_size=300,
            max_size=1024,
            similarity_threshold=0.6,
        )
        # Child: smaller precise chunks (e.g., 256 chars)
        self.child_chunker = child_chunker or SemanticChunker(
            min_size=50,
            max_size=256,
            similarity_threshold=0.8,
        )
    
    def chunk(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Create parent chunks, then child chunks within each parent."""
        parents = self.parent_chunker.chunk(text, metadata)
        all_children = []
        
        for parent in parents:
            parent_id = f"parent_{parent.index}"
            parent.metadata["chunk_type"] = "parent"
            parent.metadata["chunk_id"] = parent_id
            
            # Split parent into children
            children = self.child_chunker.chunk(parent.text, metadata={
                **(metadata or {}),
                "parent_id": parent_id,
                "parent_index": parent.index,
                "chunk_type": "child",
            })
            
            for child in children:
                child.parent_chunk_id = parent_id
                child.metadata["parent_text"] = parent.text[:200]  # preview
            
            all_children.extend(children)
        
        # Return children for indexing, but parents are referenced
        return all_children