from typing import Generator
from fastapi import Header, HTTPException, status

from rag_engine.pipeline import RAGPipeline


# Singleton pipeline instance
_pipeline: RAGPipeline = None


def get_pipeline() -> RAGPipeline:
    """Lazy-init RAG pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


def get_user_id(x_user_id: str = Header(default="default")) -> str:
    """Extract user_id from header. Production: JWT validation."""
    if not x_user_id or x_user_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header required",
        )
    return x_user_id