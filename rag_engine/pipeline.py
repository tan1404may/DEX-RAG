from .extractor import ExtractorFactory
from .chunkers import SemanticChunker
from .embedders import HybridEmbedder
from .vector_store import QdrantStore
from .query import QueryTransformer
from .retrievers import HybridRetriever
from .retrievers.reranker import CrossEncoderReranker
from .generation import PromptBuilder, LLMClient
from .config import settings

class RAGPipeline:
    """
    End-to-end RAG pipeline.
    """
    
    def __init__(self):
        self.extractor = ExtractorFactory
        self.chunker = SemanticChunker()
        self.embedder = HybridEmbedder()
        self.store = QdrantStore()
        self.query_transformer = QueryTransformer(embedder=self.embedder.dense)
        self.retriever = HybridRetriever(vector_store=self.store, embedder=self.embedder)
        self.reranker = CrossEncoderReranker()
        self.prompt_builder = PromptBuilder()
        self.llm = LLMClient(
            provider="gemini",
            model=settings.GEMINI_MODEL,
            api_key=settings.GEMINI_API_KEY,
        )
    
    def ingest(self, file_path: str, user_id: str = "default", doc_id: str = None):
        """Ingest a document into the vector store."""
        # Extract
        doc = self.extractor.extract(file_path)
        
        # Chunk
        chunks = self.chunker.chunk(doc.content)
        
        # Embed
        vectors = self.embedder.embed(
            [c.text for c in chunks],
            metadata=[{**c.metadata, "doc_type": doc.doc_type.value} for c in chunks]
        )
        
        # Store
        self.store.upsert(vectors, user_id=user_id, doc_id=doc_id or doc.source)
        
        return {
            "doc_id": doc_id or doc.source,
            "title": doc.title,
            "chunks": len(chunks),
        }
    
    def query(self, question: str, user_id: str = "default", top_k: int = 5) -> dict:
        """Answer a question using RAG."""
        # Transform query
        transformed = self.query_transformer.transform(question)
        
        # Retrieve
        results = self.retriever.retrieve(
            query_embedding=transformed.embedding,
            user_id=user_id,
            limit=20,
        )
        
        # Rerank
        ranked = self.reranker.rerank(question, results, top_k=top_k)
        
        # Build prompt
        prompt = self.prompt_builder.build(question, ranked)
        
        # Generate
        answer = self.llm.generate(prompt.full_prompt)
        
        return {
            "question": question,
            "answer": answer,
            "sources": [
                {"text": r.text[:200], "score": r.score, "metadata": r.metadata}
                for r in ranked
            ],
        }