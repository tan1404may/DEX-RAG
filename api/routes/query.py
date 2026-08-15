from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..dependency import get_pipeline, get_user_id
from ..models import QueryRequest, QueryResponse, Source
from rag_engine.pipeline import RAGPipeline


router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """
    Ask a question over your ingested documents.
    Returns answer + source chunks with relevance scores.
    """
    try:
        result = pipeline.query(
            question=request.question,
            user_id=request.user_id,
            top_k=request.top_k,
        )
        
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            sources=[Source(**s) for s in result["sources"]],
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """
    Stream the RAG response chunk by chunk.
    Requires LLM streaming support (placeholder).
    """
    # TODO: Implement streaming when LLM client supports it
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented",
    )