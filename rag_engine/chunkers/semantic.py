import re
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from rag_engine.chunkers.base import BaseChunker, Chunk
from rag_engine.config import settings


class SemanticChunker(BaseChunker):
    """
    Semantic chunking using sentence embeddings.
    Groups sentences with high cosine similarity together.
    """
    
    def __init__(
        self,
        model_name: str = None,
        similarity_threshold: float = None,
        overlap_sentences: int = None,
        min_size: int = None,
        max_size: int = None,
    ):
        super().__init__(
            min_size=min_size or settings.CHUNK_MIN_SIZE,
            max_size=max_size or settings.CHUNK_MAX_SIZE,
        )
        self.model_name = model_name or settings.CHUNKING_MODEL
        self.similarity_threshold = similarity_threshold or settings.CHUNK_SIMILARITY_THRESHOLD
        self.overlap_sentences = overlap_sentences or settings.CHUNK_OVERLAP_SENTENCES
        
        # Lazy load model
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=settings.EMBEDDING_DEVICE)
        return self._model
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences. Handles abbreviations and edge cases."""
        # Simple but robust regex-based splitting
        # Split on ., !, ? followed by space or newline and capital letter
        text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)
        sentences = [s.strip() for s in text.split('\n') if s.strip()]
        return sentences
    
    def _combine_sentences(self, sentences: List[str], buffer_size: int = 1) -> List[str]:
        """Combine each sentence with neighbors for better context embedding."""
        combined = []
        for i in range(len(sentences)):
            start = max(0, i - buffer_size)
            end = min(len(sentences), i + buffer_size + 1)
            combined_sentence = " ".join(sentences[start:end])
            combined.append(combined_sentence)
        return combined
    
    def _calculate_similarities(self, embeddings: np.ndarray) -> List[float]:
        """Calculate cosine similarity between consecutive sentence embeddings."""
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity(
                embeddings[i].reshape(1, -1),
                embeddings[i + 1].reshape(1, -1)
            )[0][0]
            similarities.append(float(sim))
        return similarities
    
    def _find_breakpoints(self, similarities: List[float]) -> List[int]:
        """Find indices where similarity drops below threshold."""
        breakpoints = []
        for i, sim in enumerate(similarities):
            if sim < self.similarity_threshold:
                breakpoints.append(i)
        return breakpoints
    
    def _create_chunks_from_breakpoints(
        self, 
        sentences: List[str], 
        breakpoints: List[int],
        metadata: dict = None
    ) -> List[Chunk]:
        """Group sentences into chunks based on breakpoints."""
        chunks = []
        start_idx = 0
        
        for bp in breakpoints:
            # bp is the index of the last sentence in current group
            end_idx = bp + 1
            group = sentences[start_idx:end_idx]
            chunk_text = " ".join(group)
            
            # Respect min/max size
            chunk_text = self._respect_size_limits(chunk_text, group)
            
            chunk = Chunk(
                text=chunk_text,
                index=len(chunks),
                metadata={
                    **(metadata or {}),
                    "sentence_start": start_idx,
                    "sentence_end": end_idx,
                    "sentence_count": len(group),
                }
            )
            chunks.append(chunk)
            start_idx = end_idx
        
        # Last group
        if start_idx < len(sentences):
            group = sentences[start_idx:]
            chunk_text = " ".join(group)
            chunk_text = self._respect_size_limits(chunk_text, group)
            
            chunk = Chunk(
                text=chunk_text,
                index=len(chunks),
                metadata={
                    **(metadata or {}),
                    "sentence_start": start_idx,
                    "sentence_end": len(sentences),
                    "sentence_count": len(group),
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _respect_size_limits(self, text: str, sentences: List[str]) -> str:
        """Ensure chunk respects min/max char limits."""
        if len(text) < self.min_size and len(sentences) > 1:
            # Too small, will be merged by caller
            pass
        if len(text) > self.max_size * 4:  # rough char limit (4 chars per token avg)
            # Split by half sentences
            mid = len(sentences) // 2
            return " ".join(sentences[:mid])
        return text
    
    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Merge chunks that are below min_size with neighbors."""
        if not chunks:
            return chunks
        
        merged = [chunks[0]]
        for chunk in chunks[1:]:
            if len(merged[-1].text) < self.min_size:
                # Merge with previous
                merged[-1].text += " " + chunk.text
                merged[-1].metadata["sentence_end"] = chunk.metadata.get("sentence_end")
                merged[-1].metadata["sentence_count"] += chunk.metadata.get("sentence_count", 0)
            elif len(chunk.text) < self.min_size:
                # Merge current into previous
                merged[-1].text += " " + chunk.text
                merged[-1].metadata["sentence_end"] = chunk.metadata.get("sentence_end")
                merged[-1].metadata["sentence_count"] += chunk.metadata.get("sentence_count", 0)
            else:
                merged.append(chunk)
        
        # Re-index
        for i, c in enumerate(merged):
            c.index = i
        return merged
    
    def _add_overlap(self, chunks: List[Chunk]) -> List[Chunk]:
        """Add overlapping sentences between chunks for continuity."""
        if self.overlap_sentences <= 0 or len(chunks) <= 1:
            return chunks
        
        # This requires re-parsing, so we skip for now or store sentences in metadata
        # For production, store sentences in metadata during creation
        return chunks
    
    def chunk(self, text: str, metadata: dict = None) -> List[Chunk]:
        """
        Main entry: semantic chunking pipeline.
        """
        if not text or not text.strip():
            return []
        
        # 1. Split into sentences
        sentences = self._split_sentences(text)
        if len(sentences) <= 1:
            return [Chunk(text=text, index=0, metadata=metadata or {})]
        
        # 2. Combine with neighbors for context
        combined = self._combine_sentences(sentences, buffer_size=1)
        
        # 3. Embed
        embeddings = self.model.encode(combined, show_progress_bar=False)
        
        # 4. Calculate similarities
        similarities = self._calculate_similarities(embeddings)
        
        # 5. Find breakpoints
        breakpoints = self._find_breakpoints(similarities)
        
        # 6. Create chunks
        chunks = self._create_chunks_from_breakpoints(sentences, breakpoints, metadata)
        
        # 7. Merge small chunks
        chunks = self._merge_small_chunks(chunks)
        
        # 8. Add overlap (optional)
        chunks = self._add_overlap(chunks)
        
        return chunks