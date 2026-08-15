from typing import List
from dataclasses import dataclass

from ..vector_store.base import SearchResult  # NOT from ..generation


@dataclass
class RAGPrompt:
    system: str
    context: str
    query: str
    full_prompt: str


class PromptBuilder:
    """
    Build RAG prompts with context window management.
    """
    
    SYSTEM_TEMPLATE = """You are a helpful assistant. Answer the user's question based ONLY on the provided context. If the context doesn't contain the answer, say "I don't have enough information to answer that." Do not make up information."""

    def __init__(self, max_context_tokens: int = 3000):
        self.max_context_tokens = max_context_tokens
        self.max_context_chars = max_context_tokens * 4
    
    def build(self, query: str, results: List[SearchResult]) -> RAGPrompt:
        context_parts = []
        total_chars = 0
        
        for i, result in enumerate(results):
            chunk_text = f"[{i+1}] {result.text.strip()}"
            if total_chars + len(chunk_text) > self.max_context_chars:
                break
            context_parts.append(chunk_text)
            total_chars += len(chunk_text)
        
        context = "\n\n".join(context_parts)
        
        full_prompt = f"""{self.SYSTEM_TEMPLATE}

Context:
{context}

Question: {query}

Answer:"""
        
        return RAGPrompt(
            system=self.SYSTEM_TEMPLATE,
            context=context,
            query=query,
            full_prompt=full_prompt,
        )