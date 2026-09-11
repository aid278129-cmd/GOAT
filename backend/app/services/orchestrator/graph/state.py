"""LangGraph State Contract for Layer 3 AI Orchestrator (Milestones M24.2 & M24.3).

Cardinal Principles Enforced:
1. "The agents reason about the task. The deterministic engines reason about compliance."
2. ONE LLM: Model execution delegates strictly to the single LLM singleton.
3. ZERO COMPLIANCE AUTHORITY: LangGraph and tools have 0.0% compliance authority.
4. REUSE EXISTING MODELS: Reuses ProductDNACore, OrchestratedAIResponse, etc.
5. OBSERVABILITY PREPARATION: Tracks node-level and tool-level execution metadata ready for future tracing.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class NodeExecutionTrace(TypedDict, total=False):
    """Execution metadata record for an individual graph node (observability ready)."""
    node_name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str  # SUCCESS | FAILED | SKIPPED
    error: Optional[str]


class ToolExecutionTrace(TypedDict, total=False):
    """Execution metadata record for a controlled tool call (M24.3)."""
    tool_name: str
    tool_call_id: str
    node_name: str
    timestamp: str
    duration_ms: float
    input_summary: str
    status: str  # SUCCESS | REJECTED | FAILED
    error: Optional[str]


class BISComplianceGraphState(TypedDict, total=False):
    """Strongly typed LangGraph state contract for Layer 3 compliance orchestration."""

    # 1. Request
    correlation_id: str
    user_query: str
    sanitized_query: str
    timestamp: str

    # 2. Security
    security_flag: bool
    security_reason: Optional[str]
    security_warnings: List[str]

    # 3. Product DNA
    product_dna: Optional[Any]  # ProductDNACore or dict
    dna_sufficient: bool
    missing_attributes: List[str]

    # 4. Intent / Task
    user_intent: str  # OrchestratorIntent value
    task_type: str
    retrieval_required: bool

    # 5. Retrieval
    target_standard_number: str
    target_standard_title: str
    generated_search_queries: List[str]
    retrieved_candidate_clauses: List[Dict[str, Any]]

    # 6. Evidence
    available_evidence_ids: List[str]
    verified_evidence_records: List[Dict[str, Any]]
    unverified_claims_blocked: List[str]
    evidence_status: str  # VERIFIED | UNVERIFIED | CONFLICT | NO_VERIFIED_SOURCE

    # 7. Deterministic Results (Downstream Authorities: Layers 5, 7, 8)
    applicability_decision: Optional[Dict[str, Any]]
    gap_analysis_summary: Optional[Dict[str, Any]]
    unsatisfied_clauses: List[Dict[str, Any]]
    evaluation_records: List[Dict[str, Any]]

    # 8. AI Reasoning (Language Intelligence Only: 0% Compliance Authority)
    analysis_explanation: str
    action_plan_items: List[Dict[str, Any]]

    # 9. Control
    expert_review_required: bool
    grounding_status: str  # GroundingStatus value
    warnings: List[str]
    errors: List[str]

    # 10. Authority (Hard invariants: Always 0.0% LLM authority, regulatory_conclusion="NONE")
    regulatory_conclusion: str  # "NONE"
    llm_compliance_authority: float  # 0.0
    authority_records: List[Dict[str, Any]]  # AuthoritativeRecord serializations
    untrusted_ai_claims: List[str]  # Detected and suppressed pseudo-compliance assertions

    # 11. Final Output Payload (OrchestratedAIResponse)
    final_response: Optional[Dict[str, Any]]

    # 12. Observability & Tracing Metadata (Phase 14 & 19 preparation)
    execution_traces: List[NodeExecutionTrace]
    tool_traces: List[ToolExecutionTrace]
    tool_call_count: int
