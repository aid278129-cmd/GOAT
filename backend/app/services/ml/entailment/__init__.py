"""ML Entailment Subpackage."""

from backend.app.services.ml.entailment.verifier import (
    claim_evidence_nli,
    ClaimEvidenceEntailmentVerifier,
)

__all__ = ["claim_evidence_nli", "ClaimEvidenceEntailmentVerifier"]
