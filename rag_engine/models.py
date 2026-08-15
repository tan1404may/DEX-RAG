from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    MARKDOWN = "markdown"
    CODE = "code"
    CSV = "csv"
    XLSX = "xlsx"
    TXT = "txt"
    UNKNOWN = "unknown"


class ExtractedSection(BaseModel):
    """A section/paragraph/chunk from a document with context."""
    text: str
    page_number: Optional[int] = None
    section_header: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """Standard output from any extractor."""
    source: str  # file path or URL
    doc_type: DocumentType
    title: Optional[str] = None
    content: str  # Full concatenated text
    sections: List[ExtractedSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Raw metadata from file
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    language: Optional[str] = "en"


class ExtractionConfig(BaseModel):
    """Config for extractors."""
    max_file_size_mb: int = 100
    extract_images: bool = False  # OCR later
    preserve_formatting: bool = True
    include_page_numbers: bool = True
    table_extraction: bool = True