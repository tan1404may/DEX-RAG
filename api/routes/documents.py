from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependency import get_pipeline, get_user_id
from ..models import DocumentListResponse, DocumentListItem
from rag_engine.pipeline import RAGPipeline
from rag_engine.vector_store import QdrantStore


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user_id: str = Depends(get_user_id),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """
    List all documents for a user.
    TODO: Implement proper listing via Qdrant aggregation or metadata store.
    """
    # Placeholder — Qdrant doesn't have easy "list unique doc_ids"
    # Production: maintain a metadata DB (SQLite/Postgres)
    return DocumentListResponse(documents=[], total=0)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_user_id),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """Delete a document and all its chunks."""
    try:
        pipeline.store.delete_by_filter(
            user_id=user_id,
            doc_id=doc_id,
        )
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Delete failed: {str(e)}",
        )