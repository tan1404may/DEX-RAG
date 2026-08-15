from pathlib import Path
from typing import Union, BinaryIO
from io import BytesIO
import re

from bs4 import BeautifulSoup
from readability import Document as ReadabilityDoc

from .base import BaseExtractor
from ..models import ExtractedDocument, ExtractedSection, DocumentType


class HTMLExtractor(BaseExtractor):
    """Extracts clean article content from HTML using readability-lxml."""
    
    supported_types = [DocumentType.HTML]
    
    def extract(self, source: Union[str, Path, BinaryIO], **kwargs) -> ExtractedDocument:
        if isinstance(source, (str, Path)):
            html = Path(source).read_text(encoding='utf-8', errors='ignore')
            file_size = Path(source).stat().st_size
            mime = self._detect_mime(source)
            source_name = str(source)
        else:
            source.seek(0)
            html = source.read().decode('utf-8', errors='ignore')
            source.seek(0, 2)
            file_size = source.tell()
            source.seek(0)
            mime = "text/html"
            source_name = kwargs.get("filename", "uploaded.html")
        
        return self._process_html(html, source_name, file_size, mime)
    
    def extract_from_bytes(self, data: bytes, filename: str = None, **kwargs) -> ExtractedDocument:
        html = data.decode('utf-8', errors='ignore')
        return self._process_html(html, filename or "uploaded.html", len(data), "text/html")
    
    def _process_html(self, html: str, source_name: str, file_size: int, mime: str) -> ExtractedDocument:
        # Clean readability extraction
        doc = ReadabilityDoc(html)
        title = doc.title()
        summary = doc.summary()  # Clean HTML content
        
        # Parse with BeautifulSoup for structure
        soup = BeautifulSoup(summary, 'html.parser')
        
        # Remove script/style
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        # Extract sections by headers
        sections = []
        full_text_parts = []
        current_header = None
        current_text = []
        
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div']):
            text = elem.get_text(strip=True)
            if not text:
                continue
            
            if elem.name.startswith('h') and len(text) < 200:
                # Save previous section
                if current_text:
                    section_text = ' '.join(current_text)
                    sections.append(ExtractedSection(
                        text=section_text,
                        section_header=current_header,
                        metadata={"tag": elem.name}
                    ))
                    full_text_parts.append(section_text)
                
                current_header = text
                current_text = []
            else:
                current_text.append(text)
        
        # Don't forget the last section
        if current_text:
            section_text = ' '.join(current_text)
            sections.append(ExtractedSection(
                text=section_text,
                section_header=current_header
            ))
            full_text_parts.append(section_text)
        
        # Fallback: if no sections, just grab all text
        if not sections:
            clean_text = soup.get_text(separator='\n', strip=True)
            clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
            sections = [ExtractedSection(text=clean_text)]
            full_text_parts = [clean_text]
        
        return ExtractedDocument(
            source=source_name,
            doc_type=DocumentType.HTML,
            title=title,
            content="\n\n".join(full_text_parts),
            sections=sections,
            metadata={
                "original_length": len(html),
                "extracted_length": len("\n\n".join(full_text_parts)),
            },
            file_size_bytes=file_size,
            mime_type=mime
        )