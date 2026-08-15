from pathlib import Path
from typing import Union, BinaryIO
from io import BytesIO
import re

import markdown
from bs4 import BeautifulSoup

from .base import BaseExtractor
from ..models import ExtractedDocument, ExtractedSection, DocumentType


class MarkdownExtractor(BaseExtractor):
    """Extracts structured content from Markdown files."""
    
    supported_types = [DocumentType.MARKDOWN]
    
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def extract(self, source: Union[str, Path, BinaryIO], **kwargs) -> ExtractedDocument:
        if isinstance(source, (str, Path)):
            md_text = Path(source).read_text(encoding='utf-8', errors='ignore')
            file_size = Path(source).stat().st_size
            mime = self._detect_mime(source)
            source_name = str(source)
        else:
            source.seek(0)
            md_text = source.read().decode('utf-8', errors='ignore')
            source.seek(0, 2)
            file_size = source.tell()
            source.seek(0)
            mime = "text/markdown"
            source_name = kwargs.get("filename", "uploaded.md")
        
        return self._process_markdown(md_text, source_name, file_size, mime)
    
    def extract_from_bytes(self, data: bytes, filename: str = None, **kwargs) -> ExtractedDocument:
        md_text = data.decode('utf-8', errors='ignore')
        return self._process_markdown(md_text, filename or "uploaded.md", len(data), "text/markdown")
    
    def _process_markdown(self, md_text: str, source_name: str, file_size: int, mime: str) -> ExtractedDocument:
        # Convert to HTML for structure parsing
        html = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc'])
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title from first H1
        title = None
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        
        # Split by headers for sections
        sections = []
        full_text_parts = []
        current_header = None
        current_text = []
        
        # Get all top-level elements
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'ul', 'ol', 'table']):
            text = elem.get_text(strip=True)
            if not text:
                continue
            
            if elem.name.startswith('h'):
                if current_text:
                    section_text = '\n'.join(current_text)
                    sections.append(ExtractedSection(
                        text=section_text,
                        section_header=current_header,
                        metadata={"header_level": int(elem.name[1])}
                    ))
                    full_text_parts.append(section_text)
                
                current_header = text
                current_text = []
            else:
                # Preserve code blocks with markers
                if elem.name == 'pre':
                    code = elem.get_text()
                    current_text.append(f"```\n{code}\n```")
                else:
                    current_text.append(text)
        
        if current_text:
            section_text = '\n'.join(current_text)
            sections.append(ExtractedSection(
                text=section_text,
                section_header=current_header
            ))
            full_text_parts.append(section_text)
        
        # Fallback
        if not sections:
            sections = [ExtractedSection(text=md_text)]
            full_text_parts = [md_text]
        
        return ExtractedDocument(
            source=source_name,
            doc_type=DocumentType.MARKDOWN,
            title=title,
            content="\n\n".join(full_text_parts),
            sections=sections,
            metadata={
                "heading_count": len(self.HEADING_PATTERN.findall(md_text)),
                "code_block_count": md_text.count('```'),
            },
            file_size_bytes=file_size,
            mime_type=mime
        )