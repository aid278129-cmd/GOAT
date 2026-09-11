"""Layer 8: Source Validation & Citation Guard — Domain Models.

Architecture:
LAYER 7 RESULT
→ CLAIM EXTRACTION
→ SOURCE VALIDATION
→ STANDARD / CLAUSE VALIDATION
→ EVIDENCE PROVENANCE VALIDATION
→ CITATION VALIDATION
→ CONFLICT / STALENESS CHECK
→ TRUST DECISION
→ LAYER 9 OUTPUT

Cardinal Invariant:
NO VERIFIED SOURCE → NO REGULATORY CLAIM
LLM COMPLIANCE AUTHORITY = 0%
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ValidationOutcome(str, Enum):
    """Allowed validation outcomes for Layer 8 Source Validation & Citation Guard."""
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    INSUFFICIENT_SOURCE = "INSUFFICIENT_SOURCE"
    CONFLICTING_SOURCE = "CONFLICTING_SOURCE"
    STALE_SOURCE = "STALE_SOURCE"
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    CITATION_INVALID = "CITATION_INVALID"


class TrustChain(BaseModel):
    """Machine-readable auditable provenance chain:
    CLAIM → SOURCE → STANDARD → CLAUSE → EVIDENCE → VERIFICATION → DECISION
    """
    claim: str
    source: str
    standard: str
    clause: str
    evidence: str
    verification: str
    decision: ValidationOutcome


class CitationValidationResult(BaseModel):
    """Machine-readable assessment of an individual regulatory or compliance claim."""
    claim: str
    source_id: str
    standard: str
    clause: str
    evidence_id: Optional[str] = None
    document_id: Optional[str] = None
    page: Optional[int] = None
    verification_status: str = "UNVERIFIED"
    knowledge_version: str = "v1.2.0-gazette-verified"
    validation_result: ValidationOutcome
    failure_reason: Optional[str] = None
    evidence_hash: Optional[str] = None
    calculated_hash: Optional[str] = None
    product_dna_version: Optional[str] = "v1.0"
    assessment_version: Optional[int] = 1
    trust_chain: Optional[TrustChain] = None
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_llm_generated: bool = False
    llm_authority_claimed: float = 0.0


class BatchValidationReport(BaseModel):
    """Aggregated validation report over multiple claims or Layer 7 requirements."""
    total_claims: int
    verified_claims: int
    rejected_claims: int
    flagged_claims: int
    overall_trust_decision: ValidationOutcome
    results: List[CitationValidationResult] = Field(default_factory=list)
    audit_trail: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
