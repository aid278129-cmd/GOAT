"""Layer 3: AI Orchestrator Data Contracts & Schemas.

Strictly follows SIH Presentation Layer 3 architecture:
LAYER 2 PRODUCT DNA -> AI ORCHESTRATOR -> ONE LLM -> VERIFIED BIS KNOWLEDGE / RETRIEVAL
-> CITATION GUARD -> DETERMINISTIC DOWNSTREAM ENGINES.

Cardinal Invariants Enforced:
ONE LLM FOR LANGUAGE INTELLIGENCE
VERIFIED BIS KNOWLEDGE FOR FACTS
DETERMINISTIC ENGINES FOR COMPLIANCE
CITATION GUARD FOR TRUST
LLM COMPLIANCE AUTHORITY = 0%
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class OrchestratorIntent(str, Enum):
    """Classified user query intent."""
    QUERY_REQUIREMENT = "QUERY_REQUIREMENT"
    EXPLAIN_GAP = "EXPLAIN_GAP"
    CLARIFY_PRODUCT = "CLARIFY_PRODUCT"
    AUDIT_TRACE = "AUDIT_TRACE"
    GENERAL_GUIDANCE = "GENERAL_GUIDANCE"
    GENERAL_BIS_INFORMATION = "GENERAL_BIS_INFORMATION"
    CONSUMER_ASSISTANCE = "CONSUMER_ASSISTANCE"
    HALLMARKING = "HALLMARKING"
    MALICIOUS_OVERRIDE_ATTEMPT = "MALICIOUS_OVERRIDE_ATTEMPT"
    UNKNOWN_INTENT = "UNKNOWN_INTENT"


class GroundingStatus(str, Enum):
    """Grounding verification state for AI responses."""
    SUPPORTED = "SUPPORTED"
    UNCERTAIN = "UNCERTAIN"
    UNKNOWN = "UNKNOWN"
    NOT_IN_KNOWLEDGE_BASE = "NOT_IN_KNOWLEDGE_BASE"
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"


class CitationItem(BaseModel):
    """Authentic verified citation linking strictly to Indian Standards."""
    standard_number: str = Field(..., description="e.g. IS 302-2-201:2008")
    clause_number: Optional[str] = Field(None, description="e.g. 22.101")
    clause_title: Optional[str] = None
    source_authority: str = "Bureau of Indian Standards (Official Gazette)"
    verified: bool = True


class OrchestratorContext(BaseModel):
    """Controlled, isolated context provided to the single LLM."""
    product_name: str
    category: str
    product_dna_facts: Dict[str, Any] = Field(default_factory=dict)
    target_standard: Optional[str] = None
    applicable_clauses: List[Dict[str, Any]] = Field(default_factory=list)
    available_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    system_guardrails: str = (
        "Strict Grounding Policy: You are an explanatory assistant. "
        "You have ZERO authority to decide or declare compliance. "
        "Never output SATISFIED, COMPLIANT, or final certification status. "
        "Every technical fact must cite verified BIS standard clauses."
    )


class OrchestratedAIResponse(BaseModel):
    """Production-grade grounded AI response produced by Layer 3."""
    answer: str
    intent: OrchestratorIntent
    grounding_status: GroundingStatus
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    citations: List[CitationItem] = Field(default_factory=list)
    missing_information_notes: Optional[str] = None
    expert_review_recommended: bool = False
    deterministic_fallback_used: bool = False
    regulatory_conclusion: str = "NONE"  # Always NONE; LLM has zero compliance authority
    disclaimer: str = (
        "Grounding Invariant: The AI assistant provides explanatory and guidance support only. "
        "All compliance determinations, satisfaction gates, and gap evaluations are computed "
        "strictly by deterministic downstream engines based on verified laboratory evidence."
    )

    @field_validator("regulatory_conclusion")
    @classmethod
    def enforce_zero_regulatory_authority(cls, v: str) -> str:
        # LLM has 0.0% compliance authority; force any non-NONE or pseudo-status to "NONE"
        return "NONE"


class AuditLogRecord(BaseModel):
    """Comprehensive audit log record for every orchestration interaction."""
    audit_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_query: str
    sanitized_query: str
    classified_intent: OrchestratorIntent
    target_standard: Optional[str] = None
    retrieved_clause_count: int = 0
    grounding_status: GroundingStatus
    raw_llm_output: Optional[str] = None
    suppressed_claims: List[str] = Field(default_factory=list)
    final_answer: str
