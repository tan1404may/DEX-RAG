from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class IngestRequest(BaseModel):
    user_id: str = Field(default="default", min_length=1, max_length=100)
    doc_id: Optional[str] = Field(default=None, max_length=200)


class IngestResponse(BaseModel):
    status: str
    doc_id: str
    title: Optional[str]
    chunks: int
    message: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="default", min_length=1, max_length=100)
    top_k: int = Field(default=5, ge=1, le=20)
    doc_id: str | None = Field(default=None, max_length=200)


class Source(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]

class DocumentListItem(BaseModel):
    doc_id: str
    title: str | None = None
    chunks: int = 0  # Add default
    created_at: str = ""


class DocumentListResponse(BaseModel):
    documents: List[DocumentListItem]
    total: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None