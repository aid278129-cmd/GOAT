"""Unified Input Schema for Layer 1: Input Processing.

Normalizes all multi-modal inputs (PDF, Image/OCR, Voice, BOM, Manual Spec)
into a single, strictly validated schema before handoff to Layer 2 Product DNA.
Enforces zero-hallucination and provenance tracking:
USER TEXT != EVIDENCE != COMPLIANCE.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class InputMode(str, Enum):
    """Supported multi-modal input channels as defined in SIH Presentation."""
    PDF = "pdf"
    IMAGE_OCR = "image_ocr"
    VOICE = "voice"
    BOM = "bom"
    MANUAL = "manual"


class InputProvenanceType(str, Enum):
    """Immutable record of where an input parameter originated."""
    USER_CLAIM = "USER_CLAIM"
    DOCUMENT_EVIDENCE = "DOCUMENT_EVIDENCE"
    OCR = "OCR"
    VOICE_TRANSCRIPT = "VOICE_TRANSCRIPT"
    BOM = "BOM"
    MANUAL_INPUT = "MANUAL_INPUT"
    DERIVED_VALUE = "DERIVED_VALUE"


class FieldRequirementLevel(str, Enum):
    """Classification of technical attributes required by verified BIS standards."""
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    UNKNOWN = "UNKNOWN / INFORMATION REQUIRED"


class FieldReadinessStatus(str, Enum):
    """Readiness state of an individual attribute."""
    SATISFIED = "PRESENT"  # Present in input, NOT regulatory satisfaction
    MISSING = "MISSING"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


class TechnicalRequirementItem(BaseModel):
    """Specification of an expected attribute derived from verified BIS/QCO knowledge."""
    field_id: str
    field_name: str
    level: FieldRequirementLevel
    category: str  # Identification | Electrical | Physical | Safety | Sub-assembly
    description: str
    sample_value: Optional[str] = None
    unit: Optional[str] = None
    standard_reference: Optional[str] = None


class ReadinessFieldEvaluation(BaseModel):
    """Evaluation of an individual field's readiness."""
    field_id: str
    field_name: str
    level: FieldRequirementLevel
    status: FieldReadinessStatus
    extracted_value: Optional[Any] = None
    provenance: Optional[InputProvenanceType] = None
    action_required: Optional[str] = None


class ReadinessChecklist(BaseModel):
    """Document readiness and input completeness evaluation.
    
    CRITICAL: Readiness score reflects INPUT COMPLETENESS only and NEVER implies compliance.
    """
    total_required_fields: int
    present_required_fields: int
    missing_required_fields: int
    optional_fields_count: int
    present_optional_fields: int
    completeness_percentage: float = Field(..., ge=0.0, le=100.0)
    evaluations: List[ReadinessFieldEvaluation] = Field(default_factory=list)
    missing_critical_fields: List[str] = Field(default_factory=list)
    is_ready_for_dna_compilation: bool
    regulatory_disclaimer: str = (
        "Document readiness score evaluates input completeness only. "
        "Under the Zyntrix Evidence Gate, user inputs establish declared product claims (USER_CLAIM) "
        "and NEVER by themselves establish regulatory compliance or BIS ISI mark certification."
    )


class UnifiedAttributeItem(BaseModel):
    """Normalized attribute item with strict provenance."""
    name: str
    value: Union[str, int, float, bool, List[str]]
    unit: Optional[str] = None
    provenance_type: InputProvenanceType
    source_filename: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_snippet: Optional[str] = None


class BOMComponentItem(BaseModel):
    """Parsed sub-assembly component from BOM."""
    part_number: str
    name: str
    material: str
    specification: str
    quantity: str
    provenance_type: InputProvenanceType = InputProvenanceType.BOM


class DocumentMetadataItem(BaseModel):
    """Verified attached document metadata."""
    filename: str
    sha256_hash: str
    file_size_bytes: int
    mime_type: str
    is_verified_format: bool
    pages_count: Optional[int] = None
    provenance_type: InputProvenanceType


class ValidationIssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationIssue(BaseModel):
    code: str
    field: Optional[str] = None
    severity: ValidationIssueSeverity
    message: str
    actionable_remediation: str


class DocumentValidationResult(BaseModel):
    """Comprehensive pre-flight validation outcome."""
    is_valid: bool
    input_mode: InputMode
    filename: Optional[str] = None
    file_size_bytes: int = 0
    sha256_hash: Optional[str] = None
    issues: List[ValidationIssue] = Field(default_factory=list)
    detected_format: Optional[str] = None
    contains_placeholder_tokens: bool = False
    is_empty: bool = False
    is_duplicate: bool = False


class UnifiedInputPayload(BaseModel):
    """The authoritative unified schema produced by Layer 1 and consumed by Layer 2."""
    input_mode: InputMode
    product_name: str
    category: str
    description: str
    declared_attributes: List[UnifiedAttributeItem] = Field(default_factory=list)
    components_bom: List[BOMComponentItem] = Field(default_factory=list)
    attached_documents: List[DocumentMetadataItem] = Field(default_factory=list)
    readiness_checklist: ReadinessChecklist
    authoritative_mode: bool = False
