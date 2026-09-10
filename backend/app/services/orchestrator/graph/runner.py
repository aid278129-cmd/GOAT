"""LangGraph Execution Runner for Layer 3 (Milestone M24.2).

Provides run_compliance_graph(...) facade translating between Layer 3 caller input
and LangGraph StateGraph execution, with safe fallback handling.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from backend.app.services.orchestrator.graph.state import BISComplianceGraphState
from backend.app.services.orchestrator.graph.builder import compliance_graph
from backend.app.services.orchestrator.schemas import (
    OrchestratedAIResponse,
    OrchestratorIntent,
    GroundingStatus,
)
from backend.app.core.logging import logger


def run_compliance_graph(
    user_query: str,
    product_dna: Optional[Any] = None,
    assessment_context: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> OrchestratedAIResponse:
    """Execute compliance query through the LangGraph StateGraph pipeline."""
    correlation_id = f"GRAPH-L3-{uuid.uuid4().hex[:8].upper()}"
    thread_key = thread_id or correlation_id

    # Initialize state
    initial_state: BISComplianceGraphState = {
        "correlation_id": correlation_id,
        "user_query": user_query,
        "sanitized_query": user_query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "security_flag": False,
        "security_warnings": [],
        "product_dna": product_dna,
        "dna_sufficient": True,
        "missing_attributes": [],
        "user_intent": OrchestratorIntent.QUERY_REQUIREMENT.value,
        "task_type": "QUERY_REQUIREMENT",
        "retrieval_required": True,
        "target_standard_number": assessment_context.get("standard_number", "IS 302-2-201:2008") if assessment_context else "IS 302-2-201:2008",
        "target_standard_title": "",
        "generated_search_queries": [],
        "retrieved_candidate_clauses": assessment_context.get("evaluations", []) if assessment_context else [],
        "available_evidence_ids": [e.get("id") for e in assessment_context.get("available_evidence", [])] if assessment_context and assessment_context.get("available_evidence") else [],
        "verified_evidence_records": assessment_context.get("available_evidence", []) if assessment_context else [],
        "unverified_claims_blocked": [],
        "evidence_status": "NO_VERIFIED_SOURCE",
        "applicability_decision": None,
        "gap_analysis_summary": None,
        "unsatisfied_clauses": [],
        "evaluation_records": [],
        "analysis_explanation": "",
        "action_plan_items": [],
        "expert_review_required": False,
        "grounding_status": GroundingStatus.SUPPORTED.value,
        "warnings": [],
        "errors": [],
        "regulatory_conclusion": "NONE",
        "llm_compliance_authority": 0.0,
        "final_response": None,
        "execution_traces": [],
    }

    try:
        config = {"configurable": {"thread_id": thread_key}}
        final_state = compliance_graph.invoke(initial_state, config=config)

        if final_state and final_state.get("final_response"):
            resp_dict = final_state["final_response"]
            return OrchestratedAIResponse.model_validate(resp_dict)
    except Exception as exc:
        logger.error(f"[LangGraphRunner] StateGraph execution failed: {exc}. Enforcing safe deterministic fallback.")

    # Safe deterministic fallback if graph or node failed
    return OrchestratedAIResponse(
        answer="An unexpected error occurred during reasoning graph execution. Enforcing deterministic zero-authority fallback.",
        intent=OrchestratorIntent.UNKNOWN_INTENT,
        grounding_status=GroundingStatus.UNKNOWN,
        confidence_score=0.0,
        citations=[],
        deterministic_fallback_used=True,
        regulatory_conclusion="NONE",
    )
