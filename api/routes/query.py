from fastapi import APIRouter, Depends, HTTPException

from ..dependency import get_pipeline, get_user_id
from ..models import QueryRequest, QueryResponse, Source
from rag_engine.pipeline import RAGPipeline


router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    try:
        result = pipeline.query(
            question=request.question,
            user_id=request.user_id,
            top_k=request.top_k,
            doc_id=request.doc_id,
        )

        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            sources=[Source(**s) for s in result["sources"]],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")