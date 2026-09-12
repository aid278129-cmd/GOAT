"""LangGraph State Contract for Layer 3 AI Orchestrator (Milestones M24.2, M24.3 & M24.4.1).

Cardinal Principles Enforced:
1. "The agents reason about the task. The deterministic engines reason about compliance."
2. ONE LLM: Model execution delegates strictly to the single LLM singleton.
3. ZERO COMPLIANCE AUTHORITY: LangGraph and tools have 0.0% compliance authority.
4. REUSE EXISTING MODELS: Reuses ProductDNACore, OrchestratedAIResponse, etc.
5. TYPED NODE CONTRACTS: Formal Pydantic v2 schemas for each node's input/output boundary.
6. RUNTIME OPTIMIZATION: Bounded reasoning, context minimization, caching, and deduplication.
7. OBSERVABILITY & METRICS: Tracks node-level, tool-level, and efficiency metrics.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Typed Node Contract Models (M24.4.1)
# ------------------------------------------------------------------------------

class RequestUnderstandingContract(BaseModel):
    """Strongly typed output contract for request_understanding node (extended in M24.4.3A)."""
    sanitized_query: str
    user_intent: str
    security_flag: bool = False
    security_reason: Optional[str] = None
    security_warnings: List[str] = Field(default_factory=list)
    # M24.4.3A Query Agent Intelligence Upgrades:
    query_understanding: Optional[Dict[str, Any]] = None
    request_type: Optional[str] = None
    complexity: Optional[str] = None
    task_count: int = 0
    clarification_required: bool = False
    missing_information: List[str] = Field(default_factory=list)
    extracted_standards: List[str] = Field(default_factory=list)
    extracted_clauses: List[str] = Field(default_factory=list)
    retrieval_hints: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    authority: str = "AI_DERIVED"



class ProductDNAContract(BaseModel):
    """Strongly typed output contract for product_dna_check node."""
    dna_sufficient: bool = True
    missing_attributes: List[str] = Field(default_factory=list)
    identified_facts_count: int = 0


class TaskRouterContract(BaseModel):
    """Strongly typed output contract for task_router node."""
    target_standard_number: str
    target_standard_title: str
    retrieval_required: bool
    task_type: str
    deterministic_short_circuit: bool = False
    short_circuit_handler: Optional[str] = None


class RetrievalAgentContract(BaseModel):
    """Strongly typed output contract for retrieval_agent node (M24.4.3B)."""
    standard_number: str
    retrieved_clauses_count: int
    candidate_clauses: List[Dict[str, Any]] = Field(default_factory=list)
    from_cache: bool = False
    retrieval_strategy: Optional[str] = None
    retrieval_quality_tier: Optional[str] = None
    retrieval_plan: Optional[Dict[str, Any]] = None
    retrieval_package: Optional[Dict[str, Any]] = None
    cross_standard_violations: List[Dict[str, Any]] = Field(default_factory=list)
    total_quarantined: int = 0
    provenance: str = "AI_DERIVED / CANDIDATE"
    authority: str = "AI_DERIVED"
    llm_compliance_authority: float = 0.0
    regulatory_conclusion: str = "NONE"


class EvidenceGateContract(BaseModel):
    """Strongly typed output contract for evidence_validation_gate node."""
    evidence_status: str  # VERIFIED | UNVERIFIED | CONFLICT | NO_VERIFIED_SOURCE
    verified_evidence_count: int
    unverified_claims_blocked: List[str] = Field(default_factory=list)


class AnalysisAgentContract(BaseModel):
    """Strongly typed output contract for analysis_agent node.
    
    Hard Invariant: Provenance is explicitly AI_DERIVED / CANDIDATE.
    """
    analysis_explanation: str
    provenance: str = "AI_DERIVED / CANDIDATE"
    llm_called: bool = False
    grounding_status: str
    context_size_chars: int = 0
    structured_analysis: Optional[Dict[str, Any]] = None
    candidate_assessment: Optional[str] = None
    evidence_sufficiency: Optional[str] = None
    conflicts_detected: int = 0
    missing_evidence_count: int = 0


class DeterministicGateContract(BaseModel):
    """Strongly typed output contract for deterministic_compliance_gate node.
    
    Hard Invariant: Authority source is strictly downstream deterministic engine.
    """
    total_evaluated: int
    unsatisfied_count: int
    authority_source: str = "LAYER_7_COMPLIANCE_GAP_ENGINE"
    deterministic: bool = True
    llm_authority: float = 0.0


class PlanningAgentContract(BaseModel):
    """Strongly typed output contract for planning_agent node.
    
    Hard Invariant: Action plan items are AI_DERIVED / CANDIDATE suggestions.
    """
    action_plan_items_count: int
    action_plan_items: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: str = "AI_DERIVED / CANDIDATE"
    action_plan: Optional[Dict[str, Any]] = None
    blockers_count: int = 0
    critical_actions_count: int = 0
    expert_review_required: bool = False


class OutputIntegrityContract(BaseModel):
    """Strongly typed output contract for output_integrity_gate node."""
    sanitized: bool
    citations_count: int
    regulatory_conclusion: str = "NONE"
    llm_compliance_authority: float = 0.0


# ------------------------------------------------------------------------------
# Observability Traces
# ------------------------------------------------------------------------------

class NodeExecutionTrace(TypedDict, total=False):
    """Execution metadata record for an individual graph node (observability ready)."""
    node_name: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str  # SUCCESS | FAILED | SKIPPED
    error: Optional[str]


class ToolExecutionTrace(TypedDict, total=False):
    """Execution metadata record for a controlled tool call (M24.3 & M24.4.1)."""
    tool_name: str
    tool_call_id: str
    node_name: str
    timestamp: str
    duration_ms: float
    input_summary: str
    status: str  # SUCCESS | REJECTED | FAILED | CACHED
    error: Optional[str]
    cached: bool


# ------------------------------------------------------------------------------
# LangGraph Core State Contract
# ------------------------------------------------------------------------------

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

    # 7. Deterministic Results (Downstream Authorities: Layers 5, 7, 8; Output Integrity: Layer 9)
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

    # 13. M24.4.1 Runtime Optimization & Efficiency Metrics
    llm_call_count: int
    duplicate_tool_calls_prevented: int
    retrieval_call_count: int
    context_size_chars: int
    short_circuited: bool
    short_circuit_reason: Optional[str]
    tool_cache: Dict[str, Any]
    node_contracts: Dict[str, Dict[str, Any]]

    # 14. M24.4.3A Query Agent Intelligence Upgrades
    query_understanding: Optional[Dict[str, Any]]
    request_type: Optional[str]
    query_complexity: Optional[str]
    decomposed_tasks: Optional[List[Dict[str, Any]]]
    retrieval_hints: Optional[List[Dict[str, Any]]]
    out_of_domain: Optional[bool]

    # 15. M24.4.3B Retrieval Agent Intelligence Upgrades
    retrieval_plan: Optional[Dict[str, Any]]
    retrieval_package: Optional[Dict[str, Any]]
    cross_standard_violations: Optional[List[Dict[str, Any]]]

    # 16. M24.4.3C Analysis Agent Intelligence Upgrades
    structured_analysis: Optional[Dict[str, Any]]
    comparison_candidates: Optional[List[Dict[str, Any]]]
    evidence_conflicts: Optional[List[Dict[str, Any]]]

    # 17. M24.4.3D Planning Agent Intelligence Upgrades
    structured_action_plan: Optional[Dict[str, Any]]
    action_blockers: Optional[List[Dict[str, Any]]]

    # 18. M24.4.3E Controlled Agent Coordination Upgrades
    handoff_traces: Optional[List[Dict[str, Any]]]
    state_snapshots: Optional[List[Dict[str, Any]]]
    agent_traces: Optional[List[Dict[str, Any]]]
    budget_exceeded: Optional[bool]
    duplicate_work_prevented: Optional[int]

