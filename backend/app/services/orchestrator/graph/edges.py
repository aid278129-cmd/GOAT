"""LangGraph Deterministic Conditional Edges for Layer 3 (Milestone M24.2).

Routing Rules:
1. NO AUTONOMOUS AGENT LOOPS: All transitions are strictly acyclic and conditionally deterministic.
2. NO LLM-CONTROLLED ROUTING: Next node is computed by Python logic over validated state attributes.
3. SECURITY FIRST: Security flag -> controlled_refusal -> END.
4. PRODUCT DNA INTEGRITY: Missing essential DNA -> clarification_request -> END.
5. RETRIEVAL DISPATCH: Requirements / Gaps / Audits -> retrieval_agent; others -> analysis_agent.
6. EVIDENCE VALIDATION: Conflicts or unverified standards route to safe uncertainty / expert review.
"""

from typing import Literal
from backend.app.services.orchestrator.graph.state import BISComplianceGraphState


def route_after_request_understanding(state: BISComplianceGraphState) -> Literal["controlled_refusal", "product_dna_check"]:
    """Route to controlled refusal if adversarial prompt injection is detected."""
    if state.get("security_flag", False):
        return "controlled_refusal"
    return "product_dna_check"


def route_after_product_dna_check(state: BISComplianceGraphState) -> Literal["clarification_request", "task_router"]:
    """Route to clarification if product facts are insufficient."""
    if state.get("user_intent") in ("GENERAL_BIS_INFORMATION", "CONSUMER_ASSISTANCE"):
        return "task_router"
    if not state.get("dna_sufficient", True):
        return "clarification_request"
    return "task_router"


def route_after_task_router(state: BISComplianceGraphState) -> Literal["retrieval_agent", "analysis_agent"]:
    """Route to retrieval agent if verified knowledge search is required."""
    if state.get("retrieval_required", False):
        return "retrieval_agent"
    return "analysis_agent"


def route_after_evidence_validation(state: BISComplianceGraphState) -> Literal["analysis_agent", "output_integrity_gate"]:
    """Route directly to output integrity if severe unverified source or conflict is detected."""
    if state.get("user_intent") in ("GENERAL_BIS_INFORMATION", "CONSUMER_ASSISTANCE"):
        return "analysis_agent"
    ev_stat = state.get("evidence_status", "")
    if ev_stat in ("NO_VERIFIED_SOURCE", "CONFLICT") and state.get("unverified_claims_blocked"):
        return "output_integrity_gate"
    return "analysis_agent"
