from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """A single search result."""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]
    dense_vector: List[float] = None


class BaseVectorStore(ABC):
    """Abstract base for vector stores."""
    
    @abstractmethod
    def create_collection(self, name: str, vector_size: int, **kwargs) -> bool:
        """Create a new collection."""
        pass
    
    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        pass
    
    @abstractmethod
    def upsert(self, collection: str, vectors: List, **kwargs) -> bool:
        """Insert or update vectors."""
        pass
    
    @abstractmethod
    def search(
        self,
        collection: str,
        query_vector: Any,
        limit: int = 10,
        filters: Dict = None,
        **kwargs
    ) -> List[SearchResult]:
        """Search vectors."""
        pass
    
    @abstractmethod
    def delete_by_filter(self, collection: str, filters: Dict) -> bool:
        """Delete vectors matching filter."""
        pass