"""Layer 5: Applicability Engine — API Router.

Provides endpoints for:
- Direct deterministic applicability evaluation against Product DNA
- Inspection of declarative rules and verification statuses
- Inspection of product category taxonomy and attribute profiles
- 7 canonical applicability states and regulatory invariants
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.schemas.product_dna import ProductDNACore
from backend.app.services.applicability.applicability_models import (
    ApplicabilityDecision,
    ApplicabilityState,
    ScopeStatus,
    QCOStatus,
    ApplicabilityAction,
    DeclarativeRule,
)
from backend.app.services.applicability.engine import (
    determine_applicability,
    load_declarative_rules,
)
from backend.app.services.applicability.taxonomy import (
    TAXONOMY_REGISTRY,
    REQUIRED_ATTRIBUTE_PROFILES,
)

router = APIRouter(prefix="/applicability", tags=["Layer 5 — Applicability Engine"])


class ApplicabilityEvaluationRequest(BaseModel):
    product_dna: ProductDNACore
    authoritative_mode: bool = True


class ApplicabilityEvaluationResponse(BaseModel):
    layer: str = "Layer 5: Applicability Engine"
    authoritative_mode: bool
    total_decisions: int
    decisions: List[ApplicabilityDecision]
    llm_authority_percentage: float = 0.0
    supported_states: List[str] = [s.value for s in ApplicabilityState]


@router.post("/evaluate", response_model=ApplicabilityEvaluationResponse)
def evaluate_product_applicability(req: ApplicabilityEvaluationRequest) -> ApplicabilityEvaluationResponse:
    """Evaluate Indian Standards applicability deterministically from Layer 2 Product DNA.
    
    Adheres strictly to the 5 cardinal safeguards:
    1. LLM authority over final applicability = 0%
    2. Missing required attribute triggers MORE_INFORMATION_REQUIRED (Never guess)
    3. Coverage gap != NOT_APPLICABLE
    4. Regulatory mandate strictly separated from technical scope
    5. In authoritative mode, unverified rules are never applied
    """
    decisions = determine_applicability(
        dna=req.product_dna,
        authoritative_only=req.authoritative_mode,
    )

    return ApplicabilityEvaluationResponse(
        authoritative_mode=req.authoritative_mode,
        total_decisions=len(decisions),
        decisions=decisions,
        llm_authority_percentage=0.0,
    )


@router.get("/rules", response_model=List[DeclarativeRule])
def get_rules() -> List[DeclarativeRule]:
    """Retrieve all loaded declarative Indian Standard applicability rules."""
    return load_declarative_rules()


@router.get("/taxonomy")
def get_taxonomy() -> Dict[str, Any]:
    """Retrieve canonical product category taxonomy and required attribute profiles."""
    return {
        "categories": {
            k: v.model_dump() for k, v in TAXONOMY_REGISTRY.items()
        },
        "attribute_profiles": {
            k: v.model_dump() for k, v in REQUIRED_ATTRIBUTE_PROFILES.items()
        },
    }


@router.get("/states")
def get_canonical_states() -> Dict[str, Any]:
    """Retrieve the 7 canonical applicability states from the SIH Presentation."""
    return {
        "states": [
            {
                "state": ApplicabilityState.APPLICABLE.value,
                "description": "All technical criteria, scope boundaries, and mandatory requirements are satisfied.",
                "action": ApplicabilityAction.CONTINUE_TO_REQUIREMENTS.value,
            },
            {
                "state": ApplicabilityState.POTENTIALLY_APPLICABLE.value,
                "description": "Candidate standard identified; awaiting secondary technical parameter confirmation.",
                "action": ApplicabilityAction.CONTINUE_TO_REQUIREMENTS.value,
            },
            {
                "state": ApplicabilityState.MORE_INFORMATION_REQUIRED.value,
                "description": "Essential blocking attributes missing. Explicit clarification question generated.",
                "action": ApplicabilityAction.ASK_FOR_INFORMATION.value,
            },
            {
                "state": ApplicabilityState.NOT_APPLICABLE.value,
                "description": "Product is definitively out of standard scope based on verified exclusion criteria.",
                "action": ApplicabilityAction.CONTINUE_TO_REQUIREMENTS.value,
            },
            {
                "state": ApplicabilityState.COVERAGE_GAP.value,
                "description": "Category or standard is not yet codified in the verified rule base (NOT an exemption).",
                "action": ApplicabilityAction.REVIEW_COVERAGE_GAP.value,
            },
            {
                "state": ApplicabilityState.CONFLICTING_RULES.value,
                "description": "Opposing rule conditions or contradictory product claims detected.",
                "action": ApplicabilityAction.EXPERT_REVIEW.value,
            },
            {
                "state": ApplicabilityState.EXPERT_REVIEW_REQUIRED.value,
                "description": "Unverified rule or edge-case scope boundary requiring human BIS legal review.",
                "action": ApplicabilityAction.EXPERT_REVIEW.value,
            },
        ],
        "invariants": [
            "NO VERIFIED SCOPE/RULE → NO AUTHORITATIVE APPLICABILITY CLAIM",
            "MISSING REQUIRED FACT → ASK (Never Guess)",
            "COVERAGE GAP ≠ NOT_APPLICABLE",
            "STANDARD EXISTS ≠ AUTOMATICALLY MANDATORY",
            "LLM AUTHORITY OVER FINAL APPLICABILITY = 0%",
        ],
    }
