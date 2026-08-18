from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependency import get_pipeline, get_user_id
from ..models import DocumentListResponse, DocumentListItem
from rag_engine.pipeline import RAGPipeline
from rag_engine.config import settings
from qdrant_client.models import Filter, FieldCondition, MatchValue


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user_id: str = Depends(get_user_id),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """List all unique documents for a user from Qdrant."""
    try:
        all_points = []
        offset = None

        while True:
            scroll_result = pipeline.store.client.scroll(
                collection_name=settings.COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            
            # Handle both tuple and object return types
            if isinstance(scroll_result, tuple):
                points, next_offset = scroll_result
            else:
                points = scroll_result.points
                next_offset = scroll_result.next_page_offset
            
            all_points.extend(points)
            if next_offset is None:
                break
            offset = next_offset

        seen = set()
        documents: List[DocumentListItem] = []
        for point in all_points:
            doc_id = point.payload.get("doc_id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                documents.append(
                    DocumentListItem(
                        doc_id=doc_id,
                        title=point.payload.get("title") or doc_id,
                        created_at=str(point.payload.get("extracted_at", "")),
                    )
                )

        return DocumentListResponse(documents=documents, total=len(documents))

    except Exception as e:
        import traceback
        print("DOCUMENTS ERROR:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    user_id: str = Depends(get_user_id),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """Delete a document and all its chunks."""
    try:
        pipeline.store.delete_by_filter(user_id=user_id, doc_id=doc_id)
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")