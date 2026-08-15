import pymupdf  
import pdfplumber
from pathlib import Path
from typing import Union, BinaryIO
from io import BytesIO

from .base import BaseExtractor
from ..models import ExtractedDocument, ExtractedSection, DocumentType


class PDFExtractor(BaseExtractor):
    """Production-grade PDF extraction with PyMuPDF + pdfplumber fallback for tables."""
    
    supported_types = [DocumentType.PDF]
    
    def extract(self, source: Union[str, Path, BinaryIO], **kwargs) -> ExtractedDocument:
        if isinstance(source, (str, Path)):
            doc = pymupdf.open(str(source))
            file_size = Path(source).stat().st_size
            mime = self._detect_mime(source)
            source_name = str(source)
        else:
            # It's a file-like object
            source.seek(0)
            doc = pymupdf.open(stream=source.read(), filetype="pdf")
            source.seek(0, 2)
            file_size = source.tell()
            source.seek(0)
            mime = "application/pdf"
            source_name = kwargs.get("filename", "uploaded.pdf")
        
        return self._process_fitz_doc(doc, source_name, file_size, mime)
    
    def extract_from_bytes(self, data: bytes, filename: str = None, **kwargs) -> ExtractedDocument:
        doc = pymupdf.open(stream=data, filetype="pdf")
        return self._process_fitz_doc(
            doc, 
            filename or "uploaded.pdf", 
            len(data), 
            "application/pdf"
        )
    
    def _process_fitz_doc(self, doc, source_name: str, file_size: int, mime: str) -> ExtractedDocument:
        sections = []
        full_text_parts = []
        title = None
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if not text.strip():
                continue
                
            # Try to detect title from first page
            if page_num == 0 and not title:
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if lines:
                    title = lines[0][:200]  # First non-empty line as title
            
            section = ExtractedSection(
                text=text,
                page_number=page_num + 1,
                metadata={
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation,
                }
            )
            sections.append(section)
            full_text_parts.append(text)
        
        # Extract tables with pdfplumber if enabled
        if self.config.table_extraction:
            table_metadata = self._extract_tables(doc)
            for i, section in enumerate(sections):
                if str(section.page_number) in table_metadata:
                    section.metadata["tables"] = table_metadata[str(section.page_number)]
        
        doc.close()
        
        return ExtractedDocument(
            source=source_name,
            doc_type=DocumentType.PDF,
            title=title,
            content="\n\n".join(full_text_parts),
            sections=sections,
            metadata={
                "total_pages": len(sections),
                "has_text": len(full_text_parts) > 0,
            },
            file_size_bytes=file_size,
            mime_type=mime
        )
    
    def _extract_tables(self, doc) -> dict:
        """Extract tables per page using pdfplumber."""
        tables_by_page = {}
        try:
            # pdfplumber needs file path, so this is best-effort
            if hasattr(doc, 'name') and Path(doc.name).exists():
                with pdfplumber.open(doc.name) as pdf:
                    for i, page in enumerate(pdf.pages):
                        tables = page.extract_tables()
                        if tables:
                            tables_by_page[str(i + 1)] = [
                                {
                                    "rows": len(table),
                                    "columns": len(table[0]) if table else 0,
                                    "data": table
                                }
                                for table in tables
                            ]
        except Exception:
            pass
        return tables_by_page