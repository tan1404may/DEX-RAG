from typing import List
from dataclasses import dataclass

from ..embedders.dense import DenseEmbedder


@dataclass
class TransformedQuery:
    original: str
    expanded: List[str]      # Multi-query variants
    hyde_text: str = None    # Hypothetical document
    embedding: any = None    # Dense vector


class QueryTransformer:
    """
    Query expansion techniques:
    - Multi-query: Generate 3 variants of the question
    - HyDE: Generate hypothetical answer, embed that
    """
    
    def __init__(self, embedder: DenseEmbedder = None):
        self.embedder = embedder or DenseEmbedder()
    
    def expand(self, query: str, num_variants: int = 3) -> List[str]:
        """Simple rule-based expansion. Production: use LLM."""
        variants = [query]
        
        # Add question variants
        if not query.endswith('?'):
            variants.append(query + '?')
        
        # Add "what is" prefix if missing
        lower = query.lower()
        if not any(lower.startswith(w) for w in ['what', 'how', 'why', 'when', 'where', 'who', 'explain', 'describe']):
            variants.append(f"What is {query}?")
            variants.append(f"Explain {query}")
        
        # Add "information about" variant
        variants.append(f"Information about {query}")
        
        return variants[:num_variants]
    
    def hyde(self, query: str, llm_generate_fn = None) -> str:
        """
        HyDE: Hypothetical Document Embedding.
        Generate a fake answer, embed that instead of the query.
        """
        if llm_generate_fn:
            prompt = f"Write a short passage that would answer this question: {query}"
            return llm_generate_fn(prompt)
        
        # Fallback: use query as-is (no HyDE without LLM)
        return query
    
    def transform(self, query: str, use_hyde: bool = False, llm_generate_fn = None) -> TransformedQuery:
        """Full query transformation pipeline."""
        expanded = self.expand(query)
        
        hyde_text = None
        if use_hyde:
            hyde_text = self.hyde(query, llm_generate_fn)
            # Embed the hypothetical doc instead
            embedding = self.embedder.embed_query(hyde_text).dense
        else:
            embedding = self.embedder.embed_query(query).dense
        
        return TransformedQuery(
            original=query,
            expanded=expanded,
            hyde_text=hyde_text,
            embedding=embedding,
        )