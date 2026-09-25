"""Milestone M26.3: Evidence-Backed Compliance Passport Schemas.

Strict Invariants & Authority Boundaries:
1. Product identity and Product DNA provenance.
2. Applicable BIS standard(s) and revision(s).
3. Applicable clauses and requirements with requirement-by-requirement status.
4. Evidence supporting each requirement, including provenance, authenticity, and retention lineage.
5. Explicit compliance gaps retaining the 10-element auditable chain.
6. Required next actions and categorized action roadmaps.
7. Expert-review items surfaced cleanly without automated clearance.
8. Authoritative source references.
9. Overall deterministic assessment state (projected strictly from Layer 7).
10. SHA-256 integrity seal / artifact fingerprint (reproducible from identical inputs).
11. Document Title: Strictly "Evidence-Backed Pre-Certification Compliance Assessment".
12. Prominent Disclaimer: "Compliance Passport ≠ BIS Certification".
13. Prohibited terms rejected: "BIS Certificate", "BIS Approval", "Official Certification", "Guaranteed Compliance", "Certified by BIS".
14. Layer 7 is sole compliance decision authority; Layer 8 is sole evidence/source trust authority; Layer 9 is output-integrity authority; LLM authority = 0.0%.
15. Zero invented evidence, clauses, laboratory results, fees, timelines, or regulatory facts.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.product_evidence import (
    EvidenceType,
    SourceAuthenticity,
    ArtifactIntegrityStatus,
    EvidenceVerificationStatus,
    EvidenceOntologyTier,
    EvidenceChainRecord,
    StandardRequirementDefinition,
)
from backend.app.schemas.compliance import (
    RequirementGapStatus,
    GapNextAction,
    ComplianceGapItem,
    DeterministicGapAggregationResult,
)


PASSPORT_DOCUMENT_TITLE = "Evidence-Backed Pre-Certification Compliance Assessment"

PASSPORT_PROHIBITED_LABELS = [
    "BIS Certificate",
    "BIS Approval",
    "Official Certification",
    "Guaranteed Compliance",
    "Certified by BIS",
]

STATUTORY_DISCLAIMER_TEXT = (
    "Compliance Passport ≠ BIS Certification. "
    "This document is an evidence-backed engineering pre-certification assessment. "
    "It does not constitute a statutory Bureau of Indian Standards (BIS) license, "
    "BIS certificate, statutory approval, or certification issued by BIS."
)


class PassportProductIdentity(BaseModel):
    """Product identity and Product DNA provenance representation."""
    product_id: str = Field(..., description="Unique product identifier")
    product_name: str = Field(..., description="Product commercial name")
    category: str = Field(..., description="Product category / taxonomy classification")
    sub_category: Optional[str] = Field(None, description="Product sub-category or variant")
    product_dna_attributes: Dict[str, Any] = Field(default_factory=dict, description="Normalized Product DNA key-value attributes")
    product_dna_provenance: str = Field(default="USER_CLAIM", description="Origin classification of Product DNA")
    product_dna_digest: str = Field(..., description="SHA-256 cryptographic digest of canonical Product DNA snapshot")
    product_facts: List[Dict[str, Any]] = Field(default_factory=list, description="Granular Product DNA facts with individual provenance")


class PassportStandardReference(BaseModel):
    """Applicable BIS standard and statutory revision reference."""
    standard_code: str = Field(..., description="Base standard code e.g. IS 17526")
    revision: str = Field(..., description="Statutory revision year e.g. 2021")
    full_standard_number: str = Field(..., description="Full standard designation e.g. IS 17526:2021")
    title: str = Field(..., description="Official standard title")
    qco_order: Optional[str] = Field(None, description="Quality Control Order reference if mandatory")
    regulatory_status: str = Field(default="MANDATORY_QCO", description="Regulatory status e.g. MANDATORY_QCO or VOLUNTARY")
    source_reference: str = Field(default="", description="Official Gazette or BIS catalog citation")


class PassportRequirementItem(BaseModel):
    """Requirement-by-requirement evaluation row showing status, evidence, provenance, and next action."""
    standard: str = Field(..., description="Standard code e.g. IS 17526")
    revision: str = Field(..., description="Standard revision year e.g. 2021")
    clause_number: str = Field(..., description="Clause designation e.g. 5.4")
    clause_title: str = Field(..., description="Clause title e.g. Thermal Heat Retention")
    requirement_id: str = Field(..., description="Requirement identifier e.g. REQ-IS17526-5.4")
    requirement_class: str = Field(..., description="Requirement classification e.g. LAB_TEST_REQUIREMENT")
    status: RequirementGapStatus = Field(..., description="Deterministic status from M26.2 taxonomy")
    required_condition: str = Field(..., description="Statutory threshold or condition specified by standard")
    observed_value: Optional[str] = Field(None, description="Empirical or documentary value extracted from evidence")
    deterministic_result: str = Field(..., description="Deterministic result: PASS, FAIL, GAP_IDENTIFIED, UNVERIFIED")
    
    # Supporting Evidence Details
    evidence_id: Optional[str] = Field(None, description="Backing evidence identifier or None if missing")
    evidence_type: Optional[str] = Field(None, description="Backing evidence type e.g. LABORATORY_TEST_REPORT")
    evidence_status: str = Field(default="MISSING", description="Evidence status: VERIFIED, UNVERIFIED, CONFLICTING, MISSING")
    evidence_sha256: Optional[str] = Field(None, description="SHA-256 hash of the evidence artifact")
    evidence_provenance: Optional[str] = Field(None, description="Origin and issuer of evidence")
    source_authenticity: Optional[str] = Field(None, description="Source authenticity status")
    artifact_integrity: Optional[str] = Field(None, description="Artifact integrity status e.g. HASH_VALID")
    
    # Gap & Next Action
    required_next_action: GapNextAction = Field(..., description="Deterministic next action from M26.2 taxonomy")
    reason: str = Field(..., description="Deterministic audit rationale for status")
    audit_chain_summary: str = Field(default="", description="Summary of the 10-element compliance gap chain")


class PassportNextActionItem(BaseModel):
    """Structured next action recommendation for the MSME / manufacturer."""
    action_type: GapNextAction = Field(..., description="Next action taxonomy")
    clause_number: str = Field(..., description="Governing clause number")
    requirement_id: str = Field(..., description="Associated requirement identifier")
    title: str = Field(..., description="Action summary title")
    description: str = Field(..., description="Operational guidance for completing the action")
    required_evidence_type: str = Field(..., description="Evidence type required to satisfy this requirement")


class PassportExpertReviewItem(BaseModel):
    """Explicit item routed to technical expert adjudication."""
    clause_number: str = Field(..., description="Governing clause number")
    requirement_id: str = Field(..., description="Associated requirement identifier")
    reason: str = Field(..., description="Reason expert review is mandated (e.g. conflicting evidence)")
    conflicting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of contradictory evidence records")
    review_recommendation: str = Field(..., description="Specific recommendation for expert adjudicator")


class PassportSourceReference(BaseModel):
    """Authoritative source reference backing standards and citations."""
    source_id: str = Field(..., description="Identifier for this source record")
    source_type: str = Field(..., description="Source classification: BIS_STANDARD, GAZETTE_QCO, NABL_REPORT")
    reference: str = Field(..., description="Formal reference text or document title")
    publisher_or_authority: str = Field(..., description="Issuing authority e.g. Bureau of Indian Standards, DPIIT")
    verification_status: str = Field(default="VERIFIED", description="Verification status e.g. VERIFIED, RECOGNIZED")
    sha256_hash: Optional[str] = Field(None, description="Cryptographic hash of the source document if available")


class EvidenceBackedCompliancePassport(BaseModel):
    """Production-grade Layer 9 Evidence-Backed Compliance Passport (Milestone M26.3).
    
    Deterministic projection of existing verified results:
    - Layer 5: Statutory Applicability
    - Layer 8: Evidence Validation & Provenance
    - Layer 8: Evidence-to-Requirement Mapping
    - Layer 7: Compliance Gap Aggregation
    - Layer 9: Output Integrity Gate & SHA-256 Integrity Seal
    """
    passport_id: str = Field(..., description="Unique passport identifier e.g. PASSPORT-PROD01-IS17526-v1")
    assessment_id: str = Field(..., description="Parent assessment identifier")
    assessment_number: str = Field(..., description="Assessment tracking reference number")
    document_title: str = Field(
        default=PASSPORT_DOCUMENT_TITLE,
        description="Formal title: strictly 'Evidence-Backed Pre-Certification Compliance Assessment'",
    )
    
    # 1. Product Identity and Product DNA Provenance
    product: PassportProductIdentity = Field(..., description="Product identity and Product DNA provenance")
    
    # 2. Applicable BIS Standard(s) and Revision(s)
    applicable_standards: List[PassportStandardReference] = Field(
        default_factory=list,
        description="Statutory BIS standards and revisions evaluated",
    )
    
    # 3. Requirement-by-Requirement Status & Evidence Supporting Each
    requirements_matrix: List[PassportRequirementItem] = Field(
        default_factory=list,
        description="Complete requirement evaluation rows with evidence & provenance",
    )
    
    # 4. Compliance Gaps (10-Element Chain)
    compliance_gaps: List[ComplianceGapItem] = Field(
        default_factory=list,
        description="Explicit compliance gaps retaining the 10-element auditable chain",
    )
    
    # 5. Required Next Actions & Categorized Roadmaps
    required_next_actions: List[PassportNextActionItem] = Field(
        default_factory=list,
        description="Actionable next steps across all unsatisfied requirements",
    )
    roadmap_lab_test: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_document: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_declaration: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_marking: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_corrective_action: List[ComplianceGapItem] = Field(default_factory=list)
    roadmap_expert_review: List[ComplianceGapItem] = Field(default_factory=list)
    
    # 6. Expert-Review Items
    expert_review_items: List[PassportExpertReviewItem] = Field(
        default_factory=list,
        description="Explicit items requiring human expert review",
    )
    
    # 7. Authoritative Source References
    source_references: List[PassportSourceReference] = Field(
        default_factory=list,
        description="Authoritative sources backing the assessment",
    )
    
    # 8. Overall Deterministic Assessment State (Layer 7 Projection)
    overall_verdict: str = Field(
        ...,
        description="Overall compliance verdict: COMPLIANT, NON_COMPLIANT, GAPS_IDENTIFIED, UNVERIFIED",
    )
    total_requirements: int = Field(default=0)
    satisfied_count: int = Field(default=0)
    not_satisfied_count: int = Field(default=0)
    missing_evidence_count: int = Field(default=0)
    unverified_count: int = Field(default=0)
    conflicting_count: int = Field(default=0)
    expert_review_count: int = Field(default=0)
    not_applicable_count: int = Field(default=0)
    
    # 9. SHA-256 Integrity Seal / Artifact Fingerprint
    integrity_seal: str = Field(
        ...,
        description="Cryptographic SHA-256 fingerprint sealing the deterministic passport contents",
    )
    
    # 10. Generation Timestamp & Source Snapshot / Version Information
    generated_at: str = Field(..., description="Deterministic generation timestamp in ISO 8601 format")
    source_snapshot_version: str = Field(default="v1.2.0-gazette-verified", description="Version of source snapshot")
    knowledge_version: str = Field(default="v1.2.0-gazette-verified", description="Version of BIS knowledge base")
    ruleset_version: str = Field(default="2026.03-gazette", description="Version of regulatory ruleset")
    output_version: int = Field(default=1, description="Sequential output version number")
    
    # 11. Clear Labeling & Disclaimers
    statutory_disclaimer: str = Field(
        default=STATUTORY_DISCLAIMER_TEXT,
        description="Non-negotiable disclaimer: Compliance Passport ≠ BIS Certification",
    )
    disclaimers: List[str] = Field(default_factory=list, description="Comprehensive list of legal boundaries")
    prohibited_labels_asserted: List[str] = Field(
        default_factory=list,
        description="Should always be empty; tracks any suppressed prohibited terms",
    )
    
    # 12. Authority Boundary Invariants
    compliance_authority: str = Field(
        default="LAYER_7_ONLY",
        description="Layer 7 is sole compliance decision authority",
    )
    evidence_authority: str = Field(
        default="LAYER_8_ONLY",
        description="Layer 8 is sole evidence/source trust authority",
    )
    output_integrity_authority: str = Field(
        default="LAYER_9_PASSPORT_COMPILER",
        description="Layer 9 is output-integrity authority",
    )
    llm_compliance_authority: float = Field(
        default=0.0,
        description="LLM has exactly 0.0% compliance authority",
    )
    regulatory_conclusion: str = Field(
        default="NONE",
        description="Non-authoritative status placeholder; must be 'NONE'",
    )
    
    # 13. UI & Backwards-Compatibility Fields (Optional projections for frontend renderer)
    product_name: Optional[str] = Field(None, description="Convenience projection of product.product_name")
    category: Optional[str] = Field(None, description="Convenience projection of product.category")
    product_dna_version: str = Field(default="v1.0")
    lifecycle_state: str = Field(default="FINALIZED")
    snapshot_hash: str = Field(default="", description="Alias for integrity_seal for backwards compatibility")
    evidence_hashes: Dict[str, str] = Field(default_factory=dict)
    compliance_evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    testing_roadmap: List[Dict[str, Any]] = Field(default_factory=list)
    recognized_laboratories: List[Dict[str, Any]] = Field(default_factory=list)
    source_index: List[Dict[str, Any]] = Field(default_factory=list)
    trust_basis: Dict[str, Any] = Field(default_factory=dict)
    claim_statement: str = Field(default="Evidence-Backed Pre-Certification Evaluation Roadmap")
    mode: str = Field(default="AUTHORITATIVE_MODE")
    limitations: List[str] = Field(default_factory=list)

    @field_validator("document_title")
    @classmethod
    def enforce_document_title(cls, v: str) -> str:
        if v.strip() != PASSPORT_DOCUMENT_TITLE:
            raise ValueError(
                f"Prohibited title: Document MUST be titled '{PASSPORT_DOCUMENT_TITLE}', but received '{v}'."
            )
        return v

    @field_validator("prohibited_labels_asserted")
    @classmethod
    def reject_prohibited_labels(cls, v: List[str]) -> List[str]:
        if len(v) > 0:
            raise ValueError(f"Prohibited regulatory labels detected in passport output: {v}")
        return v
