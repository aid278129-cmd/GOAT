"""M22 Canonical Data Models for Real BIS Data & Ground-Truth Dataset.

Enforces:
1. Strict separation of BIS normative knowledge from product evidence.
2. QCO regulatory information separated from technical standard clauses.
3. Explicit acquisition and verification states.
4. Cryptographic SHA-256 traceability from source document to individual clause.
5. Invariant: AI / ML confidence is never regulatory compliance authority.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class SourceTrustState(str, Enum):
    """Explicit trust and acquisition states for BIS sources."""
    CATALOG_ONLY = "CATALOG_ONLY"
    QCO_VERIFIED = "QCO_VERIFIED"
    DOCUMENT_ACQUIRED = "DOCUMENT_ACQUIRED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    CLAUSE_INDEXED = "CLAUSE_INDEXED"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"
    INVALID_SOURCE = "INVALID_SOURCE"
    REJECTED_SOURCE = "REJECTED_SOURCE"


class ReviewState(str, Enum):
    """Human-review validation states for ground-truth cases."""
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CaseType(str, Enum):
    """Classification of ground-truth evaluation cases."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class ExtractionMethodType(str, Enum):
    """Document extraction method."""
    TEXT_EXTRACTION = "TEXT_EXTRACTION"
    OCR = "OCR"
    HYBRID = "HYBRID"


class StandardRecord(BaseModel):
    """Authoritative or catalog record for an Indian Standard (IS)."""
    standard_id: str = Field(..., description="Unique internal standard ID, e.g. BIS-STD-001 or STD-IS-17526")
    standard_number: str = Field(..., description="Canonical standard code, e.g. IS 17526:2021")
    title: str = Field(..., description="Official title of the standard")
    short_title: Optional[str] = None
    edition: Optional[str] = None
    year: Optional[int] = None
    category: str = Field(..., description="Product category/domain")
    scope: Optional[str] = None
    status: str = Field(default="ACTIVE", description="ACTIVE | WITHDRAWN | SUPERSEDED")
    source_type: str = Field(default="BIS_OFFICIAL", description="BIS_OFFICIAL | GAZETTE_NOTIFICATION | OTHER")
    source_url: Optional[str] = None
    source_authority: str = Field(default="Bureau of Indian Standards", description="Issuing/governing body")
    retrieval_date: Optional[str] = None
    verification_status: SourceTrustState = Field(default=SourceTrustState.QCO_VERIFIED)
    acquisition_status: SourceTrustState = Field(default=SourceTrustState.ACQUISITION_PENDING)
    document_hash: Optional[str] = Field(default=None, description="SHA-256 hash of associated standard document")
    dataset_version: str = Field(default="v1.2.0")
    license_access_notes: Optional[str] = None
    qco_reference: Optional[str] = None
    effective_date: Optional[str] = None
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    amendments_count: int = 0
    amendments: List[Dict[str, Any]] = Field(default_factory=list)
    key_testing_parameters: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class QCORecord(BaseModel):
    """Quality Control Order / Gazette Regulatory Record.
    
    CRITICAL: QCO information remains strictly separate from standard clause content.
    """
    qco_id: str = Field(..., description="Unique QCO ID, e.g. QCO-DPIIT-FLASKS-2023")
    order_title: str = Field(..., description="Title of the Quality Control Order")
    gazette_reference: Optional[Any] = Field(default=None, description="Official Gazette notification number or object")
    issuing_authority: str = Field(default="DPIIT, Ministry of Commerce and Industry")
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    standard_number: str = Field(..., description="Governed Indian Standard number")
    product_description: Optional[str] = None
    applicability_text: Optional[str] = None
    exemptions: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    source_hash: Optional[str] = Field(default=None, description="SHA-256 of gazette notification document")
    verification_status: SourceTrustState = Field(default=SourceTrustState.QCO_VERIFIED)
    is_mandatory: bool = True
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class StandardDocument(BaseModel):
    """Physical or digital BIS Standard document metadata and acquisition status."""
    document_id: str = Field(..., description="Unique document ID, e.g. DOC-IS-17526-2021")
    standard_number: str = Field(..., description="Associated standard code")
    title: str = Field(..., description="Title of the document")
    document_type: str = Field(default="INDIAN_STANDARD", description="INDIAN_STANDARD | QCO_ORDER | PRODUCT_MANUAL")
    source: str = Field(default="BIS_OFFICIAL")
    source_url: Optional[str] = None
    acquisition_status: SourceTrustState = Field(default=SourceTrustState.ACQUISITION_PENDING)
    verification_status: SourceTrustState = Field(default=SourceTrustState.DOCUMENT_VERIFIED)
    file_hash: Optional[str] = Field(default=None, description="SHA-256 checksum of original file")
    page_count: Optional[int] = None
    extracted_text_hash: Optional[str] = None
    acquired_at: Optional[str] = None
    verified_at: Optional[str] = None
    dataset_version: str = Field(default="v1.2.0")
    access_license_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class ClauseRecord(BaseModel):
    """Verified, traceable clause record extracted from an authoritative document."""
    clause_id: str = Field(..., description="Canonical clause ID, e.g. CL-IS-17526-4.2.1")
    standard_number: str = Field(..., description="Standard code, e.g. IS 17526:2021")
    clause_number: str = Field(..., description="Clause number e.g. 4.2.1 or 5.4")
    clause_title: str = Field(..., description="Clause title")
    parent_clause: Optional[str] = None
    text: str = Field(..., description="Exact textual content of the clause")
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    requirement_type: str = Field(default="PERFORMANCE", description="MATERIAL | PERFORMANCE | SAFETY | MARKING | SAMPLING")
    requirement_text: Optional[str] = None
    test_method: Optional[str] = None
    test_parameter: Optional[str] = None
    units: Optional[str] = None
    marking_requirement: Optional[str] = None
    evidence_type: str = Field(default="TEST_REPORT", description="TEST_REPORT | MATERIAL_CERTIFICATE | LABEL_PHOTO | SPECIFICATION")
    source_document_id: str = Field(..., description="Traceable parent document ID")
    source_hash: str = Field(..., description="SHA-256 hash of parent document")
    extraction_method: ExtractionMethodType = Field(default=ExtractionMethodType.TEXT_EXTRACTION)
    verification_status: SourceTrustState = Field(default=SourceTrustState.CLAUSE_INDEXED)

    model_config = ConfigDict(use_enum_values=True)


class RequirementRecord(BaseModel):
    """Granular, verifiable testable requirement within a clause."""
    requirement_id: str = Field(..., description="Unique requirement ID e.g. REQ-IS-17526-CL4.2.1-01")
    standard_number: str
    clause_id: str
    requirement_text: str
    requirement_type: str = Field(default="MANDATORY")
    parameter: Optional[str] = None
    operator: Optional[str] = None  # GTE | LTE | EQ | IN | CONTAINS
    expected_value: Optional[str] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    unit: Optional[str] = None
    test_method: Optional[str] = None
    required_evidence: str = Field(default="TEST_REPORT")
    applicability_condition: Optional[str] = None
    source_reference: str = ""
    verification_status: str = Field(default="VERIFIED")

    model_config = ConfigDict(use_enum_values=True)


class ProductEvidenceRecord(BaseModel):
    """Real or submitted product evidence.
    
    CRITICAL: Product evidence is stored separately from BIS normative knowledge.
    User claim is NEVER verified evidence.
    """
    evidence_id: str = Field(..., description="Unique evidence ID, e.g. EV-LAB-IS17526-001")
    product_id: str = Field(..., description="Associated product or assessment identifier")
    evidence_type: str = Field(..., description="MANUFACTURER_SPEC | BOM | MATERIAL_CERTIFICATE | TEST_REPORT | LAB_REPORT | PHOTO | DECLARATION")
    filename: str
    source: str = Field(..., description="Source authority or issuing lab e.g. NABL_ACCREDITED_LAB_01")
    provenance_type: str = Field(..., description="LAB_TEST | MANUFACTURER_SPEC | REGULATOR | USER_ASSERTION")
    extracted_facts: Dict[str, Any] = Field(default_factory=dict)
    document_hash: str = Field(..., description="SHA-256 checksum of submitted evidence file")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verification_status: str = Field(default="UNVERIFIED", description="VERIFIED | UNVERIFIED | REJECTED | REQUIRES_REVIEW")
    reviewer_status: ReviewState = Field(default=ReviewState.UNREVIEWED)
    linked_requirements: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class GroundTruthCase(BaseModel):
    """Formal ground-truth evaluation case for hallucination resistance & accuracy."""
    case_id: str = Field(..., description="Unique case identifier e.g. GT-IS17526-VACUUM-FLASK-001")
    case_type: CaseType = Field(..., description="POSITIVE | NEGATIVE | UNKNOWN | CONFLICT | OUT_OF_DOMAIN | INSUFFICIENT_INFORMATION")
    product_description: str
    product_dna: Dict[str, Any] = Field(default_factory=dict)
    expected_standard_candidates: List[str] = Field(default_factory=list)
    expected_applicability: Dict[str, Any] = Field(default_factory=dict)
    expected_clauses: List[str] = Field(default_factory=list)
    expected_requirements: List[str] = Field(default_factory=list)
    evidence_records: List[Dict[str, Any]] = Field(default_factory=list)
    expected_gap_classification: str = Field(default="SATISFIED", description="SATISFIED | POTENTIAL_GAP | ACTION_REQUIRED | UNKNOWN")
    expected_testing_roadmap: List[str] = Field(default_factory=list)
    expected_conflicts: List[str] = Field(default_factory=list)
    expected_unknown_fields: List[str] = Field(default_factory=list)
    expected_expert_review: bool = False
    source_references: List[str] = Field(default_factory=list)
    reviewer: str = Field(default="BIS Compliance Engineering Auditor")
    review_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    review_status: ReviewState = Field(default=ReviewState.APPROVED)
    dataset_version: str = Field(default="v1.2.0")
    golden_sih_demo: bool = False

    model_config = ConfigDict(use_enum_values=True)


class ModelDataContract(BaseModel):
    """Immutable data contract for any future auxiliary ML/DL model predictions."""
    model_name: str
    model_version: str
    prediction: Any
    confidence: float = Field(..., ge=0.0, le=1.0)
    input_hash: str = Field(..., description="SHA-256 of the input payload")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fallback_used: bool = False
    model_source: str = "PRETRAINED"

    model_config = ConfigDict(use_enum_values=True)


class ConfidenceModel(BaseModel):
    """Enforces strict conceptual separation between model confidence and regulatory authority."""
    ai_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_verification: bool = False
    regulatory_decision: str = "PENDING"
    explanation: str = ""

    def evaluate_verdict(self) -> str:
        """Cardinal invariant: Compliance result CANNOT be SATISFIED if source_verification is False or evidence is unverified."""
        if not self.source_verification:
            return "UNVERIFIED_SOURCE_BLOCK"
        if self.evidence_confidence < 0.90:
            return "REQUIRES_EVIDENCE_REVIEW"
        return "REGULATORY_EVALUATED"


class DatasetManifest(BaseModel):
    """Cryptographic manifest of the BIS dataset."""
    dataset_name: str = "BIS Compliance Compiler Knowledge Dataset"
    version: str = "v1.2.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    standards_count: int = 0
    qco_count: int = 0
    documents_count: int = 0
    verified_documents_count: int = 0
    clause_count: int = 0
    requirement_count: int = 0
    ground_truth_cases: int = 0
    approved_cases: int = 0
    acquisition_pending_count: int = 0
    sha256: str = ""
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)
