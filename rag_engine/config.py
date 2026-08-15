from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Chunking
    CHUNKING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_MIN_SIZE: int = 100
    CHUNK_MAX_SIZE: int = 512
    CHUNK_SIMILARITY_THRESHOLD: float = 0.75
    CHUNK_OVERLAP_SENTENCES: int = 1

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_NORMALIZE: bool = True

    # Sparse
    SPARSE_MODEL: str = "splade"
    SPARSE_USE: bool = True

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    COLLECTION_NAME: str = "documents"
    VECTOR_SIZE: int = 384

    # LLM
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()