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
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class EvidenceType(str, Enum):
    """Supported real-world product evidence types."""
    PRODUCT_SPECIFICATION = "PRODUCT_SPECIFICATION"
    DATASHEET = "DATASHEET"
    USER_MANUAL = "USER_MANUAL"
    TECHNICAL_DRAWING = "TECHNICAL_DRAWING"
    LABEL_PHOTO = "LABEL_PHOTO"
    RATING_PLATE_PHOTO = "RATING_PLATE_PHOTO"
    BOM = "BOM"
    TEST_REPORT = "TEST_REPORT"
    DECLARATION = "DECLARATION"
    CERTIFICATE_REFERENCE = "CERTIFICATE_REFERENCE"
    MANUFACTURER_DOCUMENT = "MANUFACTURER_DOCUMENT"
    USER_PROVIDED_CLAIM = "USER_PROVIDED_CLAIM"


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


class ProductEvidenceRecord(BaseModel):
    """A typed, immutable record of product evidence with SHA-256 integrity and source authenticity."""
    evidence_id: str = Field(..., description="Unique identifier e.g. EVID-001")
    product_id: str = Field(default="PRODUCT-DEFAULT", description="Target product identifier")
    evidence_type: EvidenceType = Field(..., description="Category of evidence artifact")
    hierarchy_level: EvidenceHierarchyLevel = Field(..., description="Deterministic authority hierarchy level")
    source_type: str = Field(..., description="Input modality e.g. PDF, IMAGE_OCR, BOM, MANUAL")
    source_reference: str = Field(..., description="Document filename, citation, or reference URI")
    source_location: Optional[str] = Field(None, description="Page number, bounding box, or BOM row")
    extracted_value: str = Field(..., description="Raw text snippet extracted from source artifact")
    normalized_value: Optional[Any] = Field(None, description="Structured parsed value e.g. 230, 'SS 304'")
    unit: Optional[str] = Field(None, description="Physical unit e.g. V, W, mm, L, kg")
    attribute: str = Field(..., description="Canonical product attribute e.g. rated_voltage, capacity")
    extraction_method: str = Field(default="MANUAL", description="Engine used e.g. OPENDATALOADER_PDF, PYMUPDF, OCR")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score (informational only)")
    provenance: str = Field(..., description="Full provenance statement")
    sha256: str = Field(..., description="SHA-256 digest of the source artifact")
    verified: bool = Field(default=False, description="Whether evidence has been verified against trusted source")
    verification_status: EvidenceVerificationStatus = Field(default=EvidenceVerificationStatus.UNVERIFIED)
    
    # Milestone M25.2A: Decoupled Source Authenticity and Artifact Integrity
    source_authenticity: SourceAuthenticity = Field(
        default=SourceAuthenticity.UNVERIFIED,
        description="Authenticity classification of source artifact",
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

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = Field(None, description="Audit or qualification notes")

    model_config = ConfigDict(from_attributes=True)

    def is_authoritative(self, allow_synthetic: bool = True) -> bool:
        """Determines if this evidence is eligible to support an authoritative regulatory determination.
        
        Strict Invariants (M25.2A):
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


def get_hierarchy_for_evidence_type(ev_type: EvidenceType) -> EvidenceHierarchyLevel:
    """Map evidence type to default authority hierarchy level."""
    if ev_type == EvidenceType.USER_PROVIDED_CLAIM:
        return EvidenceHierarchyLevel.UNTRUSTED_USER_CLAIM
    elif ev_type in (
        EvidenceType.TEST_REPORT,
    ):
        return EvidenceHierarchyLevel.VERIFIED_TEST_EVIDENCE
    elif ev_type in (
        EvidenceType.CERTIFICATE_REFERENCE,
    ):
        return EvidenceHierarchyLevel.VERIFIED_CERTIFICATION_EVIDENCE
    elif ev_type in (
        EvidenceType.PRODUCT_SPECIFICATION,
        EvidenceType.DATASHEET,
        EvidenceType.USER_MANUAL,
        EvidenceType.TECHNICAL_DRAWING,
        EvidenceType.LABEL_PHOTO,
        EvidenceType.RATING_PLATE_PHOTO,
        EvidenceType.BOM,
        EvidenceType.MANUFACTURER_DOCUMENT,
        EvidenceType.DECLARATION,
    ):
        return EvidenceHierarchyLevel.DOCUMENTARY_PRODUCT_EVIDENCE
    return EvidenceHierarchyLevel.UNTRUSTED_USER_CLAIM
