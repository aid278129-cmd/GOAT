"""LangGraph StateGraph Builder & Compiler for Layer 3 (Milestone M24.2).

Compiles the 9-node controlled compliance reasoning workflow with MemorySaver checkpointing.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.app.services.orchestrator.graph.state import BISComplianceGraphState
from backend.app.services.orchestrator.graph.nodes import (
    request_understanding_node,
    product_dna_check_node,
    task_router_node,
    retrieval_agent_node,
    evidence_validation_gate_node,
    analysis_agent_node,
    deterministic_compliance_gate_node,
    planning_agent_node,
    output_integrity_gate_node,
    controlled_refusal_node,
    clarification_request_node,
)
from backend.app.services.orchestrator.graph.edges import (
    route_after_request_understanding,
    route_after_product_dna_check,
    route_after_task_router,
    route_after_evidence_validation,
)


def build_compliance_graph(checkpointer: bool = True):
    """Builds and compiles the deterministic BIS compliance reasoning StateGraph."""
    graph = StateGraph(BISComplianceGraphState)

    # 1. Add Canonical Nodes
    graph.add_node("request_understanding", request_understanding_node)
    graph.add_node("controlled_refusal", controlled_refusal_node)
    graph.add_node("product_dna_check", product_dna_check_node)
    graph.add_node("clarification_request", clarification_request_node)
    graph.add_node("task_router", task_router_node)
    graph.add_node("retrieval_agent", retrieval_agent_node)
    graph.add_node("evidence_validation_gate", evidence_validation_gate_node)
    graph.add_node("analysis_agent", analysis_agent_node)
    graph.add_node("deterministic_compliance_gate", deterministic_compliance_gate_node)
    graph.add_node("planning_agent", planning_agent_node)
    graph.add_node("output_integrity_gate", output_integrity_gate_node)

    # 2. Add Flow Edges
    graph.add_edge(START, "request_understanding")

    # Conditional after request understanding
    graph.add_conditional_edges(
        "request_understanding",
        route_after_request_understanding,
        {
            "controlled_refusal": "controlled_refusal",
            "product_dna_check": "product_dna_check",
        },
    )
    graph.add_edge("controlled_refusal", END)

    # Conditional after Product DNA check
    graph.add_conditional_edges(
        "product_dna_check",
        route_after_product_dna_check,
        {
            "clarification_request": "clarification_request",
            "task_router": "task_router",
        },
    )
    graph.add_edge("clarification_request", END)

    # Conditional after Task Router
    graph.add_conditional_edges(
        "task_router",
        route_after_task_router,
        {
            "retrieval_agent": "retrieval_agent",
            "analysis_agent": "analysis_agent",
        },
    )

    # Edge after Retrieval Agent
    graph.add_edge("retrieval_agent", "evidence_validation_gate")

    # Conditional after Evidence Validation
    graph.add_conditional_edges(
        "evidence_validation_gate",
        route_after_evidence_validation,
        {
            "analysis_agent": "analysis_agent",
            "output_integrity_gate": "output_integrity_gate",
        },
    )

    # Core Reasoning & Authority Pipeline
    graph.add_edge("analysis_agent", "deterministic_compliance_gate")
    graph.add_edge("deterministic_compliance_gate", "planning_agent")
    graph.add_edge("planning_agent", "output_integrity_gate")
    graph.add_edge("output_integrity_gate", END)

    # Compile with optional MemorySaver for state inspectability
    memory = MemorySaver() if checkpointer else None
    compiled_app = graph.compile(checkpointer=memory)
    return compiled_app


# Pre-compiled canonical instance
compliance_graph = build_compliance_graph(checkpointer=True)
