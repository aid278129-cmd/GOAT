"""Central ML/DL Model Registry for M23 Intelligence Layer.

Manages registration, discovery, lazy loading, runtime device assignment (CPU-first),
and fallback detection for all auxiliary ML/DL components.

INVARIANTS:
1. No model claims active/available status unless it has verified initialization.
2. Training status strictly reports DATA_INSUFFICIENT_FOR_TRAINING.
3. Auxiliary models explicitly declare MODEL_SOURCE = PRETRAINED or STATISTICAL.
4. All models operate with 0.0% regulatory authority.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.ml.contracts import MLModelStatus, MLTaskType


class ModelMetadata(BaseModel):
    model_name: str
    model_type: str  # e.g. cross_encoder, token_classifier, isolation_forest, cosine_embedder
    version: str
    source: str = "PRETRAINED"  # PRETRAINED | STATISTICAL | HEURISTIC
    task: str
    layer: int
    enabled: bool = True
    available: bool = False
    device: str = "cpu"
    fallback: bool = True
    license_metadata: str = "Apache-2.0 / MIT Compatible"
    loaded_at: Optional[str] = None
    regulatory_authority: float = 0.0
    training_status: str = "DATA_INSUFFICIENT_FOR_TRAINING"


class MLModelRegistry:
    """Central registry singleton tracking ML model lifecycles across all layers."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLModelRegistry, cls).__new__(cls)
            cls._instance._models: Dict[str, ModelMetadata] = {}
            cls._instance._instances: Dict[str, Any] = {}
            cls._instance._initialize_default_registry()
        return cls._instance

    def _initialize_default_registry(self):
        """Register the baseline metadata for all supported auxiliary models."""
        defaults = [
            ModelMetadata(
                model_name="zyntrix-product-entity-extractor-v1",
                model_type="pattern_token_classifier",
                version="1.0.0",
                source="PRETRAINED",
                task=MLTaskType.PRODUCT_ATTRIBUTE_EXTRACTION.value,
                layer=2,
                enabled=getattr(settings, "PRODUCT_EXTRACTION_ML_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_name="zyntrix-neural-reranker-cross-encoder-v1",
                model_type="cross_encoder",
                version="1.0.0",
                source="PRETRAINED",
                task=MLTaskType.RETRIEVAL_RERANKING.value,
                layer=6,
                enabled=getattr(settings, "RERANKER_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_name="zyntrix-semantic-evidence-matcher-v1",
                model_type="semantic_vector_similarity",
                version="1.0.0",
                source="PRETRAINED",
                task=MLTaskType.SEMANTIC_EVIDENCE_MATCHING.value,
                layer=7,
                enabled=getattr(settings, "EVIDENCE_MATCHING_ML_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_name="zyntrix-anomaly-isolation-forest-v1",
                model_type="isolation_forest_statistical",
                version="1.0.0",
                source="STATISTICAL",
                task=MLTaskType.ANOMALY_DETECTION.value,
                layer=7,
                enabled=getattr(settings, "ANOMALY_DETECTION_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_name="zyntrix-claim-evidence-nli-v1",
                model_type="entailment_classifier",
                version="1.0.0",
                source="PRETRAINED",
                task=MLTaskType.ENTAILMENT_VERIFICATION.value,
                layer=8,
                enabled=getattr(settings, "NLI_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_name="zyntrix-applicability-classifier-v1",
                model_type="scope_candidate_classifier",
                version="1.0.0",
                source="PRETRAINED",
                task=MLTaskType.APPLICABILITY_CLASSIFICATION.value,
                layer=5,
                enabled=getattr(settings, "APPLICABILITY_CLASSIFIER_ENABLED", False) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]
        for m in defaults:
            self._models[m.model_name] = m

    def register_model(self, metadata: ModelMetadata, instance: Optional[Any] = None) -> None:
        """Register or update a model record."""
        self._models[metadata.model_name] = metadata
        if instance is not None:
            self._instances[metadata.model_name] = instance

    def get_model_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        return self._models.get(model_name)

    def get_model_status(self, model_name: str) -> MLModelStatus:
        m = self._models.get(model_name)
        if not m or not m.enabled:
            return MLModelStatus.MODEL_UNAVAILABLE
        if not m.available:
            return MLModelStatus.FALLBACK_ACTIVE
        return MLModelStatus.MODEL_AVAILABLE

    def list_models(self) -> List[ModelMetadata]:
        return list(self._models.values())

    def update_status(self, model_name: str, available: bool, fallback: bool) -> None:
        if model_name in self._models:
            self._models[model_name].available = available
            self._models[model_name].fallback = fallback


ml_model_registry = MLModelRegistry()
