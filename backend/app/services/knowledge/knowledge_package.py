"""Layer 4: Segmented BIS Knowledge Base — Schemas & Data Models.

Implements the hierarchical Standard Knowledge Package structure from SIH PPT:

STANDARD
├── SCOPE
├── QCO / REGULATORY INSTRUMENT
├── PRODUCT MANUAL / STI
├── CLAUSES / SECTIONS
│   └── REQUIREMENTS
├── TEST METHODS
├── TEST PARAMETERS
├── MARKING / PACKAGING
└── REQUIRED EVIDENCE

Every knowledge item preserves full provenance chain:
standard_number, title, edition/year, document_type, QCO, issuing_authority,
scope, clause/section, requirement, test/method, parameter, unit, source_document,
page/location, verification_status, source_authority, knowledge_version,
content_hash, acquisition_status.

Critical Invariants:
NO VERIFIED SOURCE → NO REGULATORY CLAIM
UNKNOWN → UNKNOWN
MISSING CLAUSE TEXT → DO NOT INVENT (OFFICIAL_DOCUMENT_ACQUISITION_PENDING)
WRONG STANDARD → REJECT
UNVERIFIED KNOWLEDGE → NOT AUTHORITATIVE
LLM NEVER CREATES BIS KNOWLEDGE
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class KnowledgeVerificationStatus(str, Enum):
    """Verification state of a knowledge item."""
    VERIFIED = "VERIFIED"
    PENDING_ACQUISITION = "PENDING_ACQUISITION"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"


class KnowledgeAcquisitionStatus(str, Enum):
    """Document acquisition state."""
    FULL_TEXT_AVAILABLE = "FULL_TEXT_AVAILABLE"
    METADATA_ONLY = "METADATA_ONLY"
    OFFICIAL_DOCUMENT_ACQUISITION_PENDING = "OFFICIAL_DOCUMENT_ACQUISITION_PENDING"
    PARTIAL_TEXT = "PARTIAL_TEXT"


class KnowledgeDocumentType(str, Enum):
    """Type of BIS knowledge document."""
    INDIAN_STANDARD = "INDIAN_STANDARD"
    QCO_ORDER = "QCO_ORDER"
    PRODUCT_MANUAL = "PRODUCT_MANUAL"
    STI_DOCUMENT = "STI_DOCUMENT"
    GAZETTE_NOTIFICATION = "GAZETTE_NOTIFICATION"
    AMENDMENT = "AMENDMENT"
    TEST_REPORT_TEMPLATE = "TEST_REPORT_TEMPLATE"


class QCOInstrument(BaseModel):
    """Quality Control Order / Regulatory Instrument."""
    order_name: str
    notification_number: Optional[str] = None
    issuing_ministry: Optional[str] = None
    enactment_date: Optional[str] = None
    gazette_url: Optional[str] = None
    mandatory: bool = True
    verification_status: KnowledgeVerificationStatus = KnowledgeVerificationStatus.VERIFIED


class KnowledgeRequirement(BaseModel):
    """A single segmented requirement from a standard clause."""
    requirement_id: str
    clause_number: str
    clause_title: str
    section: Optional[str] = None
    requirement_text: str
    parameter: Optional[str] = None
    unit: Optional[str] = None
    limit_value: Optional[str] = None
    test_method: Optional[str] = None
    page_location: Optional[str] = None
    evidence_types: List[str] = Field(default_factory=lambda: ["LAB_REPORT"])
    verification_status: KnowledgeVerificationStatus = KnowledgeVerificationStatus.VERIFIED
    acquisition_status: KnowledgeAcquisitionStatus = KnowledgeAcquisitionStatus.FULL_TEXT_AVAILABLE


class KnowledgeTestParameter(BaseModel):
    """A testing parameter from a standard."""
    parameter_name: str
    test_method: Optional[str] = None
    limit_value: Optional[str] = None
    unit: Optional[str] = None
    clause_reference: Optional[str] = None
    source_standard: str


class KnowledgeItem(BaseModel):
    """Atomic knowledge item with full provenance chain."""
    item_id: str
    standard_number: str
    title: str
    edition_year: Optional[str] = None
    document_type: KnowledgeDocumentType = KnowledgeDocumentType.INDIAN_STANDARD
    qco_instrument: Optional[str] = None
    issuing_authority: Optional[str] = None
    scope: Optional[str] = None
    clause_section: Optional[str] = None
    requirement: Optional[str] = None
    test_method: Optional[str] = None
    parameter: Optional[str] = None
    unit: Optional[str] = None
    source_document: Optional[str] = None
    page_location: Optional[str] = None
    verification_status: KnowledgeVerificationStatus = KnowledgeVerificationStatus.VERIFIED
    source_authority: str = "Bureau of Indian Standards (Official Gazette)"
    knowledge_version: str = "v1.2.0-gazette-verified"
    content_hash: Optional[str] = None
    acquisition_status: KnowledgeAcquisitionStatus = KnowledgeAcquisitionStatus.METADATA_ONLY


class StandardKnowledgePackage(BaseModel):
    """Hierarchical knowledge package for a single Indian Standard.

    STANDARD
    ├── SCOPE
    ├── QCO / REGULATORY INSTRUMENT
    ├── PRODUCT MANUAL / STI
    ├── CLAUSES / SECTIONS → REQUIREMENTS
    ├── TEST METHODS
    ├── TEST PARAMETERS
    ├── MARKING / PACKAGING
    └── REQUIRED EVIDENCE
    """
    standard_number: str
    full_standard_code: str
    title: str
    short_title: Optional[str] = None
    product_category: str
    industry: Optional[str] = None
    scheme: Optional[str] = None
    certification_route: Optional[str] = None
    edition_year: Optional[str] = None
    publication_date: Optional[str] = None
    revision_date: Optional[str] = None
    status: str = "Active"

    # Hierarchy segments
    scope: Optional[str] = None
    qco_instrument: Optional[QCOInstrument] = None
    regulatory_order_name: Optional[str] = None
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    amendments: List[str] = Field(default_factory=list)

    # Segmented knowledge
    requirements: List[KnowledgeRequirement] = Field(default_factory=list)
    test_parameters: List[KnowledgeTestParameter] = Field(default_factory=list)
    marking_requirements: List[str] = Field(default_factory=list)
    required_evidence_types: List[str] = Field(default_factory=list)
    materials: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

    # Provenance
    source_url: Optional[str] = None
    document_url: Optional[str] = None
    source_type: Optional[str] = None
    source_date: Optional[str] = None
    retrieved_at: Optional[str] = None
    verification_status: KnowledgeVerificationStatus = KnowledgeVerificationStatus.VERIFIED
    verification_note: Optional[str] = None
    knowledge_version: str = "v1.2.0-gazette-verified"
    content_hash: Optional[str] = None
    acquisition_status: KnowledgeAcquisitionStatus = KnowledgeAcquisitionStatus.METADATA_ONLY

    # Legal source
    legal_source: Optional[Dict[str, Any]] = None


class KnowledgeRetrievalResult(BaseModel):
    """Provenance-rich retrieval result for a knowledge query."""
    standard_number: str
    clause_section: Optional[str] = None
    title: str
    content: str
    source: str
    document_type: KnowledgeDocumentType = KnowledgeDocumentType.INDIAN_STANDARD
    verification_status: KnowledgeVerificationStatus = KnowledgeVerificationStatus.VERIFIED
    exact_location: Optional[str] = None
    knowledge_version: str = "v1.2.0-gazette-verified"
    relevance_score: float = 0.0
    provenance: str = "Bureau of Indian Standards (Official Gazette)"


class KnowledgeCoverageDashboard(BaseModel):
    """Knowledge Coverage Dashboard statistics."""
    total_standards: int = 0
    total_qcos: int = 0
    standards_with_full_text: int = 0
    standards_with_metadata_only: int = 0
    pending_documents: int = 0
    requirements_indexed: int = 0
    searchable_chunks: int = 0
    last_ingestion: Optional[str] = None
    dataset_version: str = "v1.2.0-gazette-verified"
    integrity_hash: Optional[str] = None
    source_verification_status: str = "VERIFIED"
    categories_covered: int = 0
    amendments_tracked: int = 0
