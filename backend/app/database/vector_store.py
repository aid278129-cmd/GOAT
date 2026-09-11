"""Vector Store Foundation for BIS Compliance Knowledge Base.

Provides typed interfaces and schema abstractions for pgvector-backed clause retrieval.
Actual indexing and RAG pipeline are scheduled for M1.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class VectorSearchResult(BaseModel):
    clause_id: str
    standard_number: str
    clause_number: str
    title: str
    text_content: str
    similarity_score: float
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = {}


class VectorStoreContract:
    """Contract interface for pgvector similarity searches."""

    async def search_similar_clauses(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        standard_number: Optional[str] = None,
        min_score: float = 0.65,
    ) -> List[VectorSearchResult]:
        raise NotImplementedError("Vector store search implementation is scheduled for M1.")
