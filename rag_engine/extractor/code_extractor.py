from pathlib import Path
from typing import Union, BinaryIO
from io import BytesIO
import re

from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.util import ClassNotFound

from .base import BaseExtractor
from ..models import ExtractedDocument, ExtractedSection, DocumentType


class CodeExtractor(BaseExtractor):
    """Extracts code files with language detection and structure."""
    
    supported_types = [DocumentType.CODE]
    
    # Extensions we treat as code
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.m',
        '.cs', '.sh', '.bash', '.ps1', '.sql', '.yaml', '.yml', '.json',
        '.xml', '.toml', '.ini', '.cfg', '.dockerfile', '.makefile'
    }
    
    def extract(self, source: Union[str, Path, BinaryIO], **kwargs) -> ExtractedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            code = path.read_text(encoding='utf-8', errors='ignore')
            file_size = path.stat().st_size
            mime = self._detect_mime(source)
            source_name = str(source)
            filename = path.name
        else:
            source.seek(0)
            code = source.read().decode('utf-8', errors='ignore')
            source.seek(0, 2)
            file_size = source.tell()
            source.seek(0)
            mime = "text/plain"
            source_name = kwargs.get("filename", "uploaded.code")
            filename = kwargs.get("filename", "uploaded.code")
        
        return self._process_code(code, source_name, filename, file_size, mime)
    
    def extract_from_bytes(self, data: bytes, filename: str = None, **kwargs) -> ExtractedDocument:
        code = data.decode('utf-8', errors='ignore')
        return self._process_code(code, filename or "uploaded.code", filename or "uploaded.code", 
                                  len(data), "text/plain")
    
    def _detect_language(self, filename: str, code: str) -> tuple:
        """Returns (language, lexer_name)."""
        try:
            lexer = get_lexer_for_filename(filename)
            return lexer.name.lower(), lexer.aliases[0] if lexer.aliases else lexer.name.lower()
        except ClassNotFound:
            try:
                lexer = guess_lexer(code[:2000])
                return lexer.name.lower(), lexer.aliases[0] if lexer.aliases else lexer.name.lower()
            except ClassNotFound:
                return "unknown", "unknown"
    
    def _extract_functions_classes(self, code: str, language: str) -> list:
        """Best-effort extraction of top-level definitions."""
        patterns = {
            'python': r'^(?:async\s+)?def\s+(\w+)|^class\s+(\w+)',
            'javascript': r'^(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)|^class\s+(\w+)|^const\s+(\w+)\s*=',
            'typescript': r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)|^class\s+(\w+)|^interface\s+(\w+)',
            'java': r'^(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:class|interface|enum)\s+(\w+)|^(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(',
            'go': r'^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)|^type\s+(\w+)',
        }
        
        pattern = patterns.get(language, r'^(?:def|function|func|class|interface)\s+(\w+)')
        matches = []
        for i, line in enumerate(code.split('\n'), 1):
            m = re.match(pattern, line.strip())
            if m:
                name = next((g for g in m.groups() if g), None)
                if name:
                    matches.append({"name": name, "line": i, "type": "function/class"})
        return matches
    
    def _process_code(self, code: str, source_name: str, filename: str, file_size: int, mime: str) -> ExtractedDocument:
        language, lexer_alias = self._detect_language(filename, code)
        
        # Split into logical sections (by double newlines or class/function boundaries)
        lines = code.split('\n')
        sections = []
        
        # Simple sectioning: group by top-level blocks
        current_section = []
        current_header = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect function/class start as section boundary
            if re.match(r'^(?:async\s+)?(?:def|class|function|func|interface|type)\s', stripped):
                if current_section:
                    section_text = '\n'.join(current_section)
                    sections.append(ExtractedSection(
                        text=section_text,
                        section_header=current_header,
                        line_start=i - len(current_section) + 1,
                        line_end=i,
                        metadata={"language": language}
                    ))
                
                current_header = stripped[:100]  # First line as header
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            section_text = '\n'.join(current_section)
            sections.append(ExtractedSection(
                text=section_text,
                section_header=current_header,
                metadata={"language": language}
            ))
        
        # If no sections, whole file is one section
        if not sections:
            sections = [ExtractedSection(text=code, metadata={"language": language})]
        
        definitions = self._extract_functions_classes(code, language)
        
        return ExtractedDocument(
            source=source_name,
            doc_type=DocumentType.CODE,
            title=filename,
            content=code,
            sections=sections,
            metadata={
                "language": language,
                "lexer": lexer_alias,
                "line_count": len(lines),
                "definitions": definitions,
                "filename": filename,
            },
            file_size_bytes=file_size,
            mime_type=mime
        )