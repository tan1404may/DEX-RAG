from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, BinaryIO
from ..models import ExtractedDocument, ExtractionConfig


class BaseExtractor(ABC):
    """Abstract base for all document extractors."""
    
    supported_types: list = []
    
    def __init__(self, config: ExtractionConfig = None):
        self.config = config or ExtractionConfig()
    
    @abstractmethod
    def extract(self, source: Union[str, Path, BinaryIO], **kwargs) -> ExtractedDocument:
        """Extract content from source. Source can be path or file-like object."""
        pass
    
    @abstractmethod
    def extract_from_bytes(self, data: bytes, filename: str = None, **kwargs) -> ExtractedDocument:
        """Extract from raw bytes (for API uploads)."""
        pass
    
    def _detect_mime(self, source: Union[str, Path]) -> str:
        import magic
        return magic.from_file(str(source), mime=True)