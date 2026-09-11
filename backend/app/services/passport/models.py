"""Layer 9: Output Layer & Compliance Passport — Domain Models.

Primary Pipeline:
PRODUCT ASSESSMENT
→ APPLICABILITY RESULT
→ VERIFIED CLAUSE / REQUIREMENT
→ EVIDENCE EVALUATION
→ GAP ANALYSIS
→ SOURCE VALIDATION
→ FINAL OUTPUT

Cardinal Invariants:
1. LAYER 9 NEVER CREATES A NEW REGULATORY FACT.
2. LAYER 9 ONLY PRESENTS VERIFIED UPSTREAM RESULTS.
3. NO VERIFIED SOURCE → NO REGULATORY CLAIM
4. NO VERIFIED EVIDENCE → NO SATISFIED
5. INVALID CITATION → NO FINAL CLAIM
6. CONFLICT → EXPERT REVIEW
7. UNKNOWN → UNKNOWN
8. LLM COMPLIANCE AUTHORITY = 0.0%

Required Document Title:
"Evidence-Backed Pre-Certification Compliance Assessment"

Prohibited Output Terms (Strictly Enforced):
- "BIS Certificate"
- "BIS Approval"
- "Official Certification"
- "Guaranteed Compliance"
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.services.citation_guard.models import TrustChain, CitationValidationResult, ValidationOutcome


PROHIBITED_LABELS = [
    "BIS Certificate",
    "BIS Approval",
    "Official Certification",
    "Guaranteed Compliance",
    "Certified by BIS",
]

PASSPORT_TITLE = "Evidence-Backed Pre-Certification Compliance Assessment"


class OutputLifecycleState(str, Enum):
    """Lifecycle states of the output artifact."""
    DRAFT = "DRAFT"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    IN_PROGRESS = "IN_PROGRESS"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    FINALIZED = "FINALIZED"


class OutputIntegrityGateResult(BaseModel):
    """Result of pre-publication Output Integrity Gate verification."""
    is_valid: bool
    can_finalize: bool
    issues: List[str] = Field(default_factory=list)
    blocked_reasons: List[str] = Field(default_factory=list)
    verified_sources_count: int = 0
    unverified_claims_count: int = 0
    satisfied_without_evidence_count: int = 0
    tampered_evidence_count: int = 0
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RequirementResultRow(BaseModel):
    """Standardized 12-field requirement row displaying deterministic evaluation & Layer 8 provenance."""
    standard: str
    clause_number: str
    clause_title: str
    code: str
    status: str
    required_evidence: str
    available_evidence: Optional[str] = None
    verification: str
    observed_value: Optional[str] = None
    required_value: Optional[str] = None
    deterministic_result: str
    gap_state: str
    recommended_action: str
    source_citation: str
    page_number: Optional[int] = 1
    evidence_id: Optional[str] = None
    evidence_hash: Optional[str] = None
    trust_chain: Optional[TrustChain] = None


class GapReportItem(BaseModel):
    """Item in the prioritized Gap Register."""
    priority: str  # CRITICAL | HIGH | MEDIUM | LOW
    standard: str
    clause_number: str
    requirement_name: str
    why_it_is_a_gap: str
    missing_evidence: str
    recommended_action: str
    requires_lab_testing: bool
    requires_expert_review: bool
    supporting_source: str


class ActionCenterItem(BaseModel):
    """Individual operational recommendation in the MSME Action Center."""
    code: str
    title: str
    detail: str
    clause_ref: Optional[str] = None
    action_type: str


class MSMEActionCenter(BaseModel):
    """Actionable operational dashboard for the MSME manufacturer."""
    what_you_have: List[str] = Field(default_factory=list)
    what_is_missing: List[str] = Field(default_factory=list)
    what_to_test: List[ActionCenterItem] = Field(default_factory=list)
    what_to_upload: List[ActionCenterItem] = Field(default_factory=list)
    what_needs_expert_review: List[ActionCenterItem] = Field(default_factory=list)
    what_can_be_finalized: List[str] = Field(default_factory=list)


class ExecutiveSummary(BaseModel):
    """Honest, count-based executive summary without arbitrary percentage score gaming."""
    product_name: str
    category: str
    applicable_standards: List[str]
    total_requirements_evaluated: int
    verified_evidence_count: int
    satisfied_count: int
    potentially_satisfied_count: int
    missing_evidence_count: int
    potential_gaps_count: int
    conflicting_evidence_count: int
    expert_review_count: int
    overall_status: OutputLifecycleState
    statutory_disclaimer: str = (
        "This document is an evidence-backed engineering pre-certification assessment. "
        "It does not constitute a statutory Bureau of Indian Standards (BIS) license, "
        "product approval, or certificate of conformity."
    )


class ProductionCompliancePassport(BaseModel):
    """Production-grade Layer 9 Compliance Passport.
    
    Persists the exact, reproducible regulatory posture of the MSME assessment.
    """
    passport_id: str
    assessment_id: str
    assessment_number: str
    output_version: int = 1
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    document_title: str = PASSPORT_TITLE
    lifecycle_state: OutputLifecycleState
    integrity_gate: OutputIntegrityGateResult
    executive_summary: ExecutiveSummary
    action_center: MSMEActionCenter
    product_dna_version: str = "v1.0"
    knowledge_version: str = "v1.2.0-gazette-verified"
    applicable_standards: List[Dict[str, Any]] = Field(default_factory=list)
    qco_regulatory_orders: List[Dict[str, Any]] = Field(default_factory=list)
    requirements_matrix: List[RequirementResultRow] = Field(default_factory=list)
    gap_report: List[GapReportItem] = Field(default_factory=list)
    testing_roadmap: List[Dict[str, Any]] = Field(default_factory=list)
    recognized_laboratories: List[Dict[str, Any]] = Field(default_factory=list)
    citation_audit_trail: List[CitationValidationResult] = Field(default_factory=list)
    evidence_hashes: Dict[str, str] = Field(default_factory=dict)
    disclaimers: List[str] = Field(default_factory=list)
    snapshot_hash: str = ""


class DownloadableReportData(BaseModel):
    """Export-ready payload for PDF, HTML, and JSON representations."""
    passport: ProductionCompliancePassport
    html_printable: str
    json_metadata: Dict[str, Any]
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
