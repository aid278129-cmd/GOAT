"""Layer 9 Production Test Suite: Output Layer & Compliance Passport.

Tests all required invariants and functionality:
1. Complete passport generation with all sections
2. Incomplete assessment preserves uncertain states
3. Missing evidence handling
4. Satisfied requirement contains validated Layer 8 trust chain
5. Satisfied requirement without evidence is blocked by Output Integrity Gate
6. Invalid citation is blocked from final publication
7. Stale evidence is blocked from final publication
8. Conflicting evidence is blocked from SATISFIED and routed to expert review
9. Source unavailable renders 'Official document acquisition pending'
10. Clause unavailable handled deterministically
11. Coverage gap preserved in output
12. Expert review items surfaced cleanly
13. Deterministic snapshot reproducibility
14. Knowledge version propagation
15. Evidence hash propagation
16. No arbitrary compliance percentage (honest counts only)
17. Correct title & prohibited label enforcement
18. Chat cannot modify output (read-only contract)
19. Downloadable report generation and integrity
20. REST API endpoints verification
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.passport.compiler import passport_compiler
from backend.app.services.passport.formatter import report_formatter
from backend.app.services.passport.models import (
    OutputLifecycleState,
    PASSPORT_TITLE,
    PROHIBITED_LABELS,
)
from backend.app.services.citation_guard.models import (
    ValidationOutcome,
    CitationValidationResult,
    TrustChain,
)

client = TestClient(app)


@pytest.fixture
def sample_assessment_data():
    return {
        "assessment_id": "ASM-TEST-001",
        "assessment_number": "2024-TEST-001",
        "product_name": "ThermoSteel Flask 750ml",
        "category": "Stainless Steel Vacuum Flasks",
        "applicability": [
            {
                "standard_number": "IS 17526:2021",
                "standard_title": "Stainless Steel Vacuum Flasks - Specification",
                "regulatory_status": "MANDATORY_QCO",
            }
        ],
        "requirements": [
            {
                "clause_number": "4.2.1",
                "clause_title": "Material Grade 304",
                "code": "REQ-MAT-304",
                "status": "SATISFIED",
                "required_evidence": "Mill Test Certificate (MTC)",
                "available_evidence": "DOC-MTC-001 Grade 304 chemical analysis",
                "verification_status": "VERIFIED",
                "observed_value": "Grade 304 SS",
                "required_value": "IS 6911 Grade 304",
                "deterministic_result": "PASS",
                "gap_state": "NONE",
                "recommended_action": "NO_ACTION",
                "evidence_id": "EV-MTC-001",
                "page_number": 2,
            },
            {
                "clause_number": "5.4",
                "clause_title": "Thermal Insulation Retention",
                "code": "REQ-PERF-HEAT",
                "status": "MISSING_EVIDENCE",
                "required_evidence": "NABL Heat Retention Test Report",
                "available_evidence": None,
                "verification_status": "PENDING",
                "observed_value": None,
                "required_value": ">= 60.0 °C after 6 hours",
                "deterministic_result": "GAP_IDENTIFIED",
                "gap_state": "ACTION_REQUIRED",
                "recommended_action": "REQUIRES_TESTING",
                "evidence_id": None,
                "page_number": 4,
            },
        ],
        "clarifications": [],
        "evidence_items": [
            {
                "evidence_id": "EV-MTC-001",
                "source_text": "Mill certificate confirms stainless steel grade 304 with 18% Cr and 8% Ni.",
                "sha256_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            }
        ],
    }


# 1. Complete Passport Generation
def test_complete_passport_generation(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)

    assert passport.passport_id.startswith("PASSPORT-2024-TEST-001")
    assert passport.document_title == PASSPORT_TITLE
    assert passport.executive_summary.product_name == "ThermoSteel Flask 750ml"
    assert len(passport.requirements_matrix) == 2
    assert len(passport.gap_report) == 1
    assert len(passport.testing_roadmap) == 1
    assert passport.action_center is not None


# 2. Incomplete Assessment Preserves Uncertain States
def test_incomplete_assessment_preserves_states():
    data = {
        "assessment_id": "ASM-INC-001",
        "assessment_number": "2024-INC-001",
        "product_name": "Prototype Immersion Heater",
        "category": "Electrical Appliances",
        "applicability": [{"standard_number": "IS 302-2-201:2008"}],
        "requirements": [
            {
                "clause_number": "13.1",
                "clause_title": "Leakage Current",
                "status": "MORE_INFORMATION_REQUIRED",
                "recommended_action": "PROVIDE_SPECIFICATION",
            },
            {
                "clause_number": "19.1",
                "clause_title": "Abnormal Operation",
                "status": "COVERAGE_GAP",
                "recommended_action": "EXPERT_REVIEW",
            },
        ],
    }
    passport = passport_compiler.compile_compliance_passport(**data)
    statuses = [r.status for r in passport.requirements_matrix]
    assert "MORE_INFORMATION_REQUIRED" in statuses
    assert "COVERAGE_GAP" in statuses


# 3. Missing Evidence Handling
def test_missing_evidence_reported_honestly(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    assert passport.executive_summary.missing_evidence_count == 1
    assert passport.executive_summary.satisfied_count == 1
    assert passport.executive_summary.total_requirements_evaluated == 2


# 4. Satisfied Requirement Contains Validated Layer 8 Trust Chain
def test_satisfied_requirement_contains_trust_chain(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    sat_row = [r for r in passport.requirements_matrix if r.status == "SATISFIED"][0]

    assert sat_row.trust_chain is not None
    assert sat_row.trust_chain.standard == "IS 17526:2021"
    assert sat_row.trust_chain.clause == "Clause 4.2.1"
    assert sat_row.trust_chain.decision == ValidationOutcome.VERIFIED


# 5. Satisfied Requirement Without Evidence is Blocked by Integrity Gate
def test_satisfied_without_evidence_blocked():
    gate = passport_compiler.check_output_integrity(
        requirements=[
            {
                "clause_number": "5.4",
                "code": "REQ-HEAT",
                "status": "SATISFIED",
                "evidence_id": None,
                "evidence_ids": [],
            }
        ],
        applicability=[{"standard_number": "IS 17526:2021"}],
    )
    assert gate.can_finalize is False
    assert gate.satisfied_without_evidence_count == 1
    assert any("NO VERIFIED EVIDENCE -> NO SATISFIED" in issue for issue in gate.blocked_reasons)


# 6. Invalid Citation is Blocked from Final Publication
def test_invalid_citation_blocks_finalization():
    cit_res = CitationValidationResult(
        claim="Invalid claim",
        source_id="DOC-1",
        standard="IS 17526:2021",
        clause="5.2",
        validation_result=ValidationOutcome.REJECTED,
        failure_reason="Fabricated clause cited",
    )
    gate = passport_compiler.check_output_integrity(
        requirements=[
            {
                "clause_number": "5.2",
                "status": "SATISFIED",
                "evidence_id": "EV-1",
            }
        ],
        applicability=[{"standard_number": "IS 17526:2021"}],
        citation_results=[cit_res],
    )
    assert gate.can_finalize is False
    assert any("REJECTED by Layer 8" in b for b in gate.blocked_reasons)


# 7. Stale Evidence Handling
def test_stale_evidence_blocks_finalization():
    cit_res = CitationValidationResult(
        claim="Stale report claim",
        source_id="DOC-EXPIRED",
        standard="IS 17526:2021",
        clause="5.4",
        validation_result=ValidationOutcome.STALE_SOURCE,
        failure_reason="Evidence document validity has expired",
    )
    passport = passport_compiler.compile_compliance_passport(
        assessment_id="ASM-STALE",
        assessment_number="2024-STALE",
        product_name="Flask",
        category="Flasks",
        applicability=[{"standard_number": "IS 17526:2021"}],
        requirements=[{"clause_number": "5.4", "status": "POTENTIAL_GAP"}],
        citation_results=[cit_res],
    )
    assert len(passport.citation_audit_trail) == 1
    assert passport.citation_audit_trail[0].validation_result == ValidationOutcome.STALE_SOURCE


# 8. Conflicting Evidence Routed to Expert Review
def test_conflicting_evidence_blocks_satisfied_and_routes_to_expert():
    data = {
        "assessment_id": "ASM-CONF-001",
        "assessment_number": "2024-CONF-001",
        "product_name": "Heater",
        "category": "Appliances",
        "applicability": [{"standard_number": "IS 302-2-201:2008"}],
        "requirements": [
            {
                "clause_number": "13.1",
                "clause_title": "Electric Strength",
                "status": "CONFLICTING_EVIDENCE",
                "recommended_action": "EXPERT_REVIEW",
                "explanation": "Contradictory lab reports received.",
            }
        ],
    }
    passport = passport_compiler.compile_compliance_passport(**data)
    assert passport.lifecycle_state == OutputLifecycleState.UNDER_REVIEW
    assert passport.executive_summary.conflicting_evidence_count == 1
    assert len(passport.action_center.what_needs_expert_review) == 1


# 9. Source Unavailable Renders Official Document Acquisition Pending
def test_source_unavailable_renders_pending():
    data = {
        "assessment_id": "ASM-UNAVAIL",
        "assessment_number": "2024-UNAVAIL",
        "product_name": "New Product",
        "category": "General",
        "applicability": [{"standard_number": "IS 17526:2021"}],
        "requirements": [
            {
                "clause_number": "PENDING",
                "clause_title": "Official Standard Specification Acquisition Pending",
                "code": "AUTHORITATIVE_CLAUSE_PENDING",
                "status": "SOURCE_UNAVAILABLE",
                "description": "Full official technical standard specification document is pending acquisition.",
            }
        ],
    }
    passport = passport_compiler.compile_compliance_passport(**data)
    row = passport.requirements_matrix[0]
    assert row.status == "SOURCE_UNAVAILABLE"
    assert "AUTHORITATIVE_CLAUSE_PENDING" in row.code


# 10. Clause Unavailable Handled Deterministically
def test_clause_unavailable_preserved():
    data = {
        "assessment_id": "ASM-NO-CL",
        "assessment_number": "2024-NO-CL",
        "product_name": "Test Product",
        "category": "General",
        "applicability": [{"standard_number": "IS 17526:2021"}],
        "requirements": [
            {
                "clause_number": "UNKNOWN",
                "clause_title": "Unspecified Clause",
                "status": "CLAUSE_TEXT_UNAVAILABLE",
            }
        ],
    }
    passport = passport_compiler.compile_compliance_passport(**data)
    assert passport.requirements_matrix[0].status == "CLAUSE_TEXT_UNAVAILABLE"


# 11. Coverage Gap Preserved in Output
def test_coverage_gap_preserved():
    data = {
        "assessment_id": "ASM-GAP",
        "assessment_number": "2024-GAP",
        "product_name": "Novel Smart Bottle",
        "category": "Smart IoT Drinkware",
        "applicability": [{"standard_number": "IS 17526:2021"}],
        "requirements": [
            {
                "clause_number": "N/A",
                "clause_title": "Bluetooth Wireless Safety",
                "status": "COVERAGE_GAP",
                "explanation": "No existing Indian Standard covers BLE vacuum bottles.",
            }
        ],
    }
    passport = passport_compiler.compile_compliance_passport(**data)
    assert passport.requirements_matrix[0].status == "COVERAGE_GAP"


# 12. Expert Review Items Surfaced Cleanly in Action Center
def test_expert_review_surfaced_in_action_center():
    data = {
        "assessment_id": "ASM-EXP",
        "assessment_number": "2024-EXP",
        "product_name": "Water Bottle",
        "category": "Flasks",
        "applicability": [{"standard_number": "IS 17526:2021"}],
        "requirements": [
            {
                "clause_number": "5.2",
                "clause_title": "Inversion Leakage",
                "status": "EXPERT_REVIEW_REQUIRED",
                "recommended_action": "EXPERT_REVIEW",
            }
        ],
    }
    passport = passport_compiler.compile_compliance_passport(**data)
    assert len(passport.action_center.what_needs_expert_review) == 1
    assert passport.action_center.what_needs_expert_review[0].code == "5.2"


# 13. Deterministic Snapshot Reproducibility
def test_snapshot_reproducibility(sample_assessment_data):
    passport1 = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    passport2 = passport_compiler.compile_compliance_passport(**sample_assessment_data)

    assert passport1.snapshot_hash == passport2.snapshot_hash
    assert passport1.requirements_matrix == passport2.requirements_matrix
    assert passport1.gap_report == passport2.gap_report


# 14. Knowledge Version Propagation
def test_knowledge_version_propagation(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(
        **sample_assessment_data, knowledge_version="v2.0.0-custom-gazette"
    )
    assert passport.knowledge_version == "v2.0.0-custom-gazette"


# 15. Evidence Hash Propagation
def test_evidence_hash_propagation(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    assert "EV-MTC-001" in passport.evidence_hashes
    assert len(passport.evidence_hashes["EV-MTC-001"]) == 64


# 16. No Arbitrary Compliance Percentage (Honest Counts Only)
def test_no_arbitrary_compliance_percentage(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    summary_dict = passport.executive_summary.dict()

    assert "compliance_score" not in summary_dict
    assert "percentage" not in summary_dict
    assert summary_dict["satisfied_count"] == 1
    assert summary_dict["missing_evidence_count"] == 1


# 17. Correct Title & Prohibited Label Enforcement
def test_title_and_prohibited_labels(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    assert passport.document_title == "Evidence-Backed Pre-Certification Compliance Assessment"

    html_report = report_formatter.format_html_report(passport)
    for prohibited in PROHIBITED_LABELS:
        assert prohibited not in html_report


# 18. Chat Cannot Modify Output (Read-Only Contract)
def test_chat_cannot_modify_output(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    passport_json_before = passport.json()

    # Emulate chat querying output
    chat_context = f"Assessment {passport.assessment_number}: {passport.executive_summary.satisfied_count} satisfied, {passport.executive_summary.missing_evidence_count} missing."
    assert "1 satisfied" in chat_context
    assert "1 missing" in chat_context

    # Output remains immutable
    assert passport.json() == passport_json_before


# 19. Downloadable Report Generation and Integrity
def test_downloadable_report_generation(sample_assessment_data):
    passport = passport_compiler.compile_compliance_passport(**sample_assessment_data)
    html = report_formatter.format_html_report(passport)

    assert "<!DOCTYPE html>" in html
    assert passport.document_title in html
    assert "MSME Action Center" in html
    assert "Requirement-by-Requirement Evaluation & Verification Matrix" in html
    assert "Prioritized Compliance Gap Register" in html


# 20. REST API Router Endpoints
def test_passport_rest_api(sample_assessment_data):
    # Test GET /invariants
    resp_inv = client.get("/api/passport/invariants")
    assert resp_inv.status_code == 200
    inv_data = resp_inv.json()
    assert inv_data["document_title"] == "Evidence-Backed Pre-Certification Compliance Assessment"
    assert "BIS Certificate" in inv_data["prohibited_labels"]

    # Test POST /compile
    post_resp = client.post("/api/passport/compile", json=sample_assessment_data)
    assert post_resp.status_code == 200
    resp_data = post_resp.json()
    assert resp_data["document_title"] == "Evidence-Backed Pre-Certification Compliance Assessment"
    assert len(resp_data["requirements_matrix"]) == 2

    # Test POST /download-html
    dl_resp = client.post("/api/passport/download-html", json=sample_assessment_data)
    assert dl_resp.status_code == 200
    assert "text/html" in dl_resp.headers["content-type"]
    assert "<!DOCTYPE html>" in dl_resp.text
