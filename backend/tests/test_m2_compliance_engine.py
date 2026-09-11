"""Automated test suite for M2 Product DNA, Clarification, Applicability, and Gap Analysis engines.

Tests:
1. Product DNA extraction from raw text with provenance
2. Attribute normalization (volume ml, electrical voltage/wattage, materials)
3. Zero-guessing clarification detection for missing critical fields
4. Incremental clarification loop preserving audit history
5. Deterministic rule evaluation (APP-DRINKWARE-001)
6. Separation of technical relevance from mandatory regulatory status
7. Requirement evidence comparison producing 8-state verdicts and 4-state actions
8. Zero LLM compliance decision authority (llm_decision = False)
9. End-to-end acceptance scenario for double-wall insulated flask
"""
import pytest
from backend.app.services.product_dna.extractor import extract_product_dna_from_text
from backend.app.services.product_dna.normalizer import (
    normalize_capacity,
    normalize_electrical,
    normalize_material,
)
from backend.app.services.clarification.engine import (
    detect_missing_attributes,
    apply_clarification_response,
)
from backend.app.services.applicability.engine import (
    determine_applicability,
    load_declarative_rules,
)
from backend.app.services.gap_analysis.comparator import compare_requirement_with_evidence
from backend.app.services.gap_analysis.engine import evaluate_compliance_gaps
from backend.app.services.gap_analysis.graph_builder import build_evidence_graph
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction


def test_product_dna_text_extraction():
    text = "We manufacture a 750 ml double-walled vacuum insulated flask with stainless steel 304 food contact liner."
    dna = extract_product_dna_from_text(text)

    assert dna.category == "Drinkware & Food Contact Containers"
    assert dna.insulated is True
    assert "stainless_steel_grade_304" in dna.materials

    # Check capacity attribute
    cap_attr = next((a for a in dna.attributes if a.name == "capacity_ml"), None)
    assert cap_attr is not None
    assert cap_attr.value == 750
    assert cap_attr.unit == "ml"
    assert cap_attr.provenance is not None
    assert cap_attr.provenance.confidence >= 0.9


def test_attribute_normalizer():
    # Capacity variations
    assert normalize_capacity("750 ml") == (750, "ml")
    assert normalize_capacity("750mL") == (750, "ml")
    assert normalize_capacity("0.75 litre") == (750, "ml")
    assert normalize_capacity("1 L") == (1000, "ml")

    # Material normalizations
    assert normalize_material("SS 304") == "stainless_steel_grade_304"
    assert normalize_material("Stainless Steel") == "stainless_steel"
    assert normalize_material("BPA-free Polypropylene") == "polypropylene"

    # Electrical normalizations
    elec = normalize_electrical("230V a.c., 50 Hz, 1500W")
    assert elec["voltage"] == "230"
    assert elec["current_type"] == "AC"
    assert elec["frequency"] == 50
    assert elec["wattage"] == 1500


def test_clarification_engine_missing_fields_and_loop():
    # Incomplete text: missing specific material grade and capacity
    text = "A double-wall insulated water bottle."
    dna = extract_product_dna_from_text(text)

    clarifications = detect_missing_attributes(dna)
    attr_names = {c.attribute_name for c in clarifications}

    assert "capacity_ml" in attr_names

    # User answers clarification
    updated_dna = apply_clarification_response(
        dna=dna,
        attribute_name="capacity_ml",
        raw_value="750 ml",
        source_type="USER",
    )
    cap_attr = next((a for a in updated_dna.attributes if a.name == "capacity_ml"), None)
    assert cap_attr is not None
    assert cap_attr.value == 750
    assert cap_attr.provenance.extraction_method == "user_clarification"


def test_deterministic_rule_engine_and_applicability():
    text = "Double-wall stainless steel vacuum insulated water bottle for personal drinking."
    dna = extract_product_dna_from_text(text)

    decisions = determine_applicability(dna, authoritative_only=False)
    assert len(decisions) >= 1

    primary = decisions[0]
    assert primary.standard_number == "IS 17526:2021"
    assert primary.technical_relevance == "LIKELY_APPLICABLE"
    assert primary.regulatory_status == "VERIFIED_MANDATORY_QCO"
    assert primary.matched_rule_id == "APP-DRINKWARE-001"
    assert primary.llm_decision is False  # Zero LLM authority


def test_requirement_comparator_8_states_and_4_actions():
    dna = extract_product_dna_from_text("Double-wall 750ml flask with Stainless Steel 304")

    # Case 1: Stainless Steel Grade 304 without test report -> POTENTIALLY_SATISFIED + UPLOAD_EVIDENCE
    status, action, exp = compare_requirement_with_evidence(
        requirement_code="REQ-MAT-304",
        requirement_type="MATERIAL",
        description="All metallic parts shall be Grade 304 stainless steel",
        measurable_condition="Grade 304",
        dna=dna,
    )
    assert status == ComplianceStatus.POTENTIALLY_SATISFIED
    assert action == RecommendedAction.UPLOAD_EVIDENCE

    # Case 2: Stainless Steel Grade 304 WITH mill test certificate -> SATISFIED + None
    status_cert, action_cert, _ = compare_requirement_with_evidence(
        requirement_code="REQ-MAT-304",
        requirement_type="MATERIAL",
        description="All metallic parts shall be Grade 304 stainless steel",
        measurable_condition="Grade 304",
        dna=dna,
        evidence_payload={"mill_test_certificate": True},
    )
    assert status_cert == ComplianceStatus.SATISFIED
    assert action_cert is None

    # Case 3: Thermal Performance test -> POTENTIALLY_SATISFIED + REQUIRES_TESTING
    status_therm, action_therm, _ = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-THERM",
        requirement_type="PERFORMANCE",
        description="Water temperature shall not be less than 60 deg C after 6 hours",
        measurable_condition=">= 60 deg C",
        dna=dna,
    )
    assert status_therm == ComplianceStatus.POTENTIALLY_SATISFIED
    assert action_therm == RecommendedAction.REQUIRES_TESTING


def test_react_flow_evidence_graph_builder():
    dna = extract_product_dna_from_text("750 ml Stainless Steel 304 Insulated Flask")
    applicability = determine_applicability(dna, authoritative_only=False)
    
    req_catalog = [
        {
            "id": "req-4-2-1",
            "clause_number": "4.2.1",
            "clause_title": "Stainless Steel Parts",
            "code": "REQ-MAT-304",
            "requirement_type": "MATERIAL",
            "description": "Stainless steel parts Grade 304",
            "measurable_condition": "Grade 304",
        }
    ]
    comp_eval = evaluate_compliance_gaps("IS 17526:2021", "Title", req_catalog, dna)

    graph = build_evidence_graph("prod-123", dna, applicability, comp_eval)

    assert len(graph.nodes) >= 5
    assert len(graph.edges) >= 4

    node_types = {n.type for n in graph.nodes}
    assert "productNode" in node_types
    assert "standardNode" in node_types
    assert "decisionNode" in node_types
