"""Layer 8: Source Validation & Citation Guard REST API Router.

Exposes deterministic verification endpoints for regulatory claims, standard citations,
evidence hashes, and provenance audit chains.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.services.citation_guard.models import (
    ValidationOutcome,
    CitationValidationResult,
    BatchValidationReport,
)
from backend.app.services.citation_guard.validator import (
    citation_validator,
    calculate_sha256,
)

citation_guard_router = APIRouter(prefix="/citation-guard", tags=["Layer 8 - Citation Guard"])


class ValidateClaimPayload(BaseModel):
    claim: str
    target_standard: str
    target_clause: str
    evidence_id: Optional[str] = None
    document_id: Optional[str] = None
    source_authority: Optional[str] = None
    page_number: Optional[int] = None
    verification_status: Optional[str] = "UNVERIFIED"
    evidence_text: Optional[str] = None
    evidence_hash: Optional[str] = None
    evidence_standard: Optional[str] = None
    knowledge_version: Optional[str] = None
    is_expired: bool = False
    has_conflict: bool = False
    is_llm_generated: bool = False
    is_authoritative_pending: bool = False


class BatchValidatePayload(BaseModel):
    claims: List[Dict[str, Any]]
    standard_number: str = "IS 17526:2021"
    knowledge_version: Optional[str] = None


@citation_guard_router.post("/validate-claim", response_model=CitationValidationResult)
def validate_single_claim(payload: ValidateClaimPayload) -> CitationValidationResult:
    """Validate a single regulatory or compliance claim using Layer 8 deterministic guards."""
    return citation_validator.validate_citation_claim(
        claim=payload.claim,
        target_standard=payload.target_standard,
        target_clause=payload.target_clause,
        evidence_id=payload.evidence_id,
        document_id=payload.document_id,
        source_authority=payload.source_authority,
        page_number=payload.page_number,
        verification_status=payload.verification_status,
        evidence_text=payload.evidence_text,
        evidence_hash=payload.evidence_hash,
        evidence_standard=payload.evidence_standard,
        knowledge_version=payload.knowledge_version,
        is_expired=payload.is_expired,
        has_conflict=payload.has_conflict,
        is_llm_generated=payload.is_llm_generated,
        is_authoritative_pending=payload.is_authoritative_pending,
    )


@citation_guard_router.post("/validate-batch", response_model=BatchValidationReport)
def validate_claims_batch(payload: BatchValidatePayload) -> BatchValidationReport:
    """Validate a batch of regulatory claims and assemble the overall trust decision."""
    return citation_validator.validate_batch(
        claims=payload.claims,
        standard_number=payload.standard_number,
        knowledge_version=payload.knowledge_version or citation_validator.active_knowledge_version,
    )


@citation_guard_router.get("/invariants")
def get_layer8_invariants() -> Dict[str, Any]:
    """Retrieve Layer 8 cardinal invariants, rejection cases, and validation states."""
    return {
        "layer": "LAYER_8_SOURCE_VALIDATION_AND_CITATION_GUARD",
        "cardinal_rule": "NO VERIFIED SOURCE -> NO REGULATORY CLAIM",
        "llm_compliance_authority": "0.0%",
        "invariants": [
            "NO VERIFIED SOURCE -> NO REGULATORY CLAIM",
            "INVALID CITATION -> REJECT",
            "WRONG STANDARD -> REJECT",
            "MISSING PROVENANCE -> REJECT / REVIEW",
            "CONFLICT -> EXPERT REVIEW",
            "STALE EVIDENCE -> REVIEW",
            "LLM CANNOT VALIDATE ITS OWN OUTPUT",
        ],
        "allowed_outcomes": [o.value for o in ValidationOutcome],
        "hard_rejection_cases": [
            "Fabricated standard",
            "Fabricated clause",
            "Source does not contain claimed requirement",
            "Citation points to wrong document/page",
            "Evidence belongs to another standard",
            "Unverified source used as authoritative",
            "Expired/stale evidence",
            "Missing provenance",
            "Altered evidence hash (SHA-256 mismatch)",
            "Unsupported compliance statement",
            "LLM-generated fact without supporting source",
            "Conflicting sources without expert review",
        ],
        "active_knowledge_version": citation_validator.active_knowledge_version,
    }
