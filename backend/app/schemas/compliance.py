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


# =========================================================================
# Milestone M26.2: Deterministic Compliance Gap Aggregation Schemas
# =========================================================================

class RequirementGapStatus(str, Enum):
    """Deterministic status for every applicable regulatory requirement (Milestone M26.2)."""
    SATISFIED = "SATISFIED"                             # All statutory conditions proven met by authentic evidence
    NOT_SATISFIED = "NOT_SATISFIED"                     # Fails numerical threshold, material spec, or physical test
    MISSING_EVIDENCE = "MISSING_EVIDENCE"               # No artifact provided for this mandatory requirement
    UNVERIFIED = "UNVERIFIED"                           # Evidence is inauthentic, unverified, user claim, or tampered
    CONFLICTING = "CONFLICTING"                         # Contradictory evidence artifacts or conflicting test results
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"   # Ambiguous, borderline, or requiring human expert review
    NOT_APPLICABLE = "NOT_APPLICABLE"                   # Requirement outside product category or variant scope


class GapNextAction(str, Enum):
    """Deterministic next action taxonomy (Milestone M26.2)."""
    LAB_TEST_REQUIRED = "LAB_TEST_REQUIRED"                     # Empirical laboratory testing must be conducted
    DOCUMENT_REQUIRED = "DOCUMENT_REQUIRED"                     # Technical specification, drawing, or manual required
    DECLARATION_REQUIRED = "DECLARATION_REQUIRED"               # Manufacturer declaration / affidavit required
    MARKING_EVIDENCE_REQUIRED = "MARKING_EVIDENCE_REQUIRED"     # Rating plate, packaging, or ISI mark artwork required
    CORRECTIVE_ACTION_REQUIRED = "CORRECTIVE_ACTION_REQUIRED"   # Failed test requires product redesign or rework
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"           # Conflicting/ambiguous data requires human expert review
    NO_ACTION_REQUIRED = "NO_ACTION_REQUIRED"                   # Requirement is fully satisfied or not applicable


class ComplianceGapItem(BaseModel):
    """Explicit compliance gap retaining the complete 10-element auditable chain (Milestone M26.2):
    standard → revision → clause → requirement → current evidence → evidence status → gap status → reason → required next action → provenance
    """
    standard: str = Field(..., description="Step 1: Statutory standard code e.g. IS 17526")
    revision: str = Field(..., description="Step 2: Statutory standard revision year e.g. 2021")
    clause: str = Field(..., description="Step 3: Governing clause designation e.g. Clause 5.2")
    requirement: str = Field(..., description="Step 4: Linked requirement identifier e.g. REQ-IS17526-5.2")
    current_evidence: str = Field(..., description="Step 5: Current artifact identity or 'NONE'")
    evidence_status: str = Field(..., description="Step 6: Status of submitted evidence")
    gap_status: RequirementGapStatus = Field(..., description="Step 7: Deterministic gap status")
    reason: str = Field(..., description="Step 8: Deterministic audit reason for status")
    required_next_action: GapNextAction = Field(..., description="Step 9: Deterministic next action")
    provenance: str = Field(..., description="Step 10: Complete evidence provenance statement")

    def format_gap_chain(self) -> str:
        """Formatted string representation of the 10-element gap chain."""
        return (
            f"{self.standard} → {self.revision} → {self.clause} → {self.requirement} → "
            f"{self.current_evidence} → {self.evidence_status} → {self.gap_status.value} → "
            f"{self.reason} → {self.required_next_action.value} → {self.provenance}"
        )


class DeterministicGapAggregationResult(BaseModel):
    """Top-level aggregate compliance evaluation across all applicable requirements (Milestone M26.2)."""
    aggregation_id: str = Field(..., description="Unique gap aggregation identifier")
    product_id: str = Field(..., description="Target product identifier")
    target_standard: str = Field(..., description="Governing statutory standard number and revision")
    standard_revision: str = Field(..., description="Statutory revision year")
    overall_verdict: str = Field(..., description="Overall compliance verdict: COMPLIANT, NON_COMPLIANT, GAPS_IDENTIFIED")
    total_requirements: int = Field(default=0)
    satisfied_count: int = Field(default=0)
    not_satisfied_count: int = Field(default=0)
    missing_evidence_count: int = Field(default=0)
    unverified_count: int = Field(default=0)
    conflicting_count: int = Field(default=0)
    expert_review_count: int = Field(default=0)
    not_applicable_count: int = Field(default=0)
    gap_items: List[ComplianceGapItem] = Field(default_factory=list)

    # Deterministic Categorized Action Roadmaps
    roadmap_lab_test: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_document: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_declaration: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_marking: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_corrective_action: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_expert_review: List[ComplianceGapItem] = Field(default_factory=list)

    # Authority and Invariant Boundaries
    compliance_authority: str = Field(
        default="LAYER_7_ONLY",
        description="Non-negotiable invariant: Layer 7 is sole compliance decision authority",
    )
    llm_compliance_authority: float = Field(
        default=0.0,
        description="Non-negotiable invariant: LLM has exactly 0.0% compliance authority",
    )
    regulatory_conclusion: str = Field(
        default="NONE",
        description="Informational path invariant: must always be 'NONE' on evidence/gap records",
    )
    notes: Optional[str] = Field(None, description="Qualification notes or audit trace")


def validate_transition_chain(
    has_verified_evidence: bool,
    is_requirement_satisfied: bool,
    gap_status: RequirementGapStatus,
    is_overall_compliant: bool,
) -> tuple[bool, str]:
    """Strictly assert the 4-stage deterministic compliance transition chain:
    VERIFIED EVIDENCE → REQUIREMENT SATISFACTION → GAP STATUS → COMPLIANCE RESULT.
    """
    if not has_verified_evidence and is_requirement_satisfied:
        return False, "Violation: Unverified evidence cannot satisfy a requirement."

    if not is_requirement_satisfied and gap_status == RequirementGapStatus.SATISFIED:
        return False, "Violation: Requirement cannot have SATISFIED gap status without being satisfied."

    if gap_status != RequirementGapStatus.SATISFIED and is_overall_compliant:
        return False, "Violation: A product cannot be COMPLIANT if any requirement is not SATISFIED (a single satisfied requirement must never imply overall compliance)."

    return True, "Valid transition: VERIFIED EVIDENCE → REQUIREMENT SATISFACTION → GAP STATUS → COMPLIANCE RESULT."


# =========================================================================
# Milestone M26.3: Evidence-Backed Compliance Passport Re-Exports
# =========================================================================
from backend.app.schemas.compliance_passport import (
    PASSPORT_DOCUMENT_TITLE,
    PASSPORT_PROHIBITED_LABELS,
    STATUTORY_DISCLAIMER_TEXT,
    PassportProductIdentity,
    PassportStandardReference,
    PassportRequirementItem,
    PassportNextActionItem,
    PassportExpertReviewItem,
    PassportSourceReference,
    EvidenceBackedCompliancePassport,
)

