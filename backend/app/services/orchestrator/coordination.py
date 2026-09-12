"""Layer 3: Controlled Agent Coordination & Runtime Optimization (Milestone M24.4.3E).

Architectural Invariants Strictly Enforced:
1. EXACTLY ONE LLM: Model execution delegates strictly to the single LLM singleton / adapter.
2. ZERO COMPLIANCE AUTHORITY: Query, Retrieval, Analysis, and Planning Agents have exactly 0.0%
   compliance authority. Authority is strictly AI_DERIVED / CANDIDATE.
   They cannot declare, evaluate, certify, or conclude regulatory compliance.
3. PRESERVE FOUNDATIONAL TRUTHS:
   - USER_TEXT != EVIDENCE != COMPLIANCE
   - NO VERIFIED SOURCE -> NO REGULATORY CLAIM
   - NO VERIFIED EVIDENCE -> NO SATISFIED
   - NO SUFFICIENT INFORMATION -> ASK / UNKNOWN
   - CONFLICT -> EXPERT REVIEW
   - RECOMMENDATIONS != COMPLIANCE EVALUATION
4. DETERMINISTIC GRAPH CONTROLLER: LangGraph is the single authoritative controller.
   Agents reason; the graph controls; deterministic engines decide compliance.
   No agent-to-agent autonomous loops or dynamic edge transitions.
5. EXPLICIT HANDOFF CONTRACTS & STATE OWNERSHIP: Typed state handoff validation prevents
   corrupted state propagation. State snapshots provide complete input auditing.
6. FAILURE ISOLATION & UNCERTAINTY PROPAGATION: Failures gracefully convert to controlled
   uncertainty states rather than fabricated downstream claims.
7. EXECUTION BUDGETS: Hard bounds on LLM calls, tool calls, and retrieval executions.
"""

import hashlib
import json
import time
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, Field

from backend.app.services.compliance.authority_types import AuthorityLevel, AuthoritySource
from backend.app.services.orchestrator.schemas import OrchestratorIntent, GroundingStatus
from backend.app.core.logging import logger


# ==============================================================================
# ENUMS & CONSTANTS
# ==============================================================================

class HandoffStage(str, Enum):
    """Enumeration of explicit agent handoff transitions."""
    QUERY_TO_RETRIEVAL = "QUERY_TO_RETRIEVAL"
    RETRIEVAL_TO_ANALYSIS = "RETRIEVAL_TO_ANALYSIS"
    ANALYSIS_TO_LAYER7 = "ANALYSIS_TO_LAYER7"
    LAYER7_TO_PLANNING = "LAYER7_TO_PLANNING"
    PLANNING_TO_OUTPUT = "PLANNING_TO_OUTPUT"


class ReadinessStatus(str, Enum):
    """Deterministic readiness grading for downstream stage execution."""
    READY = "READY"
    BLOCKED = "BLOCKED"
    SHORT_CIRCUITED = "SHORT_CIRCUITED"
    FAILED = "FAILED"


# ==============================================================================
# DATA CONTRACTS (Pydantic v2)
# ==============================================================================

class ExecutionBudget(BaseModel):
    """Configurable execution budget bounds preventing runaway loops."""
    max_llm_calls: int = 3
    max_tool_calls: int = 10
    max_retrieval_calls: int = 3
    max_analysis_items: int = 10
    max_planning_actions: int = 15


class AgentHandoffContract(BaseModel):
    """Explicit typed contract validating inter-agent data exchange."""
    stage: HandoffStage
    producer_agent: str
    consumer_agent: str
    payload_hash: str
    authority_level: str = "AI_DERIVED / CANDIDATE"
    provenance: str = "AI_DERIVED"
    validation_status: ReadinessStatus = ReadinessStatus.READY
    validation_errors: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class StateSnapshot(BaseModel):
    """Cryptographic snapshot of state input received by an agent for auditability."""
    snapshot_id: str
    node_name: str
    state_hash: str
    keys_snapshot: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class AgentExecutionTrace(BaseModel):
    """Structured execution trace tracking individual stage performance and provenance."""
    stage_name: str
    status: str = "SUCCESS"
    duration_ms: float = 0.0
    input_contract_hash: str = ""
    output_contract_hash: str = ""
    authority: str = "AI_DERIVED / CANDIDATE"
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    tool_calls: int = 0
    llm_calls: int = 0
    cache_hits: int = 0


# ==============================================================================
# COORDINATION ENGINES
# ==============================================================================

class SnapshotManager:
    """Computes deterministic cryptographic fingerprints for state snapshots."""

    @classmethod
    def compute_fingerprint(cls, data: Any) -> str:
        """Computes SHA-256 hash of JSON-serializable state content."""
        try:
            serialized = json.dumps(data, sort_keys=True, default=str)
        except Exception:
            serialized = str(data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def capture_snapshot(cls, node_name: str, state_subset: Dict[str, Any]) -> StateSnapshot:
        """Creates an auditable snapshot record of state received by an agent."""
        s_hash = cls.compute_fingerprint(state_subset)
        return StateSnapshot(
            snapshot_id=f"SNAP-{node_name[:4].upper()}-{s_hash[:6]}",
            node_name=node_name,
            state_hash=s_hash,
            keys_snapshot=list(state_subset.keys()),
        )


class HandoffValidator:
    """Validates prerequisite data contracts before an agent consumes downstream state."""

    @classmethod
    def validate_handoff(
        cls,
        stage: HandoffStage,
        state: Dict[str, Any],
    ) -> AgentHandoffContract:
        """Enforces schema, provenance, and data completeness for each transition."""
        errors: List[str] = []
        payload_data: Dict[str, Any] = {}

        if stage == HandoffStage.QUERY_TO_RETRIEVAL:
            payload_data = {
                "query_understanding": state.get("query_understanding"),
                "target_standard": state.get("target_standard_number"),
            }
            if state.get("out_of_domain") is True:
                errors.append("Query is classified OUT_OF_DOMAIN; retrieval must be short-circuited.")
            target_std = state.get("target_standard_number")
            qu = state.get("query_understanding")
            has_std = bool(target_std) or (isinstance(qu, dict) and bool(qu.get("explicit_standard_refs")))
            if not has_std and not (state.get("sanitized_query") or state.get("user_query")):
                errors.append("Target standard number is missing in query understanding.")

        elif stage == HandoffStage.RETRIEVAL_TO_ANALYSIS:
            payload_data = {
                "retrieval_package": state.get("retrieval_package"),
                "candidate_clauses": state.get("retrieval_candidate_clauses") or state.get("retrieved_candidate_clauses"),
            }
            if state.get("cross_standard_violations"):
                errors.append("Cross-standard violation detected; foreign clauses present.")
            if state.get("retrieval_status") == "FAILED":
                errors.append("Retrieval stage reported FAILED; analysis cannot proceed with normal evaluation.")

        elif stage == HandoffStage.ANALYSIS_TO_LAYER7:
            payload_data = {
                "structured_analysis": state.get("structured_analysis"),
                "comparison_candidates": state.get("comparison_candidates"),
            }
            analysis = state.get("structured_analysis") or {}
            cand_assessment = analysis.get("candidate_assessment")
            if cand_assessment == "SATISFIED":
                errors.append("Illegal Authority Claim: Analysis Agent cannot emit authoritative 'SATISFIED'.")
            if state.get("regulatory_conclusion") not in (None, "NONE"):
                errors.append("Illegal Authority Claim: Analysis Agent cannot set non-NONE regulatory conclusion.")
            if state.get("llm_compliance_authority", 0.0) > 0.0:
                errors.append("Illegal Authority Claim: LLM compliance authority must be exactly 0.0%.")

        elif stage == HandoffStage.LAYER7_TO_PLANNING:
            payload_data = {
                "gap_summary": state.get("gap_analysis_summary"),
                "unsatisfied_clauses": state.get("unsatisfied_clauses"),
            }
            # Layer 7 must be deterministic
            if not state.get("gap_analysis_summary"):
                errors.append("Layer 7 gap analysis summary is missing; planning requires deterministic findings.")

        elif stage == HandoffStage.PLANNING_TO_OUTPUT:
            payload_data = {
                "action_plan": state.get("structured_action_plan"),
            }
            plan = state.get("structured_action_plan") or {}
            for a in plan.get("actions", []):
                if a.get("status") in ("SATISFIED", "COMPLETED"):
                    errors.append("Illegal Authority Claim: Planning Agent cannot mark actions SATISFIED/COMPLETED.")
            if state.get("regulatory_conclusion") not in (None, "NONE"):
                errors.append("Illegal Authority Claim: Planning Agent cannot set non-NONE regulatory conclusion.")
            if state.get("llm_compliance_authority", 0.0) > 0.0:
                errors.append("Illegal Authority Claim: LLM compliance authority must be exactly 0.0%.")

        payload_hash = SnapshotManager.compute_fingerprint(payload_data)
        producer, consumer = stage.value.split("_TO_")

        status = ReadinessStatus.READY if not errors else ReadinessStatus.BLOCKED
        return AgentHandoffContract(
            stage=stage,
            producer_agent=producer,
            consumer_agent=consumer,
            payload_hash=payload_hash,
            authority_level="AI_DERIVED / CANDIDATE",
            provenance="AI_DERIVED",
            validation_status=status,
            validation_errors=errors,
        )


class AgentReadinessGate:
    """Deterministic evaluation of whether an agent is cleared to execute."""

    @classmethod
    def check_readiness(cls, stage: HandoffStage, state: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Returns: (is_ready, blocker_reason)"""
        # Global Budget Check
        if state.get("budget_exceeded"):
            return False, "EXECUTION_BUDGET_EXCEEDED"

        handoff = HandoffValidator.validate_handoff(stage, state)
        if handoff.validation_status != ReadinessStatus.READY:
            return False, "; ".join(handoff.validation_errors)

        return True, None


class BudgetEnforcer:
    """Enforces execution limits to guarantee termination and prevent cost runaways."""

    @classmethod
    def check_and_increment_llm(cls, state: Dict[str, Any], budget: ExecutionBudget) -> bool:
        """Returns True if within budget, False if budget exceeded."""
        current = state.get("llm_call_count", 0)
        if current >= budget.max_llm_calls:
            state["budget_exceeded"] = True
            logger.warning(f"[BudgetEnforcer] LLM call limit reached ({current}/{budget.max_llm_calls}). Halting execution.")
            return False
        state["llm_call_count"] = current + 1
        return True

    @classmethod
    def check_and_increment_tool(cls, state: Dict[str, Any], budget: ExecutionBudget) -> bool:
        """Returns True if within budget, False if budget exceeded."""
        current = state.get("tool_call_count", 0)
        if current >= budget.max_tool_calls:
            state["budget_exceeded"] = True
            logger.warning(f"[BudgetEnforcer] Tool call limit reached ({current}/{budget.max_tool_calls}). Halting execution.")
            return False
        state["tool_call_count"] = current + 1
        return True


class AgentCoordinationManager:
    """Centralized coordinator orchestrating handoffs, snapshots, and audit metrics."""

    def __init__(self, budget: Optional[ExecutionBudget] = None):
        self.budget = budget or ExecutionBudget()
        self.shared_cache: Dict[str, Any] = {}
        self.metrics: Dict[str, int] = {
            "handoffs_validated": 0,
            "handoff_blocks": 0,
            "snapshots_recorded": 0,
            "duplicate_work_prevented": 0,
            "short_circuits": 0,
            "budget_violations": 0,
        }

    def reset_metrics(self) -> None:
        """Reset execution counters."""
        self.shared_cache.clear()
        for k in self.metrics:
            self.metrics[k] = 0

    def record_stage_execution(
        self,
        state: Dict[str, Any],
        stage_name: str,
        duration_ms: float,
        status: str = "SUCCESS",
        tool_calls: int = 0,
        llm_calls: int = 0,
        cache_hits: int = 0,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> AgentExecutionTrace:
        """Records a comprehensive execution trace for the stage."""
        trace = AgentExecutionTrace(
            stage_name=stage_name,
            status=status,
            duration_ms=duration_ms,
            authority="AI_DERIVED / CANDIDATE",
            errors=errors or [],
            warnings=warnings or [],
            tool_calls=tool_calls,
            llm_calls=llm_calls,
            cache_hits=cache_hits,
        )
        agent_traces = state.get("agent_traces", [])
        agent_traces.append(trace.model_dump())
        state["agent_traces"] = agent_traces
        return trace


# Global Singleton Instance
agent_coordinator = AgentCoordinationManager()
