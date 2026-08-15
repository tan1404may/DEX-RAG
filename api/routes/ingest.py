import uuid
import shutil
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from typing import Optional
from ..dependency import get_pipeline, get_user_id
from ..models import IngestRequest, IngestResponse
from rag_engine.pipeline import RAGPipeline


router = APIRouter(prefix="/ingest", tags=["Ingestion"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    user_id: str = Form(default="default"),
    doc_id: Optional[str] = Form(default=None),
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    """
    Upload a document (PDF, DOCX, HTML, MD, CSV, code files).
    Extracts, chunks, embeds, and stores in vector DB.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Generate doc_id if not provided
    doc_id = doc_id or f"doc_{uuid.uuid4().hex[:12]}"
    
    # Save temp file
    ext = Path(file.filename).suffix
    temp_path = UPLOAD_DIR / f"{doc_id}{ext}"
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Ingest into RAG pipeline
        result = pipeline.ingest(
            file_path=str(temp_path),
            user_id=user_id,
            doc_id=doc_id,
        )
        
        return IngestResponse(
            status="success",
            doc_id=doc_id,
            title=result.get("title"),
            chunks=result["chunks"],
            message=f"Document ingested with {result['chunks']} chunks",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()