"""LangGraph Execution Runner for Layer 3 (Milestones M24.2, M24.3 & M24.4.1).

Provides run_compliance_graph(...) and run_compliance_graph_with_state(...) facades
translating between Layer 3 caller input and LangGraph StateGraph execution,
with safe fallback handling and runtime optimization metrics.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from backend.app.services.orchestrator.graph.state import BISComplianceGraphState
from backend.app.services.orchestrator.graph.builder import compliance_graph
from backend.app.services.orchestrator.schemas import (
    OrchestratedAIResponse,
    OrchestratorIntent,
    GroundingStatus,
)
from backend.app.core.logging import logger


def run_compliance_graph_with_state(
    user_query: str,
    product_dna: Optional[Any] = None,
    assessment_context: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> Tuple[OrchestratedAIResponse, BISComplianceGraphState]:
    """Execute compliance query through LangGraph and return both the final response and final state."""
    correlation_id = f"GRAPH-L3-{uuid.uuid4().hex[:8].upper()}"
    thread_key = thread_id or correlation_id

    # Initialize state with M24.4.1 runtime optimization metrics
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
        "target_standard_number": assessment_context.get("standard_number") if assessment_context else None,
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
        "tool_traces": [],
        "tool_call_count": 0,
        # M24.4.1 Optimization fields
        "llm_call_count": 0,
        "duplicate_tool_calls_prevented": 0,
        "retrieval_call_count": 0,
        "context_size_chars": 0,
        "short_circuited": False,
        "short_circuit_reason": None,
        "tool_cache": {},
        "node_contracts": {},
    }

    try:
        from backend.app.services.orchestrator.graph.tracing import get_langsmith_config
        config = get_langsmith_config(
            correlation_id=correlation_id,
            thread_id=thread_key,
            metadata={
                "target_standard": initial_state.get("target_standard_number"),
                "task_type": initial_state.get("task_type"),
            },
        )
        final_state = compliance_graph.invoke(initial_state, config=config)

        if final_state and final_state.get("final_response"):
            resp_dict = final_state["final_response"]
            return OrchestratedAIResponse.model_validate(resp_dict), final_state
    except Exception as exc:
        logger.error(f"[LangGraphRunner] StateGraph execution failed: {exc}. Enforcing safe deterministic fallback.")

    # Safe deterministic fallback if graph or node failed
    fallback_response = OrchestratedAIResponse(
        answer="An unexpected error occurred during reasoning graph execution. Enforcing deterministic zero-authority fallback.",
        intent=OrchestratorIntent.UNKNOWN_INTENT,
        grounding_status=GroundingStatus.UNKNOWN,
        confidence_score=0.0,
        citations=[],
        deterministic_fallback_used=True,
        regulatory_conclusion="NONE",
    )
    return fallback_response, initial_state


def run_compliance_graph(
    user_query: str,
    product_dna: Optional[Any] = None,
    assessment_context: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> OrchestratedAIResponse:
    """Execute compliance query through the LangGraph StateGraph pipeline."""
    response, _ = run_compliance_graph_with_state(
        user_query=user_query,
        product_dna=product_dna,
        assessment_context=assessment_context,
        thread_id=thread_id,
    )
    return response
