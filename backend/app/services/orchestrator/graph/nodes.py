"""LangGraph Canonical Nodes for Layer 3 AI Orchestrator (Milestone M24.2).

Architecture:
1. request_understanding
2. product_dna_check
3. task_router
4. retrieval_agent
5. evidence_validation_gate
6. analysis_agent
7. deterministic_compliance_gate
8. planning_agent
9. output_integrity_gate
Auxiliary Routing Terminals:
- controlled_refusal
- clarification_request
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.app.services.orchestrator.graph.state import (
    BISComplianceGraphState,
    NodeExecutionTrace,
)
from backend.app.services.orchestrator.schemas import (
    OrchestratorIntent,
    GroundingStatus,
    OrchestratedAIResponse,
    CitationItem,
    OrchestratorContext,
)
from backend.app.services.orchestrator.intent_router import intent_router
from backend.app.services.orchestrator.knowledge_selector import (
    verified_knowledge_selector,
    VERIFIED_STANDARDS_CATALOG,
)
from backend.app.services.orchestrator.context_builder import context_builder
from backend.app.services.orchestrator.grounding_guard import grounding_guard
from backend.app.services.orchestrator.langchain_adapter import langchain_chat_adapter
from backend.app.services.orchestrator.llm_interface import single_structured_llm
from backend.app.core.logging import logger


def _record_trace(state: BISComplianceGraphState, node_name: str, start_time: float, status: str = "SUCCESS", error: Optional[str] = None):
    end_time = time.time()
    trace: NodeExecutionTrace = {
        "node_name": node_name,
        "start_time": datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
        "end_time": datetime.fromtimestamp(end_time, tz=timezone.utc).isoformat(),
        "duration_ms": round((end_time - start_time) * 1000, 2),
        "status": status,
        "error": error,
    }
    traces = state.get("execution_traces", [])
    traces.append(trace)
    state["execution_traces"] = traces


# ------------------------------------------------------------------------------
# Node 1: Request Understanding
# ------------------------------------------------------------------------------
def request_understanding_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Sanitizes query, classifies intent, and detects adversarial prompt injection."""
    t0 = time.time()
    user_q = state.get("user_query", "")

    intent, sanitized, warnings = intent_router.classify_intent(user_q)
    security_flag = (intent == OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT) or len(warnings) > 0

    state["sanitized_query"] = sanitized
    state["user_intent"] = intent.value
    state["security_flag"] = security_flag
    state["security_reason"] = "Adversarial prompt injection / override attempt intercepted" if security_flag else None
    state["security_warnings"] = warnings

    _record_trace(state, "request_understanding", t0)
    return state


# ------------------------------------------------------------------------------
# Auxiliary Terminal: Controlled Refusal
# ------------------------------------------------------------------------------
def controlled_refusal_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Returns safe, zero-authority refusal response when security violation occurs."""
    t0 = time.time()
    refusal_response = OrchestratedAIResponse(
        answer=(
            "The AI assistant has ZERO authority to declare, override, or certify compliance. "
            "Under Zyntrix architecture, compliance determinations are strictly computed by the "
            "deterministic compliance gate based on verified empirical laboratory evidence. "
            "LLM compliance authority is exactly 0%."
        ),
        intent=OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT,
        grounding_status=GroundingStatus.SUPPORTED,
        confidence_score=1.0,
        citations=[CitationItem(standard_number=state.get("target_standard_number", "IS 302-2-201:2008"), source_authority="Zero-Hallucination Regulatory Integrity Gate")],
        deterministic_fallback_used=True,
        regulatory_conclusion="NONE",
    )
    state["regulatory_conclusion"] = "NONE"
    state["llm_compliance_authority"] = 0.0
    state["final_response"] = refusal_response.model_dump()

    _record_trace(state, "controlled_refusal", t0)
    return state


# ------------------------------------------------------------------------------
# Node 2: Product DNA Check
# ------------------------------------------------------------------------------
def product_dna_check_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Inspects Product DNA facts to determine if mandatory parameters are present."""
    t0 = time.time()
    dna = state.get("product_dna")

    dna_sufficient = True
    missing_attrs: List[str] = []

    if dna is None:
        # If no DNA provided at all, check if query is generic guidance or requires product context
        dna_sufficient = True
    elif isinstance(dna, dict):
        if not dna.get("product_name") and not dna.get("category"):
            dna_sufficient = False
            missing_attrs = ["product_name", "category"]
    elif hasattr(dna, "product_name"):
        if not dna.product_name and not getattr(dna, "category", None):
            dna_sufficient = False
            missing_attrs = ["product_name", "category"]

    state["dna_sufficient"] = dna_sufficient
    state["missing_attributes"] = missing_attrs

    _record_trace(state, "product_dna_check", t0)
    return state


# ------------------------------------------------------------------------------
# Auxiliary Terminal: Clarification Request
# ------------------------------------------------------------------------------
def clarification_request_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Generates clarification request when Product DNA is insufficient."""
    t0 = time.time()
    missing_str = ", ".join(state.get("missing_attributes", []))
    clarification_response = OrchestratedAIResponse(
        answer=(
            f"Product DNA contains insufficient attributes to evaluate compliance. "
            f"Please specify: {missing_str}. The system refuses to guess missing product parameters."
        ),
        intent=OrchestratorIntent.CLARIFY_PRODUCT,
        grounding_status=GroundingStatus.UNKNOWN,
        confidence_score=0.0,
        citations=[],
        missing_information_notes=f"Missing essential attributes: {missing_str}",
        deterministic_fallback_used=True,
        regulatory_conclusion="NONE",
    )
    state["regulatory_conclusion"] = "NONE"
    state["llm_compliance_authority"] = 0.0
    state["final_response"] = clarification_response.model_dump()

    _record_trace(state, "clarification_request", t0)
    return state


# ------------------------------------------------------------------------------
# Node 3: Task Router
# ------------------------------------------------------------------------------
def task_router_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Deterministically identifies target standard and whether retrieval is required."""
    t0 = time.time()
    sanitized_q = state.get("sanitized_query", "")

    # Match target standard
    target_std, _ = verified_knowledge_selector.match_standard_in_query(sanitized_q)
    target_std = target_std or state.get("target_standard_number") or "IS 302-2-201:2008"
    state["target_standard_number"] = target_std

    std_data = VERIFIED_STANDARDS_CATALOG.get(target_std, {})
    state["target_standard_title"] = std_data.get("title", "")

    intent_val = state.get("user_intent", OrchestratorIntent.QUERY_REQUIREMENT.value)
    # Retrieval required for requirements, gaps, audit traces
    retrieval_required = intent_val in (
        OrchestratorIntent.QUERY_REQUIREMENT.value,
        OrchestratorIntent.EXPLAIN_GAP.value,
        OrchestratorIntent.AUDIT_TRACE.value,
    ) or any(w in sanitized_q.lower() for w in ["clause", "is ", "standard", "test", "limit", "gap"])

    state["retrieval_required"] = retrieval_required
    state["task_type"] = intent_val

    _record_trace(state, "task_router", t0)
    return state


# ------------------------------------------------------------------------------
# Node 4: Retrieval Agent
# ------------------------------------------------------------------------------
def retrieval_agent_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Retrieves verified standard clauses and specifications from Layer 4/6."""
    t0 = time.time()
    target_std = state.get("target_standard_number", "IS 302-2-201:2008")
    sanitized_q = state.get("sanitized_query", "")

    std_data = VERIFIED_STANDARDS_CATALOG.get(target_std, {})
    clauses_dict = std_data.get("clauses", {})

    retrieved: List[Dict[str, Any]] = []
    import re
    m_cl = re.search(r"\bclause\s*(\d+(?:\.\d+)+)\b", sanitized_q.lower())
    if m_cl:
        cl_num = m_cl.group(1)
        if cl_num in clauses_dict:
            cl_info = clauses_dict[cl_num]
            retrieved.append({
                "clause_number": cl_num,
                "clause_title": cl_info.get("title", ""),
                "requirement_text": cl_info.get("req", ""),
                "standard_number": target_std,
                "verified": True,
            })
    else:
        # Return all cataloged clauses for this standard
        for cnum, cdata in clauses_dict.items():
            retrieved.append({
                "clause_number": cnum,
                "clause_title": cdata.get("title", ""),
                "requirement_text": cdata.get("req", ""),
                "standard_number": target_std,
                "verified": True,
            })

    state["retrieved_candidate_clauses"] = retrieved
    _record_trace(state, "retrieval_agent", t0)
    return state


# ------------------------------------------------------------------------------
# Node 5: Evidence Validation Gate
# ------------------------------------------------------------------------------
def evidence_validation_gate_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Validates provided evidence records against Layer 8 provenance gates."""
    t0 = time.time()
    target_std = state.get("target_standard_number", "")
    avail_evs = state.get("available_evidence_ids", [])

    # Check unverified standard
    if target_std and target_std not in VERIFIED_STANDARDS_CATALOG:
        state["evidence_status"] = "NO_VERIFIED_SOURCE"
        state["unverified_claims_blocked"] = [f"Standard {target_std} is unverified"]
        _record_trace(state, "evidence_validation_gate", t0)
        return state

    # Check conflict flag
    if state.get("expert_review_required"):
        state["evidence_status"] = "CONFLICT"
        _record_trace(state, "evidence_validation_gate", t0)
        return state

    if avail_evs:
        state["evidence_status"] = "VERIFIED"
    else:
        state["evidence_status"] = "NO_VERIFIED_SOURCE"

    _record_trace(state, "evidence_validation_gate", t0)
    return state


# ------------------------------------------------------------------------------
# Node 6: Analysis Agent
# ------------------------------------------------------------------------------
def analysis_agent_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Invokes langchain_chat_adapter (wrapping single_structured_llm) for language analysis."""
    t0 = time.time()
    intent_val = state.get("user_intent", OrchestratorIntent.QUERY_REQUIREMENT.value)
    intent = OrchestratorIntent(intent_val) if intent_val in OrchestratorIntent._value2member_map_ else OrchestratorIntent.QUERY_REQUIREMENT
    sanitized_q = state.get("sanitized_query", "")
    target_std = state.get("target_standard_number", "IS 302-2-201:2008")

    dna = state.get("product_dna")
    context = context_builder.build_context(
        product_dna=dna,
        verified_standard=target_std,
        retrieved_clauses=state.get("retrieved_candidate_clauses"),
        available_evidence=state.get("verified_evidence_records"),
    )

    try:
        response: OrchestratedAIResponse = langchain_chat_adapter.generate_orchestrated_response(
            intent=intent,
            sanitized_query=sanitized_q,
            context=context,
        )
        state["analysis_explanation"] = response.answer
        state["grounding_status"] = response.grounding_status.value
        state["final_response"] = response.model_dump()
    except Exception as exc:
        logger.error(f"[LangGraph:AnalysisAgent] Generation error: {exc}")
        state["errors"] = state.get("errors", []) + [str(exc)]
        state["analysis_explanation"] = "An error occurred during analysis generation. Fallback enforced."
        state["grounding_status"] = GroundingStatus.UNKNOWN.value

    _record_trace(state, "analysis_agent", t0)
    return state


# ------------------------------------------------------------------------------
# Node 7: Deterministic Compliance Gate
# ------------------------------------------------------------------------------
def deterministic_compliance_gate_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Authoritative downstream compliance calculation. LLM authority remains 0%."""
    t0 = time.time()

    # Invariant enforcement
    state["regulatory_conclusion"] = "NONE"
    state["llm_compliance_authority"] = 0.0

    retrieved = state.get("retrieved_candidate_clauses", [])
    ev_status = state.get("evidence_status", "NO_VERIFIED_SOURCE")

    unsatisfied = []
    for cl in retrieved:
        if ev_status != "VERIFIED":
            unsatisfied.append({
                "clause_number": cl.get("clause_number"),
                "clause_title": cl.get("clause_title"),
                "gap_reason": "No verified laboratory test report or evidence record attached.",
                "action": "REQUIRES_TESTING",
            })

    state["unsatisfied_clauses"] = unsatisfied
    state["gap_analysis_summary"] = {
        "total_evaluated": len(retrieved),
        "unsatisfied_count": len(unsatisfied),
        "authority": "Deterministic Downstream Gate (Layers 5 & 7)",
    }

    _record_trace(state, "deterministic_compliance_gate", t0)
    return state


# ------------------------------------------------------------------------------
# Node 8: Planning Agent
# ------------------------------------------------------------------------------
def planning_agent_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Converts deterministic gaps into concrete, actionable steps."""
    t0 = time.time()
    unsatisfied = state.get("unsatisfied_clauses", [])
    target_std = state.get("target_standard_number", "IS 302-2-201:2008")

    plan_items = []
    for item in unsatisfied:
        cnum = item.get("clause_number", "")
        plan_items.append({
            "step": f"Acquire test certificate for Clause {cnum}",
            "clause": cnum,
            "required_evidence": "Accredited NABL Test Report",
            "standard": target_std,
        })

    state["action_plan_items"] = plan_items
    _record_trace(state, "planning_agent", t0)
    return state


# ------------------------------------------------------------------------------
# Node 9: Output Integrity Gate
# ------------------------------------------------------------------------------
def output_integrity_gate_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Final Layer 9 validation: Strips illegal verdicts, enforces citations & zero authority."""
    t0 = time.time()
    raw_payload = state.get("final_response") or {}
    raw_answer = raw_payload.get("answer", state.get("analysis_explanation", ""))
    target_std = state.get("target_standard_number", "IS 302-2-201:2008")

    # Sanitize any attempted compliance declarations
    sanitized_answer, stripped = grounding_guard.sanitize_regulatory_assertions(raw_answer)

    # Validate citations
    verified_citations, suppressed = grounding_guard.validate_citations(
        text=sanitized_answer,
        target_standard=target_std,
    )

    intent_val = state.get("user_intent", OrchestratorIntent.QUERY_REQUIREMENT.value)
    intent = OrchestratorIntent(intent_val) if intent_val in OrchestratorIntent._value2member_map_ else OrchestratorIntent.QUERY_REQUIREMENT
    confidence = raw_payload.get("confidence_score", 0.95)
    g_status_val = state.get("grounding_status", GroundingStatus.SUPPORTED.value)
    g_status = GroundingStatus(g_status_val) if g_status_val in GroundingStatus._value2member_map_ else GroundingStatus.SUPPORTED

    if stripped or suppressed or state.get("unverified_claims_blocked"):
        g_status = GroundingStatus.NOT_IN_KNOWLEDGE_BASE
        confidence = 0.0

    final_resp = OrchestratedAIResponse(
        answer=sanitized_answer,
        intent=intent,
        grounding_status=g_status,
        confidence_score=confidence,
        citations=verified_citations,
        missing_information_notes=raw_payload.get("missing_information_notes"),
        expert_review_recommended=state.get("expert_review_required", False),
        deterministic_fallback_used=raw_payload.get("deterministic_fallback_used", False) or (confidence == 0.0),
        regulatory_conclusion="NONE",  # Cardinal Invariant: LLM / LangGraph has zero compliance authority
    )

    state["regulatory_conclusion"] = "NONE"
    state["llm_compliance_authority"] = 0.0
    state["final_response"] = final_resp.model_dump()

    _record_trace(state, "output_integrity_gate", t0)
    return state
