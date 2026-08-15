from pathlib import Path
from typing import Union, BinaryIO
from io import BytesIO, StringIO

import pandas as pd

from .base import BaseExtractor
from ..models import ExtractedDocument, ExtractedSection, DocumentType

class CSVExtractor(BaseExtractor):
    """Extracts CSV/Excel as structured text or raw."""
    
    supported_types = [DocumentType.CSV, DocumentType.XLSX]
    
    def extract(self, source: Union[str, Path, BinaryIO], **kwargs) -> ExtractedDocument:
        if isinstance(source, (str, Path)):
            path = Path(source)
            file_size = path.stat().st_size
            mime = self._detect_mime(source)
            source_name = str(source)
            return self._process_file(path, source_name, file_size, mime)
        else:
            source.seek(0)
            data = source.read()
            source.seek(0, 2)
            file_size = source.tell()
            source.seek(0)
            mime = kwargs.get("mime_type", "text/csv")
            source_name = kwargs.get("filename", "uploaded.csv")
            return self._process_bytes(data, source_name, file_size, mime, kwargs.get("filename", "uploaded.csv"))
    
    def extract_from_bytes(self, data: bytes, filename: str = None, **kwargs) -> ExtractedDocument:
        mime = kwargs.get("mime_type", "text/csv")
        return self._process_bytes(data, filename or "uploaded.csv", len(data), mime, filename or "uploaded.csv")
    
    def _process_file(self, path: Path, source_name: str, file_size: int, mime: str) -> ExtractedDocument:
        if path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path)
        return self._dataframe_to_document(df, source_name, file_size, mime)
    
    def _process_bytes(self, data: bytes, source_name: str, file_size: int, mime: str, filename: str) -> ExtractedDocument:
        if any(ext in filename.lower() for ext in ['.xlsx', '.xls']):
            df = pd.read_excel(BytesIO(data))
        else:
            df = pd.read_csv(BytesIO(data))
        return self._dataframe_to_document(df, source_name, file_size, mime)
    
    def _dataframe_to_document(self, df: pd.DataFrame, source_name: str, file_size: int, mime: str) -> ExtractedDocument:
        # Convert to structured text
        text_parts = []
        
        # Schema description
        columns = df.columns.tolist()
        schema = f"Columns: {', '.join(columns)}. "
        schema += f"Total rows: {len(df)}. "
        text_parts.append(schema)
        
        # Sample rows (first 20)
        sample = df.head(20).to_string(index=False)
        text_parts.append("Sample data:\n" + sample)
        
        # Summary stats for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe().to_string()
            text_parts.append("Numeric summary:\n" + stats)
        
        full_text = "\n\n".join(text_parts)
        
        # Sections: one per chunk of rows (for large files)
        sections = []
        chunk_size = 100
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            chunk_text = chunk.to_string(index=False)
            sections.append(ExtractedSection(
                text=chunk_text,
                section_header=f"Rows {i+1}-{min(i+chunk_size, len(df))}",
                metadata={"row_start": i, "row_end": min(i+chunk_size, len(df))}
            ))
        
        doc_type = DocumentType.XLSX if 'excel' in mime or 'spreadsheet' in mime else DocumentType.CSV
        
        return ExtractedDocument(
            source=source_name,
            doc_type=doc_type,
            title=Path(source_name).name,
            content=full_text,
            sections=sections,
            metadata={
                "columns": columns,
                "row_count": len(df),
                "column_count": len(columns),
                "dtypes": {k: str(v) for k, v in df.dtypes.to_dict().items()},
            },
            file_size_bytes=file_size,
            mime_type=mime
        )