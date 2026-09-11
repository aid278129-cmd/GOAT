"""LangGraph Canonical Nodes for Layer 3 AI Orchestrator (Milestones M24.2, M24.3 & M24.4.1).

Architecture:
1. request_understanding
2. product_dna_check
3. task_router
4. retrieval_agent (invokes controlled search_bis_standards / search_bis_clauses tools)
5. evidence_validation_gate (invokes get_verified_evidence tool)
6. analysis_agent (invokes normalize_unit tool and langchain_chat_adapter, with deterministic short-circuiting)
7. deterministic_compliance_gate
8. planning_agent (invokes get_product_facts tool)
9. output_integrity_gate
Auxiliary Terminals:
- controlled_refusal
- clarification_request

M24.4.1 Enhancements:
- Strongly typed node contracts for every agent/gate.
- Duplicate tool call prevention with caching and deduplication accounting.
- Deterministic short-circuiting for unit conversion and pre-computed deterministic gaps.
- Minimal context construction with query-focused clause pruning.
- Explicit AI_DERIVED / CANDIDATE tagging for all AI reasoning outputs.
- Comprehensive runtime efficiency metrics.
"""

import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.app.services.orchestrator.graph.state import (
    BISComplianceGraphState,
    NodeExecutionTrace,
    ToolExecutionTrace,
    RequestUnderstandingContract,
    ProductDNAContract,
    TaskRouterContract,
    RetrievalAgentContract,
    EvidenceGateContract,
    AnalysisAgentContract,
    DeterministicGateContract,
    PlanningAgentContract,
    OutputIntegrityContract,
)
from backend.app.services.orchestrator.schemas import (
    OrchestratorIntent,
    GroundingStatus,
    OrchestratedAIResponse,
    CitationItem,
    OrchestratorContext,
)
from backend.app.services.orchestrator.intent_router import intent_router
from backend.app.services.orchestrator.query_agent import query_agent
from backend.app.services.orchestrator.knowledge_selector import (
    verified_knowledge_selector,
    VERIFIED_STANDARDS_CATALOG,
)
from backend.app.services.orchestrator.context_builder import context_builder
from backend.app.services.orchestrator.grounding_guard import grounding_guard
from backend.app.services.orchestrator.langchain_adapter import langchain_chat_adapter
from backend.app.services.orchestrator.llm_interface import single_structured_llm
from backend.app.services.orchestrator.tools import (
    tool_registry,
    ToolSecurityError,
)
from backend.app.services.compliance import (
    AuthorityLevel,
    AuthoritySource,
    DecisionType,
    AuthoritativeRecord,
    AuthorityFirewallViolation,
    compliance_firewall,
    authority_audit_logger,
)
from backend.app.core.logging import logger

# Maximum allowed tool calls per graph run to prevent runaway loops
MAX_TOOL_CALLS_PER_RUN = 10


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


def _execute_controlled_tool(
    state: BISComplianceGraphState,
    node_name: str,
    tool_name: str,
    tool_input: Dict[str, Any],
    role: str,
) -> Any:
    """Safely executes a tool with deduplication, execution limits, role permission enforcement, and audit tracking."""
    # Deduplication & Caching check
    tool_cache = state.get("tool_cache")
    if tool_cache is None:
        tool_cache = {}
        state["tool_cache"] = tool_cache

    try:
        cache_key = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
    except Exception:
        cache_key = f"{tool_name}:{str(tool_input)}"

    if cache_key in tool_cache:
        # Prevent duplicate execution
        cached_result = tool_cache[cache_key]
        state["duplicate_tool_calls_prevented"] = state.get("duplicate_tool_calls_prevented", 0) + 1
        
        tool_trace: ToolExecutionTrace = {
            "tool_name": tool_name,
            "tool_call_id": f"CACHED-{uuid.uuid4().hex[:6].upper()}",
            "node_name": node_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 0.0,
            "input_summary": str(list(tool_input.keys())),
            "status": "CACHED",
            "error": None,
            "cached": True,
        }
        t_traces = state.get("tool_traces", [])
        t_traces.append(tool_trace)
        state["tool_traces"] = t_traces
        return cached_result

    current_count = state.get("tool_call_count", 0)
    if current_count >= MAX_TOOL_CALLS_PER_RUN:
        logger.warning(f"[LangGraphToolGuard] Tool call limit exceeded ({MAX_TOOL_CALLS_PER_RUN}). Rejecting '{tool_name}'.")
        raise ToolSecurityError(f"Execution Limit Exceeded: Maximum of {MAX_TOOL_CALLS_PER_RUN} tool calls reached.")

    t0 = time.time()
    call_id = f"TOOL-{uuid.uuid4().hex[:6].upper()}"
    status = "SUCCESS"
    err_str = None
    res = None

    try:
        res = tool_registry.execute_tool(tool_name, tool_input, role=role)
        state["tool_call_count"] = current_count + 1
        # Store in deduplication cache
        tool_cache[cache_key] = res
    except Exception as exc:
        status = "FAILED"
        err_str = str(exc)
        logger.error(f"[LangGraphTool] Tool execution error for {tool_name}: {exc}")
        raise exc
    finally:
        duration = round((time.time() - t0) * 1000, 2)
        tool_trace: ToolExecutionTrace = {
            "tool_name": tool_name,
            "tool_call_id": call_id,
            "node_name": node_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration,
            "input_summary": str(list(tool_input.keys())),
            "status": status,
            "error": err_str,
            "cached": False,
        }
        t_traces = state.get("tool_traces", [])
        t_traces.append(tool_trace)
        state["tool_traces"] = t_traces

    return res


def _detect_unit_conversion_query(query: str) -> Optional[Dict[str, Any]]:
    """Detects if query asks for a deterministic engineering unit conversion."""
    q = query.strip()
    # Pattern: convert|normalize <num> <from_unit> to|in <to_unit>
    m1 = re.search(r"(?:convert|normalize)\s+([0-9.]+)\s*([a-zA-Z°]+)\s+(?:to|in)\s*([a-zA-Z°]+)", q, re.IGNORECASE)
    if m1:
        try:
            return {"value": float(m1.group(1)), "from_unit": m1.group(2).strip(), "to_unit": m1.group(3).strip()}
        except ValueError:
            pass
    # Pattern: <num> <from_unit> to <to_unit> (e.g. 100 F to C)
    m2 = re.search(r"\b([0-9.]+)\s*(fahrenheit|celsius|[fc]|w|kw|v|kv|a|ma)\s+(?:to|in)\s*([a-zA-Z°]+)\b", q, re.IGNORECASE)
    if m2:
        try:
            return {"value": float(m2.group(1)), "from_unit": m2.group(2).strip(), "to_unit": m2.group(3).strip()}
        except ValueError:
            pass
    return None


# ------------------------------------------------------------------------------
# Node 1: Request Understanding
# ------------------------------------------------------------------------------
def request_understanding_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Sanitizes query, classifies intent, decomposes tasks, detects ambiguity and adversarial injection."""
    t0 = time.time()
    user_q = state.get("user_query", "")
    prod_dna = state.get("product_dna")

    # M24.4.3A Advanced Query Agent execution
    understanding = query_agent.understand_query(user_q, product_dna=prod_dna)

    security_flag = (not understanding.is_safe) or (understanding.intent == OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT) or len(understanding.security_flags) > 0 or understanding.out_of_domain

    if understanding.out_of_domain:
        security_reason = "Out-of-domain request intercepted (outside BIS regulatory scope)"
    elif security_flag:
        security_reason = "Adversarial prompt injection / override attempt intercepted"
    else:
        security_reason = None

    state["sanitized_query"] = understanding.normalized_query
    state["user_intent"] = understanding.intent.value
    state["security_flag"] = security_flag
    state["security_reason"] = security_reason
    state["security_warnings"] = understanding.security_flags
    state["out_of_domain"] = understanding.out_of_domain
    state["request_type"] = understanding.request_type.value
    state["query_complexity"] = understanding.complexity.value
    state["query_understanding"] = understanding.model_dump()
    state["decomposed_tasks"] = [t.model_dump() for t in understanding.task_list]
    state["retrieval_hints"] = [h.model_dump() for h in understanding.retrieval_hints]

    # Propagate explicit standard to state if not yet set
    if understanding.explicit_standard_refs and not state.get("target_standard_number"):
        state["target_standard_number"] = understanding.explicit_standard_refs[0]

    # Typed contract (backwards-compatible with M24.4.1 while exposing M24.4.3A upgrades)
    contract = RequestUnderstandingContract(
        sanitized_query=understanding.normalized_query,
        user_intent=understanding.intent.value,
        security_flag=security_flag,
        security_reason=security_reason,
        security_warnings=understanding.security_flags,
        query_understanding=understanding.model_dump(),
        request_type=understanding.request_type.value,
        complexity=understanding.complexity.value,
        task_count=len(understanding.task_list),
        clarification_required=understanding.clarification_required,
        missing_information=understanding.missing_information,
        extracted_standards=understanding.explicit_standard_refs,
        extracted_clauses=understanding.explicit_clause_refs,
        retrieval_hints=[f"{h.hint_type}:{h.value}" for h in understanding.retrieval_hints],
        confidence=understanding.confidence,
        authority="AI_DERIVED",
    )
    contracts = state.get("node_contracts", {})
    contracts["request_understanding"] = contract.model_dump()
    state["node_contracts"] = contracts

    _record_trace(state, "request_understanding", t0)
    return state


# ------------------------------------------------------------------------------
# Auxiliary Terminal: Controlled Refusal
# ------------------------------------------------------------------------------
def controlled_refusal_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Returns safe, zero-authority refusal response when security violation or out-of-domain occurs."""
    t0 = time.time()
    if state.get("out_of_domain", False):
        refusal_response = OrchestratedAIResponse(
            answer=(
                "I am a specialized Bureau of Indian Standards (BIS) compliance assistant. "
                "I can only assist with Indian Standards, technical regulations, Quality Control Orders (QCOs), "
                "laboratory test reports, and compliance verification. The requested topic is outside my operational domain."
            ),
            intent=OrchestratorIntent.UNKNOWN_INTENT,
            grounding_status=GroundingStatus.SUPPORTED,
            confidence_score=1.0,
            citations=[],
            deterministic_fallback_used=True,
            regulatory_conclusion="NONE",
        )
        short_reason = "OUT_OF_DOMAIN"
    else:
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
        short_reason = "SECURITY_REFUSAL"

    state["regulatory_conclusion"] = "NONE"
    state["llm_compliance_authority"] = 0.0
    state["final_response"] = refusal_response.model_dump()
    state["short_circuited"] = True
    state["short_circuit_reason"] = short_reason

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
    facts_count = 0

    if dna is None:
        dna_sufficient = True
    elif isinstance(dna, dict):
        facts_count = len(dna.get("facts", []))
        if not dna.get("product_name") and not dna.get("category"):
            dna_sufficient = False
            missing_attrs = ["product_name", "category"]
    elif hasattr(dna, "product_name"):
        facts_count = len(getattr(dna, "facts", []))
        if not dna.product_name and not getattr(dna, "category", None):
            dna_sufficient = False
            missing_attrs = ["product_name", "category"]

    state["dna_sufficient"] = dna_sufficient
    state["missing_attributes"] = missing_attrs

    # Typed contract
    contract = ProductDNAContract(
        dna_sufficient=dna_sufficient,
        missing_attributes=missing_attrs,
        identified_facts_count=facts_count,
    )
    contracts = state.get("node_contracts", {})
    contracts["product_dna_check"] = contract.model_dump()
    state["node_contracts"] = contracts

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
    state["short_circuited"] = True
    state["short_circuit_reason"] = "INSUFFICIENT_PRODUCT_DNA"

    _record_trace(state, "clarification_request", t0)
    return state


# ------------------------------------------------------------------------------
# Node 3: Task Router
# ------------------------------------------------------------------------------
def task_router_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Deterministically identifies target standard, checks for short-circuits, and routes."""
    t0 = time.time()
    sanitized_q = state.get("sanitized_query", "")

    # Match target standard
    target_std, _ = verified_knowledge_selector.match_standard_in_query(sanitized_q)
    target_std = target_std or state.get("target_standard_number") or "IS 302-2-201:2008"
    state["target_standard_number"] = target_std

    std_data = VERIFIED_STANDARDS_CATALOG.get(target_std, {})
    state["target_standard_title"] = std_data.get("title", "")

    intent_val = state.get("user_intent", OrchestratorIntent.QUERY_REQUIREMENT.value)

    # Optimization: Detect deterministic unit conversion query
    unit_conv = _detect_unit_conversion_query(sanitized_q)
    deterministic_short_circuit = False
    short_circuit_handler = None

    if unit_conv:
        deterministic_short_circuit = True
        short_circuit_handler = "DETERMINISTIC_UNIT_CONVERSION"
        state["short_circuited"] = True
        state["short_circuit_reason"] = "DETERMINISTIC_UNIT_CONVERSION"
        retrieval_required = False
    elif state.get("gap_analysis_summary") and len(state.get("retrieved_candidate_clauses", [])) > 0:
        # Pre-computed gap already supplied
        deterministic_short_circuit = True
        short_circuit_handler = "PRECOMPUTED_DETERMINISTIC_GAP"
        state["short_circuited"] = True
        state["short_circuit_reason"] = "PRECOMPUTED_DETERMINISTIC_GAP"
        retrieval_required = False
    else:
        q_tokens = set(re.findall(r"\b[a-z0-9-]+\b", sanitized_q.lower()))
        retrieval_required = intent_val in (
            OrchestratorIntent.QUERY_REQUIREMENT.value,
            OrchestratorIntent.EXPLAIN_GAP.value,
            OrchestratorIntent.AUDIT_TRACE.value,
        ) or bool(q_tokens & {"clause", "is", "standard", "test", "limit", "gap"})

    state["retrieval_required"] = retrieval_required
    state["task_type"] = intent_val

    # Typed contract
    contract = TaskRouterContract(
        target_standard_number=target_std,
        target_standard_title=state["target_standard_title"],
        retrieval_required=retrieval_required,
        task_type=intent_val,
        deterministic_short_circuit=deterministic_short_circuit,
        short_circuit_handler=short_circuit_handler,
    )
    contracts = state.get("node_contracts", {})
    contracts["task_router"] = contract.model_dump()
    state["node_contracts"] = contracts

    _record_trace(state, "task_router", t0)
    return state


# ------------------------------------------------------------------------------
# Node 4: Retrieval Agent (Uses Controlled Tools)
# ------------------------------------------------------------------------------
def retrieval_agent_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Retrieves verified standard clauses and specifications using search_bis_clauses tool."""
    t0 = time.time()
    target_std = state.get("target_standard_number", "IS 302-2-201:2008")
    sanitized_q = state.get("sanitized_query", "")

    existing_clauses = state.get("retrieved_candidate_clauses", [])
    retrieved: List[Dict[str, Any]] = []
    from_cache = False

    # Optimization: If clauses are already pre-populated for this target standard, reuse them
    if existing_clauses and any(c.get("standard_number") == target_std for c in existing_clauses):
        retrieved = existing_clauses
        from_cache = True
        state["duplicate_tool_calls_prevented"] = state.get("duplicate_tool_calls_prevented", 0) + 1
    else:
        # Controlled Tool Call: search_bis_clauses
        try:
            state["retrieval_call_count"] = state.get("retrieval_call_count", 0) + 1
            tool_res = _execute_controlled_tool(
                state=state,
                node_name="retrieval_agent",
                tool_name="search_bis_clauses",
                tool_input={"standard_number": target_std, "query": sanitized_q, "top_k": 10},
                role="retrieval_agent",
            )
            for cl in tool_res.clauses:
                retrieved.append({
                    "clause_number": cl.clause_number,
                    "clause_title": cl.clause_title,
                    "requirement_text": cl.requirement_text,
                    "standard_number": cl.standard_number,
                    "verified": cl.verified,
                })
        except Exception as exc:
            logger.error(f"[RetrievalAgent] Tool execution failed: {exc}")
            state["errors"] = state.get("errors", []) + [str(exc)]

    state["retrieved_candidate_clauses"] = retrieved

    # Typed contract
    contract = RetrievalAgentContract(
        standard_number=target_std,
        retrieved_clauses_count=len(retrieved),
        candidate_clauses=retrieved,
        from_cache=from_cache,
    )
    contracts = state.get("node_contracts", {})
    contracts["retrieval_agent"] = contract.model_dump()
    state["node_contracts"] = contracts

    _record_trace(state, "retrieval_agent", t0)
    return state


# ------------------------------------------------------------------------------
# Node 5: Evidence Validation Gate (Uses Controlled Tools)
# ------------------------------------------------------------------------------
def evidence_validation_gate_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Validates evidence records against Layer 8 using get_verified_evidence tool."""
    t0 = time.time()
    target_std = state.get("target_standard_number", "")
    avail_evs = state.get("available_evidence_ids", [])

    if target_std and target_std not in VERIFIED_STANDARDS_CATALOG:
        state["evidence_status"] = "NO_VERIFIED_SOURCE"
        state["unverified_claims_blocked"] = [f"Standard {target_std} is unverified"]
        
        contract = EvidenceGateContract(
            evidence_status="NO_VERIFIED_SOURCE",
            verified_evidence_count=0,
            unverified_claims_blocked=state["unverified_claims_blocked"],
        )
        contracts = state.get("node_contracts", {})
        contracts["evidence_validation_gate"] = contract.model_dump()
        state["node_contracts"] = contracts

        _record_trace(state, "evidence_validation_gate", t0)
        return state

    if state.get("expert_review_required"):
        state["evidence_status"] = "CONFLICT"
        contract = EvidenceGateContract(
            evidence_status="CONFLICT",
            verified_evidence_count=0,
            unverified_claims_blocked=[],
        )
        contracts = state.get("node_contracts", {})
        contracts["evidence_validation_gate"] = contract.model_dump()
        state["node_contracts"] = contracts
        _record_trace(state, "evidence_validation_gate", t0)
        return state

    if avail_evs:
        try:
            ev_output = _execute_controlled_tool(
                state=state,
                node_name="evidence_validation_gate",
                tool_name="get_verified_evidence",
                tool_input={"evidence_ids": avail_evs, "standard_number": target_std},
                role="analysis_agent",
            )
            state["verified_evidence_records"] = [r.model_dump() for r in ev_output.records]
            state["unverified_claims_blocked"] = ev_output.unverified_suppressed
            state["evidence_status"] = "VERIFIED" if ev_output.total_verified > 0 else "UNVERIFIED"
        except Exception as exc:
            logger.error(f"[EvidenceValidationGate] Tool error: {exc}")
            state["evidence_status"] = "UNVERIFIED"
    else:
        state["evidence_status"] = "NO_VERIFIED_SOURCE"

    contract = EvidenceGateContract(
        evidence_status=state["evidence_status"],
        verified_evidence_count=len(state.get("verified_evidence_records", [])),
        unverified_claims_blocked=state.get("unverified_claims_blocked", []),
    )
    contracts = state.get("node_contracts", {})
    contracts["evidence_validation_gate"] = contract.model_dump()
    state["node_contracts"] = contracts

    _record_trace(state, "evidence_validation_gate", t0)
    return state


# ------------------------------------------------------------------------------
# Node 6: Analysis Agent (Specialized Reasoning with Deterministic Short-Circuit)
# ------------------------------------------------------------------------------
def analysis_agent_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Invokes langchain_chat_adapter for language analysis, or short-circuits deterministically."""
    t0 = time.time()
    # Snapshot deterministic fields to prevent AI mutation
    preserved_app = state.get("applicability_decision")
    preserved_gap = state.get("gap_analysis_summary")
    preserved_unsat = state.get("unsatisfied_clauses")
    preserved_ev = state.get("verified_evidence_records")
    preserved_auth = state.get("authority_records", [])

    intent_val = state.get("user_intent", OrchestratorIntent.QUERY_REQUIREMENT.value)
    intent = OrchestratorIntent(intent_val) if intent_val in OrchestratorIntent._value2member_map_ else OrchestratorIntent.QUERY_REQUIREMENT
    sanitized_q = state.get("sanitized_query", "")
    target_std = state.get("target_standard_number", "IS 302-2-201:2008")

    llm_called = False
    context_size = 0

    # Optimization 1: Deterministic Unit Conversion Short-Circuit
    unit_conv = _detect_unit_conversion_query(sanitized_q)
    if unit_conv or state.get("short_circuit_reason") == "DETERMINISTIC_UNIT_CONVERSION":
        unit_info = unit_conv or {"value": 0.0, "from_unit": "", "to_unit": ""}
        val = unit_info.get("value", 0.0)
        from_u = unit_info.get("from_unit", "")
        to_u = unit_info.get("to_unit", "")
        try:
            norm_res = _execute_controlled_tool(
                state=state,
                node_name="analysis_agent",
                tool_name="normalize_unit",
                tool_input={"value": val, "from_unit": from_u, "to_unit": to_u},
                role="analysis_agent",
            )
            conv_val = norm_res.converted_value
            f_unit = norm_res.to_unit
            clean_answer = (
                f"Deterministic Unit Conversion: {val} {from_u} = {conv_val} {f_unit}. "
                f"Computed deterministically via gap analysis engineering unit engine."
            )
        except Exception as exc:
            logger.error(f"[AnalysisAgent] Unit normalization failed: {exc}")
            clean_answer = f"Unit conversion error: {exc}"

        state["analysis_explanation"] = clean_answer
        state["grounding_status"] = GroundingStatus.SUPPORTED.value
        state["final_response"] = {
            "answer": clean_answer,
            "intent": intent_val,
            "grounding_status": GroundingStatus.SUPPORTED.value,
            "confidence_score": 1.0,
            "citations": [],
            "deterministic_fallback_used": True,
            "regulatory_conclusion": "NONE",
        }
        state["short_circuited"] = True
        state["short_circuit_reason"] = "DETERMINISTIC_UNIT_CONVERSION"

    # Optimization 2: Pre-computed Deterministic Gap Short-Circuit
    elif state.get("short_circuit_reason") == "PRECOMPUTED_DETERMINISTIC_GAP" and preserved_gap:
        total_eval = preserved_gap.get("total_evaluated", 0)
        unsat_cnt = preserved_gap.get("unsatisfied_count", 0)
        clean_answer = (
            f"Evaluated {total_eval} clauses against standard {target_std}. "
            f"{unsat_cnt} clauses are unsatisfied due to missing verified laboratory test evidence. "
            f"Compliance status is deterministically computed by Layer 7."
        )
        state["analysis_explanation"] = clean_answer
        state["grounding_status"] = GroundingStatus.SUPPORTED.value
        state["final_response"] = {
            "answer": clean_answer,
            "intent": intent_val,
            "grounding_status": GroundingStatus.SUPPORTED.value,
            "confidence_score": 1.0,
            "citations": [CitationItem(standard_number=target_std, source_authority="Layer 7 Gap Engine").model_dump()],
            "deterministic_fallback_used": True,
            "regulatory_conclusion": "NONE",
        }

    # Standard Reasoning Path: Bounded minimal context + SingleStructuredLLM via LangChain adapter
    else:
        # Minimal Context Construction: Prune candidate clauses to the most relevant
        all_clauses = state.get("retrieved_candidate_clauses", [])
        pruned_clauses = all_clauses
        # If query specifies a clause number (e.g. 19.1), only include that clause in context
        c_nums = re.findall(r"\b\d+(?:\.\d+)*\b", sanitized_q)
        if c_nums:
            matched_clauses = [c for c in all_clauses if any(cn in c.get("clause_number", "") for cn in c_nums)]
            if matched_clauses:
                pruned_clauses = matched_clauses
        elif len(all_clauses) > 3:
            # Bound context to top 3 clauses
            pruned_clauses = all_clauses[:3]

        dna = state.get("product_dna")
        context = context_builder.build_context(
            product_dna=dna,
            verified_standard=target_std,
            retrieved_clauses=pruned_clauses,
            available_evidence=state.get("verified_evidence_records"),
        )
        context_str = str(context)
        context_size = len(context_str)
        state["context_size_chars"] = context_size

        try:
            state["llm_call_count"] = state.get("llm_call_count", 0) + 1
            llm_called = True
            response: OrchestratedAIResponse = langchain_chat_adapter.generate_orchestrated_response(
                intent=intent,
                sanitized_query=sanitized_q,
                context=context,
            )
            # Sanitize any pseudo-regulatory assertions from AI output
            clean_answer, stripped_claims = compliance_firewall.sanitize_untrusted_compliance_claims(response.answer)
            if stripped_claims:
                state["untrusted_ai_claims"] = state.get("untrusted_ai_claims", []) + stripped_claims

            state["analysis_explanation"] = clean_answer
            state["grounding_status"] = response.grounding_status.value
            state["final_response"] = response.model_dump()
            state["final_response"]["answer"] = clean_answer
        except Exception as exc:
            logger.error(f"[LangGraph:AnalysisAgent] Generation error: {exc}")
            state["errors"] = state.get("errors", []) + [str(exc)]
            state["analysis_explanation"] = "An error occurred during analysis generation. Fallback enforced."
            state["grounding_status"] = GroundingStatus.UNKNOWN.value

    # Typed contract
    contract = AnalysisAgentContract(
        analysis_explanation=state.get("analysis_explanation", ""),
        provenance="AI_DERIVED / CANDIDATE" if llm_called else "DETERMINISTIC_ENGINE",
        llm_called=llm_called,
        grounding_status=state.get("grounding_status", GroundingStatus.UNKNOWN.value),
        context_size_chars=context_size,
    )
    contracts = state.get("node_contracts", {})
    contracts["analysis_agent"] = contract.model_dump()
    state["node_contracts"] = contracts

    # Re-enforce deterministic state immutability against AI node tampering
    state["applicability_decision"] = preserved_app
    state["gap_analysis_summary"] = preserved_gap
    state["unsatisfied_clauses"] = preserved_unsat
    state["verified_evidence_records"] = preserved_ev
    state["authority_records"] = preserved_auth
    state["regulatory_conclusion"] = "NONE"
    state["llm_compliance_authority"] = 0.0

    _record_trace(state, "analysis_agent", t0)
    return state


# ------------------------------------------------------------------------------
# Node 7: Deterministic Compliance Gate
# ------------------------------------------------------------------------------
def deterministic_compliance_gate_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Authoritative downstream compliance calculation. LLM authority remains 0%."""
    t0 = time.time()

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
    gap_summary = {
        "total_evaluated": len(retrieved),
        "unsatisfied_count": len(unsatisfied),
        "authority": "Deterministic Downstream Gate (Layers 5 & 7)",
    }
    state["gap_analysis_summary"] = gap_summary

    # Authoritative record generation through Compliance Authority Firewall
    cid = state.get("correlation_id", f"RUN-{uuid.uuid4().hex[:8]}")
    total_eval = len(retrieved)
    unsatisfied_cnt = len(unsatisfied)
    det_status = "SATISFIED" if (total_eval > 0 and unsatisfied_cnt == 0 and ev_status == "VERIFIED") else "UNSATISFIED"
    try:
        auth_record = compliance_firewall.validate_compliance_authority(
            decision_type=DecisionType.GAP_EVALUATION,
            decision_value=det_status,
            source=AuthoritySource.LAYER_7_COMPLIANCE_GAP_ENGINE,
            source_layer=7,
            deterministic=True,
            correlation_id=cid,
            metadata={"total_evaluated": total_eval, "unsatisfied_count": unsatisfied_cnt},
        )
        authority_audit_logger.record_decision(auth_record)
        state["authority_records"] = state.get("authority_records", []) + [auth_record.model_dump()]
    except Exception as exc:
        logger.error(f"[DeterministicComplianceGate] Authority firewall error: {exc}")

    # Typed contract
    contract = DeterministicGateContract(
        total_evaluated=total_eval,
        unsatisfied_count=unsatisfied_cnt,
        authority_source="LAYER_7_COMPLIANCE_GAP_ENGINE",
        deterministic=True,
        llm_authority=0.0,
    )
    contracts = state.get("node_contracts", {})
    contracts["deterministic_compliance_gate"] = contract.model_dump()
    state["node_contracts"] = contracts

    _record_trace(state, "deterministic_compliance_gate", t0)
    return state


# ------------------------------------------------------------------------------
# Node 8: Planning Agent (Uses get_product_facts tool)
# ------------------------------------------------------------------------------
def planning_agent_node(state: BISComplianceGraphState) -> BISComplianceGraphState:
    """Converts deterministic gaps into concrete, actionable steps using get_product_facts."""
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

    # Typed contract
    contract = PlanningAgentContract(
        action_plan_items_count=len(plan_items),
        action_plan_items=plan_items,
        provenance="AI_DERIVED / CANDIDATE",
    )
    contracts = state.get("node_contracts", {})
    contracts["planning_agent"] = contract.model_dump()
    state["node_contracts"] = contracts

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

    sanitized_answer, stripped = grounding_guard.sanitize_regulatory_assertions(raw_answer)
    sanitized_answer, firewall_stripped = compliance_firewall.sanitize_untrusted_compliance_claims(sanitized_answer)
    if firewall_stripped:
        stripped = True
        state["untrusted_ai_claims"] = state.get("untrusted_ai_claims", []) + firewall_stripped

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
        regulatory_conclusion="NONE",
    )

    state["regulatory_conclusion"] = "NONE"
    state["llm_compliance_authority"] = 0.0
    state["final_response"] = final_resp.model_dump()

    # Typed contract
    contract = OutputIntegrityContract(
        sanitized=stripped or bool(firewall_stripped),
        citations_count=len(verified_citations),
        regulatory_conclusion="NONE",
        llm_compliance_authority=0.0,
    )
    contracts = state.get("node_contracts", {})
    contracts["output_integrity_gate"] = contract.model_dump()
    state["node_contracts"] = contracts

    _record_trace(state, "output_integrity_gate", t0)
    return state
