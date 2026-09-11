"""Layer 7: Compliance Gap Analysis Engine — API Router.

Endpoints for:
- Requirement-by-requirement deterministic gap evaluation
- Gap Register inspection with deterministic severities (CRITICAL, HIGH, MEDIUM, LOW)
- Categorized Testing Roadmap generation
- Honest Compliance Coverage Summary (no arbitrary percentage score)
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.schemas.product_dna import ProductDNACore
from backend.app.services.gap_analysis.engine import (
    StandardComplianceEvaluation,
    evaluate_compliance_gaps,
    GapPriority,
    GapRegisterItem,
    TestingRoadmap,
    ComplianceCoverageSummary,
)
from backend.app.services.applicability.engine import determine_applicability
from backend.app.services.rag.engine import layer6_clause_rag

router = APIRouter(prefix="/gap-analysis", tags=["Layer 7 — Compliance Gap Analysis Engine"])


class GapAnalysisEvaluationRequest(BaseModel):
    product_dna: ProductDNACore
    standard_number: Optional[str] = Field(None, description="Target Indian Standard; defaults to Layer 5 primary applicable standard")
    evidence_payload: Optional[Dict[str, Any]] = None
    linked_evidences_map: Optional[Dict[str, List[Any]]] = None
    conflicts_map: Optional[Dict[str, bool]] = None


@router.post("/evaluate", response_model=StandardComplianceEvaluation)
def evaluate_gaps(request: GapAnalysisEvaluationRequest) -> StandardComplianceEvaluation:
    """Execute Layer 7 deterministic requirement-by-requirement gap evaluation."""
    dna = request.product_dna

    # 1. Resolve target standard (using Layer 5 Applicability if not explicitly supplied)
    target_std = request.standard_number
    target_title = "Indian Standard Specification"
    if not target_std:
        decisions = determine_applicability(dna, authoritative_only=True)
        if decisions:
            target_std = decisions[0].standard_number
            target_title = decisions[0].standard_title or "Indian Standard Specification"
        else:
            target_std = "IS 17526:2021"
            target_title = "Domestic Stainless Steel Vacuum Flask/Bottle"

    # 2. Gather verified requirements from Layer 6
    clauses = layer6_clause_rag.clause_catalog.get(target_std, [])
    req_catalog = []
    for c in clauses:
        ev_req = c.get("evidence_requirement") or {}
        req_catalog.append({
            "id": ev_req.get("requirement_id", f"REQ-{c['clause_number']}"),
            "clause_number": c["clause_number"],
            "clause_title": c["title"],
            "code": ev_req.get("requirement_id", f"REQ-{c['clause_number']}"),
            "requirement_type": "MATERIAL" if "material" in c["title"].lower() or "stainless" in c["title"].lower() else ("MARKING" if "marking" in c["title"].lower() else "PERFORMANCE"),
            "description": c["text_content"],
            "measurable_condition": ev_req.get("measurable_condition"),
        })

    # Fallback to default catalog if empty
    if not req_catalog:
        req_catalog = [
            {
                "id": "REQ-1.0",
                "clause_number": "1.0",
                "clause_title": "Scope",
                "code": "REQ-SCOPE",
                "requirement_type": "SCOPE",
                "description": f"Scope compliance for {target_std}",
                "measurable_condition": "Product within declared scope",
            }
        ]

    # 3. Execute Layer 7 deterministic evaluation
    return evaluate_compliance_gaps(
        standard_number=target_std,
        standard_title=target_title,
        requirements_catalog=req_catalog,
        dna=dna,
        evidence_payload=request.evidence_payload,
        linked_evidences_map=request.linked_evidences_map,
        conflicts_map=request.conflicts_map,
    )


@router.get("/invariants")
def get_layer7_invariants() -> Dict[str, Any]:
    """Retrieve Layer 7 compliance invariants and gap priority rules."""
    return {
        "layer": "Layer 7: Compliance Gap Analysis Engine",
        "cardinal_invariants": [
            "CLAUSE RETRIEVED != REQUIREMENT SATISFIED",
            "PRODUCT FACT != COMPLIANCE EVIDENCE",
            "USER CLAIM != COMPLIANCE EVIDENCE",
            "NO VERIFIED EVIDENCE -> NO SATISFIED",
            "NO DETERMINISTIC PASS -> NO SATISFIED",
            "CONFLICT -> EXPERT REVIEW",
            "LLM COMPLIANCE AUTHORITY = 0%",
        ],
        "hard_gate_formula": (
            "VERIFIED REQUIREMENT + VERIFIED EVIDENCE + REQUIREMENT/EVIDENCE LINK "
            "+ VALID EXTRACTION + DETERMINISTIC PASS + NO CONFLICT = SATISFIED"
        ),
        "gap_priorities": {
            "CRITICAL": "Life-safety, electric shock, toy choking, chemical toxicity",
            "HIGH": "Thermal performance, mechanical drop impact, raw material grade deficiency",
            "MEDIUM": "Inversion leakage weeping, marking and ISI layout, dimensions",
            "LOW": "Cosmetic finish, care instructions, documentation",
        },
    }
