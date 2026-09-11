"""Layer 6: Clause-Level RAG — Data Models & Schemas.

Strictly follows Layer 6 of the SIH Presentation architecture:
LAYER 5 APPLICABILITY
  ↓
STANDARD-RESTRICTED RETRIEVAL
  ↓
QUERY UNDERSTANDING
  ↓
HYBRID SEARCH (BM25 Lexical + Dense Vector)
  ↓
METADATA FILTERING
  ↓
RERANKING
  ↓
PARENT-CHILD CLAUSE CONTEXT
  ↓
EXACT SOURCE / CITATION
  ↓
GROUNDING VALIDATION
  ↓
LAYER 7 GAP ENGINE
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RetrievalConfidence(str, Enum):
    """Deterministic retrieval confidence classifications."""
    STRONG_MATCH = "STRONG_MATCH"          # Score >= 0.65
    UNCERTAIN_MATCH = "UNCERTAIN_MATCH"    # 0.35 <= Score < 0.65
    NO_RELIABLE_MATCH = "NO_RELIABLE_MATCH" # Score < 0.35
    INSUFFICIENT_VERIFIED_EVIDENCE = "INSUFFICIENT_VERIFIED_EVIDENCE"


class RetrievalMethod(str, Enum):
    """Retrieval algorithmic modalities."""
    HYBRID = "HYBRID"
    BM25 = "BM25"
    VECTOR = "VECTOR"


class RetrievalResultState(str, Enum):
    """Retrieval outcome states."""
    VERIFIED_MATCH = "VERIFIED_MATCH"
    CLAUSE_TEXT_UNAVAILABLE = "CLAUSE_TEXT_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    NOT_IN_KNOWLEDGE_BASE = "NOT_IN_KNOWLEDGE_BASE"
    OUT_OF_SCOPE_REFUSAL = "OUT_OF_SCOPE_REFUSAL"


class ParentClauseContext(BaseModel):
    """Context of parent section or clause if it exists in the verified knowledge base."""
    clause_number: str
    title: str
    section: Optional[str] = None
    text_snippet: Optional[str] = None


class EvidenceRequirementSpec(BaseModel):
    """Structured evidence requirement specifications for Layer 7 Gap Engine handoff."""
    requirement_id: str
    parameter_name: Optional[str] = None
    test_method_reference: Optional[str] = None
    evidence_type: Optional[str] = None  # e.g., LAB_TEST_REPORT, FACTORY_INSPECTION
    measurable_condition: Optional[str] = None
    mandatory_threshold: Optional[str] = None


class CitationSpec(BaseModel):
    """Immutable source citation linking directly to Layer 4 knowledge package."""
    standard_number: str
    standard_title: str
    clause_number: str
    clause_title: str
    section: Optional[str] = None
    page_number: Optional[int] = None
    exact_location: Optional[str] = None
    source_document: str
    verification_status: str
    knowledge_version: str = "v1.2.0-gazette-verified"


class ClauseRAGResult(BaseModel):
    """Production-grade retrieved clause record with full provenance, context, and Layer 7 handoff."""
    standard_number: str
    standard_title: str
    clause_number: str
    clause_title: str
    section: Optional[str] = None
    requirement_id: Optional[str] = None
    retrieved_text: str
    source_document: str
    page_number: Optional[int] = None
    exact_location: Optional[str] = None
    verification_status: str
    knowledge_version: str = "v1.2.0-gazette-verified"
    retrieval_score: float
    retrieval_confidence: RetrievalConfidence
    retrieval_method: str = "HYBRID"
    result_state: RetrievalResultState = RetrievalResultState.VERIFIED_MATCH
    why_retrieved: str
    match_factors: Dict[str, Any] = Field(default_factory=dict)
    parent_context: Optional[ParentClauseContext] = None
    evidence_requirement: Optional[EvidenceRequirementSpec] = None
    citation: CitationSpec
    llm_authority_percentage: float = 0.0


class ClauseRAGSearchRequest(BaseModel):
    """Query parameters for Layer 6 Clause-Level RAG."""
    query: str = Field(..., min_length=1, description="Semantic or keyword query")
    standard_filter: Optional[str] = Field(None, description="Strict standard isolation filter")
    category_filter: Optional[str] = None
    document_type_filter: Optional[str] = None
    verification_filter: Optional[str] = None
    clause_filter: Optional[str] = None
    retrieval_mode: str = Field("HYBRID", description="HYBRID | BM25 | VECTOR")
    top_k: int = Field(5, ge=1, le=50)
    min_confidence_score: float = Field(0.15, ge=0.0, le=1.0)
    include_parent_context: bool = True


class ClauseRAGSearchResponse(BaseModel):
    """Response payload for Layer 6 Clause-Level RAG search."""
    layer: str = "Layer 6: Clause-Level RAG"
    query: str
    standard_filter: Optional[str] = None
    total_results: int
    results: List[ClauseRAGResult]
    llm_authority_percentage: float = 0.0
    invariants_enforced: List[str] = Field(
        default_factory=lambda: [
            "NO VERIFIED SOURCE -> NO REGULATORY CLAIM",
            "RETRIEVE ONLY FROM APPLICABLE STANDARD",
            "NO EXACT SOURCE -> NO INVENTED CLAUSE (CLAUSE_TEXT_UNAVAILABLE)",
            "UNKNOWN STANDARD -> NOT_IN_KNOWLEDGE_BASE",
            "LOW CONFIDENCE -> INSUFFICIENT_VERIFIED_EVIDENCE",
            "LLM AUTHORITY = 0%",
        ]
    )


class ClauseExplanationRequest(BaseModel):
    """Request for grounded explanation of a clause."""
    standard_number: str
    clause_number: str
    user_question: Optional[str] = "Why does this requirement matter?"


class ClauseExplanationResponse(BaseModel):
    """Grounded explanation of a clause backed exclusively by verified source text."""
    standard_number: str
    clause_number: str
    clause_title: str
    grounded_explanation: str
    source_document: str
    is_verified_source: bool
    citation: CitationSpec
