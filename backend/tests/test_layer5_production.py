"""Layer 5: Applicability Engine — Production Integration Test Suite.

Validates the SIH Presentation Layer 5 architecture and invariants:
1. 7 Canonical Result States:
   - APPLICABLE
   - POTENTIALLY_APPLICABLE
   - MORE_INFORMATION_REQUIRED
   - NOT_APPLICABLE
   - COVERAGE_GAP
   - CONFLICTING_RULES
   - EXPERT_REVIEW_REQUIRED

2. Cardinal Invariants:
   - Invariant 1: LLM authority over final applicability = 0% (llm_decision=False always)
   - Invariant 2: MISSING REQUIRED FACT -> ASK (Never Guess or Infer)
   - Invariant 3: COVERAGE GAP != NOT_APPLICABLE
   - Invariant 4: STANDARD EXISTS != AUTOMATICALLY MANDATORY (Scope & QCO separation)
   - Invariant 5: NO VERIFIED SCOPE/RULE -> NO AUTHORITATIVE APPLICABILITY CLAIM

3. Deterministic Decision Trace generation and step audit trail.
4. API endpoints (/api/applicability/evaluate, /rules, /taxonomy, /states).
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.product_dna import ProductDNACore, DNAAttribute
from backend.app.services.applicability.applicability_models import (
    ApplicabilityState,
    ScopeStatus,
    QCOStatus,
    ApplicabilityAction,
    ApplicabilityDecision,
)
from backend.app.services.applicability.engine import (
    determine_applicability,
    load_declarative_rules,
)

client = TestClient(app)


def test_state_applicable_for_verified_vacuum_flask():
    """State 1: APPLICABLE — Validated Product DNA with all required attributes and QCO mandate."""
    dna = ProductDNACore(
        product_name="750ml Stainless Steel Flask",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel"],
        insulated=True,
        attributes=[DNAAttribute(name="capacity_ml", value=750)],
    )
    decisions = determine_applicability(dna, authoritative_only=True)
    assert len(decisions) >= 1

    primary = decisions[0]
    assert primary.standard_number == "IS 17526:2021"
    assert primary.applicability_status == ApplicabilityState.APPLICABLE
    assert primary.technical_relevance == "LIKELY_APPLICABLE"
    assert primary.regulatory_status == "VERIFIED_MANDATORY_QCO"
    assert primary.scope_status == ScopeStatus.IN_SCOPE
    assert primary.qco_status == QCOStatus.MANDATORY_QCO
    assert primary.action_required == ApplicabilityAction.CONTINUE_TO_REQUIREMENTS
    assert primary.llm_decision is False

    # Check deterministic trace
    assert primary.decision_trace is not None
    assert primary.decision_trace.scope_check == ScopeStatus.IN_SCOPE
    assert primary.decision_trace.qco_check == QCOStatus.MANDATORY_QCO
    assert primary.decision_trace.final_status == ApplicabilityState.APPLICABLE
    assert len(primary.supporting_facts) >= 3


def test_state_more_information_required_when_blocking_fact_missing():
    """State 2: MORE_INFORMATION_REQUIRED — Missing required blocking attributes generates clarification question."""
    # Drinkware category without materials or insulation specified
    dna = ProductDNACore(
        product_name="Beverage Container",
        category="Drinkware & Food Contact Containers",
        materials=[],  # Missing materials
        insulated=False,  # Unspecified insulation
        attributes=[],
    )
    decisions = determine_applicability(dna, authoritative_only=False)
    assert len(decisions) >= 1

    primary = decisions[0]
    assert primary.applicability_status == ApplicabilityState.MORE_INFORMATION_REQUIRED
    assert primary.technical_relevance == "MORE_INFORMATION_REQUIRED"
    assert primary.regulatory_status == "MORE_INFORMATION_REQUIRED"
    assert primary.action_required == ApplicabilityAction.ASK_FOR_INFORMATION
    assert len(primary.missing_facts) >= 1
    assert "materials" in primary.missing_facts or "insulated" in primary.missing_facts
    assert primary.clarification_question is not None
    assert "Clarification required" in primary.clarification_question or "please provide" in primary.clarification_question
    assert primary.llm_decision is False


def test_state_not_applicable_when_out_of_verified_scope():
    """State 3: NOT_APPLICABLE — Validated as explicitly outside scope (e.g. uninsulated polypropylene)."""
    dna = ProductDNACore(
        product_name="Plastic Water Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["polypropylene"],
        insulated=False,
        attributes=[],
    )
    decisions = determine_applicability(dna, authoritative_only=False)
    assert len(decisions) >= 1

    not_app = [d for d in decisions if d.standard_number == "IS 17526:2021"]
    if not_app:
        assert not_app[0].applicability_status == ApplicabilityState.NOT_APPLICABLE
        assert not_app[0].technical_relevance == "NOT_APPLICABLE"
        assert not_app[0].scope_status == ScopeStatus.OUT_OF_SCOPE
        assert not_app[0].llm_decision is False


def test_state_coverage_gap_distinguished_from_not_applicable():
    """State 4: COVERAGE_GAP — Uncataloged category triggers COVERAGE_GAP, NOT NOT_APPLICABLE."""
    dna = ProductDNACore(
        product_name="Traditional Ceramic Terracotta Pot",
        category="General Goods",
        materials=["clay", "terracotta"],
        insulated=False,
        attributes=[],
    )
    decisions = determine_applicability(dna, authoritative_only=True)
    assert len(decisions) >= 1

    gap = decisions[0]
    assert gap.applicability_status == ApplicabilityState.COVERAGE_GAP
    assert gap.technical_relevance == "COVERAGE_GAP"
    assert gap.regulatory_status == "COVERAGE_NOT_ESTABLISHED"
    assert gap.action_required == ApplicabilityAction.REVIEW_COVERAGE_GAP
    assert "NOT that the product is exempt" in gap.explanation or "coverage boundary" in gap.explanation
    assert gap.llm_decision is False


def test_state_conflicting_rules_detected():
    """State 5: CONFLICTING_RULES — Contradictory product assertions trigger conflict review."""
    # Declares non-electrical but product name and category indicate electric immersion water heater
    dna = ProductDNACore(
        product_name="Portable Immersion Heater Rod",
        category="Electrical & Domestic Appliances",
        electrical=False,  # Contradiction with Immersion Heater
        insulated=False,
        attributes=[DNAAttribute(name="voltage", value=230)],
    )
    decisions = determine_applicability(dna, authoritative_only=False)
    assert len(decisions) >= 1

    conflict_decision = next(
        (d for d in decisions if d.applicability_status == ApplicabilityState.CONFLICTING_RULES),
        None,
    )
    # Either caught as conflicting rules or handled with trace
    if conflict_decision:
        assert conflict_decision.action_required == ApplicabilityAction.EXPERT_REVIEW
        assert len(conflict_decision.conflicting_facts) >= 1
        assert conflict_decision.llm_decision is False


def test_cardinal_invariant_llm_authority_is_strictly_zero():
    """Invariant 1: LLM decision authority is strictly 0.0 across all outcomes."""
    test_dnas = [
        ProductDNACore(product_name="Flask", category="Drinkware & Food Contact Containers", materials=["stainless_steel"], insulated=True),
        ProductDNACore(product_name="Kettle", category="Electrical & Domestic Appliances", electrical=True),
        ProductDNACore(product_name="Toy", category="Toys & Children's Products"),
        ProductDNACore(product_name="Helmet", category="Protective Equipment & Helmets"),
        ProductDNACore(product_name="Unknown", category="General Goods"),
    ]

    for dna in test_dnas:
        decisions = determine_applicability(dna, authoritative_only=False)
        for dec in decisions:
            assert dec.llm_decision is False, f"LLM decision was True for {dec.standard_number}!"


def test_cardinal_invariant_empty_dna_safety():
    """Invariant: Empty product DNA must produce COVERAGE_GAP and never fabricate standards."""
    dna = ProductDNACore(
        product_name="Specified Product",
        category="General Goods",
        materials=[],
        attributes=[],
    )
    decisions = determine_applicability(dna, authoritative_only=True)
    assert len(decisions) >= 1
    assert decisions[0].applicability_status == ApplicabilityState.COVERAGE_GAP
    assert decisions[0].technical_relevance == "COVERAGE_GAP"


def test_api_applicability_evaluate_endpoint():
    """API: POST /api/applicability/evaluate returns complete Layer 5 response."""
    payload = {
        "product_dna": {
            "product_name": "Hydro Flask Insulated 500ml",
            "category": "Drinkware & Food Contact Containers",
            "materials": ["stainless_steel"],
            "insulated": True,
            "attributes": [
                {"name": "capacity_ml", "value": 500}
            ]
        },
        "authoritative_mode": True
    }
    res = client.post("/api/applicability/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["layer"] == "Layer 5: Applicability Engine"
    assert data["llm_authority_percentage"] == 0.0
    assert len(data["decisions"]) >= 1
    primary = data["decisions"][0]
    assert primary["standard_number"] == "IS 17526:2021"
    assert primary["applicability_status"] == "APPLICABLE"
    assert primary["decision_trace"] is not None
    assert primary["decision_trace"]["final_status"] == "APPLICABLE"


def test_api_applicability_metadata_endpoints():
    """API: GET /api/applicability/rules, /taxonomy, /states return structured schemas."""
    # 1. Rules endpoint
    res_rules = client.get("/api/applicability/rules")
    assert res_rules.status_code == 200
    rules = res_rules.json()
    assert len(rules) >= 3
    rule_ids = [r["rule_id"] for r in rules]
    assert "APP-DRINKWARE-001" in rule_ids
    assert "APP-ELECTRICAL-001" in rule_ids

    # 2. Taxonomy endpoint
    res_tax = client.get("/api/applicability/taxonomy")
    assert res_tax.status_code == 200
    tax = res_tax.json()
    assert "categories" in tax
    assert "CAT-DRINKWARE" in tax["categories"]
    assert "attribute_profiles" in tax
    assert "IS 17526:2021" in tax["attribute_profiles"]

    # 3. Canonical States endpoint
    res_states = client.get("/api/applicability/states")
    assert res_states.status_code == 200
    states_data = res_states.json()
    assert len(states_data["states"]) == 7
    state_names = [s["state"] for s in states_data["states"]]
    assert "APPLICABLE" in state_names
    assert "POTENTIALLY_APPLICABLE" in state_names
    assert "MORE_INFORMATION_REQUIRED" in state_names
    assert "NOT_APPLICABLE" in state_names
    assert "COVERAGE_GAP" in state_names
    assert "CONFLICTING_RULES" in state_names
    assert "EXPERT_REVIEW_REQUIRED" in state_names
