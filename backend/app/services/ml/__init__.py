"""M23 ML/DL Intelligence Layer Package.

Provides CPU-first auxiliary intelligence components:
- Extraction (Layer 2)
- Retrieval Reranking (Layers 4 & 6)
- Evidence Matching (Layer 7)
- Anomaly & Conflict Detection (Layer 7)
- Claim-Evidence Entailment Assistance (Layer 8)
- Advisory Applicability Classifier (Layer 5)
- Centralized Model Registry and Health Telemetry
"""

from backend.app.services.ml.contracts import (
    MLModelStatus,
    MLTaskType,
    MLPredictionContract,
    CandidateFact,
    EntailmentDecision,
    AnomalyReport,
)
from backend.app.services.ml.registry import ml_model_registry, ModelMetadata
from backend.app.services.ml.health import get_ml_system_health, ml_telemetry

__all__ = [
    "MLModelStatus",
    "MLTaskType",
    "MLPredictionContract",
    "CandidateFact",
    "EntailmentDecision",
    "AnomalyReport",
    "ml_model_registry",
    "ModelMetadata",
    "get_ml_system_health",
    "ml_telemetry",
]
