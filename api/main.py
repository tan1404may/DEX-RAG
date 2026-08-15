from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, ingest, query, documents
from .middleware.error_handler import validation_exception_handler, general_exception_handler
from fastapi.exceptions import RequestValidationError


def create_app() -> FastAPI:
    app = FastAPI(
        title="DEX-RAG API",
        description="Production RAG with semantic search and Google Gemini",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Production: restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Error handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Routes
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(query.router)
    app.include_router(documents.router)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)