"""M23 ML Component 3: Semantic Evidence Matcher.

Layer: Layer 7 (Compliance Gap Engine)
Model Name: zyntrix-semantic-evidence-matcher-v1
Model Type: Dense Semantic Vector Cosine & Token Interaction Matcher
Device: CPU

INVARIANTS:
1. High semantic similarity != SATISFIED.
2. Only identifies CANDIDATE evidence for downstream deterministic evaluation.
3. 0% regulatory authority.
4. If model disabled or unavailable, falls back to keyword lexical matching.
"""

import time
from typing import List, Dict, Any, Optional
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

MODEL_NAME = "zyntrix-semantic-evidence-matcher-v1"
MODEL_VERSION = "1.0.0"


class EvidenceMatchCandidate(BaseModel):
    requirement_code: str
    requirement_title: str
    evidence_id: str
    evidence_snippet: str
    similarity_score: float
    confidence: float
    is_candidate: bool
    model_name: str = MODEL_NAME
    regulatory_verdict_granted: bool = False  # Cardinal Invariant: ALWAYS FALSE


class SemanticEvidenceMatcher:
    """Matches product evidence documents against technical requirements."""

    def __init__(self):
        self.model_name = MODEL_NAME
        self.model_version = MODEL_VERSION

    def is_available(self) -> bool:
        return (
            getattr(settings, "ML_ENABLED", True)
            and getattr(settings, "EVIDENCE_MATCHING_ML_ENABLED", True)
        )

    def match_evidence_to_requirement(
        self,
        requirement_code: str,
        requirement_text: str,
        evidence_items: List[Dict[str, Any]],
        similarity_threshold: float = 0.25,
    ) -> List[EvidenceMatchCandidate]:
        """Identify candidate evidence items matching a requirement.
        
        CRITICAL: Never marks SATISFIED. Only yields candidates for Layer 7 deterministic evaluation.
        """
        t0 = time.time()
        input_hash = MLPredictionContract.compute_input_hash({
            "req": requirement_code,
            "evidence_count": len(evidence_items),
        })

        if not self.is_available():
            candidates = self._fallback_keyword_match(requirement_code, requirement_text, evidence_items)
            latency = (time.time() - t0) * 1000.0
            ml_telemetry.record_inference(self.model_name, latency, fallback_used=True)
            return candidates

        req_emb = default_embedding_provider.embed_text(f"{requirement_code} {requirement_text}")
        candidates: List[EvidenceMatchCandidate] = []

        for item in evidence_items:
            ev_text = item.get("content") or item.get("text") or item.get("snippet") or ""
            ev_id = str(item.get("id") or item.get("source_id") or "ev-unknown")

            if not ev_text:
                continue

            ev_emb = default_embedding_provider.embed_text(ev_text)
            sim = round(cosine_similarity(req_emb, ev_emb), 4)

            # Bonus for exact keywords (e.g. "thermal", "drop", "leakage", "pressure")
            req_words = set(w.lower() for w in requirement_text.split() if len(w) > 3)
            overlap = sum(1 for w in req_words if w in ev_text.lower())
            bonus = min(0.40, overlap * 0.10)
            adjusted_sim = round(min(1.0, sim + bonus), 4)

            if adjusted_sim >= similarity_threshold or overlap >= 2:
                candidates.append(
                    EvidenceMatchCandidate(
                        requirement_code=requirement_code,
                        requirement_title=requirement_text[:80],
                        evidence_id=ev_id,
                        evidence_snippet=ev_text[:200],
                        similarity_score=max(adjusted_sim, 0.40 if overlap >= 2 else adjusted_sim),
                        confidence=round(min(0.95, max(0.60, adjusted_sim * 0.90)), 3),
                        is_candidate=True,
                        regulatory_verdict_granted=False,
                    )
                )

        candidates.sort(key=lambda x: x.similarity_score, reverse=True)
        latency = (time.time() - t0) * 1000.0
        ml_telemetry.record_inference(self.model_name, latency, fallback_used=False)

        return candidates

    def _fallback_keyword_match(
        self,
        requirement_code: str,
        requirement_text: str,
        evidence_items: List[Dict[str, Any]],
    ) -> List[EvidenceMatchCandidate]:
        """Lexical keyword fallback when ML is inactive."""
        req_words = set(w.lower() for w in requirement_text.split() if len(w) > 3)
        candidates = []
        for item in evidence_items:
            ev_text = item.get("content") or item.get("text") or ""
            ev_id = str(item.get("id") or "ev-fallback")
            overlap = sum(1 for w in req_words if w in ev_text.lower())
            if overlap >= 2:
                candidates.append(
                    EvidenceMatchCandidate(
                        requirement_code=requirement_code,
                        requirement_title=requirement_text[:80],
                        evidence_id=ev_id,
                        evidence_snippet=ev_text[:200],
                        similarity_score=0.60,
                        confidence=0.65,
                        is_candidate=True,
                        regulatory_verdict_granted=False,
                    )
                )
        return candidates


semantic_evidence_matcher = SemanticEvidenceMatcher()
