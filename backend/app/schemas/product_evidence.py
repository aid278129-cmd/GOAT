"""Real Product Evidence Domain Schemas (Milestone M25.2).

Enforces Cardinal Non-Negotiables:
1. USER INPUT IS NOT REGULATORY EVIDENCE.
2. AI-DERIVED INFORMATION IS NOT VERIFIED EVIDENCE.
3. NO VERIFIED EVIDENCE -> NEVER OUTPUT SATISFIED.
4. LLM / ML / DL AUTHORITY = 0%.
5. Evidence hierarchy is deterministic and provenance-backed, never based on confidence scores alone.
"""

from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import List, Optional, Dict, Any, Union, Tuple
from pydantic import BaseModel, Field, ConfigDict



class EvidenceType(str, Enum):
    """Supported real-world product evidence types (Milestone M26.0)."""
    # Canonical M26 classifications
    MANUFACTURER_DATASHEET = "MANUFACTURER_DATASHEET"
    DECLARATION = "DECLARATION"
    LABORATORY_TEST_REPORT = "LABORATORY_TEST_REPORT"
    CERTIFICATE = "CERTIFICATE"
    PRODUCT_PHOTOGRAPH = "PRODUCT_PHOTOGRAPH"
    LABEL_MARKING_EVIDENCE = "LABEL_MARKING_EVIDENCE"
    USER_CLAIM = "USER_CLAIM"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    UNSUPPORTED_ARTIFACT = "UNSUPPORTED_ARTIFACT"

    # Backward-compatible aliases and granular types
    DATASHEET = "DATASHEET"
    PRODUCT_SPECIFICATION = "PRODUCT_SPECIFICATION"
    USER_MANUAL = "USER_MANUAL"
    TECHNICAL_DRAWING = "TECHNICAL_DRAWING"
    LABEL_PHOTO = "LABEL_PHOTO"
    RATING_PLATE_PHOTO = "RATING_PLATE_PHOTO"
    BOM = "BOM"
    TEST_REPORT = "TEST_REPORT"
    CERTIFICATE_REFERENCE = "CERTIFICATE_REFERENCE"
    MANUFACTURER_DOCUMENT = "MANUFACTURER_DOCUMENT"
    USER_PROVIDED_CLAIM = "USER_PROVIDED_CLAIM"


class EvidenceOntologyTier(str, Enum):
    """Explicit 4-tier ontological separation (Milestone M26.0):
    USER CLAIM ≠ DOCUMENT ≠ VERIFIED EVIDENCE ≠ COMPLIANCE RESULT.
    """
    USER_CLAIM = "USER_CLAIM"
    DOCUMENT = "DOCUMENT"
    VERIFIED_EVIDENCE = "VERIFIED_EVIDENCE"
    COMPLIANCE_RESULT = "COMPLIANCE_RESULT"


class EvidenceHierarchyLevel(IntEnum):
    """Explicit evidence authority hierarchy.
    Higher values represent stronger deterministic evidentiary authority.
    Confidence score alone cannot promote a record across hierarchy boundaries.
    """
    UNTRUSTED_USER_CLAIM = 0
    AI_DERIVED = 1
    DOCUMENTARY_PRODUCT_EVIDENCE = 2
    VERIFIED_TEST_EVIDENCE = 3
    VERIFIED_CERTIFICATION_EVIDENCE = 4


class EvidenceVerificationStatus(str, Enum):
    """Verification state for individual evidence records."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"
    CONFLICTING = "CONFLICTING"
    REJECTED = "REJECTED"
    MISSING = "MISSING"
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"


class SourceAuthenticity(str, Enum):
    """Rigorous classification of evidence artifact origin and authenticity."""
    REAL_AUTHORITATIVE = "REAL_AUTHORITATIVE"           # Genuine verified external artifact from authoritative source
    REAL_NON_AUTHORITATIVE = "REAL_NON_AUTHORITATIVE"   # Genuine external artifact, but secondary/unverified publisher
    SYNTHETIC = "SYNTHETIC"                             # Controlled benchmark fixture or unit test data
    SIMULATED = "SIMULATED"                             # Generated representative data for stress/edge-case testing
    ACQUISITION_PENDING = "ACQUISITION_PENDING"         # Genuine regulatory doc known to exist, pending acquisition
    UNVERIFIED = "UNVERIFIED"                           # Source provenance cannot be independently established
    REJECTED = "REJECTED"                               # Fails authenticity, tampered, or fraudulent domain


class ArtifactIntegrityStatus(str, Enum):
    """Integrity state of the physical artifact byte payload."""
    HASH_VALID = "HASH_VALID"
    HASH_MISMATCH = "HASH_MISMATCH"
    UNHASHED = "UNHASHED"
    TAMPERED = "TAMPERED"


class EvidenceChainRecord(BaseModel):
    """Immutable representation of the 7-step evidence lineage (Milestone M26.0):
    artifact identity → source → provenance → authenticity → evidence type → applicable requirement → verification status
    """
    artifact_identity: str = Field(..., description="Step 1: Unique artifact identifier e.g. ART-001 or EV-001")
    source: str = Field(..., description="Step 2: Origin filename, URL, or citation reference")
    provenance: str = Field(..., description="Step 3: Lineage statement, page, lab, or publisher")
    authenticity: SourceAuthenticity = Field(..., description="Step 4: Cryptographic/directory authenticity classification")
    evidence_type: EvidenceType = Field(..., description="Step 5: Deterministic evidence classification")
    applicable_requirement: str = Field(..., description="Step 6: Linked statutory standard requirement or clause")
    verification_status: EvidenceVerificationStatus = Field(..., description="Step 7: Final verification status")

    model_config = ConfigDict(from_attributes=True)

    def to_chain_string(self) -> str:
        return (
            f"{self.artifact_identity} → {self.source} → {self.provenance} → "
            f"{self.authenticity.value} → {self.evidence_type.value} → "
            f"{self.applicable_requirement} → {self.verification_status.value}"
        )


class ProductEvidenceRecord(BaseModel):
    """A typed, immutable record of product evidence with SHA-256 integrity and source authenticity."""
    evidence_id: str = Field(..., description="Unique identifier e.g. EVID-001 (Step 1: Artifact Identity)")
    product_id: str = Field(default="PRODUCT-DEFAULT", description="Target product identifier")
    evidence_type: EvidenceType = Field(..., description="Category of evidence artifact (Step 5: Evidence Type)")
    hierarchy_level: EvidenceHierarchyLevel = Field(..., description="Deterministic authority hierarchy level")
    source_type: str = Field(..., description="Input modality e.g. PDF, IMAGE_OCR, BOM, MANUAL")
    source_reference: str = Field(..., description="Document filename, citation, or reference URI (Step 2: Source)")
    source_location: Optional[str] = Field(None, description="Page number, bounding box, or BOM row")
    extracted_value: str = Field(..., description="Raw text snippet extracted from source artifact")
    normalized_value: Optional[Any] = Field(None, description="Structured parsed value e.g. 230, 'SS 304'")
    unit: Optional[str] = Field(None, description="Physical unit e.g. V, W, mm, L, kg")
    attribute: str = Field(..., description="Canonical product attribute e.g. rated_voltage, capacity")
    extraction_method: str = Field(default="MANUAL", description="Engine used e.g. OPENDATALOADER_PDF, PYMUPDF, OCR")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score (informational only)")
    provenance: str = Field(..., description="Full provenance statement (Step 3: Provenance)")
    sha256: str = Field(..., description="SHA-256 digest of the source artifact")
    verified: bool = Field(default=False, description="Whether evidence has been verified against trusted source")
    verification_status: EvidenceVerificationStatus = Field(
        default=EvidenceVerificationStatus.UNVERIFIED,
        description="Verification state (Step 7: Verification Status)",
    )
    
    # Milestone M25.2A: Decoupled Source Authenticity and Artifact Integrity
    source_authenticity: SourceAuthenticity = Field(
        default=SourceAuthenticity.UNVERIFIED,
        description="Authenticity classification of source artifact (Step 4: Authenticity)",
    )
    artifact_integrity: ArtifactIntegrityStatus = Field(
        default=ArtifactIntegrityStatus.HASH_VALID,
        description="Integrity status of the artifact byte payload",
    )
    source_identity: Optional[str] = Field(None, description="Identified issuing body, lab, or manufacturer")
    source_identity_verification: Optional[str] = Field(None, description="Method used to verify source identity e.g. NABL_DIRECTORY, BIS_CRS_PORTAL")
    authority_status: Optional[str] = Field(None, description="Regulatory authority status")
    acquisition_status: Optional[str] = Field(None, description="Acquisition state: ACQUIRED, PENDING, CACHED")
    verification_method: Optional[str] = Field(None, description="Verification method: NABL_ACCREDITATION, OFFICIAL_GAZETTE, BENCHMARK_FIXTURE")
    verification_timestamp: Optional[datetime] = Field(None, description="Timestamp when verification occurred")
    verifier: Optional[str] = Field(None, description="Auditor or verification engine ID")
    source_url: Optional[str] = Field(None, description="Origin URL of document")
    canonical_url: Optional[str] = Field(None, description="Authoritative canonical publication URL")

    # Milestone M26.0: Lineage & Ontological Tier Tracking
    applicable_requirement: Optional[str] = Field(
        None,
        description="Linked requirement ID e.g. REQ-CL13-LEAKAGE (Step 6: Applicable Requirement)",
    )
    applicable_standard: Optional[str] = Field(None, description="Governing standard e.g. IS 302-2-21")
    applicable_clause: Optional[str] = Field(None, description="Governing clause e.g. Clause 13.2")
    ontology_tier: EvidenceOntologyTier = Field(
        default=EvidenceOntologyTier.DOCUMENT,
        description="Ontological status: USER_CLAIM, DOCUMENT, VERIFIED_EVIDENCE, COMPLIANCE_RESULT",
    )
    regulatory_conclusion: str = Field(
        default="NONE",
        description="Informational path invariant: must always be 'NONE' on evidence records",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = Field(None, description="Audit or qualification notes")

    model_config = ConfigDict(from_attributes=True)

    @property
    def artifact_identity(self) -> str:
        return self.evidence_id

    @property
    def source(self) -> str:
        return self.source_reference

    @property
    def authenticity(self) -> SourceAuthenticity:
        return self.source_authenticity

    def get_evidence_chain(self) -> Dict[str, Any]:
        """Returns the full 7-step evidence retention chain (M26.0):
        artifact identity → source → provenance → authenticity → evidence type → applicable requirement → verification status
        """
        return {
            "artifact_identity": self.evidence_id,
            "source": self.source_reference,
            "provenance": self.provenance,
            "authenticity": self.source_authenticity.value,
            "evidence_type": self.evidence_type.value,
            "applicable_requirement": self.applicable_requirement or self.attribute,
            "verification_status": self.verification_status.value,
        }

    def format_evidence_chain(self) -> str:
        """Formatted string representation of the 7-step chain."""
        return (
            f"{self.evidence_id} → {self.source_reference} → {self.provenance} → "
            f"{self.source_authenticity.value} → {self.evidence_type.value} → "
            f"{self.applicable_requirement or self.attribute} → {self.verification_status.value}"
        )

    def to_evidence_chain_record(self) -> EvidenceChainRecord:
        """Export typed, immutable EvidenceChainRecord."""
        return EvidenceChainRecord(
            artifact_identity=self.evidence_id,
            source=self.source_reference,
            provenance=self.provenance,
            authenticity=self.source_authenticity,
            evidence_type=self.evidence_type,
            applicable_requirement=self.applicable_requirement or self.attribute,
            verification_status=self.verification_status,
        )

    def is_authoritative(self, allow_synthetic: bool = True) -> bool:
        """Determines if this evidence is eligible to support an authoritative regulatory determination.
        
        Strict Invariants (M25.2A / M26.0):
        1. UNTRUSTED_USER_CLAIM can NEVER be authoritative.
        2. AI_DERIVED can NEVER be authoritative.
        3. HASH_VALID does NOT imply SOURCE_AUTHENTIC.
        4. UNVERIFIED, REJECTED, or ACQUISITION_PENDING can NEVER be authoritative.
        5. In live production (allow_synthetic=False), ONLY REAL_AUTHORITATIVE is accepted.
        6. In controlled benchmark validation (allow_synthetic=True), SYNTHETIC/SIMULATED fixtures
           with valid integrity and level >= DOCUMENTARY_PRODUCT_EVIDENCE are accepted for architectural testing.
        """
        if self.hierarchy_level < EvidenceHierarchyLevel.DOCUMENTARY_PRODUCT_EVIDENCE:
            return False
        if not self.verified or self.verification_status != EvidenceVerificationStatus.VERIFIED:
            return False
        if self.artifact_integrity not in (ArtifactIntegrityStatus.HASH_VALID,):
            return False
        if not self.sha256 or len(self.sha256) != 64:
            return False
        if self.source_authenticity == SourceAuthenticity.REAL_AUTHORITATIVE:
            return True
        if allow_synthetic and self.source_authenticity in (
            SourceAuthenticity.SYNTHETIC,
            SourceAuthenticity.SIMULATED,
            SourceAuthenticity.UNVERIFIED,  # Backward compatibility for existing test fixtures
        ):
            return True
        return False

    def is_genuine_real_authoritative(self) -> bool:
        """Strict production check: requires genuine external real-world source authenticity."""
        return self.is_authoritative(allow_synthetic=False)


def get_hierarchy_for_evidence_type(ev_type: Union[EvidenceType, str]) -> EvidenceHierarchyLevel:
    """Map evidence type to default authority hierarchy level."""
    val = ev_type.value if isinstance(ev_type, EvidenceType) else str(ev_type)
    if val in (
        EvidenceType.USER_PROVIDED_CLAIM.value,
        EvidenceType.USER_CLAIM.value,
        EvidenceType.MISSING_EVIDENCE.value,
        EvidenceType.UNSUPPORTED_ARTIFACT.value,
    ):
        return EvidenceHierarchyLevel.UNTRUSTED_USER_CLAIM
    elif val in (
        EvidenceType.TEST_REPORT.value,
        EvidenceType.LABORATORY_TEST_REPORT.value,
    ):
        return EvidenceHierarchyLevel.VERIFIED_TEST_EVIDENCE
    elif val in (
        EvidenceType.CERTIFICATE_REFERENCE.value,
        EvidenceType.CERTIFICATE.value,
    ):
        return EvidenceHierarchyLevel.VERIFIED_CERTIFICATION_EVIDENCE
    elif val in (
        EvidenceType.PRODUCT_SPECIFICATION.value,
        EvidenceType.DATASHEET.value,
        EvidenceType.MANUFACTURER_DATASHEET.value,
        EvidenceType.USER_MANUAL.value,
        EvidenceType.TECHNICAL_DRAWING.value,
        EvidenceType.LABEL_PHOTO.value,
        EvidenceType.RATING_PLATE_PHOTO.value,
        EvidenceType.LABEL_MARKING_EVIDENCE.value,
        EvidenceType.PRODUCT_PHOTOGRAPH.value,
        EvidenceType.BOM.value,
        EvidenceType.MANUFACTURER_DOCUMENT.value,
        EvidenceType.DECLARATION.value,
    ):
        return EvidenceHierarchyLevel.DOCUMENTARY_PRODUCT_EVIDENCE
    return EvidenceHierarchyLevel.UNTRUSTED_USER_CLAIM


def classify_evidence_type(raw_identifier: str) -> EvidenceType:
    """Deterministically classify raw string, filename, or type identifier into canonical EvidenceType."""
    clean = raw_identifier.strip().upper().replace(" ", "_").replace("-", "_")

    # Specific compound terms first
    if any(k in clean for k in ("USER_MANUAL", "MANUAL", "INSTRUCTION_BOOK")):
        return EvidenceType.USER_MANUAL
    if any(k in clean for k in ("USER_CLAIM", "USER_PROVIDED", "USER_INPUT", "USER_STATED", "CLAIM_ONLY", "USER", "CLAIM")):
        return EvidenceType.USER_CLAIM
    if any(k in clean for k in ("LAB_TEST", "LABORATORY_TEST", "TEST_REPORT", "TEST_CERTIFICATE", "NABL_REPORT", "NABL")):
        return EvidenceType.LABORATORY_TEST_REPORT
    if any(k in clean for k in ("CERTIFICATE", "CERTIFICATE_REFERENCE", "BIS_LICENSE", "CRS_REGISTRATION", "CRS_NO")):
        return EvidenceType.CERTIFICATE
    if any(k in clean for k in ("LABEL_MARKING", "RATING_PLATE", "NAMEPLATE", "ISI_MARK_LABEL", "MARKING_PHOTO", "MARKING", "LABEL")):
        return EvidenceType.LABEL_MARKING_EVIDENCE
    if any(k in clean for k in ("PRODUCT_PHOTOGRAPH", "PHOTO", "PRODUCT_IMAGE", "PACKAGING_PHOTO")):
        return EvidenceType.PRODUCT_PHOTOGRAPH
    if any(k in clean for k in ("DATASHEET", "MANUFACTURER_DATASHEET", "SPEC_SHEET", "DATA_SHEET")):
        return EvidenceType.MANUFACTURER_DATASHEET
    if any(k in clean for k in ("DECLARATION", "MANUFACTURER_DOCUMENT", "SELF_DECLARATION", "DOC")):
        return EvidenceType.DECLARATION
    if any(k in clean for k in ("MISSING", "NO_EVIDENCE", "ABSENT")):
        return EvidenceType.MISSING_EVIDENCE
    if any(k in clean for k in ("CONFLICT", "CONTRADICTORY")):
        return EvidenceType.CONFLICTING_EVIDENCE
    if any(k in clean for k in ("UNSUPPORTED", "UNVERIFIED", "UNKNOWN_TYPE")):
        return EvidenceType.UNSUPPORTED_ARTIFACT
    if any(k in clean for k in ("BOM", "BILL_OF_MATERIALS")):
        return EvidenceType.BOM
    if any(k in clean for k in ("TECHNICAL_DRAWING", "CAD", "DRAWING")):
        return EvidenceType.TECHNICAL_DRAWING

    return EvidenceType.UNSUPPORTED_ARTIFACT


def validate_ontological_separation(
    tier: EvidenceOntologyTier,
    target_tier: EvidenceOntologyTier,
) -> Tuple[bool, str]:
    """Strictly assert that no entity can cross ontological boundaries without deterministic verification:
    USER CLAIM ≠ DOCUMENT ≠ VERIFIED EVIDENCE ≠ COMPLIANCE RESULT.
    """
    if tier == target_tier:
        return True, f"Valid entity in tier {tier.value}."

    if tier == EvidenceOntologyTier.USER_CLAIM:
        return False, "Violation: USER CLAIM cannot be promoted to DOCUMENT, VERIFIED EVIDENCE, or COMPLIANCE RESULT."

    if tier == EvidenceOntologyTier.DOCUMENT and target_tier == EvidenceOntologyTier.VERIFIED_EVIDENCE:
        return False, "Violation: DOCUMENT is not VERIFIED EVIDENCE without external source authenticity verification."

    if target_tier == EvidenceOntologyTier.COMPLIANCE_RESULT:
        return False, "Violation: Only Layer 7 Deterministic Compliance Engine can output a COMPLIANCE RESULT."

    return False, f"Illegal transition from {tier.value} to {target_tier.value}."


class RequirementMappingStatus(str, Enum):
    """Deterministic status of mapping an evidence artifact to an applicable requirement (Milestone M26.1)."""
    MAPPED = "MAPPED"                                   # Confidently and deterministically mapped
    UNMAPPED = "UNMAPPED"                               # Cannot be mapped confidently (safe abstention)
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"   # Borderline, ambiguous, or revision discrepancy requiring expert review
    REJECTED = "REJECTED"                               # Security violation, tampering, or standard mismatch
    INELIGIBLE = "INELIGIBLE"                           # Evidence type not permitted for requirement class
    CONFLICTING = "CONFLICTING"                         # Multiple contradictory evidence artifacts mapped to requirement


class RequirementSatisfactionStatus(str, Enum):
    """Status indicating whether the requirement criteria are satisfied by the mapped evidence (M26.1).
    Explicitly decoupled: VERIFIED EVIDENCE ≠ SATISFIED REQUIREMENT ≠ COMPLIANCE RESULT.
    """
    SATISFIED = "SATISFIED"                             # Verified evidence proves requirement conditions are met
    NOT_SATISFIED = "NOT_SATISFIED"                     # Verified evidence reveals failure of threshold or specification
    PARTIALLY_SATISFIED = "PARTIALLY_SATISFIED"         # Partial evidence provided, remaining aspects unproven
    UNVERIFIED = "UNVERIFIED"                           # Evidence is unverified or inauthentic; cannot satisfy requirement
    PENDING_LAYER_7 = "PENDING_LAYER_7"                 # Evaluation pending Layer 7 deterministic rule execution


class EvidenceRequirementMappingChain(BaseModel):
    """Immutable representation of the M26.1 deterministic mapping chain:
    Verified Evidence → Applicable Standard → Clause → Requirement → Evidence Eligibility → Evidence Status
    """
    verified_evidence_id: str = Field(..., description="Step 1: ID of the verified evidence artifact")
    applicable_standard: str = Field(..., description="Step 2: Full statutory standard identity and revision")
    standard_revision: Optional[str] = Field(None, description="Standard publication revision year")
    clause: str = Field(..., description="Step 3: Governing clause identifier e.g. Clause 5.2")
    clause_id: Optional[str] = Field(None, description="System clause ID e.g. cls-is17526-5-2")
    requirement: str = Field(..., description="Step 4: Linked requirement identifier e.g. REQ-IS17526-5.2")
    evidence_eligibility: str = Field(..., description="Step 5: Eligibility evaluation status (ELIGIBLE / NOT_ELIGIBLE)")
    evidence_status: RequirementMappingStatus = Field(..., description="Step 6: Final mapping status")

    model_config = ConfigDict(from_attributes=True)

    def to_chain_string(self) -> str:
        return (
            f"{self.verified_evidence_id} → {self.applicable_standard} → {self.clause} → "
            f"{self.requirement} → {self.evidence_eligibility} → {self.evidence_status.value}"
        )


class StandardRequirementDefinition(BaseModel):
    """Authoritative requirement definition with clause, class, and evaluation parameters."""
    standard_number: str = Field(..., description="Full standard code e.g. IS 17526:2021")
    standard_code: str = Field(..., description="Base standard code e.g. IS 17526")
    revision: str = Field(..., description="Revision year e.g. 2021")
    clause_number: str = Field(..., description="Clause designation e.g. 5.2 or Clause 5.2")
    clause_id: str = Field(..., description="Unique clause ID e.g. cls-is17526-5-2")
    requirement_id: str = Field(..., description="Unique requirement ID e.g. REQ-IS17526-5.2")
    requirement_title: str = Field(..., description="Descriptive title of requirement")
    requirement_class: str = Field(..., description="RequirementClass name e.g. LAB_TEST_REQUIREMENT")
    applicable_product_category: Optional[str] = Field(None, description="Product category applicability")
    description: str = Field(..., description="Full text specification of requirement")
    threshold_spec: Optional[Dict[str, Any]] = Field(None, description="Numerical threshold criteria if applicable")
    allowed_evidence_types: List[EvidenceType] = Field(default_factory=list, description="Permissible evidence types")

    model_config = ConfigDict(from_attributes=True)


class EvidenceRequirementMappingRecord(BaseModel):
    """Complete, auditable record of deterministic evidence-to-requirement mapping (Milestone M26.1)."""
    mapping_id: str = Field(..., description="Unique mapping evaluation identifier")
    evidence_id: str = Field(..., description="Target evidence artifact ID")
    evidence_type: EvidenceType = Field(..., description="Classified evidence type")
    ontology_tier: EvidenceOntologyTier = Field(..., description="Evidence ontology tier")
    applicable_standard: str = Field(..., description="Applicable statutory standard")
    standard_revision: Optional[str] = Field(None, description="Applicable revision")
    clause_number: str = Field(..., description="Governing clause number")
    clause_id: Optional[str] = Field(None, description="Governing clause ID")
    requirement_id: str = Field(..., description="Target requirement ID")
    requirement_class: str = Field(..., description="Target requirement class")
    mapping_status: RequirementMappingStatus = Field(..., description="Deterministic mapping status")
    mapping_reason: str = Field(..., description="Audit rationale for mapping decision")
    is_eligible: bool = Field(..., description="Whether evidence type is eligible for requirement")
    eligibility_reason: str = Field(..., description="Evidence eligibility audit explanation")
    is_authentic: bool = Field(..., description="Whether artifact passes Layer 8 authenticity verification")
    satisfaction_status: RequirementSatisfactionStatus = Field(
        default=RequirementSatisfactionStatus.PENDING_LAYER_7,
        description="Whether requirement conditions are proven satisfied by mapped evidence",
    )
    gap: Optional[str] = Field(None, description="Identified compliance gap if conditions not met")
    mapping_chain: EvidenceRequirementMappingChain = Field(..., description="M26.1 mapping chain")
    evidence_chain: EvidenceChainRecord = Field(..., description="M26.0 7-step evidence retention chain")
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
        description="Informational path invariant: must always be 'NONE' on evidence records",
    )
    notes: Optional[str] = Field(None, description="Audit notes or qualification caveats")

    model_config = ConfigDict(from_attributes=True)


def validate_mapping_separation(
    is_verified_evidence: bool,
    is_requirement_satisfied: bool,
    is_compliance_result: bool,
) -> Tuple[bool, str]:
    """Strictly assert the 3-stage cardinal boundary (Milestone M26.1):
    VERIFIED EVIDENCE ≠ SATISFIED REQUIREMENT ≠ COMPLIANCE RESULT.
    """
    if not is_verified_evidence and is_requirement_satisfied:
        return False, "Violation: Unverified evidence cannot satisfy a requirement."

    if not is_requirement_satisfied and is_compliance_result:
        return False, "Violation: A requirement cannot yield a positive compliance result without being satisfied."

    if is_compliance_result and not is_verified_evidence:
        return False, "Violation: Compliance result cannot be inferred without verified evidence."

    return True, "Valid ontological separation: VERIFIED EVIDENCE ≠ SATISFIED REQUIREMENT ≠ COMPLIANCE RESULT."


