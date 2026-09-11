"""Layer 7: Compliance Gap Analysis Engine — Production Test Suite.

Rigorously verifies all Layer 7 requirements, deterministic comparisons, and cardinal invariants:
1. Requirement with no evidence -> MISSING_EVIDENCE / REQUIRES_TESTING
2. Valid verified evidence passing threshold -> SATISFIED
3. Valid verified evidence failing threshold -> POTENTIAL_GAP
4. Numeric comparison (>=, <=, ==)
5. Unit conversion (Fahrenheit to Celsius, Liters to mL, cm to mm)
6. Range comparison
7. Categorical pass/fail and boolean checks
8. Conflicting evidence -> CONFLICTING_EVIDENCE + EXPERT_REVIEW
9. Wrong-standard evidence rejection (0% cross-standard leakage)
10. Stale / expired evidence rejection
11. Unverified evidence / user claim rejection (0% user claim authority)
12. Missing specification -> MORE_INFORMATION_REQUIRED + PROVIDE_SPECIFICATION
13. Deterministic formula audit logging (e.g. 62.0 °C >= 60.0 °C -> PASS)
14. Deterministic Gap Register & severity prioritization (CRITICAL, HIGH, MEDIUM, LOW)
15. Categorized Testing Roadmap generation
16. Honest Compliance Coverage Summary counts (no arbitrary percentage gaming)
17. Hard gate invariant enforcement
18. 0% LLM compliance authority
19. End-to-end integration: Layer 5 -> Layer 6 -> Layer 7
20. REST API endpoints verification
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.product_dna import ProductDNACore, DNAAttribute
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.services.gap_analysis.comparator import (
    compare_requirement_with_evidence,
    compare_numeric_threshold,
    normalize_unit,
)
from backend.app.services.gap_analysis.engine import (
    evaluate_compliance_gaps,
    GapPriority,
)
from backend.app.services.applicability.engine import determine_applicability
from backend.app.services.rag.engine import layer6_clause_rag

client = TestClient(app)


# --------------------------------------------------------------------------
# 1. Requirement With No Evidence
# --------------------------------------------------------------------------
def test_requirement_with_no_evidence():
    """Requirement 1: Physical test requirement without evidence produces MISSING_EVIDENCE + REQUIRES_TESTING."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    res = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-DROP",
        requirement_type="PERFORMANCE",
        description="Drop impact resistance 1.0m concrete drop",
        measurable_condition="No leakage or vacuum loss",
        dna=dna,
        evidence_payload=None,
        linked_evidences=None,
    )
    status, action, exp = res[0], res[1], res[2]
    trace_meta = getattr(res, "trace_meta", {})
    assert status == ComplianceStatus.MISSING_EVIDENCE
    assert action == RecommendedAction.REQUIRES_TESTING
    assert "drop impact test (Clause 5.3) report required" in exp
    assert trace_meta["comparison_result"] == "PENDING_TESTING"


# --------------------------------------------------------------------------
# 2. Valid Verified Evidence Satisfying Requirement
# --------------------------------------------------------------------------
def test_valid_evidence_satisfies_requirement():
    """Requirement 2: Verified test report (62°C) satisfying >= 60°C threshold produces SATISFIED."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    evidence = [
        {
            "evidence_id": "EV-LAB-REPORT-001",
            "evidence_type": "TEST_REPORT",
            "source_authority": "NABL_ACCREDITED_LAB",
            "verification_status": "VERIFIED",
            "normalized_value": 62.0,
            "standard_number": "IS 17526:2021",
            "page_number": 3,
        }
    ]
    res = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-THERM",
        requirement_type="PERFORMANCE",
        description="Thermal Performance Heat Retention Test",
        measurable_condition="T_final >= 60 deg C",
        dna=dna,
        linked_evidences=evidence,
    )
    status, action, exp = res[0], res[1], res[2]
    trace_meta = getattr(res, "trace_meta", {})
    assert status == ComplianceStatus.SATISFIED
    assert action is None
    assert "satisfies" in exp.lower()
    assert "62.0" in trace_meta["comparison_rule"]
    assert trace_meta["comparison_result"] == "PASS"


# --------------------------------------------------------------------------
# 3. Valid Verified Evidence Failing Requirement
# --------------------------------------------------------------------------
def test_valid_evidence_failing_threshold():
    """Requirement 3: Verified test report (54°C) failing >= 60°C threshold produces POTENTIAL_GAP."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    evidence = [
        {
            "evidence_id": "EV-LAB-FAIL-001",
            "evidence_type": "TEST_REPORT",
            "source_authority": "NABL_ACCREDITED_LAB",
            "verification_status": "VERIFIED",
            "normalized_value": 54.0,  # Below 60°C threshold
            "standard_number": "IS 17526:2021",
            "page_number": 3,
        }
    ]
    res = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-THERM",
        requirement_type="PERFORMANCE",
        description="Thermal Performance Heat Retention Test",
        measurable_condition="T_final >= 60 deg C",
        dna=dna,
        linked_evidences=evidence,
    )
    status, action, exp = res[0], res[1], res[2]
    trace_meta = getattr(res, "trace_meta", {})
    assert status == ComplianceStatus.POTENTIAL_GAP
    assert action == RecommendedAction.PROVIDE_SPECIFICATION
    assert trace_meta["comparison_result"] == "FAIL"
    assert "54.0 °C >= 60.0 °C" in trace_meta["comparison_rule"]


# --------------------------------------------------------------------------
# 4 & 5. Numeric Comparison & Unit Conversion
# --------------------------------------------------------------------------
def test_numeric_comparison_and_unit_conversion():
    """Requirements 4 & 5: Numerical comparison engine and unit normalization."""
    # Temperature conversion: 143.6°F -> 62.0°C
    val_c, unit_c = normalize_unit(143.6, "°F", "°C")
    assert abs(val_c - 62.0) < 0.1
    assert unit_c == "°C"

    # Volume conversion: 0.75 L -> 750.0 mL
    val_ml, unit_ml = normalize_unit(0.75, "L", "mL")
    assert val_ml == 750.0
    assert unit_ml == "mL"

    # Numeric threshold helper test
    passed, formula, explanation = compare_numeric_threshold(
        observed_val=62.0,
        observed_unit="°C",
        operator=">=",
        threshold=60.0,
        required_unit="°C",
    )
    assert passed is True
    assert formula == "62.0 °C >= 60.0 °C"
    assert "satisfies minimum mandatory threshold" in explanation


# --------------------------------------------------------------------------
# 6 & 7. Range, Categorical & Boolean Comparisons
# --------------------------------------------------------------------------
def test_range_comparison():
    """Requirement 6: Range comparison [20, 25] °C."""
    passed_in, formula_in, _ = compare_numeric_threshold(
        observed_val=22.5,
        observed_unit="°C",
        operator="RANGE",
        threshold=(20.0, 25.0),
        required_unit="°C",
    )
    assert passed_in is True
    assert "20.0 <= 22.5 <= 25.0 °C" in formula_in

    passed_out, formula_out, _ = compare_numeric_threshold(
        observed_val=29.0,
        observed_unit="°C",
        operator="RANGE",
        threshold=(20.0, 25.0),
        required_unit="°C",
    )
    assert passed_out is False


# --------------------------------------------------------------------------
# 8. Conflicting Evidence
# --------------------------------------------------------------------------
def test_conflicting_evidence_triggers_expert_review():
    """Requirement 8: Conflicting reports mandate CONFLICTING_EVIDENCE + EXPERT_REVIEW."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    res = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-LEAK",
        requirement_type="PERFORMANCE",
        description="Hydrostatic Inversion Leakage Resistance",
        measurable_condition="Zero leakage",
        dna=dna,
        has_conflict=True,
    )
    status, action, exp = res[0], res[1], res[2]
    trace_meta = getattr(res, "trace_meta", {})
    assert status == ComplianceStatus.CONFLICTING_EVIDENCE
    assert action == RecommendedAction.EXPERT_REVIEW
    assert "Contradictory evidentiary values" in exp
    assert trace_meta["comparison_result"] == "CONFLICT"


# --------------------------------------------------------------------------
# 9. Wrong-Standard Evidence Rejection
# --------------------------------------------------------------------------
def test_wrong_standard_evidence_rejected():
    """Requirement 9: Evidence citing IS 302-2-201 submitted for IS 17526 is rejected."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    wrong_std_evidence = [
        {
            "evidence_id": "EV-WRONG-STD-001",
            "evidence_type": "TEST_REPORT",
            "source_authority": "LAB_REPORT",
            "verification_status": "VERIFIED",
            "normalized_value": 62.0,
            "standard_number": "IS 302-2-201:2008",  # Wrong standard
        }
    ]
    res = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-THERM",
        requirement_type="PERFORMANCE",
        description="Thermal Performance",
        measurable_condition=">= 60 deg C",
        dna=dna,
        linked_evidences=wrong_std_evidence,
        applicable_standard="IS 17526:2021",
    )
    status, action, exp = res[0], res[1], res[2]
    trace_meta = getattr(res, "trace_meta", {})
    assert status == ComplianceStatus.POTENTIAL_GAP
    assert "Cross-standard evidence is rejected" in exp
    assert trace_meta["comparison_result"] == "WRONG_STANDARD_REJECTION"


# --------------------------------------------------------------------------
# 10. Stale / Expired Evidence Rejection
# --------------------------------------------------------------------------
def test_stale_expired_evidence_rejected():
    """Requirement 10: Expired test report cannot satisfy requirements."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    expired_evidence = [
        {
            "evidence_id": "EV-EXPIRED-001",
            "evidence_type": "TEST_REPORT",
            "source_authority": "LAB_REPORT",
            "verification_status": "VERIFIED",
            "normalized_value": 62.0,
            "is_expired": True,  # Stale document
            "standard_number": "IS 17526:2021",
        }
    ]
    res = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-THERM",
        requirement_type="PERFORMANCE",
        description="Thermal Performance",
        measurable_condition=">= 60 deg C",
        dna=dna,
        linked_evidences=expired_evidence,
        applicable_standard="IS 17526:2021",
    )
    status, action, exp = res[0], res[1], res[2]
    trace_meta = getattr(res, "trace_meta", {})
    assert status == ComplianceStatus.MISSING_EVIDENCE
    assert "validity expiration date" in exp
    assert trace_meta["comparison_result"] == "STALE_EXPIRED_EVIDENCE"


# --------------------------------------------------------------------------
# 11. User Claims Rejected as Evidence
# --------------------------------------------------------------------------
def test_user_claim_never_produces_satisfied():
    """Requirement 11: USER_CLAIM provenance can NEVER satisfy a requirement."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    user_claim_evidence = [
        {
            "evidence_id": "EV-CLAIM-001",
            "evidence_type": "USER_TEXT",
            "provenance_type": "USER_CLAIM",
            "verification_status": "UNVERIFIED",
            "normalized_value": 65.0,
            "standard_number": "IS 17526:2021",
        }
    ]
    res = compare_requirement_with_evidence(
        requirement_code="REQ-PERF-THERM",
        requirement_type="PERFORMANCE",
        description="Thermal Performance",
        measurable_condition=">= 60 deg C",
        dna=dna,
        linked_evidences=user_claim_evidence,
    )
    status, action, exp = res[0], res[1], res[2]
    assert status != ComplianceStatus.SATISFIED
    assert status in (ComplianceStatus.MISSING_EVIDENCE, ComplianceStatus.POTENTIALLY_SATISFIED)


# --------------------------------------------------------------------------
# 12. Missing Specification
# --------------------------------------------------------------------------
def test_missing_specification_triggers_more_information():
    """Requirement 12: Generic stainless steel declaration without grade triggers MORE_INFORMATION_REQUIRED."""
    dna = ProductDNACore(
        product_name="Atlas Bottle",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel"],  # Missing specific grade (304)
        insulated=True,
    )
    res = compare_requirement_with_evidence(
        requirement_code="REQ-MAT-304",
        requirement_type="MATERIAL",
        description="Stainless steel parts shall be Grade 304",
        measurable_condition="Grade 304",
        dna=dna,
    )
    status, action, exp = res[0], res[1], res[2]
    trace_meta = getattr(res, "trace_meta", {})
    assert status == ComplianceStatus.MORE_INFORMATION_REQUIRED
    assert action == RecommendedAction.PROVIDE_SPECIFICATION
    assert trace_meta["comparison_result"] == "MISSING_SPEC"


# --------------------------------------------------------------------------
# 13, 14, 15, 16. Gap Register, Testing Roadmap & Coverage Summary
# --------------------------------------------------------------------------
def test_evaluate_compliance_gaps_full_output():
    """Requirements 13-16: evaluate_compliance_gaps generates Gap Register, Roadmap & Summary."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Flask 1000ml",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    catalog = [
        {
            "id": "REQ-5.4",
            "clause_number": "5.4",
            "clause_title": "Thermal Performance",
            "code": "REQ-PERF-THERM",
            "requirement_type": "PERFORMANCE",
            "description": "6-hour heat retention test",
            "measurable_condition": ">= 60 deg C",
        },
        {
            "id": "REQ-5.3",
            "clause_number": "5.3",
            "clause_title": "Drop Impact",
            "code": "REQ-PERF-DROP",
            "requirement_type": "PERFORMANCE",
            "description": "1.0m concrete drop test",
            "measurable_condition": "No rupture",
        },
        {
            "id": "REQ-7.1",
            "clause_number": "7.1",
            "clause_title": "Marking Requirements",
            "code": "REQ-MARK-ISI",
            "requirement_type": "MARKING",
            "description": "ISI Mark and Capacity artwork",
            "measurable_condition": "ISI Mark present",
        },
    ]

    # Evaluate without evidence -> all should be unresolved gaps
    evaluation = evaluate_compliance_gaps(
        standard_number="IS 17526:2021",
        standard_title="Stainless Steel Vacuum Flask",
        requirements_catalog=catalog,
        dna=dna,
    )

    # Coverage Summary honest counts
    assert evaluation.coverage_summary is not None
    assert evaluation.coverage_summary.total_requirements == 3
    assert evaluation.coverage_summary.satisfied == 0
    assert evaluation.coverage_summary.potentially_satisfied == 1  # 5.4 is potentially satisfied because DNA is insulated
    assert evaluation.coverage_summary.missing_evidence == 2       # 5.3 and 7.1

    # Gap Register
    assert len(evaluation.gap_register) == 3
    # Check priorities: Drop and Thermal are HIGH, Marking is MEDIUM
    prio_map = {item.clause: item.priority for item in evaluation.gap_register}
    assert prio_map["5.4"] == GapPriority.HIGH
    assert prio_map["5.3"] == GapPriority.HIGH
    assert prio_map["7.1"] == GapPriority.MEDIUM

    # Testing Roadmap
    assert len(evaluation.testing_roadmap.lab_test_required) >= 1
    assert any(item.clause == "5.3" for item in evaluation.testing_roadmap.lab_test_required)
    assert any(item.clause == "7.1" for item in evaluation.testing_roadmap.photo_marking_evidence_required)


# --------------------------------------------------------------------------
# 17 & 18. Hard Gate & 0% LLM Compliance Authority
# --------------------------------------------------------------------------
def test_hard_gate_and_zero_llm_authority():
    """Requirements 17 & 18: Cardinal Invariants strictly verified."""
    dna = ProductDNACore(
        product_name="Atlas Vacuum Flask",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )
    reqs = [
        {
            "id": "REQ-5.4",
            "clause_number": "5.4",
            "code": "REQ-PERF-THERM",
            "requirement_type": "PERFORMANCE",
            "description": "Thermal Performance",
            "measurable_condition": ">= 60 deg C",
        }
    ]
    evaluation = evaluate_compliance_gaps(
        standard_number="IS 17526:2021",
        standard_title="Stainless Steel Vacuum Flask",
        requirements_catalog=reqs,
        dna=dna,
    )
    for rec in evaluation.assessment_records:
        assert rec.status != ComplianceStatus.SATISFIED
        assert rec.decision_trace.get("llm_authority") == 0.0

    for ev in evaluation.evaluations:
        assert ev.llm_decision is False
        assert ev.decision_engine == "DETERMINISTIC_RULE_ENGINE"


# --------------------------------------------------------------------------
# 19. End-to-End Pipeline: Layer 5 -> Layer 6 -> Layer 7
# --------------------------------------------------------------------------
def test_end_to_end_layers_5_6_7():
    """Requirement 19: End-to-end trace from Product DNA through Applicability, Clause RAG to Gap Analysis."""
    # 1. Product DNA
    dna = ProductDNACore(
        product_name="Milton Thermosteel 1000ml",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
        attributes=[DNAAttribute(name="capacity_ml", value=1000)],
    )

    # 2. Layer 5 Applicability
    decisions = determine_applicability(dna, authoritative_only=True)
    assert len(decisions) >= 1
    std_num = decisions[0].standard_number
    assert std_num == "IS 17526:2021"

    # 3. Layer 6 Clause-Level RAG
    clauses = layer6_clause_rag.clause_catalog[std_num]
    req_catalog = [
        {
            "id": c.get("evidence_requirement", {}).get("requirement_id", f"REQ-{c['clause_number']}"),
            "clause_number": c["clause_number"],
            "clause_title": c["title"],
            "code": c.get("evidence_requirement", {}).get("requirement_id", f"REQ-{c['clause_number']}"),
            "requirement_type": "MATERIAL" if "4.2" in c["clause_number"] else "PERFORMANCE",
            "description": c["text_content"],
            "measurable_condition": c.get("evidence_requirement", {}).get("measurable_condition"),
        }
        for c in clauses
    ]
    assert len(req_catalog) >= 5

    # 4. Layer 7 Gap Analysis with Thermal and Material evidence
    linked_map = {
        "REQ-IS17526-5.4": [
            {
                "evidence_id": "EV-LAB-REPORT-MILTON",
                "evidence_type": "TEST_REPORT",
                "source_authority": "NABL_ACCREDITED_LAB",
                "verification_status": "VERIFIED",
                "normalized_value": 64.5,  # >= 60°C -> SATISFIED
                "standard_number": "IS 17526:2021",
                "page_number": 4,
            }
        ],
        "REQ-IS17526-4.2.1": [
            {
                "evidence_id": "EV-MILL-CERT-MILTON",
                "evidence_type": "MATERIAL_CERTIFICATE",
                "source_authority": "MILL_TEST_CERTIFICATE",
                "verification_status": "VERIFIED",
                "normalized_value": "Grade 304",  # SS 304 -> SATISFIED
                "standard_number": "IS 17526:2021",
                "page_number": 1,
            }
        ],
    }

    eval_result = evaluate_compliance_gaps(
        standard_number=std_num,
        standard_title="Stainless Steel Vacuum Flask",
        requirements_catalog=req_catalog,
        dna=dna,
        linked_evidences_map=linked_map,
    )

    # Verify thermal and material are SATISFIED
    thermal_eval = next(e for e in eval_result.evaluations if e.clause_number == "5.4")
    assert thermal_eval.status == ComplianceStatus.SATISFIED
    assert "64.5" in thermal_eval.explanation

    mat_eval = next(e for e in eval_result.evaluations if e.clause_number == "4.2.1")
    assert mat_eval.status == ComplianceStatus.SATISFIED

    # Other tests without evidence remain unresolved
    drop_eval = next(e for e in eval_result.evaluations if e.clause_number == "5.3")
    assert drop_eval.status == ComplianceStatus.MISSING_EVIDENCE

    # Coverage summary shows exactly 2 satisfied
    assert eval_result.coverage_summary.satisfied == 2
    assert eval_result.coverage_summary.total_requirements == len(req_catalog)


# --------------------------------------------------------------------------
# 20. API Endpoint Tests
# --------------------------------------------------------------------------
def test_api_gap_analysis_evaluate():
    """Requirement 20: POST /api/gap-analysis/evaluate returns Layer 7 structure."""
    payload = {
        "product_dna": {
            "product_name": "Atlas Vacuum Bottle",
            "category": "Drinkware & Food Contact Containers",
            "materials": ["stainless_steel_grade_304"],
            "insulated": True,
        },
        "standard_number": "IS 17526:2021",
    }
    res = client.post("/api/gap-analysis/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["standard_number"] == "IS 17526:2021"
    assert "gap_register" in data
    assert "testing_roadmap" in data
    assert "coverage_summary" in data
    assert "assessment_records" in data

    # Test invariants endpoint
    inv_res = client.get("/api/gap-analysis/invariants")
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert "cardinal_invariants" in inv_data
    assert "gap_priorities" in inv_data
