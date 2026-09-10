"""M23 ML/DL Common Prediction Contracts, Schemas, and Provenance Types.

CARDINAL INVARIANTS:
1. regulatory_authority MUST ALWAYS EQUAL 0.0 (enforced by schema validator).
2. AI confidence != Evidence confidence != Source verification != Regulatory decision.
3. Every ML output must include input_hash, model_name, model_version, and timestamp.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
import hashlib
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class MLModelStatus(str, Enum):
    MODEL_AVAILABLE = "MODEL_AVAILABLE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    FALLBACK_ACTIVE = "FALLBACK_ACTIVE"


class MLTaskType(str, Enum):
    PRODUCT_ATTRIBUTE_EXTRACTION = "product_attribute_extraction"
    RETRIEVAL_RERANKING = "retrieval_reranking"
    SEMANTIC_EVIDENCE_MATCHING = "semantic_evidence_matching"
    ANOMALY_DETECTION = "anomaly_detection"
    ENTAILMENT_VERIFICATION = "entailment_verification"
    APPLICABILITY_CLASSIFICATION = "applicability_classification"


class MLPredictionContract(BaseModel):
    """Universal Output Contract for all M23 ML/DL Model Predictions."""
    model_name: str
    model_version: str
    task: str
    prediction: Any
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    input_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fallback_used: bool = False
    regulatory_authority: float = Field(default=0.0, ge=0.0, le=0.0)

    @field_validator("regulatory_authority")
    @classmethod
    def enforce_zero_regulatory_authority(cls, v: float) -> float:
        if v != 0.0:
            raise ValueError("Cardinal Invariant Violation: ML/DL regulatory authority must strictly equal 0.0")
        return 0.0

    @classmethod
    def compute_input_hash(cls, raw_input: Union[str, Dict[str, Any], List[Any]]) -> str:
        """Compute deterministic SHA-256 digest of input data."""
        if isinstance(raw_input, str):
            payload = raw_input.strip().encode("utf-8")
        else:
            import json
            payload = json.dumps(raw_input, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class CandidateFact(BaseModel):
    """Candidate fact produced by Layer 2 ML extraction before validation."""
    field: str
    value: Any
    raw_value: str
    unit: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    model_name: str
    model_version: str
    source_span: Optional[str] = None
    provenance: str = "ML_CANDIDATE_EXTRACTION"
    verification_state: str = "UNVERIFIED_CANDIDATE"
    regulatory_authority: float = 0.0

    @field_validator("regulatory_authority")
    @classmethod
    def check_zero_authority(cls, v: float) -> float:
        if v != 0.0:
            raise ValueError("Candidate facts cannot carry regulatory authority.")
        return 0.0


class EntailmentDecision(str, Enum):
    ENTAILMENT = "ENTAILMENT"
    CONTRADICTION = "CONTRADICTION"
    UNKNOWN = "UNKNOWN"
    NLI_UNAVAILABLE = "NLI_UNAVAILABLE"


class AnomalyReport(BaseModel):
    """Anomaly and contradiction detection result for multi-source evidence."""
    has_conflict: bool
    conflict_type: Optional[str] = None  # NUMERIC_MISMATCH, MATERIAL_CONTRADICTION, CATEGORICAL_MISMATCH
    fields_involved: List[str] = Field(default_factory=list)
    observed_values: Dict[str, Any] = Field(default_factory=dict)
    normalized_values: Dict[str, Any] = Field(default_factory=dict)
    anomaly_score: float = 0.0
    action_required: str = "NONE"  # EXPERT_REVIEW_REQUIRED, VERIFICATION_REQUIRED, NONE
    explanation: str = ""
    fallback_used: bool = False
