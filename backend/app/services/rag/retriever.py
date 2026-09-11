"""Layer 6: Clause-Level RAG Retriever Interface."""

from backend.app.services.rag.engine import (
    ClauseRAGEngine,
    layer6_clause_rag,
)
from backend.app.services.rag.models import (
    ClauseRAGResult,
    ClauseRAGSearchRequest,
    ClauseRAGSearchResponse,
    RetrievalConfidence,
    RetrievalMethod,
    RetrievalResultState,
    ParentClauseContext,
    EvidenceRequirementSpec,
    CitationSpec,
    ClauseExplanationRequest,
    ClauseExplanationResponse,
)

__all__ = [
    "ClauseRAGEngine",
    "layer6_clause_rag",
    "ClauseRAGResult",
    "ClauseRAGSearchRequest",
    "ClauseRAGSearchResponse",
    "RetrievalConfidence",
    "RetrievalMethod",
    "RetrievalResultState",
    "ParentClauseContext",
    "EvidenceRequirementSpec",
    "CitationSpec",
    "ClauseExplanationRequest",
    "ClauseExplanationResponse",
]
