import uuid
from typing import List, Optional, Dict, Any
import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
    HnswConfigDiff,
    OptimizersConfigDiff,
)

from rag_engine.vector_store.base import BaseVectorStore, SearchResult
from rag_engine.embedders.base import EmbeddingVector
from rag_engine.config import settings


class QdrantStore(BaseVectorStore):
    """
    Production Qdrant vector store with:
    - Dense vector search
    - Metadata filtering
    - Payload indexing
    - User isolation via metadata
    """

    def __init__(
        self,
        url: str = None,
        api_key: str = None,
        prefer_grpc: bool = False,
    ):
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY or None

        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            prefer_grpc=prefer_grpc,
        )

    def create_collection(
        self,
        name: str = None,
        vector_size: int = None,
        distance: Distance = Distance.COSINE,
        hnsw_ef: int = 128,
        on_disk: bool = False,
    ) -> bool:
        """Create collection with HNSW index."""
        name = name or settings.COLLECTION_NAME
        vector_size = vector_size or settings.VECTOR_SIZE

        # Delete if exists
        collections = self.client.get_collections().collections
        if any(c.name == name for c in collections):
            print(f"Collection '{name}' already exists.")
            return True

        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance,
                on_disk=on_disk,
            ),
            hnsw_config=HnswConfigDiff(
                ef_construct=hnsw_ef,
                m=16,
            ),
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=20000,
            ),
        )

        # Create payload indexes for common filters
        self._create_payload_indexes(name)

        print(f"Collection '{name}' created with size {vector_size}.")
        return True

    def _create_payload_indexes(self, collection: str):
        """Index frequently filtered fields."""
        indexed_fields = ["user_id", "doc_id", "doc_type", "chunk_type"]
        for field in indexed_fields:
            try:
                self.client.create_payload_index(
                    collection_name=collection,
                    field_name=field,
                    field_schema="keyword",
                )
            except Exception:
                pass  # Already exists or not supported

    def delete_collection(self, name: str = None) -> bool:
        name = name or settings.COLLECTION_NAME
        self.client.delete_collection(name)
        return True

    def upsert(
        self,
        vectors: List[EmbeddingVector],
        collection: str = None,
        user_id: str = "default",
        doc_id: str = None,
        batch_size: int = 100,
    ) -> bool:
        """Upsert vectors with metadata."""
        collection = collection or settings.COLLECTION_NAME

        points = []
        for i, vec in enumerate(vectors):
            point_id = str(uuid.uuid4())

            payload = {
                "text": vec.text,
                "user_id": user_id,
                "doc_id": doc_id or "unknown",
                "chunk_type": vec.metadata.get("chunk_type", "child"),
                "doc_type": vec.metadata.get("doc_type", "unknown"),
                **vec.metadata,
            }

            point = PointStruct(
                id=point_id,
                vector=vec.dense.tolist(),
                payload=payload,
            )
            points.append(point)

        # Batch upsert
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(collection_name=collection, points=batch)

        print(f"Upserted {len(points)} vectors to '{collection}'.")
        return True

    def search(
        self,
        query_vector: np.ndarray,
        collection: str = None,
        limit: int = 10,
        user_id: str = "default",
        doc_id: str = None,
        doc_type: str = None,
        score_threshold: float = None,
        ef: int = 128,
    ) -> List[SearchResult]:
        """
        Search with metadata filters.
        Always filters by user_id for multi-tenancy.
        """
        if hasattr(query_vector, 'dense'):
            query_vector = query_vector.dense
            
        collection = collection or settings.COLLECTION_NAME

        # Build filter
        must_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]

        if doc_id:
            must_conditions.append(
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
            )

        if doc_type:
            must_conditions.append(
                FieldCondition(key="doc_type", match=MatchValue(value=doc_type))
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        results = self.client.query_points(
            collection_name=collection,
            query=query_vector.tolist(),
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            score_threshold=score_threshold,
            search_params=SearchParams(hnsw_ef=ef),
        ).points

        return [
            SearchResult(
                id=str(r.id),
                score=r.score,
                text=r.payload.get("text", ""),
                metadata={k: v for k, v in r.payload.items() if k != "text"},
            )
            for r in results
        ]

    def delete_by_filter(
        self,
        user_id: str = "default",
        doc_id: str = None,
        collection: str = None,
    ) -> bool:
        """Delete all vectors for a user or specific doc."""
        collection = collection or settings.COLLECTION_NAME

        must_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]

        if doc_id:
            must_conditions.append(
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
            )

        self.client.delete(
            collection_name=collection,
            points_selector=Filter(must=must_conditions),
        )
        return True

    def get_collection_info(self, collection: str = None) -> dict:
        collection = collection or settings.COLLECTION_NAME
        return self.client.get_collection(collection).dict()