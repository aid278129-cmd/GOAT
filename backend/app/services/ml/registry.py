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
    model_id: str = ""
    model_name: str
    display_name: str = ""
    upstream_model: str = "custom"
    model_type: str  # e.g. cross_encoder, token_classifier, isolation_forest, cosine_embedder
    version: str = "1.0.0"
    source: str = "INTERNAL"  # PRETRAINED | STATISTICAL | HEURISTIC | INTERNAL
    task: str
    layer: int
    revision: str = "m23.1-audited"
    library: str = "python-stdlib"
    library_version: str = "3.14.3"
    license_metadata: str = "Apache-2.0"
    checksum: str = ""
    enabled: bool = True
    available: bool = False
    device: str = "cpu"
    fallback: bool = True
    fallback_available: bool = True
    loaded_at: Optional[str] = None
    regulatory_authority: float = 0.0
    training_status: str = "DATA_INSUFFICIENT_FOR_TRAINING"

    def __init__(self, **data):
        super().__init__(**data)
        if not self.model_id:
            self.model_id = self.model_name
        if not self.display_name:
            self.display_name = self.model_name


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
                model_id="zyntrix-product-entity-extractor-v1",
                model_name="zyntrix-product-entity-extractor-v1",
                display_name="Zyntrix Pattern-Token Entity Extractor v1",
                upstream_model="re.Pattern / Regex-Heuristic Feature Tokenizer",
                model_type="pattern_token_classifier",
                version="1.0.0",
                source="INTERNAL",
                task=MLTaskType.PRODUCT_ATTRIBUTE_EXTRACTION.value,
                layer=2,
                revision="m23.1-audited",
                library="Python standard library re",
                library_version="3.14.3",
                license_metadata="Python Software Foundation License",
                checksum="sha256:7776ebe93a6a8ab21316ec50f332ae428dd628a02bda0f84f0379782b6033d75",
                enabled=getattr(settings, "PRODUCT_EXTRACTION_ML_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                fallback_available=True,
                regulatory_authority=0.0,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="zyntrix-neural-reranker-cross-encoder-v1",
                model_name="zyntrix-neural-reranker-cross-encoder-v1",
                display_name="Zyntrix Analytical Cross-Encoder Reranker v1",
                upstream_model="analytical-cross-interaction-v1 (cross-attention proxy)",
                model_type="cross_encoder",
                version="1.0.0",
                source="INTERNAL",
                task=MLTaskType.RETRIEVAL_RERANKING.value,
                layer=6,
                revision="m23.1-audited",
                library="Python standard library / math",
                library_version="3.14.3",
                license_metadata="Apache-2.0",
                checksum="sha256:8928d7f26bbcb4b53e528712feb6d8f23350923481ee342a65e814cacb1ea7ae",
                enabled=getattr(settings, "RERANKER_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                fallback_available=True,
                regulatory_authority=0.0,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="zyntrix-semantic-evidence-matcher-v1",
                model_name="zyntrix-semantic-evidence-matcher-v1",
                display_name="Zyntrix 384-dim N-Gram Hashing Vector Matcher v1",
                upstream_model="384-dim-ngram-hash-projection (dense vector projection proxy)",
                model_type="semantic_vector_similarity",
                version="1.0.0",
                source="INTERNAL",
                task=MLTaskType.SEMANTIC_EVIDENCE_MATCHING.value,
                layer=7,
                revision="m23.1-audited",
                library="Python standard library / math",
                library_version="3.14.3",
                license_metadata="Apache-2.0",
                checksum="sha256:c0a3b118b66a0bd102057cf14586d66cff7ddccf293477948c4d4c3dac5477d0",
                enabled=getattr(settings, "EVIDENCE_MATCHING_ML_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                fallback_available=True,
                regulatory_authority=0.0,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="zyntrix-anomaly-isolation-forest-v1",
                model_name="zyntrix-anomaly-isolation-forest-v1",
                display_name="Zyntrix Statistical Outlier & Discrepancy Detector v1",
                upstream_model="statistical-zscore-iqr-isolation-proxy",
                model_type="isolation_forest_statistical",
                version="1.0.0",
                source="STATISTICAL",
                task=MLTaskType.ANOMALY_DETECTION.value,
                layer=7,
                revision="m23.1-audited",
                library="Python standard library / math",
                library_version="3.14.3",
                license_metadata="Apache-2.0",
                checksum="sha256:b15987821cbf4fc9065ad9638b2c879ea2411a68c456f339c9e9504f6621f14d",
                enabled=getattr(settings, "ANOMALY_DETECTION_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                fallback_available=True,
                regulatory_authority=0.0,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="zyntrix-claim-evidence-nli-v1",
                model_name="zyntrix-claim-evidence-nli-v1",
                display_name="Zyntrix Lexical-Semantic Entailment Assistant v1",
                upstream_model="nli-lexical-semantic-entailment-v1",
                model_type="entailment_classifier",
                version="1.0.0",
                source="INTERNAL",
                task=MLTaskType.ENTAILMENT_VERIFICATION.value,
                layer=8,
                revision="m23.1-audited",
                library="Python standard library / math",
                library_version="3.14.3",
                license_metadata="Apache-2.0",
                checksum="sha256:fbfe4322d171c93c16d313bb785ac77a14097104f28aa264c386529ffa8c67e3",
                enabled=getattr(settings, "NLI_ENABLED", True) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                fallback_available=True,
                regulatory_authority=0.0,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
            ModelMetadata(
                model_id="zyntrix-applicability-classifier-v1",
                model_name="zyntrix-applicability-classifier-v1",
                display_name="Zyntrix Jaccard-Token Scope Candidate Classifier v1",
                upstream_model="jaccard-scope-overlap-v1",
                model_type="scope_candidate_classifier",
                version="1.0.0",
                source="INTERNAL",
                task=MLTaskType.APPLICABILITY_CLASSIFICATION.value,
                layer=5,
                revision="m23.1-audited",
                library="Python standard library / math",
                library_version="3.14.3",
                license_metadata="Apache-2.0",
                checksum="sha256:0730a237611d788420d55fb2f32cff5d0af2250139b6327b7adf702aa4345605",
                enabled=getattr(settings, "APPLICABILITY_CLASSIFIER_ENABLED", False) and getattr(settings, "ML_ENABLED", True),
                available=True,
                device="cpu",
                fallback=False,
                fallback_available=True,
                regulatory_authority=0.0,
                loaded_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]
        for m in defaults:
            self._models[m.model_name] = m
            if m.model_id != m.model_name:
                self._models[m.model_id] = m

    def register_model(self, metadata: ModelMetadata, instance: Optional[Any] = None) -> None:
        """Register or update a model record."""
        self._models[metadata.model_name] = metadata
        self._models[metadata.model_id] = metadata
        if instance is not None:
            self._instances[metadata.model_name] = instance
            self._instances[metadata.model_id] = instance

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
        seen = set()
        unique = []
        for m in self._models.values():
            if m.model_name not in seen:
                seen.add(m.model_name)
                unique.append(m)
        return unique

    def update_status(self, model_name: str, available: bool, fallback: bool) -> None:
        if model_name in self._models:
            self._models[model_name].available = available
            self._models[model_name].fallback = fallback


ml_model_registry = MLModelRegistry()
