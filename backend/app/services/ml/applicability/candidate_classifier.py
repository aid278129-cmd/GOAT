"""M23 ML Component 6: Advisory Applicability Candidate Classifier.

Layer: Layer 5 (Applicability Engine)
Model Name: zyntrix-applicability-classifier-v1
Model Type: Scope Candidate Semantic Classifier
Device: CPU

INVARIANTS:
1. Purely advisory candidate suggestions.
2. The classifier can NEVER declare final applicability.
3. Layer 5 deterministic scope and QCO evaluation remains 100% authoritative.
4. 0% regulatory authority.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.ml.contracts import (
    MLPredictionContract,
    MLTaskType,
)
from backend.app.services.ml.registry import ml_model_registry
from backend.app.services.ml.health import ml_telemetry
from backend.app.services.ingestion.embedder import default_embedding_provider, cosine_similarity

MODEL_NAME = "zyntrix-applicability-classifier-v1"
MODEL_VERSION = "1.0.0"

KNOWN_STANDARD_PROFILES = [
    ("IS 17526:2021", "Domestic Stainless Steel Vacuum Flask Bottle insulated thermal beverage container food grade", "Drinkware & Food Contact Containers"),
    ("IS 302 (Part 2/Sec 15):2009", "Electric kettle liquid boiling appliance household domestic electrical heating", "Electrical & Domestic Appliances"),
    ("IS 302 (Part 2/Sec 201):2008", "Electric immersion water heater liquid heating domestic heating element", "Kitchen & Domestic Appliances"),
    ("IS 4151:2020", "Protective helmets for two wheeler motorcycle rider vehicular road safety", "Protective Equipment & Helmets"),
    ("IS 9873 (Part 1):2019", "Safety of toys mechanical physical properties children non-electric play", "Toys & Children Products"),
    ("IS 16046 (Part 2):2018", "Secondary cells batteries portable power bank lithium ion rechargeable", "Electronics & IT (CRS)"),
    ("IS 14543:2024", "Packaged drinking water other than packaged natural mineral water potable", "Food & Water"),
    ("IS 1786:2008", "High strength deformed steel bars and wires for concrete reinforcement TMT construction", "Civil, Steel & Cement"),
]


class ApplicabilityCandidate(BaseModel):
    standard_number: str
    confidence: float
    category: str
    is_authoritative: bool = False  # Cardinal Invariant: ALWAYS FALSE
    advisory_only: bool = True


class ApplicabilityCandidateClassifier:
    """Predicts candidate standard numbers from Product DNA attributes."""

    def __init__(self):
        self.model_name = MODEL_NAME
        self.model_version = MODEL_VERSION

    def is_available(self) -> bool:
        return (
            getattr(settings, "ML_ENABLED", True)
            and getattr(settings, "APPLICABILITY_CLASSIFIER_ENABLED", False)
        )

    def predict_candidate_standards(
        self,
        product_name: str,
        category: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> Tuple[List[ApplicabilityCandidate], MLPredictionContract]:
        """Suggest potential standard candidates for Layer 5 deterministic evaluation."""
        t0 = time.time()
        query_text = f"{product_name} {category or ''} " + " ".join(f"{k} {v}" for k, v in (attributes or {}).items())
        input_hash = MLPredictionContract.compute_input_hash(query_text)

        if not self.is_available():
            latency = (time.time() - t0) * 1000.0
            ml_telemetry.record_inference(self.model_name, latency, fallback_used=True)
            contract = MLPredictionContract(
                model_name=self.model_name,
                model_version=self.model_version,
                task=MLTaskType.APPLICABILITY_CLASSIFICATION.value,
                prediction=[],
                confidence=0.0,
                input_hash=input_hash,
                fallback_used=True,
                regulatory_authority=0.0,
            )
            return [], contract

        q_emb = default_embedding_provider.embed_text(query_text)
        candidates = []

        for std_num, profile, cat in KNOWN_STANDARD_PROFILES:
            prof_emb = default_embedding_provider.embed_text(f"{std_num} {profile}")
            sim = cosine_similarity(q_emb, prof_emb)
            
            # Name match boost
            q_lower = query_text.lower()
            if any(term in q_lower for term in profile.lower().split()[:4]):
                sim = min(0.98, sim + 0.25)

            if sim > 0.40:
                candidates.append(
                    ApplicabilityCandidate(
                        standard_number=std_num,
                        confidence=round(sim, 3),
                        category=cat,
                        is_authoritative=False,
                        advisory_only=True,
                    )
                )

        candidates.sort(key=lambda x: x.confidence, reverse=True)
        top_candidates = candidates[:top_k]

        latency = (time.time() - t0) * 1000.0
        ml_telemetry.record_inference(self.model_name, latency, fallback_used=False)

        contract = MLPredictionContract(
            model_name=self.model_name,
            model_version=self.model_version,
            task=MLTaskType.APPLICABILITY_CLASSIFICATION.value,
            prediction=[c.model_dump() for c in top_candidates],
            confidence=top_candidates[0].confidence if top_candidates else 0.0,
            input_hash=input_hash,
            fallback_used=False,
            regulatory_authority=0.0,
        )

        return top_candidates, contract


applicability_classifier = ApplicabilityCandidateClassifier()
