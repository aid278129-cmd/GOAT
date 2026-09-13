"""Pydantic Data Models for Official BIS Source Acquisition, Manifests, and Verification.

Enforces:
1. Strict typed enumerations for acquisition states and source types.
2. Canonical SourceManifest specification with cryptographic SHA-256 hashes.
3. Verification tracking separating 'ACQUIRED' from 'VERIFIED'.
4. Structured snapshot manifests and machine-readable corpus integrity reports.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class AcquisitionState(str, Enum):
    """Explicit lifecycle states for source acquisition."""
    DISCOVERED = "DISCOVERED"
    ACQUIRED = "ACQUIRED"
    HASHED = "HASHED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    CONTENT_VERIFIED = "CONTENT_VERIFIED"
    VERIFIED = "VERIFIED"  # Backward-compatible aggregate state
    INDEXED = "INDEXED"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"
    REJECTED = "REJECTED"
    INVALID_SOURCE = "INVALID_SOURCE"


class SourceDomainClassification(str, Enum):
    """Source domain authority classification."""
    OFFICIAL_BIS = "OFFICIAL_BIS"
    OFFICIAL_GOVERNMENT = "OFFICIAL_GOVERNMENT"
    AUTHORIZED_EXTERNAL = "AUTHORIZED_EXTERNAL"
    UNVERIFIED_EXTERNAL = "UNVERIFIED_EXTERNAL"
    UNKNOWN = "UNKNOWN"


class LicensingProvenanceStatus(str, Enum):
    """Legal, access, and acquisition compliance status."""
    OFFICIAL_OPEN_ACCESS = "OFFICIAL_OPEN_ACCESS"
    COMMERCIAL_ACCESS_RESTRICTED = "COMMERCIAL_ACCESS_RESTRICTED"
    ACQUISITION_PROVENANCE_UNVERIFIED = "ACQUISITION_PROVENANCE_UNVERIFIED"
    LICENSED_AUTHORIZED = "LICENSED_AUTHORIZED"


class SourceType(str, Enum):
    """Explicit source classification types."""
    BIS_STANDARD = "BIS_STANDARD"
    BIS_PRODUCT_MANUAL = "BIS_PRODUCT_MANUAL"
    BIS_SIT = "BIS_SIT"
    BIS_PRODUCT_GUIDELINE = "BIS_PRODUCT_GUIDELINE"
    BIS_QCO = "BIS_QCO"
    BIS_GAZETTE = "BIS_GAZETTE"
    BIS_AMENDMENT = "BIS_AMENDMENT"
    BIS_REVISION = "BIS_REVISION"
    BIS_SCHEME = "BIS_SCHEME"
    BIS_LABORATORY = "BIS_LABORATORY"
    BIS_LICENCE = "BIS_LICENCE"
    BIS_CATALOG = "BIS_CATALOG"
    DEVELOPMENT_FIXTURE = "DEVELOPMENT_FIXTURE"


class SourceManifest(BaseModel):
    """Cryptographic provenance manifest for an acquired BIS regulatory resource."""
    source_id: str = Field(..., description="Unique source identifier, e.g. BIS-STD-IS17526-2021 or BIS-QCO-DPIIT-2023")
    source_type: SourceType = Field(..., description="Classified source type")
    authority: str = Field(default="Bureau of Indian Standards", description="Official issuing authority")
    source_url: str = Field(..., description="Original retrieved URL or source path")
    canonical_url: str = Field(..., description="Normalized canonical BIS URL")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: Optional[str] = Field(default=None, description="Official publication date or UNKNOWN")
    effective_date: Optional[str] = Field(default=None, description="Legal effective/implementation date or UNKNOWN")
    standard_number: Optional[str] = Field(default=None, description="Associated Indian Standard code or UNKNOWN")
    title: str = Field(..., description="Official document or standard title")
    revision: Optional[str] = Field(default=None, description="Edition or revision details or UNKNOWN")
    document_status: str = Field(default="ACTIVE", description="ACTIVE | WITHDRAWN | SUPERSEDED | UNKNOWN")
    acquisition_status: AcquisitionState = Field(default=AcquisitionState.DISCOVERED)
    verification_status: AcquisitionState = Field(default=AcquisitionState.DISCOVERED)
    domain_classification: SourceDomainClassification = Field(default=SourceDomainClassification.OFFICIAL_BIS)
    licensing_provenance: LicensingProvenanceStatus = Field(default=LicensingProvenanceStatus.OFFICIAL_OPEN_ACCESS)
    is_administrative_document: bool = Field(default=False, description="True if administrative report/statement rather than technical standard")
    file_path: Optional[str] = Field(default=None, description="Relative path to stored original file")
    mime_type: Optional[str] = Field(default=None, description="MIME type of stored document")
    file_size: int = Field(default=0, description="Exact size in bytes")
    sha256: str = Field(default="", description="Cryptographic SHA-256 hash of original file")
    parent_source_id: Optional[str] = Field(default=None, description="ID of parent standard or parent document")
    related_standard_numbers: List[str] = Field(default_factory=list, description="Cross-referenced standard numbers")
    related_qco: List[str] = Field(default_factory=list, description="Associated QCO notification identifiers")
    related_amendments: List[str] = Field(default_factory=list, description="Associated amendment identifiers")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Audit and retrieval provenance details")
    notes: Optional[str] = Field(default=None, description="Additional context or limitation notes")
    derived_text_path: Optional[str] = Field(default=None, description="Relative path to extracted derived text")
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict, description="Extraction engine and version info")

    model_config = ConfigDict(use_enum_values=True)


class DiscoveredResource(BaseModel):
    """Resource discovered by the official crawler."""
    url: str
    title: str
    source_type: SourceType
    category: str
    standard_number: Optional[str] = None
    discovered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_url: Optional[str] = None
    is_downloadable: bool = True
    estimated_size: Optional[int] = None
    notes: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class CorpusSnapshotManifest(BaseModel):
    """Manifest for an immutable, reproducible corpus snapshot."""
    snapshot_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_count: int = 0
    acquired_count: int = 0
    verified_count: int = 0
    indexed_count: int = 0
    pending_count: int = 0
    standard_count: int = 0
    qco_count: int = 0
    amendment_count: int = 0
    revision_count: int = 0
    manifest_sha256: str = ""
    category_counts: Dict[str, int] = Field(default_factory=dict)
    sources: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class CorpusIntegrityReport(BaseModel):
    """Machine-readable corpus statistics and integrity report."""
    catalog_records: int = 0
    sources_discovered: int = 0
    sources_acquired: int = 0
    sources_verified: int = 0
    standards_verified: int = 0
    qco_verified: int = 0
    amendments_verified: int = 0
    revisions_verified: int = 0
    normative_references_verified: int = 0
    clause_indexed: int = 0
    acquisition_pending: int = 0
    invalid_sources: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    categories: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    integrity_status: str = "VALID"

    model_config = ConfigDict(use_enum_values=True)


class VerificationIssue(BaseModel):
    """A specific verification or integrity check issue."""
    source_id: str
    field: str
    message: str
    severity: str = "ERROR"  # ERROR | WARNING


class VerificationReport(BaseModel):
    """Result of running verification across the BIS corpus."""
    verified: bool
    total_checked: int = 0
    passed_count: int = 0
    failed_count: int = 0
    issues: List[VerificationIssue] = Field(default_factory=list)
    summary: str = ""

    model_config = ConfigDict(use_enum_values=True)
