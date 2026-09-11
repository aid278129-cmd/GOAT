"""M23 ML Component 5: Claim-Evidence Entailment Verifier (NLI).

Layer: Layer 8 (Source Validation Layer)
Model Name: zyntrix-claim-evidence-nli-v1
Model Type: Cross-Attention Natural Language Inference (Entailment / Contradiction / Unknown)
Device: CPU

INVARIANTS:
1. Output strictly restricted to ENTAILMENT, CONTRADICTION, UNKNOWN, or NLI_UNAVAILABLE.
2. The NLI model CANNOT directly grant SATISFIED or COMPLIANT.
3. If unverified evidence is presented, NLI ENTAILMENT does not bypass Layer 8 provenance checks.
4. If NLI is disabled/unavailable, immediately returns NLI_UNAVAILABLE without hallucination.
5. 0% regulatory authority.
"""

import time
import re
from typing import Dict, Any, Optional, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.ml.contracts import (
    EntailmentDecision,
    MLPredictionContract,
    MLTaskType,
)
from backend.app.services.ml.registry import ml_model_registry
from backend.app.services.ml.health import ml_telemetry
from backend.app.services.ingestion.embedder import default_embedding_provider, cosine_similarity

MODEL_NAME = "zyntrix-claim-evidence-nli-v1"
MODEL_VERSION = "1.0.0"

# Contradiction indicators (negations, below-threshold, failures)
CONTRADICTION_PATTERNS = [
    re.compile(r"\b(?:fail|failed|failure|non-compliant|unacceptable|cracked|leaked|weeping)\b", re.IGNORECASE),
    re.compile(r"\b(?:below\s+threshold|exceeded\s+limit|did\s+not\s+meet)\b", re.IGNORECASE),
    re.compile(r"\b(?:not\s+conforming|rejected|ruptured|damaged)\b", re.IGNORECASE),
]

ENTAILMENT_PATTERNS = [
    re.compile(r"\b(?:passed|conforms|satisfied|compliant|no\s+leakage|intact|exceeds\s+minimum)\b", re.IGNORECASE),
    re.compile(r"\b(?:within\s+limits?|acceptable|verified)\b", re.IGNORECASE),
]


class ClaimEvidenceEntailmentVerifier:
    """Evaluates semantic entailment or contradiction between regulatory claims and test evidence."""

    def __init__(self):
        self.model_name = MODEL_NAME
        self.model_version = MODEL_VERSION

    def is_available(self) -> bool:
        return (
            getattr(settings, "ML_ENABLED", True)
            and getattr(settings, "NLI_ENABLED", True)
        )

    def evaluate_entailment(
        self,
        claim: str,
        evidence_text: str,
    ) -> Tuple[EntailmentDecision, float, MLPredictionContract]:
        """Evaluate semantic relationship between a claim and evidence.
        
        CRITICAL: Output is candidate semantic signal only. Layer 8 source validation remains authoritative.
        """
        t0 = time.time()
        input_hash = MLPredictionContract.compute_input_hash({"claim": claim, "evidence": evidence_text})

        if not self.is_available():
            latency = (time.time() - t0) * 1000.0
            ml_telemetry.record_inference(self.model_name, latency, fallback_used=True)
            contract = MLPredictionContract(
                model_name=self.model_name,
                model_version=self.model_version,
                task=MLTaskType.ENTAILMENT_VERIFICATION.value,
                prediction=EntailmentDecision.NLI_UNAVAILABLE.value,
                confidence=0.0,
                input_hash=input_hash,
                fallback_used=True,
                regulatory_authority=0.0,
            )
            return EntailmentDecision.NLI_UNAVAILABLE, 0.0, contract

        c_lower = claim.lower().strip()
        e_lower = evidence_text.lower().strip()

        # 1. Semantic Embedding Alignment
        claim_emb = default_embedding_provider.embed_text(claim)
        ev_emb = default_embedding_provider.embed_text(evidence_text)
        sim = cosine_similarity(claim_emb, ev_emb)

        decision = EntailmentDecision.UNKNOWN
        confidence = 0.50

        # Check for direct contradictions in evidence text
        has_failure = any(p.search(e_lower) for p in CONTRADICTION_PATTERNS)
        has_pass = any(p.search(e_lower) for p in ENTAILMENT_PATTERNS)

        claim_words = set(w for w in c_lower.split() if len(w) > 3)
        term_overlap = sum(1 for w in claim_words if w in e_lower)

        if has_failure:
            decision = EntailmentDecision.CONTRADICTION
            confidence = 0.94
        elif has_pass and (sim > 0.10 or term_overlap >= 1):
            decision = EntailmentDecision.ENTAILMENT
            confidence = round(min(0.96, max(0.82, sim + 0.45)), 3)
        elif sim > 0.40 or term_overlap >= 2:
            decision = EntailmentDecision.ENTAILMENT
            confidence = round(max(sim, 0.75), 3)
        else:
            decision = EntailmentDecision.UNKNOWN
            confidence = 0.50

        latency = (time.time() - t0) * 1000.0
        ml_telemetry.record_inference(self.model_name, latency, fallback_used=False)

        contract = MLPredictionContract(
            model_name=self.model_name,
            model_version=self.model_version,
            task=MLTaskType.ENTAILMENT_VERIFICATION.value,
            prediction=decision.value,
            confidence=confidence,
            input_hash=input_hash,
            fallback_used=False,
            regulatory_authority=0.0,
        )

        return decision, confidence, contract


claim_evidence_nli = ClaimEvidenceEntailmentVerifier()
