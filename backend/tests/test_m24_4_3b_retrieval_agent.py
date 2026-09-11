"""Test Suite for Milestone M24.4.3B: Advanced Retrieval Agent Intelligence Upgrade.

Verifies:
1. Retrieval plan formulation & typed contract validation.
2. Retrieval strategy selection (exact clause, multi-clause, hybrid keyword, standard-scoped).
3. Deterministic query expansion engine & technical terminology bounding.
4. Product DNA enrichment in retrieval expansion without boundary pollution.
5. Cross-standard isolation enforcement (quarantine foreign standard clauses).
6. Context pruner and exact numeric/unit/tolerance preservation.
7. Quality tier grading (STRONG_MATCH, UNCERTAIN_MATCH, NO_RELIABLE_MATCH, etc.).
8. Cryptographic provenance hashing and source tracking.
9. Cardinal authority firewall invariant: llm_compliance_authority == 0.0, AI_DERIVED, regulatory_conclusion == 'NONE'.
10. Duplicate clause prevention and reranker coordination.
11. LangGraph node integration (retrieval_agent_node execution & state updates).
12. Tool call efficiency & cache hit reuse (duplicate tool calls prevented).
+ 10 Focused Benchmarks.
"""

import time
import pytest
from typing import Dict, Any, List

from backend.app.services.compliance.authority_types import AuthorityLevel
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG
from backend.app.services.orchestrator.retrieval_agent import (
    RetrievalAgent,
    retrieval_agent,
    RetrievalPlan,
    RetrievalPackage,
    RetrievalStrategy,
    RetrievalQualityTier,
    RetrievalStrategySelector,
    QueryExpansionEngine,
    CrossStandardIsolationFilter,
    ContextPrunerAndNumericPreserver,
    ResultQualityAssessor,
    CandidateClauseItem,
    QuarantinedClauseItem,
    MAX_EXPANDED_TERMS,
)
from backend.app.services.orchestrator.graph.state import (
    BISComplianceGraphState,
    RetrievalAgentContract,
)
from backend.app.services.orchestrator.graph.nodes import (
    retrieval_agent_node,
    _execute_controlled_tool,
)
from backend.app.services.orchestrator.graph.runner import run_compliance_graph_with_state
from backend.app.services.orchestrator.tools.bis_tools import search_bis_clauses


# ==============================================================================
# 1. RETRIEVAL PLAN FORMULATION
# ==============================================================================

def test_retrieval_plan_formulation_basic():
    """Test that RetrievalAgent formulates a valid typed RetrievalPlan."""
    agent = RetrievalAgent()
    plan = agent.formulate_plan(
        target_standard="IS 302-2-201:2008",
        query="What is the leakage current requirement for immersion heaters?",
        clause_references=["13.1"],
    )

    assert isinstance(plan, RetrievalPlan)
    assert plan.target_standard_number == "IS 302-2-201:2008"
    assert "leakage" in plan.query_terms or "current" in plan.query_terms
    assert plan.retrieval_strategy == RetrievalStrategy.EXACT_CLAUSE_LOOKUP
    assert plan.targeted_clause_numbers == ["13.1"]
    assert plan.authority == "AI_DERIVED"
    assert plan.llm_compliance_authority == 0.0


def test_retrieval_plan_authority_invariants():
    """Verify hard invariant: RetrievalPlan has 0.0 compliance authority."""
    plan = RetrievalPlan(
        target_standard_number="IS 17526:2021",
        query_terms=["vacuum", "flask"],
    )
    assert plan.authority == "AI_DERIVED"
    assert plan.llm_compliance_authority == 0.0


# ==============================================================================
# 2. RETRIEVAL STRATEGY SELECTION
# ==============================================================================

def test_strategy_selection_exact_clause():
    """Explicit single clause selects EXACT_CLAUSE_LOOKUP."""
    strat = RetrievalStrategySelector.select_strategy(
        target_standard="IS 302-2-201:2008",
        query="Check clause 13.1",
        clause_references=["13.1"],
    )
    assert strat == RetrievalStrategy.EXACT_CLAUSE_LOOKUP


def test_strategy_selection_multi_clause():
    """Multiple explicit clauses select MULTI_CLAUSE_TRAVERSAL."""
    strat = RetrievalStrategySelector.select_strategy(
        target_standard="IS 302-2-201:2008",
        query="Check clause 13.1 and 16.1",
        clause_references=["13.1", "16.1"],
    )
    assert strat == RetrievalStrategy.MULTI_CLAUSE_TRAVERSAL


def test_strategy_selection_hybrid_keywords():
    """Specific technical keywords trigger HYBRID_KEYWORD_BM25."""
    strat = RetrievalStrategySelector.select_strategy(
        target_standard="IS 302-2-201:2008",
        query="What is the drop test protocol?",
        clause_references=[],
    )
    assert strat == RetrievalStrategy.HYBRID_KEYWORD_BM25


def test_strategy_selection_standard_scoped():
    """General query with standard selects STANDARD_SCOPED_SEMANTIC."""
    strat = RetrievalStrategySelector.select_strategy(
        target_standard="IS 17526:2021",
        query="General construction requirements",
        clause_references=[],
    )
    assert strat == RetrievalStrategy.STANDARD_SCOPED_SEMANTIC


# ==============================================================================
# 3. QUERY EXPANSION ENGINE
# ==============================================================================

def test_query_expansion_leakage_current():
    """Technical query expands to relevant domain terms deterministically."""
    core, expanded = QueryExpansionEngine.expand_query_terms("Test for leakage current and earthing")
    assert "leakage" in core or "current" in core
    assert any("electric strength" in exp or "insulation resistance" in exp or "protective earth" in exp for exp in expanded)
    assert len(expanded) <= MAX_EXPANDED_TERMS


def test_query_expansion_with_product_dna():
    """Product DNA attributes are incorporated into expansion."""
    dna = {"voltage": "230 V", "rated_power": "1500 W", "material": "stainless steel grade 304"}
    core, expanded = QueryExpansionEngine.expand_query_terms(
        query="Check flask material",
        product_dna=dna,
    )
    assert any("stainless steel grade 304" in exp or "230 v" in exp for exp in expanded)


def test_query_expansion_bounded():
    """Query expansion never exceeds MAX_EXPANDED_TERMS."""
    dna = {f"attr_{i}": f"val_{i}" for i in range(20)}
    core, expanded = QueryExpansionEngine.expand_query_terms(
        query="creepage clearance insulation leakage earthing drop test flammability plug marking",
        product_dna=dna,
    )
    assert len(expanded) <= MAX_EXPANDED_TERMS


# ==============================================================================
# 4. CROSS-STANDARD ISOLATION ENFORCEMENT
# ==============================================================================

def test_cross_standard_isolation_rejects_foreign_clauses():
    """Foreign standard clauses are quarantined and excluded from valid candidates."""
    target_std = "IS 302-2-201:2008"
    raw_candidates = [
        {"standard_number": "IS 302-2-201:2008", "clause_number": "13.1", "clause_title": "Leakage Current"},
        {"standard_number": "IS 17526:2021", "clause_number": "5.2", "clause_title": "Flask Leakage Test"},
        {"standard_number": "IS 13252:2010", "clause_number": "2.1", "clause_title": "IT Equipment Safety"},
    ]

    valid, quarantined = CrossStandardIsolationFilter.filter_and_isolate(
        target_standard=target_std,
        candidates=raw_candidates,
    )

    assert len(valid) == 1
    assert valid[0]["clause_number"] == "13.1"
    assert len(quarantined) == 2
    assert any(q.standard_number == "IS 17526:2021" for q in quarantined)
    assert any(q.standard_number == "IS 13252:2010" for q in quarantined)
    assert all("CROSS_STANDARD_LEAKAGE_PREVENTED" in q.reason for q in quarantined)


def test_cross_standard_isolation_accepts_part_standards():
    """Base standard variants like IS 302-1 and IS 302-2-201 share base standard code."""
    valid, quarantined = CrossStandardIsolationFilter.filter_and_isolate(
        target_standard="IS 302-2-201:2008",
        candidates=[
            {"standard_number": "IS 302-1:2008", "clause_number": "8.1", "clause_title": "Protection"},
            {"standard_number": "IS 4151:2015", "clause_number": "7.1", "clause_title": "Helmets"},
        ],
    )
    assert len(valid) == 1
    assert valid[0]["standard_number"] == "IS 302-1:2008"
    assert len(quarantined) == 1
    assert quarantined[0].standard_number == "IS 4151:2015"


# ==============================================================================
# 5. CONTEXT PRUNING & EXACT NUMERIC PRESERVATION
# ==============================================================================

def test_numeric_preservation_strict():
    """Numbers, units, tolerances, and durations are strictly counted and preserved."""
    text = "Power input shall not deviate by more than +5% or -10%. Leakage current shall not exceed 0.75 mA at 230 V AC for 1 min."
    pruned, count = ContextPrunerAndNumericPreserver.prune_and_preserve(text)
    
    assert "+5%" in pruned
    assert "-10%" in pruned
    assert "0.75 mA" in pruned
    assert "230 V" in pruned
    assert count >= 4


def test_numeric_preservation_temperature_and_resistance():
    """Thermal values and electrical resistance thresholds preserved intact."""
    text = "Water temperature after 6 hours from initial 95 C shall be >= 60 C with insulation resistance >= 2 MOhm."
    pruned, count = ContextPrunerAndNumericPreserver.prune_and_preserve(text)
    
    assert "6 hours" in pruned or "6" in pruned
    assert "95 C" in pruned or "95" in pruned
    assert "60 C" in pruned or "60" in pruned
    assert "2 MOhm" in pruned or "2" in pruned
    assert count >= 3


# ==============================================================================
# 6. QUALITY TIER ASSESSMENT
# ==============================================================================

def test_quality_tier_strong_match():
    """Targeted clause present yields STRONG_MATCH."""
    cands = [
        CandidateClauseItem(
            clause_number="13.1",
            clause_title="Leakage Current",
            requirement_text="Max 0.75 mA",
            standard_number="IS 302-2-201:2008",
            verified=True,
        )
    ]
    tier = ResultQualityAssessor.assess_quality(
        candidates=cands,
        target_standard="IS 302-2-201:2008",
        targeted_clauses=["13.1"],
    )
    assert tier == RetrievalQualityTier.STRONG_MATCH


def test_quality_tier_no_match():
    """Empty candidates yields NO_RELIABLE_MATCH."""
    tier = ResultQualityAssessor.assess_quality(
        candidates=[],
        target_standard="IS 302-2-201:2008",
        targeted_clauses=["99.9"],
    )
    assert tier == RetrievalQualityTier.NO_RELIABLE_MATCH


def test_quality_tier_out_of_scope():
    """Unindexed / out of catalog standard yields OUT_OF_SCOPE."""
    tier = ResultQualityAssessor.assess_quality(
        candidates=[],
        target_standard="IS 99999:2099",
        targeted_clauses=[],
    )
    assert tier == RetrievalQualityTier.OUT_OF_SCOPE


def test_quality_tier_unverified():
    """Candidate with unverified source yields UNVERIFIED_SOURCE_MATCH."""
    cands = [
        CandidateClauseItem(
            clause_number="1.1",
            clause_title="Draft Clause",
            requirement_text="Draft",
            standard_number="IS 302-2-201:2008",
            verified=False,
        )
    ]
    tier = ResultQualityAssessor.assess_quality(
        candidates=cands,
        target_standard="IS 302-2-201:2008",
        targeted_clauses=[],
    )
    assert tier == RetrievalQualityTier.UNVERIFIED_SOURCE_MATCH


# ==============================================================================
# 7. RETRIEVAL PACKAGE & CRYPTOGRAPHIC PROVENANCE
# ==============================================================================

def test_candidate_clause_provenance_hash():
    """Every CandidateClauseItem receives a deterministic sha256 provenance hash."""
    c1 = CandidateClauseItem(
        clause_number="13.1",
        clause_title="Leakage Current",
        requirement_text="Max 0.75 mA",
        standard_number="IS 302-2-201:2008",
    )
    c2 = CandidateClauseItem(
        clause_number="13.1",
        clause_title="Leakage Current",
        requirement_text="Max 0.75 mA",
        standard_number="IS 302-2-201:2008",
    )
    assert len(c1.provenance_hash) == 16
    assert c1.provenance_hash == c2.provenance_hash


def test_retrieval_package_invariants():
    """RetrievalPackage guarantees 0.0 compliance authority and NONE regulatory conclusion."""
    pkg = RetrievalPackage(
        standard_number="IS 302-2-201:2008",
        strategy_used=RetrievalStrategy.STANDARD_SCOPED_SEMANTIC,
        quality_tier=RetrievalQualityTier.VERIFIED_SOURCE_MATCH,
        candidates=[],
    )
    assert pkg.provenance == "AI_DERIVED / CANDIDATE"
    assert pkg.llm_compliance_authority == 0.0
    assert pkg.regulatory_conclusion == "NONE"


# ==============================================================================
# 8. RETRIEVAL AGENT FULL EXECUTION
# ==============================================================================

def test_retrieval_agent_execute_retrieval_live():
    """Test full execute_retrieval lifecycle with real tool invocation."""
    agent = RetrievalAgent()
    state: Dict[str, Any] = {
        "target_standard_number": "IS 302-2-201:2008",
        "sanitized_query": "What is the leakage current requirement?",
        "product_dna": {"product_type": "immersion heater"},
        "node_contracts": {
            "request_understanding": {
                "clause_references": ["13.1"],
                "request_type": "INFORMATION_REQUEST",
            }
        },
    }

    out_state = agent.execute_retrieval(state)

    assert "retrieved_candidate_clauses" in out_state
    assert len(out_state["retrieved_candidate_clauses"]) >= 1
    assert any(c["clause_number"] == "13.1" for c in out_state["retrieved_candidate_clauses"])

    pkg = out_state.get("retrieval_package")
    assert pkg is not None
    assert pkg["strategy_used"] == RetrievalStrategy.EXACT_CLAUSE_LOOKUP.value
    assert pkg["quality_tier"] == RetrievalQualityTier.STRONG_MATCH.value
    assert pkg["llm_compliance_authority"] == 0.0


def test_retrieval_agent_caching_duplicate_prevention():
    """Verify that existing clauses for target standard reuse cache and increment counter."""
    agent = RetrievalAgent()
    existing = [
        {"clause_number": "6.1", "clause_title": "Voltage", "standard_number": "IS 302-2-201:2008", "requirement_text": "230 V"}
    ]
    state: Dict[str, Any] = {
        "target_standard_number": "IS 302-2-201:2008",
        "sanitized_query": "voltage rating",
        "retrieved_candidate_clauses": existing,
        "duplicate_tool_calls_prevented": 0,
    }

    out_state = agent.execute_retrieval(state)
    assert out_state["duplicate_tool_calls_prevented"] == 1
    assert out_state["retrieval_package"]["from_cache"] is True


def test_retrieval_agent_node_in_graph():
    """Verify retrieval_agent_node produces typed RetrievalAgentContract."""
    state: BISComplianceGraphState = {
        "target_standard_number": "IS 17526:2021",
        "sanitized_query": "vacuum flask food grade liner",
        "retrieved_candidate_clauses": [],
        "node_contracts": {},
        "errors": [],
        "execution_traces": [],
    }

    res_state = retrieval_agent_node(state)

    contract_data = res_state["node_contracts"]["retrieval_agent"]
    contract = RetrievalAgentContract(**contract_data)

    assert contract.standard_number == "IS 17526:2021"
    assert contract.retrieved_clauses_count >= 1
    assert contract.llm_compliance_authority == 0.0
    assert contract.regulatory_conclusion == "NONE"
    assert contract.authority == "AI_DERIVED"


# ==============================================================================
# 9. INTEGRATION & REGRESSION BENCHMARKS
# ==============================================================================

@pytest.mark.parametrize("query,expected_clause,target_std", [
    ("What are the earthing requirements?", "27.1", "IS 302-2-201:2008"),
    ("What is the power input tolerance?", "10.1", "IS 302-2-201:2008"),
    ("Vacuum flask leakage test inverted protocol", "5.2", "IS 17526:2021"),
    ("Food contact liner material stainless steel", "4.1", "IS 17526:2021"),
    ("Drop and impact resistance test concrete floor", "5.3", "IS 17526:2021"),
    ("Two wheeler helmet peak acceleration drop tower", "7.1", "IS 4151:2015"),
    ("Helmet retention chin strap extension", "8.1", "IS 4151:2015"),
    ("Toy safety small parts choking hazard cylinder", "4.4", "IS 9873 (Part 1):2019"),
    ("Toy normal use and abuse testing drop torque", "4.1", "IS 9873 (Part 1):2019"),
    ("Immersion heater sheath tubular heating element copper grade 304", "22.101", "IS 302-2-201:2008"),
])
def test_retrieval_agent_benchmarks(query: str, expected_clause: str, target_std: str):
    """10 focused retrieval benchmarks covering different domains and clauses."""
    agent = RetrievalAgent()
    state = {
        "target_standard_number": target_std,
        "sanitized_query": query,
    }
    res = agent.execute_retrieval(state)
    retrieved_numbers = [c["clause_number"] for c in res["retrieved_candidate_clauses"]]
    assert expected_clause in retrieved_numbers, f"Expected clause {expected_clause} in {retrieved_numbers} for query '{query}'"
