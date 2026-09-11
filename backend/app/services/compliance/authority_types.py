"""Explicit Authority Types & Provenance Enums (Milestone M24.4).

Cardinal Principle:
"The AI system can reason about evidence.
It cannot become the source of compliance authority."

Authority Levels:
UNTRUSTED_INPUT -> AI_DERIVED -> CANDIDATE -> VERIFIED_EVIDENCE -> DETERMINISTIC_EVALUATION -> AUTHORITATIVE_RESULT
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class AuthorityLevel(str, Enum):
    """Hierarchical trust classification for data and conclusions."""
    UNTRUSTED_INPUT = "UNTRUSTED_INPUT"         # User queries, PDF/OCR text, voice transcriptions, BOM strings
    AI_DERIVED = "AI_DERIVED"                   # LLM natural-language output, agent reasoning, AI suggestions
    CANDIDATE = "CANDIDATE"                     # Retrieved standard candidates, clause matches, taxonomy guesses
    VERIFIED_EVIDENCE = "VERIFIED_EVIDENCE"     # Empirical test certificates verified by Layer 8 provenance checks
    DETERMINISTIC_EVALUATION = "DETERMINISTIC_EVALUATION" # Mathematical/rule calculations from Layers 5 & 7
    AUTHORITATIVE_RESULT = "AUTHORITATIVE_RESULT"         # Signed Compliance Passport records from Layer 9


class AuthoritySource(str, Enum):
    """Identifies the originating source of a statement, claim, or calculation."""
    # Deterministic Compliance Authorities (100% Authority within their respective layers)
    LAYER_5_APPLICABILITY_ENGINE = "LAYER_5_APPLICABILITY_ENGINE"
    LAYER_7_COMPLIANCE_GAP_ENGINE = "LAYER_7_COMPLIANCE_GAP_ENGINE"
    LAYER_8_SOURCE_VALIDATOR = "LAYER_8_SOURCE_VALIDATOR"
    LAYER_9_PASSPORT_COMPILER = "LAYER_9_PASSPORT_COMPILER"

    # Non-Authoritative Sources (0.0% Compliance Authority)
    LLM = "LLM"
    LANGCHAIN = "LANGCHAIN"
    LANGGRAPH_AI_NODE = "LANGGRAPH_AI_NODE"
    CONTROLLED_TOOL = "CONTROLLED_TOOL"
    USER_INPUT = "USER_INPUT"
    DOCUMENT_OCR = "DOCUMENT_OCR"
    VOICE_TRANSCRIPTION = "VOICE_TRANSCRIPTION"
    BOM_PARSER = "BOM_PARSER"
    CLIENT_API = "CLIENT_API"


class DecisionType(str, Enum):
    """Categorization of compliance-related determinations."""
    APPLICABILITY = "APPLICABILITY"               # Layer 5
    GAP_EVALUATION = "GAP_EVALUATION"             # Layer 7
    EVIDENCE_VERIFICATION = "EVIDENCE_VERIFICATION" # Layer 8
    PASSPORT_CERTIFICATION = "PASSPORT_CERTIFICATION" # Layer 9


class AuthorityFirewallViolation(ValueError):
    """Raised when an unauthorized entity attempts to assert or modify compliance status."""
    pass


class AuthorityTransitionError(ValueError):
    """Raised when an illegal trust transition is attempted (e.g. AI_DERIVED -> AUTHORITATIVE_RESULT)."""
    pass


class AuthoritativeRecord(BaseModel):
    """Tamper-evident record of a deterministic compliance determination."""
    decision_type: DecisionType
    decision_value: str
    authority_source: AuthoritySource
    source_layer: int = Field(..., ge=5, le=9)
    deterministic: bool = True
    correlation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("deterministic")
    @classmethod
    def enforce_deterministic(cls, v: bool) -> bool:
        if not v:
            raise AuthorityFirewallViolation("Authoritative records must be deterministic=True.")
        return v

    @field_validator("authority_source")
    @classmethod
    def validate_source_layer(cls, source: AuthoritySource, info) -> AuthoritySource:
        layer = info.data.get("source_layer")
        expected_sources = {
            5: AuthoritySource.LAYER_5_APPLICABILITY_ENGINE,
            7: AuthoritySource.LAYER_7_COMPLIANCE_GAP_ENGINE,
            8: AuthoritySource.LAYER_8_SOURCE_VALIDATOR,
            9: AuthoritySource.LAYER_9_PASSPORT_COMPILER,
        }
        if layer in expected_sources and source != expected_sources[layer]:
            raise AuthorityFirewallViolation(
                f"Source layer mismatch: Layer {layer} cannot originate from source {source.value}."
            )
        return source
