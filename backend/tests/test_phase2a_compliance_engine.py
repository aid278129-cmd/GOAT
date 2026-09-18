import io
import uuid
import hashlib
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.compliance.unit_normalizer import UnitNormalizer
from backend.app.services.compliance.applicability_engine import DeterministicApplicabilityEngine


# ---------------------------------------------------------------------------
# UNIT / ISOLATION TESTS FOR SERVICES (Scenarios 6, 7, 8, 13, 14, 15)
# ---------------------------------------------------------------------------

def test_unit_normalizer_direct():
    normalizer = UnitNormalizer()
    # Scenario 6: Power normalizations
    val_w, unit_w = normalizer.normalize(1200.0, "W")
    val_kw, unit_kw = normalizer.normalize(1.5, "kW")
    assert unit_w == "W" and val_w == 1200.0
    assert unit_kw == "W" and val_kw == 1500.0
    converted = normalizer.convert(1200.0, "W", "kW")
    assert converted == 1.2

    # Scenario 7: Length and Temperature normalizations
    conv_len = normalizer.convert(0.003, "m", "mm")
    assert round(conv_len, 4) == 3.0

    conv_temp = normalizer.convert(340.0, "K", "C")
    assert round(conv_temp, 2) == 66.85

    # Scenario 8: Incompatible unit rejection
    compat = normalizer.are_compatible("V", "W")
    assert compat is False


def test_applicability_engine_direct():
    engine = DeterministicApplicabilityEngine()
    
    # Scenario 13: Applicability condition TRUE
    dna_true = {"power_rating": {"value": 1200, "unit": "W", "review_status": "ACCEPTED_EVIDENCE_BACKED"}}
    res_true = engine.evaluate_condition("IF power_rating > 1000 W THEN APPLICABLE", dna_true)
    assert res_true["state"] == "APPLICABLE"

    # Scenario 14: Applicability condition FALSE
    res_false = engine.evaluate_condition("IF power_rating > 2000 W THEN APPLICABLE", dna_true)
    assert res_false["state"] == "NOT_APPLICABLE"

    # Scenario 15: Applicability condition missing data
    dna_empty = {}
    res_missing = engine.evaluate_condition("IF external_waterproof_rating == IP67 THEN APPLICABLE", dna_empty)
    assert res_missing["state"] == "DATA_REQUIRED"


# ---------------------------------------------------------------------------
# INTEGRATION TESTS VIA FASTAPI & POSTGRESQL (Scenarios 1-5, 9-12, 16-20)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_phase2a_engine_integration_suite():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 0: Bootstrap org and admin engineer
        boot_resp = await client.post("/api/v1/auth/bootstrap")
        assert boot_resp.status_code == 200
        token = boot_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create Job
        job_res = await client.post(
            "/api/v1/jobs",
            json={
                "title": "Solar Inverter 5kVA Assessment",
                "product_name": "Inverter 5kVA",
                "manufacturer": "SolarTech Industries",
                "model_number": "ST-5K-2026",
                "stage": "02_PRODUCT_DNA",
            },
            headers=headers,
        )
        assert job_res.status_code == 201
        job_id = job_res.json()["id"]

        # Upload and Accept Evidence Artifact
        ev_bytes = b"%PDF-1.4 Accredited Test Report for Solar Inverter Parameters\nPass\n"
        ev_sha = hashlib.sha256(ev_bytes).hexdigest()
        upload_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/upload",
            files={"file": ("lab_report.pdf", io.BytesIO(ev_bytes), "application/pdf")},
            data={"source": "NABL Electrical Test Lab"},
            headers=headers,
        )
        assert upload_res.status_code == 201
        evidence_id = upload_res.json()["id"]

        # Accept evidence so parameters can be added
        review_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/{evidence_id}/review",
            json={"decision": "ACCEPTED", "reason": "Accredited lab stamp verified"},
            headers=headers,
        )
        assert review_res.status_code == 200

        # Create Standard
        std_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards",
            json={
                "standard_identifier": "IS 16221 (Part 2) : 2015",
                "title": "Safety of Power Converters for Use in Photovoltaic Power Systems",
                "revision_year": "2015",
                "applicability": "MANDATORY",
                "is_active_assessment_basis": True,
            },
            headers=headers,
        )
        assert std_res.status_code == 201
        standard_id = std_res.json()["id"]

        # Populate DNA Facts (backed by accepted evidence)
        dna_items = [
            ("operating_voltage", "230", "V", "Electrical Characteristics"),
            ("max_leakage_current", "1.2", "mA", "Safety Characteristics"),
            ("grounding_continuity", "true", "", "Safety Characteristics"),
            ("insulation_class", "Class I", "", "Safety Characteristics"),
            ("power_rating", "1200", "W", "Electrical Characteristics"),
            ("creepage_distance", "0.004", "m", "Mechanical Characteristics"),
            ("operating_temp", "340", "K", "Environmental Characteristics"),
            ("incompatible_param", "50", "V", "Electrical Characteristics"),
        ]
        for param, val, unit, cat in dna_items:
            dna_res = await client.post(
                f"/api/v1/jobs/{job_id}/dna",
                json={
                    "category": cat,
                    "parameter": param,
                    "value": val,
                    "unit": unit,
                    "source_evidence_id": evidence_id,
                },
                headers=headers,
            )
            assert dna_res.status_code == 201

        # Add requirements covering all statutory scenarios:
        # Req 1: Numeric PASS (operating_voltage <= 250 V)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "4.1",
                "requirement_id": "REQ-4.1",
                "clause_reference": "Clause 4.1",
                "requirement_text": "Rated operational voltage shall not exceed 250 V AC",
                "requirement_type": "NUMERIC",
                "parameter_key": "operating_voltage",
                "expected_unit": "V",
                "comparison_operator": "<=",
                "threshold_max": 250.0,
            },
            headers=headers,
        )

        # Req 2: Numeric GAP (max_leakage_current <= 0.75 mA)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "5.2.1",
                "requirement_id": "REQ-5.2.1",
                "clause_reference": "Clause 5.2.1",
                "requirement_text": "Maximum continuous touch leakage current must not exceed 0.75 mA",
                "requirement_type": "NUMERIC",
                "parameter_key": "max_leakage_current",
                "expected_unit": "mA",
                "comparison_operator": "<=",
                "threshold_max": 0.75,
            },
            headers=headers,
        )

        # Req 3: Range PASS (operating_voltage in [100, 240] V)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "4.2",
                "requirement_id": "REQ-4.2",
                "clause_reference": "Clause 4.2",
                "requirement_text": "Normal operating voltage window shall be 100 V to 240 V",
                "requirement_type": "RANGE",
                "parameter_key": "operating_voltage",
                "expected_unit": "V",
                "comparison_operator": "RANGE",
                "threshold_min": 100.0,
                "threshold_max": 240.0,
            },
            headers=headers,
        )

        # Req 4: Boolean PASS (grounding_continuity == true)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "6.1",
                "requirement_id": "REQ-6.1",
                "clause_reference": "Clause 6.1",
                "requirement_text": "Protective earthing continuity must be present and verified",
                "requirement_type": "BOOLEAN",
                "parameter_key": "grounding_continuity",
                "comparison_operator": "==",
                "expected_value": "true",
            },
            headers=headers,
        )

        # Req 5: Enumeration PASS (insulation_class in ["Class I", "Class II"])
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "7.3",
                "requirement_id": "REQ-7.3",
                "clause_reference": "Clause 7.3",
                "requirement_text": "Insulation construction must be Class I or Class II",
                "requirement_type": "ENUMERATION",
                "parameter_key": "insulation_class",
                "comparison_operator": "ENUMERATION",
                "allowed_values": ["Class I", "Class II"],
            },
            headers=headers,
        )

        # Req 6: Unit conversion PASS (power_rating <= 1.5 kW with 1200 W in DNA)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "8.1",
                "requirement_id": "REQ-8.1",
                "clause_reference": "Clause 8.1",
                "requirement_text": "Rated nominal power output must not exceed 1.5 kW",
                "requirement_type": "NUMERIC",
                "parameter_key": "power_rating",
                "expected_unit": "kW",
                "comparison_operator": "<=",
                "threshold_max": 1.5,
            },
            headers=headers,
        )

        # Req 7: Dimensional unit conversion PASS (creepage >= 2.5 mm with 0.004 m in DNA)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "9.4",
                "requirement_id": "REQ-9.4",
                "clause_reference": "Clause 9.4",
                "requirement_text": "Minimum creepage distance across primary to secondary shall be 2.5 mm",
                "requirement_type": "NUMERIC",
                "parameter_key": "creepage_distance",
                "expected_unit": "mm",
                "comparison_operator": ">=",
                "threshold_min": 2.5,
            },
            headers=headers,
        )

        # Req 8: Incompatible unit rejection (expected W, DNA has V)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "10.1",
                "requirement_id": "REQ-10.1",
                "clause_reference": "Clause 10.1",
                "requirement_text": "Standby loss power must be under 100 W",
                "requirement_type": "NUMERIC",
                "parameter_key": "incompatible_param",
                "expected_unit": "W",
                "comparison_operator": "<=",
                "threshold_max": 100.0,
            },
            headers=headers,
        )

        # Req 9: Missing Product DNA -> DATA_REQUIRED
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "11.1",
                "requirement_id": "REQ-11.1",
                "clause_reference": "Clause 11.1",
                "requirement_text": "Dielectric withstand voltage must be >= 1500 V",
                "requirement_type": "NUMERIC",
                "parameter_key": "missing_dielectric_param",
                "expected_unit": "V",
                "comparison_operator": ">=",
                "threshold_min": 1500.0,
            },
            headers=headers,
        )

        # Req 13: Applicability TRUE (evaluates condition and passes)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "12.1",
                "requirement_id": "REQ-12.1",
                "clause_reference": "Clause 12.1",
                "requirement_text": "High power thermal dissipation check",
                "requirement_type": "NUMERIC",
                "parameter_key": "operating_voltage",
                "expected_unit": "V",
                "comparison_operator": "<=",
                "threshold_max": 300.0,
                "applicability_condition": "IF power_rating > 1000 W THEN APPLICABLE",
            },
            headers=headers,
        )

        # Req 14: Applicability FALSE (NOT_APPLICABLE)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "12.2",
                "requirement_id": "REQ-12.2",
                "clause_reference": "Clause 12.2",
                "requirement_text": "Megawatt class cooling fan requirement",
                "requirement_type": "NUMERIC",
                "parameter_key": "operating_voltage",
                "expected_unit": "V",
                "comparison_operator": "<=",
                "threshold_max": 300.0,
                "applicability_condition": "IF power_rating > 50000 W THEN APPLICABLE",
            },
            headers=headers,
        )

        # Req 16: Qualitative Human Review (TEXT_REVIEW)
        await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            json={
                "clause_number": "13.1",
                "requirement_id": "REQ-13.1",
                "clause_reference": "Clause 13.1",
                "requirement_text": "Product rating plate must clearly display the BIS Standard Mark and manufacturer ISI license number",
                "requirement_type": "TEXT_REVIEW",
                "parameter_key": "nameplate_text",
                "comparison_operator": "TEXT_REVIEW",
            },
            headers=headers,
        )

        # -------------------------------------------------------------------
        # EXECUTE DETERMINISTIC ASSESSMENT EVALUATION
        # -------------------------------------------------------------------
        eval_resp = await client.post(
            f"/api/v1/jobs/{job_id}/assessment/evaluate",
            json={"standard_id": standard_id},
            headers=headers,
        )
        assert eval_resp.status_code in (200, 201), eval_resp.text
        eval_data = eval_resp.json()
        run_id = eval_data.get("run_id") or eval_data.get("assessment_run_id")
        assert run_id is not None
        results = {r["clause_number"].replace("Clause ", "").strip(): r for r in eval_data["results"]}

        # SCENARIO 1: Numeric PASS (Clause 4.1)
        res_41 = results["4.1"]
        assert res_41["assessment_state"] == "ENGINEERING_PASS"
        assert res_41["observed_value"] == "230"
        assert res_41["source_sha256"] == ev_sha

        # SCENARIO 2: Numeric GAP (Clause 5.2.1) + Finding Created
        res_521 = results["5.2.1"]
        assert res_521["assessment_state"] == "ENGINEERING_GAP"
        assert len(eval_data["findings"]) >= 1
        finding_521 = next(
            f for f in eval_data["findings"]
            if "5.2.1" in f.get("title", "") or f.get("requirement_id") == res_521["requirement_id"]
        )
        assert finding_521["status"] == "OPEN"
        assert "1.2" in str(finding_521.get("observed_value"))

        # SCENARIO 3: Range PASS (Clause 4.2)
        res_42 = results["4.2"]
        assert res_42["assessment_state"] == "ENGINEERING_PASS"

        # SCENARIO 4: Boolean PASS (Clause 6.1)
        res_61 = results["6.1"]
        assert res_61["assessment_state"] == "ENGINEERING_PASS"

        # SCENARIO 5: Enumeration PASS (Clause 7.3)
        res_73 = results["7.3"]
        assert res_73["assessment_state"] == "ENGINEERING_PASS"

        # SCENARIO 6: Unit Conversion Power (Clause 8.1: 1200 W <= 1.5 kW)
        res_81 = results["8.1"]
        assert res_81["assessment_state"] == "ENGINEERING_PASS"
        assert res_81["normalized_value"] == 1200.0
        assert res_81["normalized_unit"] == "W"
        assert "1500" in res_81["evaluation_expression"]

        # SCENARIO 7: Dimensional Normalization Length (Clause 9.4: 0.004 m >= 2.5 mm)
        res_94 = results["9.4"]
        assert res_94["assessment_state"] == "ENGINEERING_PASS"
        assert res_94["normalized_value"] == 0.004
        assert res_94["normalized_unit"] == "m"
        assert "0.0025" in res_94["evaluation_expression"]

        # SCENARIO 8: Incompatible unit rejection (Clause 10.1: V vs W)
        res_101 = results["10.1"]
        assert res_101["assessment_state"] in ("DATA_REQUIRED", "CONFLICT")
        assert "Incompatible" in res_101["evaluation_expression"] or "dimension" in res_101["evaluation_expression"].lower()

        # SCENARIO 9: Missing Product DNA (Clause 11.1)
        res_111 = results["11.1"]
        assert res_111["assessment_state"] == "DATA_REQUIRED"

        # SCENARIO 13: Applicability TRUE (Clause 12.1)
        res_121 = results["12.1"]
        assert res_121["applicability_state"] == "APPLICABLE"
        assert res_121["assessment_state"] == "ENGINEERING_PASS"

        # SCENARIO 14: Applicability FALSE (Clause 12.2)
        res_122 = results["12.2"]
        assert res_122["applicability_state"] == "NOT_APPLICABLE"
        assert res_122["assessment_state"] == "NOT_APPLICABLE"

        # SCENARIO 16: Qualitative Human Review (Clause 13.1)
        res_131 = results["13.1"]
        assert res_131["assessment_state"] == "HUMAN_REVIEW_REQUIRED"

        # SCENARIO 19: Persistent Assessment Results in PostgreSQL
        latest_resp = await client.get(f"/api/v1/jobs/{job_id}/assessment/latest", headers=headers)
        assert latest_resp.status_code == 200
        latest_data = latest_resp.json()
        assert latest_data.get("run_id") == run_id or latest_data.get("assessment_run_id") == run_id
        assert len(latest_data["results"]) == len(eval_data["results"])

        run_by_id_resp = await client.get(f"/api/v1/jobs/{job_id}/assessment/runs/{run_id}", headers=headers)
        assert run_by_id_resp.status_code == 200
        assert run_by_id_resp.json().get("run_id") == run_id or run_by_id_resp.json().get("assessment_run_id") == run_id

        # SCENARIO 20: Audit Trail & Finding Updates
        audit_resp = await client.get(f"/api/v1/audit/jobs/{job_id}", headers=headers)
        assert audit_resp.status_code == 200
        actions = [a["action"] for a in audit_resp.json()]
        assert "ASSESSMENT_STARTED" in actions
        assert "REQUIREMENT_EVALUATED" in actions
        assert "ASSESSMENT_COMPLETED" in actions
        assert "FINDING_CREATED" in actions

        # Update finding status (Reviewer action)
        finding_id = finding_521["id"]
        patch_finding = await client.patch(
            f"/api/v1/jobs/{job_id}/findings/{finding_id}",
            json={"status": "UNDER_REVIEW", "review_notes": "Engineering re-testing requested with secondary filter"},
            headers=headers,
        )
        assert patch_finding.status_code == 200
        assert patch_finding.json()["status"] == "UNDER_REVIEW"

        # Audit trail recorded FINDING_STATUS_UPDATED
        audit_resp2 = await client.get(f"/api/v1/audit/jobs/{job_id}", headers=headers)
        actions2 = [a["action"] for a in audit_resp2.json()]
        assert "FINDING_STATUS_UPDATED" in actions2


@pytest.mark.asyncio
async def test_tenant_isolation_and_rbac():
    # SCENARIOS 17 & 18: Tenant Isolation and RBAC Permissions
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Bootstrap default org (Org 1)
        boot_resp = await client.post("/api/v1/auth/bootstrap")
        token_eng = boot_resp.json()["access_token"]
        headers_eng = {"Authorization": f"Bearer {token_eng}"}

        # Create Job in Org 1
        job_res = await client.post(
            "/api/v1/jobs",
            json={"title": "Org 1 Confidential Assessment", "product_name": "Device 1"},
            headers=headers_eng,
        )
        job1_id = job_res.json()["id"]

        # Register a second distinct user in a different organization (Org 2)
        u_id = uuid.uuid4().hex[:8]
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"auditor_{u_id}@org2.com",
                "password": "SecurePassword123!",
                "full_name": "External Auditor",
                "organization_name": f"External Audit Corp {u_id}",
                "role": "AUDITOR",
            },
        )
        assert reg_resp.status_code in (200, 201)
        token_org2 = reg_resp.json()["access_token"]
        headers_org2 = {"Authorization": f"Bearer {token_org2}"}

        # SCENARIO 17: Org 2 attempts to evaluate or access Org 1's job -> 404 (strictly isolated)
        forbidden_eval = await client.post(
            f"/api/v1/jobs/{job1_id}/assessment/evaluate",
            json={},
            headers=headers_org2,
        )
        assert forbidden_eval.status_code in (403, 404)

        forbidden_get = await client.get(
            f"/api/v1/jobs/{job1_id}/assessment/latest",
            headers=headers_org2,
        )
        assert forbidden_get.status_code in (403, 404)

        # SCENARIO 18: RBAC Permission: User with AUDITOR role in Org 1 cannot trigger evaluation (403)
        u_id2 = uuid.uuid4().hex[:8]
        reg_auditor1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"compliance_auditor_{u_id2}@org2.com",
                "password": "SecurePassword123!",
                "full_name": "Internal Auditor Org2",
                "organization_name": f"External Audit Corp {u_id}",
                "role": "AUDITOR",
            },
        )
        assert reg_auditor1.status_code in (200, 201)
        aud_token = reg_auditor1.json()["access_token"]
        aud_headers = {"Authorization": f"Bearer {aud_token}"}
        # Attempt evaluation with AUDITOR role on their own job
        job_org2_resp = await client.post(
            "/api/v1/jobs",
            json={"title": "Auditor Org Job", "product_name": "Device 2"},
            headers=headers_org2,
        )
        job_org2_id = job_org2_resp.json()["id"]
        
        aud_eval_attempt = await client.post(
            f"/api/v1/jobs/{job_org2_id}/assessment/evaluate",
            json={},
            headers=aud_headers,
        )
        # Should be 403 Forbidden because evaluate requires ENGINEER, REVIEWER, or ADMIN
        assert aud_eval_attempt.status_code == 403
