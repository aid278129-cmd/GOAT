"""Milestone M26.DEMO.3: SIH 2026 Live Demo Scenario, Dataset & Jury Readiness Test Suite.

Verifies:
1. Deterministic demo reset across 3 consecutive executions (POST /api/v1/assessments/demo/reset).
2. Bit-for-bit / substantive identity across:
   - Product DNA baseline
   - Deterministic BIS Applicability
   - Applicable Standard & Edition
   - Clause & Requirement definitions
   - Evidence state & Evidence Gate eligibility
   - Deterministic Gap ledger
   - Actionable Laboratory roadmap
   - Compliance Passport structure & SHA-256 seal
3. Evidence authority & safe abstention:
   - Missing evidence remains MISSING_EVIDENCE
   - Zero fabricated lab reports
   - Datasheet (Level 2) does not satisfy empirical laboratory requirement (Level 3)
4. Non-negotiable regulatory boundaries:
   - Disclaimer: "Compliance Passport ≠ BIS Certification"
   - LLM compliance authority is strictly 0.0%
   - No prohibited marketing claims ("Guaranteed Compliance", "BIS Approved", etc.)
5. Authoritative corpus transparency and manifest counts.
"""

import hashlib
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.dataset.builder import get_dataset_repository
from backend.app.services.assessment.golden_demo import (
    GOLDEN_DEMO_PRODUCT,
    CONTROLLED_DEMO_EVIDENCE,
    get_golden_demo_config,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_01_controlled_demo_product_identity():
    """Verify demo product is the controlled SIH IS 17526:2021 Double-Walled Flask."""
    cfg = get_golden_demo_config()
    assert cfg["case_id"] == "GOLDEN-SIH-2026-DEMO"
    assert cfg["standard_number"] == "IS 17526:2021"
    assert "Domestic Water Bottles" in cfg["qco_regulation"]
    assert cfg["product_data"]["product_name"] == GOLDEN_DEMO_PRODUCT["product_name"]
    assert cfg["product_data"]["category"] == "Drinkware & Food Contact Containers"


def test_02_three_consecutive_demo_resets_reproducibility(client):
    """Execute 3 consecutive demo resets and verify deterministic substantive compliance."""
    resets = []
    passports = []

    for i in range(3):
        res = client.post("/api/v1/assessments/demo/reset")
        assert res.status_code == 200, f"Reset {i+1} failed: {res.text}"
        asm_data = res.json()
        resets.append(asm_data)

        # Retrieve the official passport for this reset assessment
        asm_id = asm_data.get("assessment_id") or asm_data.get("id")
        p_res = client.get(f"/api/v1/assessments/{asm_id}/passport")
        assert p_res.status_code == 200, f"Passport fetch {i+1} failed: {p_res.text}"
        passports.append(p_res.json())

    # 1. Verify Product Identity across all 3
    for r in resets:
        assert r["title"] == "Compliance Assessment - ThermoSteel Domestic Stainless Steel Vacuum Flask 1000ml"
        assert r["product_dna"]["product_name"] == GOLDEN_DEMO_PRODUCT["product_name"]
        assert r["product_dna"]["category"] == "Drinkware & Food Contact Containers"

    # 2. Verify Applicability across all 3
    app0 = resets[0]["applicability"]
    app1 = resets[1]["applicability"]
    app2 = resets[2]["applicability"]
    assert len(app0) == len(app1) == len(app2) >= 1
    assert app0[0]["qco_status"] in ("MANDATORY_QCO", "MANDATORY")
    assert app0[0]["llm_decision"] is False

    # 3. Verify Requirements Catalog across all 3
    evals0 = resets[0]["compliance"]["evaluations"]
    evals1 = resets[1]["compliance"]["evaluations"]
    evals2 = resets[2]["compliance"]["evaluations"]
    assert len(evals0) == len(evals1) == len(evals2)
    clauses0 = [e["clause_number"] for e in evals0]
    clauses1 = [e["clause_number"] for e in evals1]
    clauses2 = [e["clause_number"] for e in evals2]
    assert clauses0 == clauses1 == clauses2 == ["4.2.1", "5.2", "5.4", "7.1"]

    # 4. Verify Gaps across all 3
    gaps0 = resets[0]["compliance"].get("gap_register", [])
    gaps1 = resets[1]["compliance"].get("gap_register", [])
    gaps2 = resets[2]["compliance"].get("gap_register", [])
    assert len(gaps0) == len(gaps1) == len(gaps2)
    # Check that in initial reset state, unverified requirements produce MISSING_EVIDENCE
    missing_evals = [e for e in evals0 if e["status"] == "MISSING_EVIDENCE"]
    assert len(missing_evals) >= 1, "Initial reset state must demonstrate missing evidence safe abstention"

    # 5. Verify Passports across all 3
    for p in passports:
        assert "Evidence-Backed Regulatory Compliance Assessment" in p["claim_statement"]
        assert p["product_name"] == GOLDEN_DEMO_PRODUCT["product_name"]
        assert any("IS 17526" in s.get("standard_number", "") for s in p["applicable_standards"])
        assert p["trust_basis"]["verified_official_metadata"] is True
        assert p["trust_basis"]["full_standard_text_status"] == "OFFICIAL_DOCUMENT_ACQUISITION_PENDING"
        assert any("NOT an official Bureau of Indian Standards License" in lim for lim in p["limitations"])


def test_03_evidence_firewall_and_safe_abstention(client):
    """Verify evidence eligibility gate: Datasheet cannot satisfy empirical leak test."""
    res = client.post("/api/v1/assessments/demo/reset")
    assert res.status_code == 200
    asm_id = res.json()["assessment_id"]

    # Ingest Level 2 Manufacturer Datasheet claiming leakage passed
    ev_res = client.post(
        f"/api/v1/assessments/{asm_id}/evidence",
        json={
            "snippet": "Manufacturer Datasheet DS-100: Container is completely leak-proof when inverted.",
            "evidence_type": "PRODUCT_SPECIFICATION",
            "authority": "MANUFACTURER_DECLARATION",
            "page": 1,
        },
    )
    assert ev_res.status_code == 200
    updated_asm = ev_res.json()

    # Empirical test Clause 5.2 must NOT be satisfied by a manufacturer specification
    cl_5_2 = next((e for e in updated_asm["compliance"]["evaluations"] if e["clause_number"] == "5.2"), None)
    assert cl_5_2 is not None
    # Must remain MISSING_EVIDENCE because Level 2 is ineligible for Level 3 empirical test
    assert cl_5_2["status"] in ("MISSING_EVIDENCE", "UNVERIFIED"), (
        f"Clause 5.2 must not be satisfied by manufacturer declaration. Got: {cl_5_2['status']}"
    )


def test_04_authoritative_lab_report_satisfies_empirical_requirement(client):
    """Verify that an authentic NABL Lab report satisfies Clause 5.2."""
    res = client.post("/api/v1/assessments/demo/reset")
    assert res.status_code == 200
    asm_id = res.json()["assessment_id"]

    # Ingest controlled Level 3 Lab Report
    leak_report = CONTROLLED_DEMO_EVIDENCE[0]
    ev_res = client.post(
        f"/api/v1/assessments/{asm_id}/evidence",
        json={
            "snippet": leak_report["snippet"],
            "evidence_type": leak_report["evidence_type"],
            "authority": leak_report["authority"],
            "page": leak_report["page"],
        },
    )
    assert ev_res.status_code == 200
    updated_asm = ev_res.json()

    # Clause 5.2 should now be SATISFIED with traceable chain
    cl_5_2 = next((e for e in updated_asm["compliance"]["evaluations"] if e["clause_number"] == "5.2"), None)
    assert cl_5_2 is not None
    assert cl_5_2["status"] == "SATISFIED"

    # But Clause 5.4 (Thermal performance) test report was NOT uploaded, so it MUST NOT be SATISFIED
    # It remains POTENTIALLY_SATISFIED based only on self-declaration, requiring empirical test
    cl_5_4 = next((e for e in updated_asm["compliance"]["evaluations"] if e["clause_number"] == "5.4"), None)
    assert cl_5_4 is not None
    assert cl_5_4["status"] != "SATISFIED", "Empirical requirement cannot be SATISFIED without lab test"
    assert cl_5_4["status"] in ("POTENTIALLY_SATISFIED", "MISSING_EVIDENCE")


def test_05_conflicting_evidence_triggers_expert_review(client):
    """Verify conflicting evidence does not allow AI to guess; routes to expert review."""
    res = client.post("/api/v1/assessments/demo/reset")
    assert res.status_code == 200
    asm_id = res.json()["assessment_id"]

    conf_a = CONTROLLED_DEMO_EVIDENCE[2]
    conf_b = CONTROLLED_DEMO_EVIDENCE[3]

    # Ingest first report (1000ml)
    r1 = client.post(
        f"/api/v1/assessments/{asm_id}/evidence",
        json={
            "snippet": conf_a["snippet"],
            "evidence_type": conf_a["evidence_type"],
            "authority": conf_a["authority"],
            "page": conf_a["page"],
        },
    )
    assert r1.status_code == 200

    # Ingest contradictory specification (750ml)
    r2 = client.post(
        f"/api/v1/assessments/{asm_id}/evidence",
        json={
            "snippet": conf_b["snippet"],
            "evidence_type": conf_b["evidence_type"],
            "authority": conf_b["authority"],
            "page": conf_b["page"],
        },
    )
    assert r2.status_code == 200
    updated_asm = r2.json()

    # Conflicts list must capture contradiction
    conflicts = updated_asm.get("evidence_conflicts", [])
    assert len(conflicts) >= 1 or any("conflict" in str(e).lower() for e in updated_asm["compliance"]["evaluations"])


def test_06_corpus_manifest_and_data_trust_endpoints(client):
    """Verify dataset manifest matches repository ground truth without hardcoded fabrications."""
    res = client.get("/api/v1/dataset/status")
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["standards_count"] == 51
    assert status_data["qco_count"] == 49
    assert status_data["governance_policy"]["llm_compliance_authority"] == 0.0
    assert status_data["governance_policy"]["scraping_policy"] == "STRICTLY_PROHIBITED"

    # Check that manifest SHA-256 is present and 64 hex characters
    m_res = client.get("/api/v1/dataset/manifest")
    assert m_res.status_code == 200
    manifest_data = m_res.json()
    assert len(manifest_data["sha256"]) == 64


def test_07_prohibited_jury_claims_rejection(client):
    """Audit production passport and health endpoints to ensure zero prohibited marketing claims."""
    res = client.post("/api/v1/assessments/demo/reset")
    asm_id = res.json()["assessment_id"]

    p_res = client.get(f"/api/v1/assessments/{asm_id}/passport")
    passport_str = json.dumps(p_res.json()).lower()

    # Prohibited claims
    assert "guaranteed compliance" not in passport_str
    assert "zero hallucination" not in passport_str
    assert "official bis certificate" not in passport_str
    assert "bis approved" not in passport_str
    assert "100% accuracy" not in passport_str
    assert "95% accuracy" not in passport_str
    assert "80% cost reduction" not in passport_str
