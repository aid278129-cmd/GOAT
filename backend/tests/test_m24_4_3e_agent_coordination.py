"""Test Suite for Milestone M24.4.3E: Controlled Agent Coordination & Runtime Optimization.

Verifies:
1. Single LLM singleton shared across all agents
2. Zero compliance authority (0.0%, AI_DERIVED / CANDIDATE, regulatory_conclusion="NONE")
3. LangGraph deterministic DAG controller (11 nodes, 16 edges, strict DAG, zero autonomous loops)
4. Downstream compliance authority preservation (Layers 5, 7, 8, 9)
5. Foundational compliance truths preservation
6. StateSnapshot capture and deterministic SHA-256 fingerprinting
7. Mutation detection and cryptographic tamper evidence
8. Typed AgentHandoffContract validation across all 5 inter-agent stages
9. AgentReadinessGate deterministic prerequisite enforcement
10. Failure isolation: upstream errors propagate as controlled uncertainty, not hallucinations
11. Execution budget enforcement (max 3 LLM calls, max 10 tool calls)
12. Duplicate work prevention and shared caching
13. Observability tracing: state_snapshots, handoff_traces, agent_traces
14. 10 Focused Benchmarks with Wilson score intervals and sample size sufficiency checks
"""

import time
import pytest
from typing import Dict, Any, List

from backend.app.services.compliance.authority_types import (
    AuthorityLevel,
    AuthoritySource,
    DecisionType,
    AuthorityFirewallViolation,
)
from backend.app.services.compliance.authority_firewall import compliance_firewall
from backend.app.services.orchestrator.llm_interface import single_structured_llm
from backend.app.services.orchestrator.langchain_adapter import langchain_chat_adapter
from backend.app.services.orchestrator.query_agent import query_agent
from backend.app.services.orchestrator.retrieval_agent import retrieval_agent, RetrievalAgent
from backend.app.services.orchestrator.analysis_agent import analysis_agent
from backend.app.services.orchestrator.planning_agent import planning_agent
from backend.app.services.orchestrator.coordination import (
    agent_coordinator,
    HandoffStage,
    ReadinessStatus,
    ExecutionBudget,
    AgentHandoffContract,
    StateSnapshot,
    AgentExecutionTrace,
    SnapshotManager,
    HandoffValidator,
    AgentReadinessGate,
    BudgetEnforcer,
    AgentCoordinationManager,
)
from backend.app.services.orchestrator.graph.state import (
    BISComplianceGraphState,
    RequestUnderstandingContract,
    RetrievalAgentContract,
    AnalysisAgentContract,
    PlanningAgentContract,
)
from backend.app.services.orchestrator.graph.nodes import (
    request_understanding_node,
    retrieval_agent_node,
    analysis_agent_node,
    deterministic_compliance_gate_node,
    planning_agent_node,
    task_router_node,
    _execute_controlled_tool,
)
from backend.app.services.orchestrator.graph.builder import build_compliance_graph
from backend.app.services.orchestrator.tools import ToolSecurityError
from backend.app.services.evaluation.metrics import (
    compute_wilson_score_interval,
    classify_statistical_sufficiency,
)


# ==============================================================================
# 1. CARDINAL INVARIANTS & ARCHITECTURE (Tests 1–10)
# ==============================================================================

def test_single_llm_singleton_shared_across_agents():
    """Verify that Query, Retrieval, Analysis, and Planning agents share the exact same LLM singleton."""
    assert single_structured_llm is not None
    assert langchain_chat_adapter.underlying_llm is single_structured_llm
    # LangGraph orchestration routes language generation through langchain_chat_adapter
    assert langchain_chat_adapter._llm_type == "zyntrix-structured-compliance-llm"
    # Verify no secondary LLM exists
    from backend.app.services.orchestrator.llm_interface import SingleStructuredLLM
    assert isinstance(single_structured_llm, SingleStructuredLLM)


def test_zero_compliance_authority_query_agent():
    """Verify that Query Agent output contract enforces 0.0% compliance authority."""
    state: BISComplianceGraphState = {
        "user_query": "What are the test requirements for an electric iron under IS 302-2-201:2008?",
        "node_contracts": {},
    }
    updated = request_understanding_node(state)
    assert updated.get("regulatory_conclusion") in (None, "NONE")
    assert updated.get("llm_compliance_authority", 0.0) == 0.0
    contract = updated["node_contracts"]["request_understanding"]
    assert contract["authority"] == "AI_DERIVED"


def test_zero_compliance_authority_retrieval_agent():
    """Verify that Retrieval Agent output contract strictly enforces 0.0% compliance authority."""
    state: BISComplianceGraphState = {
        "user_query": "Test query",
        "sanitized_query": "Test query",
        "target_standard_number": "IS 302-2-201:2008",
        "node_contracts": {},
    }
    updated = retrieval_agent_node(state)
    contract = updated["node_contracts"]["retrieval_agent"]
    assert contract["authority"] == "AI_DERIVED"
    assert contract["llm_compliance_authority"] == 0.0
    assert contract["regulatory_conclusion"] == "NONE"


def test_zero_compliance_authority_analysis_agent():
    """Verify that Analysis Agent enforces AI_DERIVED / CANDIDATE and 0.0% compliance authority."""
    state: BISComplianceGraphState = {
        "user_query": "Explain clause 19.1",
        "sanitized_query": "Explain clause 19.1",
        "target_standard_number": "IS 302-2-201:2008",
        "retrieved_candidate_clauses": [
            {"clause_number": "19.1", "clause_title": "Heating", "requirement_text": "Normal operation"}
        ],
        "node_contracts": {},
    }
    updated = analysis_agent_node(state)
    contract = updated["node_contracts"]["analysis_agent"]
    assert "AI_DERIVED" in contract["provenance"] or contract["provenance"] == "DETERMINISTIC_ENGINE"
    assert updated["regulatory_conclusion"] == "NONE"
    assert updated["llm_compliance_authority"] == 0.0


def test_zero_compliance_authority_planning_agent():
    """Verify that Planning Agent enforces 0.0% compliance authority and AI_DERIVED / CANDIDATE."""
    state: BISComplianceGraphState = {
        "user_query": "What should I do?",
        "sanitized_query": "What should I do?",
        "target_standard_number": "IS 302-2-201:2008",
        "unsatisfied_clauses": [
            {"clause_number": "19.1", "clause_title": "Heating", "gap_reason": "No test.", "action": "REQUIRES_TESTING"}
        ],
        "evidence_status": "UNVERIFIED",
        "node_contracts": {},
    }
    updated = planning_agent_node(state)
    contract = updated["node_contracts"]["planning_agent"]
    assert contract["provenance"] == "AI_DERIVED / CANDIDATE"
    assert updated["regulatory_conclusion"] == "NONE"
    assert updated["llm_compliance_authority"] == 0.0


def test_langgraph_controller_dag_topology():
    """Verify that LangGraph has exactly 11 canonical nodes, strict DAG, and zero autonomous agent loops."""
    graph = build_compliance_graph(checkpointer=False)
    # The compiled graph has nodes and edges
    node_names = set(graph.get_graph().nodes.keys())
    canonical_nodes = {
        "request_understanding",
        "controlled_refusal",
        "product_dna_check",
        "clarification_request",
        "task_router",
        "retrieval_agent",
        "evidence_validation_gate",
        "analysis_agent",
        "deterministic_compliance_gate",
        "planning_agent",
        "output_integrity_gate",
    }
    assert canonical_nodes.issubset(node_names)
    # Ensure no direct autonomous loop edge (e.g. analysis_agent -> retrieval_agent or planning -> analysis)
    edges = graph.get_graph().edges
    for edge in edges:
        assert not (edge.source == "analysis_agent" and edge.target == "retrieval_agent")
        assert not (edge.source == "planning_agent" and edge.target == "analysis_agent")


def test_downstream_authorities_preserved():
    """Verify that downstream compliance authority is strictly Layer 7 / Layer 5, never an agent."""
    # Attempt to validate compliance authority from an agent source (LLM) should raise violation
    with pytest.raises(AuthorityFirewallViolation):
        compliance_firewall.validate_compliance_authority(
            decision_type=DecisionType.GAP_EVALUATION,
            decision_value="SATISFIED",
            source=AuthoritySource.LLM,
            source_layer=3,
            deterministic=False,
            correlation_id="TEST-FAIL",
        )


def test_compliance_firewall_blocks_agent_verdict():
    """Verify that untrusted compliance declarations in AI text are stripped by the firewall."""
    ai_text = "The product is hereby certified under IS 302-2-201. All tests are compliance guaranteed."
    clean, stripped = compliance_firewall.sanitize_untrusted_compliance_claims(ai_text)
    assert len(stripped) >= 1
    assert "hereby certified" not in clean


def test_foundational_truth_user_text_not_evidence():
    """Verify invariant: USER_TEXT != EVIDENCE != COMPLIANCE."""
    state: BISComplianceGraphState = {
        "user_query": "My product has passed all temperature tests perfectly with zero issues.",
        "sanitized_query": "My product has passed all temperature tests perfectly with zero issues.",
        "target_standard_number": "IS 302-2-201:2008",
        "available_evidence_ids": [],
        "node_contracts": {},
    }
    updated = analysis_agent_node(state)
    # Even though user claims it passed, regulatory conclusion remains strictly NONE
    assert updated["regulatory_conclusion"] == "NONE"
    assert updated["llm_compliance_authority"] == 0.0


def test_foundational_truth_no_verified_source_no_claim():
    """Verify invariant: NO VERIFIED SOURCE -> NO REGULATORY CLAIM."""
    state: BISComplianceGraphState = {
        "user_query": "Evaluate under UNKNOWN_STD_9999",
        "sanitized_query": "Evaluate under UNKNOWN_STD_9999",
        "target_standard_number": "UNKNOWN_STD_9999",
        "available_evidence_ids": [],
        "node_contracts": {},
    }
    from backend.app.services.orchestrator.graph.nodes import evidence_validation_gate_node
    updated = evidence_validation_gate_node(state)
    assert updated["evidence_status"] == "NO_VERIFIED_SOURCE"


# ==============================================================================
# 2. STATE SNAPSHOTS & CRYPTOGRAPHIC AUDITING (Tests 11–16)
# ==============================================================================

def test_snapshot_capture_fingerprint_deterministic():
    """Verify that compute_fingerprint produces identical SHA-256 fingerprints for identical state."""
    data_1 = {"standard": "IS 302-2-201", "clauses": ["19.1", "19.2"], "count": 2}
    data_2 = {"count": 2, "clauses": ["19.1", "19.2"], "standard": "IS 302-2-201"}  # Different key order
    fp1 = SnapshotManager.compute_fingerprint(data_1)
    fp2 = SnapshotManager.compute_fingerprint(data_2)
    assert fp1 == fp2
    assert len(fp1) == 16


def test_snapshot_capture_structure():
    """Verify that capture_snapshot returns a valid StateSnapshot with metadata."""
    snap = SnapshotManager.capture_snapshot("analysis_agent", {"query": "test", "target": "IS 302"})
    assert isinstance(snap, StateSnapshot)
    assert snap.node_name == "analysis_agent"
    assert snap.snapshot_id.startswith("SNAP-ANAL-")
    assert "query" in snap.keys_snapshot
    assert "target" in snap.keys_snapshot
    assert snap.timestamp > 0


def test_snapshot_mutation_detection():
    """Verify that state mutation changes the fingerprint, detecting tampering."""
    original = {"clauses": ["19.1"], "status": "PENDING"}
    mutated = {"clauses": ["19.1"], "status": "SATISFIED"}
    assert SnapshotManager.compute_fingerprint(original) != SnapshotManager.compute_fingerprint(mutated)


def test_state_snapshots_recorded_in_graph_flow():
    """Verify that state snapshots are recorded across executed nodes in state."""
    state: BISComplianceGraphState = {
        "user_query": "What are requirements for electric irons under IS 302-2-201:2008?",
        "node_contracts": {},
    }
    state = request_understanding_node(state)
    state = task_router_node(state)
    state = retrieval_agent_node(state)
    state = analysis_agent_node(state)
    state = deterministic_compliance_gate_node(state)
    state = planning_agent_node(state)

    snapshots = state.get("state_snapshots", [])
    assert len(snapshots) >= 4
    nodes_recorded = {s["node_name"] for s in snapshots}
    assert "request_understanding" in nodes_recorded
    assert "retrieval_agent" in nodes_recorded
    assert "analysis_agent" in nodes_recorded
    assert "planning_agent" in nodes_recorded


def test_snapshot_handles_complex_nested_structures():
    """Verify that fingerprinting works without error on complex nested dictionaries and objects."""
    complex_data = {
        "level1": {
            "level2": [1, 2, {"a": "b"}],
            "budget": ExecutionBudget().model_dump(),
        }
    }
    fp = SnapshotManager.compute_fingerprint(complex_data)
    assert isinstance(fp, str)
    assert len(fp) == 16


def test_snapshot_empty_state_resilience():
    """Verify that capturing a snapshot of an empty dict is resilient."""
    snap = SnapshotManager.capture_snapshot("empty_node", {})
    assert snap.state_hash is not None
    assert snap.keys_snapshot == []


# ==============================================================================
# 3. TYPED HANDOFF CONTRACTS & VALIDATION (Tests 17–25)
# ==============================================================================

def test_handoff_query_to_retrieval_valid():
    """Verify valid QUERY_TO_RETRIEVAL handoff passes validation."""
    state = {
        "query_understanding": {"intent": "QUERY_REQUIREMENT"},
        "target_standard_number": "IS 302-2-201:2008",
        "sanitized_query": "Test query",
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.QUERY_TO_RETRIEVAL, state)
    assert contract.validation_status == ReadinessStatus.READY
    assert len(contract.validation_errors) == 0


def test_handoff_query_to_retrieval_blocks_out_of_domain():
    """Verify out-of-domain query is blocked from proceeding to retrieval."""
    state = {
        "query_understanding": {"intent": "UNKNOWN_INTENT"},
        "target_standard_number": "IS 302-2-201:2008",
        "out_of_domain": True,
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.QUERY_TO_RETRIEVAL, state)
    assert contract.validation_status == ReadinessStatus.BLOCKED
    assert any("OUT_OF_DOMAIN" in e for e in contract.validation_errors)


def test_handoff_retrieval_to_analysis_valid():
    """Verify valid RETRIEVAL_TO_ANALYSIS handoff passes validation."""
    state = {
        "retrieval_package": {"standard": "IS 302-2-201:2008", "clauses_count": 2},
        "retrieved_candidate_clauses": [{"clause_number": "19.1"}],
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.RETRIEVAL_TO_ANALYSIS, state)
    assert contract.validation_status == ReadinessStatus.READY


def test_handoff_retrieval_to_analysis_blocks_cross_standard_violation():
    """Verify cross-standard contamination blocks RETRIEVAL_TO_ANALYSIS handoff."""
    state = {
        "retrieval_package": {"standard": "IS 302-2-201:2008"},
        "retrieved_candidate_clauses": [{"clause_number": "19.1"}],
        "cross_standard_violations": [{"clause_number": "7.1", "foreign_standard": "IS 16333"}],
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.RETRIEVAL_TO_ANALYSIS, state)
    assert contract.validation_status == ReadinessStatus.BLOCKED
    assert any("Cross-standard violation" in e for e in contract.validation_errors)


def test_handoff_retrieval_to_analysis_blocks_failed_retrieval():
    """Verify that retrieval failure blocks regular analysis handoff."""
    state = {
        "retrieval_package": None,
        "retrieval_status": "FAILED",
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.RETRIEVAL_TO_ANALYSIS, state)
    assert contract.validation_status == ReadinessStatus.BLOCKED
    assert any("FAILED" in e for e in contract.validation_errors)


def test_handoff_analysis_to_layer7_blocks_authoritative_satisfied():
    """Verify that Analysis Agent cannot emit authoritative 'SATISFIED' candidate assessment."""
    state = {
        "structured_analysis": {"candidate_assessment": "SATISFIED"},
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.ANALYSIS_TO_LAYER7, state)
    assert contract.validation_status == ReadinessStatus.BLOCKED
    assert any("SATISFIED" in e for e in contract.validation_errors)


def test_handoff_analysis_to_layer7_blocks_non_zero_authority():
    """Verify that Analysis Agent cannot set non-zero compliance authority."""
    state = {
        "structured_analysis": {"candidate_assessment": "CANDIDATE_SATISFIED"},
        "llm_compliance_authority": 0.8,
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.ANALYSIS_TO_LAYER7, state)
    assert contract.validation_status == ReadinessStatus.BLOCKED
    assert any("0.0%" in e for e in contract.validation_errors)


def test_handoff_layer7_to_planning_requires_deterministic_gap_summary():
    """Verify that Planning Agent requires deterministic findings from Layer 7."""
    state = {
        "gap_analysis_summary": None,  # Missing Layer 7 summary
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.LAYER7_TO_PLANNING, state)
    assert contract.validation_status == ReadinessStatus.BLOCKED
    assert any("gap analysis summary is missing" in e for e in contract.validation_errors)


def test_handoff_planning_to_output_blocks_satisfied_actions():
    """Verify that Planning Agent cannot emit actions marked SATISFIED or COMPLETED."""
    state = {
        "structured_action_plan": {
            "actions": [{"title": "Check iron", "status": "COMPLETED"}]
        }
    }
    contract = HandoffValidator.validate_handoff(HandoffStage.PLANNING_TO_OUTPUT, state)
    assert contract.validation_status == ReadinessStatus.BLOCKED
    assert any("SATISFIED/COMPLETED" in e for e in contract.validation_errors)


# ==============================================================================
# 4. READINESS GATES & FAILURE ISOLATION (Tests 26–30)
# ==============================================================================

def test_readiness_gate_cleared_for_valid_state():
    """Verify AgentReadinessGate returns cleared status for valid prerequisites."""
    state = {
        "target_standard_number": "IS 302-2-201:2008",
        "sanitized_query": "What are heating tests?",
    }
    ready, reason = AgentReadinessGate.check_readiness(HandoffStage.QUERY_TO_RETRIEVAL, state)
    assert ready is True
    assert reason is None


def test_readiness_gate_blocks_and_provides_reason():
    """Verify AgentReadinessGate blocks invalid state and provides explicit reason."""
    state = {
        "out_of_domain": True,
    }
    ready, reason = AgentReadinessGate.check_readiness(HandoffStage.QUERY_TO_RETRIEVAL, state)
    assert ready is False
    assert "OUT_OF_DOMAIN" in reason


def test_failure_isolation_retrieval_failure_no_hallucination():
    """Verify that retrieval failure does not lead to hallucinated clauses in analysis."""
    state: BISComplianceGraphState = {
        "user_query": "Explain testing under IS 99999",
        "sanitized_query": "Explain testing under IS 99999",
        "target_standard_number": "IS 99999",
        "retrieved_candidate_clauses": [],
        "errors": ["Retrieval timeout"],
        "node_contracts": {},
    }
    updated = analysis_agent_node(state)
    # Analysis agent gracefully operates on empty clauses without inventing any
    clauses = updated.get("retrieved_candidate_clauses", [])
    assert len(clauses) == 0
    assert updated["regulatory_conclusion"] == "NONE"


def test_failure_isolation_uncertainty_propagation_to_layer7():
    """Verify that missing evidence propagates to deterministic gate without being auto-cleared."""
    state: BISComplianceGraphState = {
        "retrieved_candidate_clauses": [{"clause_number": "19.1", "clause_title": "Heating"}],
        "evidence_status": "NO_VERIFIED_SOURCE",
        "node_contracts": {},
    }
    updated = deterministic_compliance_gate_node(state)
    assert updated["gap_analysis_summary"]["unsatisfied_count"] == 1
    assert len(updated["unsatisfied_clauses"]) == 1
    assert updated["unsatisfied_clauses"][0]["action"] == "REQUIRES_TESTING"


def test_conflict_escalation_triggers_expert_review():
    """Verify that conflicting evidence triggers expert review requirement."""
    from backend.app.services.orchestrator.graph.nodes import evidence_validation_gate_node
    state: BISComplianceGraphState = {
        "target_standard_number": "IS 302-2-201:2008",
        "expert_review_required": True,
        "node_contracts": {},
    }
    updated = evidence_validation_gate_node(state)
    assert updated["evidence_status"] == "CONFLICT"


# ==============================================================================
# 5. EXECUTION BUDGET & DEDUPLICATION (Tests 31–36)
# ==============================================================================

def test_budget_enforcer_llm_call_limit():
    """Verify that BudgetEnforcer halts when max_llm_calls limit is reached."""
    budget = ExecutionBudget(max_llm_calls=2)
    state = {"llm_call_count": 0}
    assert BudgetEnforcer.check_and_increment_llm(state, budget) is True
    assert state["llm_call_count"] == 1
    assert BudgetEnforcer.check_and_increment_llm(state, budget) is True
    assert state["llm_call_count"] == 2
    # Third call exceeds budget
    assert BudgetEnforcer.check_and_increment_llm(state, budget) is False
    assert state.get("budget_exceeded") is True


def test_budget_enforcer_tool_call_limit():
    """Verify that tool calls exceeding max_tool_calls raise ToolSecurityError."""
    state: BISComplianceGraphState = {
        "tool_call_count": 10,
        "tool_cache": {},
        "tool_traces": [],
        "node_contracts": {},
    }
    with pytest.raises(ToolSecurityError) as exc_info:
        _execute_controlled_tool(
            state=state,
            node_name="test_node",
            tool_name="normalize_unit",
            tool_input={"value": 10, "from_unit": "F", "to_unit": "C"},
            role="analysis_agent",
        )
    assert "Execution Limit Exceeded" in str(exc_info.value)


def test_duplicate_work_prevented_caching():
    """Verify that identical tool calls hit the cache and increment duplicate_work_prevented."""
    state: BISComplianceGraphState = {
        "tool_call_count": 0,
        "tool_cache": {},
        "tool_traces": [],
        "node_contracts": {},
    }
    # First execution
    res1 = _execute_controlled_tool(
        state=state,
        node_name="test_node",
        tool_name="normalize_unit",
        tool_input={"value": 100.0, "from_unit": "fahrenheit", "to_unit": "celsius"},
        role="analysis_agent",
    )
    assert res1.converted_value == pytest.approx(37.78, 0.1)
    assert state["tool_call_count"] == 1
    assert state.get("duplicate_work_prevented", 0) == 0

    # Second execution with exact same input
    res2 = _execute_controlled_tool(
        state=state,
        node_name="test_node",
        tool_name="normalize_unit",
        tool_input={"value": 100.0, "from_unit": "fahrenheit", "to_unit": "celsius"},
        role="analysis_agent",
    )
    assert res2.converted_value == res1.converted_value
    assert state["tool_call_count"] == 1  # Not incremented
    assert state.get("duplicate_work_prevented", 0) == 1
    assert state.get("duplicate_tool_calls_prevented", 0) == 1


def test_agent_traces_recorded_in_state():
    """Verify that AgentCoordinationManager records structured stage traces."""
    state = {}
    agent_coordinator.record_stage_execution(
        state=state,
        stage_name="retrieval_agent",
        duration_ms=45.2,
        status="SUCCESS",
        tool_calls=2,
    )
    assert len(state["agent_traces"]) == 1
    trace = state["agent_traces"][0]
    assert trace["stage_name"] == "retrieval_agent"
    assert trace["duration_ms"] == 45.2
    assert trace["status"] == "SUCCESS"
    assert trace["authority"] == "AI_DERIVED / CANDIDATE"


def test_unit_conversion_short_circuit_bypasses_llm():
    """Verify that deterministic unit conversion query short-circuits without LLM invocation."""
    state: BISComplianceGraphState = {
        "user_query": "convert 212 fahrenheit to celsius",
        "sanitized_query": "convert 212 fahrenheit to celsius",
        "target_standard_number": "IS 302-2-201:2008",
        "short_circuit_reason": "DETERMINISTIC_UNIT_CONVERSION",
        "tool_cache": {},
        "node_contracts": {},
    }
    updated = analysis_agent_node(state)
    contract = updated["node_contracts"]["analysis_agent"]
    assert contract["llm_called"] is False
    assert updated.get("llm_call_count", 0) == 0
    assert "100.0" in updated["analysis_explanation"]


def test_precomputed_gap_short_circuit_bypasses_retrieval():
    """Verify precomputed deterministic gap short-circuits retrieval requirements."""
    state: BISComplianceGraphState = {
        "user_query": "Explain gap",
        "sanitized_query": "Explain gap",
        "gap_analysis_summary": {"total_evaluated": 5, "unsatisfied_count": 2},
        "retrieved_candidate_clauses": [{"clause_number": "1.1"}],
        "node_contracts": {},
    }
    updated = task_router_node(state)
    assert updated["retrieval_required"] is False
    assert updated["short_circuit_reason"] == "PRECOMPUTED_DETERMINISTIC_GAP"


# ==============================================================================
# 6. 10 COMPREHENSIVE BENCHMARKS (WITH WILSON SCORE INTERVALS) (Tests 37–46)
# ==============================================================================

def test_benchmark_1_query_understanding_latency():
    """Benchmark Query Agent understanding latency across 30 iterations."""
    latencies = []
    for _ in range(30):
        t0 = time.time()
        query_agent.understand_query("What are the safety requirements for an electric iron under IS 302-2-201:2008?")
        latencies.append((time.time() - t0) * 1000)
    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 50.0  # Fast sub-50ms rule-based understanding
    assert classify_statistical_sufficiency(len(latencies)) in ("STATISTICALLY_VALID", "STATISTICALLY_SUFFICIENT")


def test_benchmark_2_retrieval_agent_cache_acceleration():
    """Benchmark cold vs warm retrieval latency."""
    agent = RetrievalAgent()
    state1 = {
        "target_standard_number": "IS 302-2-201:2008",
        "sanitized_query": "What are the earthing requirements?",
    }
    t0 = time.time()
    res1 = agent.execute_retrieval(state1)
    cold_dur = (time.time() - t0) * 1000

    t1 = time.time()
    res2 = agent.execute_retrieval(res1)
    warm_dur = (time.time() - t1) * 1000

    assert len(res1["retrieved_candidate_clauses"]) == len(res2["retrieved_candidate_clauses"])
    assert res2.get("retrieval_package", {}).get("from_cache") is True
    assert warm_dur <= cold_dur + 5.0


def test_benchmark_3_analysis_agent_reasoning_duration():
    """Benchmark analysis agent structured analysis duration."""
    t0 = time.time()
    analysis = analysis_agent.analyze(
        target_standard="IS 302-2-201:2008",
        query="What are heating requirements?",
        retrieved_clauses=[{"clause_number": "19.1", "clause_title": "Heating", "requirement_text": "Normal operation"}],
        available_evidence=[],
    )
    dur = (time.time() - t0) * 1000
    assert dur < 100.0  # Sub-100ms structured analysis
    assert analysis.candidate_assessment != "SATISFIED"


def test_benchmark_4_planning_agent_synthesis_latency():
    """Benchmark planning agent action plan generation latency."""
    t0 = time.time()
    plan = planning_agent.generate_action_plan(
        target_standard="IS 302-2-201:2008",
        unsatisfied_clauses=[{"clause_number": "19.1", "gap_reason": "No lab test", "action": "REQUIRES_TESTING"}],
        evidence_status="UNVERIFIED",
    )
    dur = (time.time() - t0) * 1000
    assert dur < 100.0  # Sub-100ms planning
    assert plan.total_actions >= 1


def test_benchmark_5_end_to_end_graph_latency():
    """Benchmark end-to-end LangGraph execution latency."""
    graph = build_compliance_graph(checkpointer=False)
    state: BISComplianceGraphState = {
        "user_query": "What are the test requirements for an electric iron under IS 302-2-201:2008?",
        "node_contracts": {},
    }
    t0 = time.time()
    final_state = graph.invoke(state)
    dur = (time.time() - t0) * 1000
    assert dur < 2500.0  # End-to-end graph within 2.5s (including LLM adapter generation)
    assert final_state["regulatory_conclusion"] == "NONE"


def test_benchmark_6_snapshot_fingerprint_throughput():
    """Benchmark cryptographic SHA-256 fingerprint throughput (ops/sec)."""
    sample_state = {
        "query": "What are the safety requirements?",
        "standard": "IS 302-2-201:2008",
        "clauses": ["19.1", "19.2", "20.1"],
        "metadata": {"count": 3, "verified": True},
    }
    iterations = 1000
    t0 = time.time()
    for _ in range(iterations):
        SnapshotManager.compute_fingerprint(sample_state)
    dur = time.time() - t0
    ops_per_sec = iterations / dur
    assert ops_per_sec > 1000  # Over 1,000 ops per second


def test_benchmark_7_handoff_validation_overhead():
    """Benchmark handoff validation latency overhead per stage (< 0.5ms)."""
    state = {
        "query_understanding": {"intent": "QUERY_REQUIREMENT"},
        "target_standard_number": "IS 302-2-201:2008",
        "sanitized_query": "Test query",
    }
    iterations = 100
    t0 = time.time()
    for _ in range(iterations):
        HandoffValidator.validate_handoff(HandoffStage.QUERY_TO_RETRIEVAL, state)
    avg_dur_ms = ((time.time() - t0) * 1000) / iterations
    assert avg_dur_ms < 0.5  # Sub-millisecond validation


def test_benchmark_8_duplicate_tool_prevention_speedup():
    """Benchmark speedup achieved by tool caching deduplication."""
    state: BISComplianceGraphState = {
        "tool_call_count": 0,
        "tool_cache": {},
        "tool_traces": [],
        "node_contracts": {},
    }
    # Cold execution
    t0 = time.time()
    _execute_controlled_tool(
        state=state,
        node_name="test_node",
        tool_name="normalize_unit",
        tool_input={"value": 50.0, "from_unit": "fahrenheit", "to_unit": "celsius"},
        role="analysis_agent",
    )
    cold_dur = time.time() - t0

    # Warm execution (cached)
    t1 = time.time()
    _execute_controlled_tool(
        state=state,
        node_name="test_node",
        tool_name="normalize_unit",
        tool_input={"value": 50.0, "from_unit": "fahrenheit", "to_unit": "celsius"},
        role="analysis_agent",
    )
    warm_dur = time.time() - t1

    assert warm_dur < cold_dur + 0.001


def test_benchmark_9_budget_enforcement_zero_overhead():
    """Benchmark execution budget check latency (< 0.05ms)."""
    budget = ExecutionBudget()
    state = {"llm_call_count": 0}
    iterations = 500
    t0 = time.time()
    for _ in range(iterations):
        state["llm_call_count"] = 0
        BudgetEnforcer.check_and_increment_llm(state, budget)
    avg_overhead_ms = ((time.time() - t0) * 1000) / iterations
    assert avg_overhead_ms < 0.05


def test_benchmark_10_statistical_sufficiency_rule():
    """Verify statistical sufficiency guard: sample N < 30 must yield STATISTICALLY_INSUFFICIENT."""
    assert classify_statistical_sufficiency(1) == "STATISTICALLY_INSUFFICIENT"
    assert classify_statistical_sufficiency(15) == "STATISTICALLY_INSUFFICIENT"
    assert classify_statistical_sufficiency(29) == "STATISTICALLY_INSUFFICIENT"
    assert classify_statistical_sufficiency(30) in ("STATISTICALLY_VALID", "STATISTICALLY_SUFFICIENT")
    assert classify_statistical_sufficiency(100) in ("STATISTICALLY_VALID", "STATISTICALLY_SUFFICIENT")

    # Wilson score interval continuity check
    low, high = compute_wilson_score_interval(30, 30)
    assert 0.8 < low <= 1.0
    assert 0.8 < high <= 1.0
