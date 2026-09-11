from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Citation Guard verification outcome."""

    SUPPORTED = "SUPPORTED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceItem(BaseModel):
    """Granular piece of evidence extracted from documents or test reports."""

    id: Optional[str] = None
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    source_text: str = Field(..., min_length=1)
    extracted_value: Optional[str] = None
    validation_status: ValidationStatus = ValidationStatus.UNVERIFIED
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CitationGuardCheckRequest(BaseModel):
    """Request payload sent to Citation Guard trust layer."""

    claim: str
    target_standard: str
    target_clause: str
    extracted_evidence_text: str


class CitationGuardCheckResponse(BaseModel):
    """Result of Citation Guard verification."""

    is_valid: bool
    status: ValidationStatus
    reasoning: str
    matched_clause_text: Optional[str] = None
    confidence: float
