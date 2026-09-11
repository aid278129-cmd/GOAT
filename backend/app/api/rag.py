"""Layer 6: Clause-Level RAG — API Router.

Provides endpoints for:
- Hybrid (BM25 + Vector) clause retrieval with standard-restricted isolation
- Pre-ranking metadata filtering
- Parent-child clause context resolution
- Source-grounded clause explanations ("Why does this requirement matter?")
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from backend.app.services.rag.models import (
    ClauseRAGSearchRequest,
    ClauseRAGSearchResponse,
    ClauseExplanationRequest,
    ClauseExplanationResponse,
)
from backend.app.services.rag.engine import layer6_clause_rag

router = APIRouter(prefix="/rag", tags=["Layer 6 — Clause-Level RAG"])


@router.post("/search", response_model=ClauseRAGSearchResponse)
def search_clauses(request: ClauseRAGSearchRequest) -> ClauseRAGSearchResponse:
    """Execute Layer 6 Clause-Level RAG search with standard isolation and confidence gating."""
    return layer6_clause_rag.search(request)


@router.post("/explain-clause", response_model=ClauseExplanationResponse)
def explain_clause(request: ClauseExplanationRequest) -> ClauseExplanationResponse:
    """Provide source-grounded explanation of a clause with authentic citation."""
    return layer6_clause_rag.explain_clause(
        standard_number=request.standard_number,
        clause_number=request.clause_number,
        user_question=request.user_question,
    )


@router.get("/invariants")
def get_layer6_invariants() -> Dict[str, Any]:
    """Retrieve the Layer 6 regulatory invariants and deterministic confidence thresholds."""
    return {
        "layer": "Layer 6: Clause-Level RAG",
        "invariants": [
            "NO VERIFIED SOURCE -> NO REGULATORY CLAIM",
            "RETRIEVE ONLY FROM APPLICABLE STANDARD (0% Cross-Standard Leakage)",
            "NO EXACT SOURCE -> NO INVENTED CLAUSE (CLAUSE_TEXT_UNAVAILABLE)",
            "UNKNOWN STANDARD -> NOT_IN_KNOWLEDGE_BASE",
            "LOW CONFIDENCE -> INSUFFICIENT_VERIFIED_EVIDENCE",
            "LLM COMPLIANCE AUTHORITY = 0%",
        ],
        "confidence_thresholds": {
            "STRONG_MATCH": ">= 0.65",
            "UNCERTAIN_MATCH": "0.35 to 0.65",
            "NO_RELIABLE_MATCH": "< 0.35",
            "REFUSAL_BEHAVIOR": "Below 0.35 without explicit clause match returns INSUFFICIENT_VERIFIED_EVIDENCE",
        },
        "retrieval_modes": ["HYBRID", "BM25", "VECTOR"],
    }
