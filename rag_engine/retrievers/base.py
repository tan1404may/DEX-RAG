from abc import ABC, abstractmethod
from typing import List

from ..vector_store.base import SearchResult


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query_embedding, **kwargs) -> List[SearchResult]:
        pass