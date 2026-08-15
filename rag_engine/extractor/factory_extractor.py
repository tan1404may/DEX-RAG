import magic
from pathlib import Path
from typing import Union, BinaryIO

from .base import BaseExtractor

from .pdf_extractor import PDFExtractor
from .html_extractor import HTMLExtractor
from .docx_extractor import DOCXExtractor
from .markdown_extractor import MarkdownExtractor
from .code_extractor import CodeExtractor
from .csv_extractor import CSVExtractor

from ..models import DocumentType, ExtractionConfig, ExtractedDocument


class ExtractorFactory:
    """Routes files to the correct extractor based on MIME type or extension."""
    
    _extractors = {
        DocumentType.PDF: PDFExtractor,
        DocumentType.HTML: HTMLExtractor,
        DocumentType.DOCX: DOCXExtractor,
        DocumentType.MARKDOWN: MarkdownExtractor,
        DocumentType.CODE: CodeExtractor,
        DocumentType.CSV: CSVExtractor,
        DocumentType.XLSX: CSVExtractor,
    }
    
    # MIME to document type mapping
    _mime_map = {
        'application/pdf': DocumentType.PDF,
        'text/html': DocumentType.HTML,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DocumentType.DOCX,
        'text/markdown': DocumentType.MARKDOWN,
        'text/x-markdown': DocumentType.MARKDOWN,
        'text/csv': DocumentType.CSV,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': DocumentType.XLSX,
        'application/vnd.ms-excel': DocumentType.XLSX,
    }
    
    # Extension to document type
    _ext_map = {
        '.pdf': DocumentType.PDF,
        '.html': DocumentType.HTML,
        '.htm': DocumentType.HTML,
        '.docx': DocumentType.DOCX,
        '.md': DocumentType.MARKDOWN,
        '.markdown': DocumentType.MARKDOWN,
        '.csv': DocumentType.CSV,
        '.xlsx': DocumentType.XLSX,
        '.xls': DocumentType.XLSX,
    }
    
    @classmethod
    def get_extractor(cls, source: Union[str, Path, bytes, BinaryIO], filename: str = None, 
                      mime_type: str = None, config: ExtractionConfig = None) -> BaseExtractor:
        """Determine the right extractor for a file."""
        doc_type = cls._detect_type(source, filename, mime_type)
        extractor_class = cls._extractors.get(doc_type)
        
        if not extractor_class:
            raise ValueError(f"No extractor available for type: {doc_type}")
        
        return extractor_class(config=config)
    
    @classmethod
    def extract(cls, source: Union[str, Path, bytes, BinaryIO], filename: str = None,
                mime_type: str = None, config: ExtractionConfig = None, **kwargs) -> ExtractedDocument:
        """One-shot extraction."""
        if isinstance(source, bytes):
            extractor = cls.get_extractor(source, filename, mime_type, config)
            return extractor.extract_from_bytes(source, filename=filename, **kwargs)
        
        extractor = cls.get_extractor(source, filename, mime_type, config)
        return extractor.extract(source, filename=filename, **kwargs)
    
    @classmethod
    def _detect_type(cls, source, filename: str = None, mime_type: str = None) -> DocumentType:
        """Detect document type from various signals."""
        # Priority 1: Explicit MIME type
        if mime_type:
            doc_type = cls._mime_map.get(mime_type)
            if doc_type:
                return doc_type
        
        # Priority 2: Filename extension
        if filename:
            ext = Path(filename).suffix.lower()
            doc_type = cls._ext_map.get(ext)
            if doc_type:
                return doc_type
        
        # Priority 3: Detect from file path
        if isinstance(source, (str, Path)):
            ext = Path(source).suffix.lower()
            doc_type = cls._ext_map.get(ext)
            if doc_type:
                return doc_type
            
            # Try MIME detection
            mime = magic.from_file(str(source), mime=True)
            doc_type = cls._mime_map.get(mime)
            if doc_type:
                return doc_type
        
        # Priority 4: Detect from bytes
        if isinstance(source, bytes):
            mime = magic.from_buffer(source, mime=True)
            doc_type = cls._mime_map.get(mime)
            if doc_type:
                return doc_type
        
        # Priority 5: Check if it's code by extension
        if filename:
            ext = Path(filename).suffix.lower()
            if ext in CodeExtractor.CODE_EXTENSIONS:
                return DocumentType.CODE
        
        return DocumentType.UNKNOWN