"""Citation Guard & Source Validation Service.

Implements Technology Pillar 05 (Citation Guard) and Layer 8 (Source Validation Layer)
from SIH Presentation Slide 2 & Slide 3.

Primary Flow:
LAYER 7 RESULT
→ CLAIM EXTRACTION
→ SOURCE VALIDATION
→ STANDARD / CLAUSE VALIDATION
→ EVIDENCE PROVENANCE VALIDATION
→ CITATION VALIDATION
→ CONFLICT / STALENESS CHECK
→ TRUST DECISION
→ LAYER 9 OUTPUT

Core Rule:
NO VERIFIED SOURCE → NO REGULATORY CLAIM
LLM COMPLIANCE AUTHORITY = 0.0%
"""

import re
from typing import Dict, Any, Optional

from backend.app.schemas.evidence import (
    CitationGuardCheckRequest,
    CitationGuardCheckResponse,
    ValidationStatus,
)
from backend.app.services.citation_guard.models import (
    ValidationOutcome,
    TrustChain,
    CitationValidationResult,
    BatchValidationReport,
)
from backend.app.services.citation_guard.validator import (
    CitationValidator,
    citation_validator,
    calculate_sha256,
)
from backend.app.core.logging import logger


class CitationGuard:
    """Enforces zero-hallucination citation provenance and evidence verification."""

    def __init__(self):
        self.validator = citation_validator
        self.min_confidence_threshold = 0.70

    def verify_claim(self, request: CitationGuardCheckRequest) -> CitationGuardCheckResponse:
        """Legacy compatibility method mapping to Layer 8 production validator."""
        ev_text = (request.extracted_evidence_text or "").strip()
        conflict_indicators = ["failed", "non-compliant", "breakdown", "spark", "exceeded limit", "burned", "melted"]
        has_conflict = any(word in ev_text.lower() for word in conflict_indicators)

        if has_conflict:
            return CitationGuardCheckResponse(
                is_valid=False,
                status=ValidationStatus.CONTRADICTED,
                reasoning=f"Evidence text contains failure/conflict indicators for {request.target_standard} Clause {request.target_clause}. Requires human auditor review.",
                matched_clause_text=ev_text[:150] if ev_text else None,
                confidence=0.45,
            )

        res = self.validator.validate_citation_claim(
            claim=request.claim,
            target_standard=request.target_standard,
            target_clause=request.target_clause,
            evidence_text=request.extracted_evidence_text,
            evidence_id="LEGACY-REQ",
            document_id="DOC-USER-INPUT",
            verification_status="VERIFIED" if request.extracted_evidence_text.strip() else "UNVERIFIED",
            has_conflict=has_conflict,
        )

        if res.validation_result == ValidationOutcome.VERIFIED:
            return CitationGuardCheckResponse(
                is_valid=True,
                status=ValidationStatus.SUPPORTED,
                reasoning=f"Claim rigorously verified against {res.standard} {res.clause} with direct empirical citation links.",
                matched_clause_text=request.extracted_evidence_text[:200] if request.extracted_evidence_text else None,
                confidence=0.98,
            )
        elif res.validation_result == ValidationOutcome.EXPERT_REVIEW_REQUIRED:
            return CitationGuardCheckResponse(
                is_valid=False,
                status=ValidationStatus.CONTRADICTED,
                reasoning=res.failure_reason or "Contradictory evidence detected; routed to expert auditor.",
                matched_clause_text=request.extracted_evidence_text[:150] if request.extracted_evidence_text else None,
                confidence=0.45,
            )
        elif res.validation_result in (ValidationOutcome.INSUFFICIENT_SOURCE, ValidationOutcome.SOURCE_UNAVAILABLE):
            return CitationGuardCheckResponse(
                is_valid=False,
                status=ValidationStatus.INSUFFICIENT_EVIDENCE,
                reasoning=res.failure_reason or "Insufficient source evidence supplied.",
                matched_clause_text=None,
                confidence=0.35,
            )
        else:
            return CitationGuardCheckResponse(
                is_valid=False,
                status=ValidationStatus.UNVERIFIED,
                reasoning=res.failure_reason or "Verification rejected by Citation Guard.",
                matched_clause_text=None,
                confidence=0.0,
            )

    def validate_claim(self, **kwargs) -> CitationValidationResult:
        """Direct Layer 8 production validation call."""
        return self.validator.validate_citation_claim(**kwargs)

    def validate_batch(self, **kwargs) -> BatchValidationReport:
        """Batch validation of claims."""
        return self.validator.validate_batch(**kwargs)


citation_guard = CitationGuard()

__all__ = [
    "CitationGuard",
    "citation_guard",
    "CitationValidator",
    "citation_validator",
    "ValidationOutcome",
    "CitationValidationResult",
    "BatchValidationReport",
    "TrustChain",
    "calculate_sha256",
]
