"""Product DNA Schemas for Layer 2: Product Fact Extraction & Clarification Engine.

Strictly follows SIH Presentation Layer 2 specifications:
RAW MULTI-MODAL INPUT -> PRODUCT FACT EXTRACTION -> FACT NORMALIZATION
-> PROVENANCE + CONFIDENCE -> MISSING/CONFLICTING FACT DETECTION
-> CLARIFICATION QUEUE -> USER CONFIRMATION -> FINAL PRODUCT DNA -> LAYER 3 AI ORCHESTRATOR.

Enforces cardinal invariants:
USER_TEXT != PRODUCT FACT != EVIDENCE != COMPLIANCE
NO SUFFICIENT PRODUCT INFORMATION -> ASK / UNKNOWN
NO VERIFIED EVIDENCE -> NO SATISFIED
LLM COMPLIANCE AUTHORITY = 0%
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class FactProvenanceType(str, Enum):
    """The 8 explicit provenance classifications for Layer 2 Product Facts."""
    VERIFIED_DOCUMENT_FACT = "VERIFIED_DOCUMENT_FACT"
    USER_CLAIM = "USER_CLAIM"
    USER_CLARIFICATION = "USER_CLARIFICATION"
    OCR_EXTRACTED = "OCR_EXTRACTED"
    VOICE_TRANSCRIPT = "VOICE_TRANSCRIPT"
    BOM_FACT = "BOM_FACT"
    DERIVED_VALUE = "DERIVED_VALUE"
    UNKNOWN = "UNKNOWN"


class FactVerificationState(str, Enum):
    """Fact validation state in Layer 2."""
    CONFIRMED = "CONFIRMED"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    CONFLICTING = "CONFLICTING"
    USER_CORRECTED = "USER_CORRECTED"


class FactAuditEntry(BaseModel):
    """Audit record capturing changes made to a product fact."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    old_value: Any
    new_value: Any
    reason: str
    updated_by: str = "user"


class ProductFact(BaseModel):
    """A deterministic, typed product fact with complete provenance and audit history."""
    fact_id: str = Field(..., description="Unique fact identifier e.g. FACT-VOLTAGE-01")
    field_name: str = Field(..., description="Canonical parameter name e.g. rated_voltage")
    display_name: str = Field(..., description="Human-readable title e.g. Rated Supply Voltage")
    value: Union[str, int, float, bool, List[str]]
    raw_value: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None  # Document name, BOM row, or manual input
    provenance: FactProvenanceType = FactProvenanceType.USER_CLAIM
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    verification_state: FactVerificationState = FactVerificationState.NEEDS_CONFIRMATION
    derivation_rule: Optional[str] = None  # Formula/rule if DERIVED_VALUE
    source_fact_ids: List[str] = Field(default_factory=list)  # Supporting facts if DERIVED_VALUE
    conflict_notes: Optional[str] = None
    history: List[FactAuditEntry] = Field(default_factory=list)

    def is_eligible_for_compliance_evidence(self) -> bool:
        """USER_CLAIM, USER_CLARIFICATION, OCR, VOICE, and BOM can NEVER by themselves constitute compliance evidence."""
        return self.provenance == FactProvenanceType.VERIFIED_DOCUMENT_FACT


class ClarificationRequirement(BaseModel):
    """Generated clarification request when an essential product discriminator is missing."""
    requirement_id: str = Field(default_factory=lambda: f"REQ-{datetime.utcnow().strftime('%M%S%f')[:8]}")
    attribute_name: str
    display_question: Optional[str] = None
    reason: str
    options: Optional[List[str]] = None
    criticality: str = "HIGH"  # HIGH | MEDIUM | LOW
    suggested_field_id: Optional[str] = None



class ProductDNAVersionRecord(BaseModel):
    """Immutable versioned snapshot of Product DNA."""
    dna_id: str
    version: str = "v1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    product_name: str
    category: str
    sub_category: Optional[str] = None
    intended_use: Optional[str] = None
    facts: List[ProductFact] = Field(default_factory=list)
    clarification_queue: List[ClarificationRequirement] = Field(default_factory=list)
    fact_completeness_percentage: float = Field(..., ge=0.0, le=100.0)
    is_ready_for_orchestrator: bool = False
    disclaimer: str = (
        "Fact completeness score measures product specification completeness only. "
        "Layer 2 establishes declared product facts and NEVER outputs regulatory compliance decisions (SATISFIED/COMPLIANT)."
    )


# Backward-compatible models for existing services
class ProvenanceClassification(str, Enum):
    USER_CLAIM = "USER_CLAIM"
    USER_CLARIFICATION = "USER_CLARIFICATION"
    DOCUMENT_EVIDENCE = "DOCUMENT_EVIDENCE"
    LAB_EVIDENCE = "LAB_EVIDENCE"
    OFFICIAL_SOURCE = "OFFICIAL_SOURCE"
    DERIVED_VALUE = "DERIVED_VALUE"


class AttributeProvenance(BaseModel):
    provenance_type: ProvenanceClassification = ProvenanceClassification.USER_CLAIM
    source_document: Optional[str] = None
    page: Optional[int] = None
    source_text: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str = "manual"

    def is_eligible_for_compliance_evidence(self) -> bool:
        return self.provenance_type in (
            ProvenanceClassification.DOCUMENT_EVIDENCE,
            ProvenanceClassification.LAB_EVIDENCE,
            ProvenanceClassification.OFFICIAL_SOURCE,
        )


class DNAAttribute(BaseModel):
    name: str
    value: Union[str, int, float, bool, List[str]]
    data_type: str = "string"
    unit: Optional[str] = None
    provenance: Optional[AttributeProvenance] = None


class ProductDNACore(BaseModel):
    product_name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    sub_category: Optional[str] = None
    intended_use: Optional[str] = None
    materials: List[str] = Field(default_factory=list)
    electrical: bool = False
    insulated: bool = False
    attributes: List[DNAAttribute] = Field(default_factory=list)
    pending_clarifications: List[ClarificationRequirement] = Field(default_factory=list)
    version: str = "v1.0"
    facts: List[ProductFact] = Field(default_factory=list)


class ProductDNACreate(ProductDNACore):
    pass


class ProductDNAResponse(ProductDNACore):
    id: str
    model_config = ConfigDict(from_attributes=True)
