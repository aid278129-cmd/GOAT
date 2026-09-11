"""End-to-End Acceptance Test for Milestone M2:
Scenario:
User enters: 'We manufacture a double-wall stainless-steel vacuum flask for domestic drinking use.'
1. Extracts Product DNA
2. Identifies missing attributes (e.g. capacity_ml, specific grade)
3. Generates structured clarification question
4. User clarifies capacity and grade
5. Re-evaluates Product DNA preserving audit provenance
6. Applies deterministic applicability rules -> IS 17526:2021
7. Distinguishes Technical Relevance from Regulatory Mandate
8. Evaluates standard requirements using 8-state verdict and 4-state action model
9. Logs DecisionRecord with llm_decision = False
10. Builds React Flow Evidence Graph with real backend IDs
"""
import pytest
from backend.app.services.product_dna.extractor import extract_product_dna_from_text
from backend.app.services.clarification.engine import (
    detect_missing_attributes,
    apply_clarification_response,
)
from backend.app.services.applicability.engine import determine_applicability
from backend.app.services.gap_analysis.engine import evaluate_compliance_gaps
from backend.app.services.gap_analysis.graph_builder import build_evidence_graph
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.services.evaluation.m2_metrics import compute_m2_evaluation_metrics


def test_m2_end_to_end_acceptance_workflow():
    # Step 1: Initial User Prompt
    raw_prompt = "We manufacture a double-wall stainless-steel vacuum flask for domestic drinking use."
    dna = extract_product_dna_from_text(raw_prompt)

    assert dna.category == "Drinkware & Food Contact Containers"
    assert dna.insulated is True
    assert dna.intended_use == "domestic_drinking"

    # Step 2: Missing Information Detection
    clarifications = detect_missing_attributes(dna)
    assert len(clarifications) >= 1
    missing_fields = [c.attribute_name for c in clarifications]
    assert "capacity_ml" in missing_fields

    # Step 3: Clarification Loop (User provides 750 ml)
    updated_dna = apply_clarification_response(
        dna=dna,
        attribute_name="capacity_ml",
        raw_value="750 ml",
        source_type="USER",
    )
    cap_attr = next(a for a in updated_dna.attributes if a.name == "capacity_ml")
    assert cap_attr.value == 750
    assert cap_attr.unit == "ml"
    assert cap_attr.provenance.extraction_method == "user_clarification"

    # Step 4: Deterministic Applicability Engine
    applicability = determine_applicability(updated_dna, authoritative_only=False)
    assert len(applicability) >= 1
    primary_app = applicability[0]

    # Step 5: Separation of Technical Relevance vs Regulatory Mandate
    assert primary_app.standard_number == "IS 17526:2021"
    assert primary_app.technical_relevance == "LIKELY_APPLICABLE"
    assert primary_app.regulatory_status == "VERIFIED_MANDATORY_QCO"
    assert primary_app.matched_rule_id == "APP-DRINKWARE-001"
    assert primary_app.llm_decision is False  # LLM has ZERO decision authority

    # Step 6: Requirement Comparator & Compliance Gap Engine
    catalog = [
        {
            "id": "req-4-2-1",
            "clause_number": "4.2.1",
            "clause_title": "Stainless Steel Parts",
            "code": "REQ-MAT-304",
            "requirement_type": "MATERIAL",
            "description": "All metallic parts in direct contact with food shall be manufactured from Stainless Steel Grade 304 or superior.",
            "measurable_condition": "Grade 304 of IS 6911",
        },
        {
            "id": "req-5-4",
            "clause_number": "5.4",
            "clause_title": "Thermal Performance Test",
            "code": "REQ-PERF-THERM",
            "requirement_type": "PERFORMANCE",
            "description": "Temperature shall not be less than 60 deg C after 6 hours.",
            "measurable_condition": ">= 60 deg C after 6 hours",
        },
    ]

    comp_eval = evaluate_compliance_gaps(
        standard_number=primary_app.standard_number,
        standard_title=primary_app.standard_title,
        requirements_catalog=catalog,
        dna=updated_dna,
    )

    assert comp_eval.total_requirements == 2
    # Clause 4.2.1 without mill certificate -> MORE_INFORMATION_REQUIRED or POTENTIALLY_SATISFIED
    assert comp_eval.evaluations[0].status in [
        ComplianceStatus.POTENTIALLY_SATISFIED,
        ComplianceStatus.MORE_INFORMATION_REQUIRED,
    ]
    # Clause 5.4 physical test required -> POTENTIALLY_SATISFIED + REQUIRES_TESTING
    assert comp_eval.evaluations[1].status == ComplianceStatus.POTENTIALLY_SATISFIED
    assert comp_eval.evaluations[1].recommended_action == RecommendedAction.REQUIRES_TESTING

    # Step 7: Decision Attribution & LLM Dependence Metrics
    decisions_log = [
        {
            "decision_id": f"dec-{ev.requirement_id}",
            "decision_engine": ev.decision_engine,
            "llm_decision": ev.llm_decision,
            "status": ev.status.value,
        }
        for ev in comp_eval.evaluations
    ]
    metrics = compute_m2_evaluation_metrics(decisions_log)
    assert metrics.llm_metrics.total_decisions == 2
    assert metrics.llm_metrics.deterministic_decisions == 2
    assert metrics.llm_metrics.llm_decision_authority == 0
    assert metrics.llm_metrics.llm_dependence_percentage == 0.0

    # Step 8: React Flow Evidence Graph Generation
    graph = build_evidence_graph("prod-test-001", updated_dna, applicability, comp_eval)
    assert len(graph.nodes) >= 6
    assert len(graph.edges) >= 5
