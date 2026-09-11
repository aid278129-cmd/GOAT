from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    """Audit-compliant multi-state evaluation flags."""

    SATISFIED = "SATISFIED"
    POTENTIALLY_SATISFIED = "POTENTIALLY_SATISFIED"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    POTENTIAL_GAP = "POTENTIAL_GAP"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    REQUIRES_EXPERT_REVIEW = "REQUIRES_EXPERT_REVIEW"


class RecommendedAction(str, Enum):
    """Expressive recommended actions decoupled from evaluation status."""

    REQUIRES_TESTING = "REQUIRES_TESTING"
    UPLOAD_EVIDENCE = "UPLOAD_EVIDENCE"
    PROVIDE_SPECIFICATION = "PROVIDE_SPECIFICATION"
    EXPERT_REVIEW = "EXPERT_REVIEW"


class ApplicabilityStatus(str, Enum):
    """Deterministic applicability resolution states."""

    LIKELY_APPLICABLE = "LIKELY_APPLICABLE"
    POSSIBLY_APPLICABLE = "POSSIBLY_APPLICABLE"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ProvenanceCitation(BaseModel):
    """First-class verifiable citation establishing claim provenance."""

    claim: str
    document_name: str
    standard_number: str
    clause_number: str
    page_number: Optional[int] = None
    supporting_text: str
    validation_status: str = "SUPPORTED"  # SUPPORTED | UNVERIFIED | CONTRADICTED | INSUFFICIENT_EVIDENCE


class ComplianceAssessmentItem(BaseModel):
    """Individual clause or requirement evaluation outcome."""

    clause_id: Optional[str] = None
    clause_number: str
    clause_title: str
    status: ComplianceStatus
    explanation: str
    citation: Optional[ProvenanceCitation] = None
    gap_details: Optional[str] = None
    recommended_action: Optional[str] = None


class ComplianceAssessmentSummary(BaseModel):
    product_id: str
    standard_number: str
    overall_status: ComplianceStatus
    total_clauses_checked: int = 0
    satisfied_count: int = 0
    gaps_count: int = 0
    missing_evidence_count: int = 0
    items: List[ComplianceAssessmentItem] = Field(default_factory=list)
