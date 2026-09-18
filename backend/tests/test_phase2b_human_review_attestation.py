import io
import uuid
import hashlib
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_phase2b_human_review_and_attestation_suite():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # -------------------------------------------------------------------
        # Step 0: Setup Users & Roles (Org A and Org B)
        # -------------------------------------------------------------------
        # Org A Admin
        boot_res = await client.post("/api/v1/auth/bootstrap")
        assert boot_res.status_code == 200
        admin_data = boot_res.json()
        admin_token = admin_data["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        org_a_name = admin_data["organization"]["name"]

        # Org A Engineer (Evaluation Creator)
        eng_email = f"engineer_{uuid.uuid4().hex[:6]}@test.zyntrix.com"
        eng_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": eng_email,
                "password": "EngineerSecurePass123!",
                "full_name": "Test Org A Engineer",
                "role": "ENGINEER",
                "organization_name": org_a_name,
            },
        )
        assert eng_reg.status_code in [200, 201]
        eng_token = eng_reg.json()["access_token"]
        eng_headers = {"Authorization": f"Bearer {eng_token}"}
        eng_id = eng_reg.json()["user"]["id"]

        # Org A Reviewer (Independent Attestor)
        rev_email = f"reviewer_{uuid.uuid4().hex[:6]}@test.zyntrix.com"
        rev_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": rev_email,
                "password": "ReviewerSecurePass123!",
                "full_name": "Test Org A Reviewer",
                "role": "REVIEWER",
                "organization_name": org_a_name,
            },
        )
        assert rev_reg.status_code in [200, 201]
        rev_token = rev_reg.json()["access_token"]
        rev_headers = {"Authorization": f"Bearer {rev_token}"}
        rev_id = rev_reg.json()["user"]["id"]

        # Org B Engineer (Tenant Isolation verification)
        org_b_email = f"org_b_eng_{uuid.uuid4().hex[:6]}@other.org"
        org_b_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": org_b_email,
                "password": "OrgBSecurePass123!",
                "full_name": "Org B Engineer",
                "role": "ENGINEER",
                "organization_name": f"Org B {uuid.uuid4().hex[:4]}",
            },
        )
        assert org_b_reg.status_code in [200, 201]
        org_b_token = org_b_reg.json()["access_token"]
        org_b_headers = {"Authorization": f"Bearer {org_b_token}"}

        # -------------------------------------------------------------------
        # Step 1: Create Job in Org A
        # -------------------------------------------------------------------
        job_res = await client.post(
            "/api/v1/jobs",
            json={
                "title": "Industrial High-Voltage Switchgear Assessment",
                "product_name": "Switchgear 33kV",
                "manufacturer": "Bharat Switchgear Ltd",
                "model_number": "BSG-33K-2026",
                "stage": "02_PRODUCT_DNA",
            },
            headers=eng_headers,
        )
        assert job_res.status_code == 201
        job_id = job_res.json()["id"]

        # Step 2: Upload and Accept Evidence Artifact
        ev_bytes = b"%PDF-1.4 Type Test Certificate & Thermal Rise Test Lab Report\n"
        ev_sha256 = hashlib.sha256(ev_bytes).hexdigest()
        upload_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/upload",
            files={"file": ("switchgear_type_test.pdf", io.BytesIO(ev_bytes), "application/pdf")},
            data={"source": "CPRI High Voltage Laboratory"},
            headers=eng_headers,
        )
        assert upload_res.status_code == 201
        ev_id = upload_res.json()["id"]

        # Accept evidence so DNA can be populated
        acc_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/{ev_id}/review",
            json={"decision": "ACCEPTED", "reason": "CPRI laboratory accreditation stamp verified"},
            headers=admin_headers,
        )
        assert acc_res.status_code == 200

        # Step 3: Populate Accepted Product DNA parameters
        dna_res = await client.post(
            f"/api/v1/jobs/{job_id}/dna",
            json={
                "category": "Electrical",
                "parameter": "insulation_resistance",
                "value": "1200",
                "unit": "MOhm",
                "confidence": 0.99,
                "source_evidence_id": ev_id,
                "page_or_sheet": "Page 14 Table 3",
            },
            headers=eng_headers,
        )
        assert dna_res.status_code in [200, 201]

        # Step 4: Assign Standard and Add Requirements
        std_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards",
            json={
                "standard_identifier": "IS 13118:2024",
                "title": "High-Voltage Alternating-Current Circuit-Breakers",
                "revision_year": "2024",
                "applicability": "MANDATORY",
                "is_active_assessment_basis": True,
            },
            headers=eng_headers,
        )
        assert std_res.status_code == 201
        std_id = std_res.json()["id"]

        # Requirement 1: Clear pass
        r1_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{std_id}/requirements",
            json={
                "requirement_id": "REQ-13118-INS-01",
                "clause_reference": "4.1",
                "section": "Insulation Performance",
                "requirement_text": "Insulation resistance must be greater than or equal to 1000 MOhm.",
                "parameter_key": "insulation_resistance",
                "expected_unit": "MOhm",
                "comparison_operator": ">=",
                "threshold_min": "1000",
                "verification_method": "TYPE_TEST",
            },
            headers=eng_headers,
        )
        assert r1_res.status_code == 201
        req1_id = r1_res.json()["id"]

        # Also populate temperature rise parameter that exceeds the statutory threshold (78 C > 65 C limit)
        await client.post(
            f"/api/v1/jobs/{job_id}/dna",
            json={
                "category": "Thermal",
                "parameter": "temperature_rise_main_contacts",
                "value": "78",
                "unit": "C",
                "confidence": 0.99,
                "source_evidence_id": ev_id,
                "page_or_sheet": "Page 18 Section 5",
            },
            headers=eng_headers,
        )

        # Requirement 2: Requires human engineering review
        r2_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{std_id}/requirements",
            json={
                "requirement_id": "REQ-13118-CONSTRUCT-02",
                "clause_reference": "5.4",
                "section": "Mechanical Interlock Assembly",
                "requirement_text": "Mechanical interlock mechanism must prevent simultaneous closing under reverse phase.",
                "parameter_key": "mechanical_interlock_mechanism",
                "requirement_type": "HUMAN_REVIEW",
                "comparison_operator": "EQUALS",
                "expected_value": "COMPLIANT",
                "verification_method": "DESIGN_INSPECTION",
            },
            headers=eng_headers,
        )
        assert r2_res.status_code == 201
        req2_id = r2_res.json()["id"]

        # Requirement 3: Missing parameter (ENGINEERING_GAP / finding)
        r3_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{std_id}/requirements",
            json={
                "requirement_id": "REQ-13118-TEMP-03",
                "clause_reference": "6.2",
                "section": "Temperature Rise Limit",
                "requirement_text": "Maximum main contact temperature rise must not exceed 65 deg C.",
                "parameter_key": "temperature_rise_main_contacts",
                "expected_unit": "C",
                "comparison_operator": "<=",
                "threshold_max": "65",
                "verification_method": "TYPE_TEST",
            },
            headers=eng_headers,
        )
        assert r3_res.status_code == 201
        req3_id = r3_res.json()["id"]

        # Step 5: Engineer triggers assessment run
        eval_res = await client.post(
            f"/api/v1/jobs/{job_id}/assessment/evaluate",
            json={"standard_id": std_id},
            headers=eng_headers,
        )
        assert eval_res.status_code == 201
        run_data = eval_res.json()
        assessment_run_id = run_data["assessment_run_id"]
        findings_data = run_data.get("findings", [])

        # -------------------------------------------------------------------
        # Scenario 1: Manual Review Item Creation
        # -------------------------------------------------------------------
        manual_rev = await client.post(
            f"/api/v1/jobs/{job_id}/reviews",
            json={
                "review_type": "GEOMETRY_REVIEW",
                "title": "Busbar Clearance 3D CAD Inspection",
                "description": "Verify minimum electrical clearance between phase busbars in CAD drawing.",
                "priority": "HIGH",
                "assessment_run_id": assessment_run_id,
                "requirement_id": req2_id,
            },
            headers=eng_headers,
        )
        assert manual_rev.status_code == 201
        m_item = manual_rev.json()
        assert m_item["status"] == "PENDING"
        assert m_item["priority"] == "HIGH"
        assert m_item["review_type"] == "GEOMETRY_REVIEW"
        manual_rev_id = m_item["id"]

        # Scenario 2: Immutable Review Snapshot Captured
        assert "review_snapshot" in m_item
        snap = m_item["review_snapshot"]
        assert snap["job_id"] == job_id
        assert len(snap["evidence_references"]) >= 1
        assert snap["evidence_references"][0]["sha256"] == ev_sha256

        # Scenario 3: Auto-populate Review Queue from Assessment Results
        pop_res = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/auto-populate",
            json={"assessment_run_id": assessment_run_id},
            headers=eng_headers,
        )
        assert pop_res.status_code == 201
        pop_data = pop_res.json()
        assert pop_data["created_count"] >= 1
        auto_item = pop_data["items"][0]
        auto_item_id = auto_item["id"]

        # Scenario 4: Review Queue Listing with Status Filter
        list_res = await client.get(
            f"/api/v1/jobs/{job_id}/reviews?status=PENDING",
            headers=eng_headers,
        )
        assert list_res.status_code == 200
        assert list_res.json()["count"] >= 2

        # Scenario 5: Reviewer Assignment - Engineer Cannot Be Assigned (Must be REVIEWER/ADMIN)
        invalid_assign = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{manual_rev_id}/assign",
            json={"reviewer_id": eng_id},
            headers=admin_headers,
        )
        assert invalid_assign.status_code == 400
        assert "cannot be assigned reviews" in invalid_assign.json()["detail"]

        # Scenario 6: Reviewer Assignment - Valid Reviewer Assignment
        valid_assign = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{manual_rev_id}/assign",
            json={"reviewer_id": rev_id},
            headers=admin_headers,
        )
        assert valid_assign.status_code == 200
        assert valid_assign.json()["status"] == "ASSIGNED"
        assert valid_assign.json()["assigned_reviewer_id"] == rev_id

        # Scenario 7: Review State Transition to IN_REVIEW
        start_res = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{manual_rev_id}/start",
            headers=rev_headers,
        )
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "IN_REVIEW"

        # Scenario 8: Review Decision RBAC - Engineer Cannot Decide (Forbidden)
        eng_decide = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{manual_rev_id}/decision",
            json={"decision": "APPROVE", "decision_notes": "Looks good from engineer view"},
            headers=eng_headers,
        )
        assert eng_decide.status_code == 403

        # Scenario 9: Mandatory Notes Enforcement on REJECT
        reject_no_notes = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{manual_rev_id}/decision",
            json={"decision": "REJECT", "decision_notes": ""},
            headers=rev_headers,
        )
        assert reject_no_notes.status_code == 400
        assert "strictly requires substantive decision notes" in reject_no_notes.json()["detail"]

        # Scenario 10: Mandatory Notes Enforcement on RETURN
        return_no_notes = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{manual_rev_id}/decision",
            json={"decision": "RETURN", "decision_notes": "   "},
            headers=rev_headers,
        )
        assert return_no_notes.status_code == 400

        # Scenario 11: Valid RETURN Decision
        return_valid = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{manual_rev_id}/decision",
            json={"decision": "RETURN", "decision_notes": "Phase busbar spacing requires dimensional tolerance re-check."},
            headers=rev_headers,
        )
        assert return_valid.status_code == 200
        assert return_valid.json()["status"] == "RETURNED"

        # Scenario 12: Valid APPROVE Decision on Auto-Populated Review Item
        approve_valid = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{auto_item_id}/decision",
            json={"decision": "APPROVE", "decision_notes": "Mechanical interlock conforms to safety standard IS 13118 clause 5.4."},
            headers=rev_headers,
        )
        assert approve_valid.status_code == 200
        assert approve_valid.json()["status"] == "APPROVED"
        assert approve_valid.json()["reviewed_by_email"] == rev_email

        # Scenario 13: Finding Resolution & Statutory Waiver Management
        if findings_data:
            test_finding_id = findings_data[0]["id"]
            
            # Resolve with mandatory notes
            resolve_res = await client.post(
                f"/api/v1/jobs/{job_id}/findings/{test_finding_id}/review",
                json={
                    "status": "RESOLVED",
                    "review_notes": "Supplementary temperature rise test report TR-9981 verifies max rise of 48 C (below 65 C limit).",
                },
                headers=rev_headers,
            )
            assert resolve_res.status_code == 200
            assert resolve_res.json()["status"] == "RESOLVED"

            # Statutory Waiver with rationale
            waive_res = await client.post(
                f"/api/v1/jobs/{job_id}/findings/{test_finding_id}/review",
                json={
                    "status": "WAIVED",
                    "review_notes": "Statutory waiver granted under BIS Section 14 Clause B due to alternative liquid-cooling design.",
                },
                headers=rev_headers,
            )
            assert waive_res.status_code == 200
            assert waive_res.json()["status"] == "WAIVED"

        # -------------------------------------------------------------------
        # Scenario 14: Attestation RBAC - Engineer Cannot Issue Attestations
        # -------------------------------------------------------------------
        eng_attest = await client.post(
            f"/api/v1/jobs/{job_id}/attestations",
            json={
                "assessment_run_id": assessment_run_id,
                "attestation_statement": "Engineer attesting compliance.",
                "decision": "CONFORMANT",
                "decision_rationale": "All clauses inspected.",
            },
            headers=eng_headers,
        )
        assert eng_attest.status_code == 403

        # -------------------------------------------------------------------
        # Scenario 15: Separation of Duties Violation
        # Assessment creator cannot attest their own assessment run
        # Let's create an assessment run initiated by reviewer to test self-attestation rejection
        # -------------------------------------------------------------------
        rev_eval_res = await client.post(
            f"/api/v1/jobs/{job_id}/assessment/evaluate",
            json={"standard_id": std_id},
            headers=rev_headers,
        )
        assert rev_eval_res.status_code == 201
        rev_assessment_run_id = rev_eval_res.json()["assessment_run_id"]

        # Reviewer trying to attest their OWN assessment run without admin override must fail
        self_attest_res = await client.post(
            f"/api/v1/jobs/{job_id}/attestations",
            json={
                "assessment_run_id": rev_assessment_run_id,
                "attestation_statement": "Self attestation declaration.",
                "decision": "CONFORMANT",
                "decision_rationale": "I evaluated and I also attest.",
            },
            headers=rev_headers,
        )
        assert self_attest_res.status_code == 403
        assert "Separation of duties violation" in self_attest_res.json()["detail"]

        # -------------------------------------------------------------------
        # Scenario 16: Authorized Human Attestation Creation
        # Independent reviewer attesting the engineer's assessment run
        # -------------------------------------------------------------------
        att_res = await client.post(
            f"/api/v1/jobs/{job_id}/attestations",
            json={
                "assessment_run_id": assessment_run_id,
                "attestation_type": "STANDARDS_CONFORMANCE",
                "attestation_statement": "I hereby formally attest that High-Voltage Switchgear BSG-33K-2026 complies with IS 13118:2024 based on CPRI accredited laboratory test results.",
                "decision": "CONFORMANT",
                "decision_rationale": "Insulation resistance, creepage distances, and mechanical interlock mechanism fully verified.",
                "conditions_or_stipulations": "Valid for production batches using electrolytic copper grade.",
            },
            headers=rev_headers,
        )
        assert att_res.status_code == 201
        att_data = att_res.json()
        assert att_data["status"] == "ACTIVE"
        assert att_data["attestor_email"] == rev_email
        assert att_data["attestor_role"] == "REVIEWER"
        att_id = att_data["id"]

        # Scenario 17: Bounded Cryptographic & Regulatory Scope
        scope = att_data["scope"]
        assert scope["job_id"] == job_id
        assert scope["standard_identifier"] == "IS 13118:2024"
        assert "4.1" in scope["clauses_covered"]
        assert ev_sha256 in scope["evidence_hashes"]

        # Scenario 18: Attestation Listing
        att_list_res = await client.get(
            f"/api/v1/jobs/{job_id}/attestations",
            headers=eng_headers,
        )
        assert att_list_res.status_code == 200
        assert att_list_res.json()["count"] >= 1

        # Scenario 19: Supersede Active Attestation (Immutability Pattern)
        super_res = await client.post(
            f"/api/v1/jobs/{job_id}/attestations/{att_id}/supersede",
            json={
                "attestation_statement": "Updated formal attestation reflecting amended clearance stipulations under IS 13118.",
                "decision": "CONDITIONAL_CONFORMANCE",
                "decision_rationale": "Conditional clearance granted pending final seismic endurance test report.",
                "conditions_or_stipulations": "Requires seismic test report within 90 days of factory commissioning.",
            },
            headers=rev_headers,
        )
        assert super_res.status_code == 200
        new_att_data = super_res.json()
        assert new_att_data["status"] == "ACTIVE"
        assert new_att_data["supersedes_attestation_id"] == att_id

        # Verify old attestation transitioned to SUPERSEDED
        old_att_res = await client.get(
            f"/api/v1/jobs/{job_id}/attestations/{att_id}",
            headers=rev_headers,
        )
        assert old_att_res.status_code == 200
        assert old_att_res.json()["status"] == "SUPERSEDED"

        # Scenario 20: Revocation with Mandatory Reason
        # Revocation without reason fails
        rev_fail = await client.post(
            f"/api/v1/jobs/{job_id}/attestations/{new_att_data['id']}/revoke",
            json={"revocation_reason": "  "},
            headers=rev_headers,
        )
        assert rev_fail.status_code == 400

        # Valid revocation
        rev_succ = await client.post(
            f"/api/v1/jobs/{job_id}/attestations/{new_att_data['id']}/revoke",
            json={"revocation_reason": "CPRI laboratory report recalled due to instrument calibration audit discrepancy."},
            headers=rev_headers,
        )
        assert rev_succ.status_code == 200
        assert rev_succ.json()["status"] == "REVOKED"
        assert rev_succ.json()["revocation_reason"] is not None

        # Scenario 21: Tamper-Evident Append-Only Audit Trail
        audit_res = await client.get(
            f"/api/v1/audit/jobs/{job_id}",
            headers=rev_headers,
        )
        assert audit_res.status_code == 200
        audit_actions = [e["action"] for e in audit_res.json()]
        assert "REVIEW_CREATED" in audit_actions
        assert "REVIEW_ASSIGNED" in audit_actions
        assert "REVIEW_STARTED" in audit_actions
        assert "REVIEW_APPROVED" in audit_actions
        assert "ATTESTATION_ACTIVATED" in audit_actions
        assert "ATTESTATION_SUPERSEDED" in audit_actions
        assert "ATTESTATION_REVOKED" in audit_actions
        assert "FINDING_RESOLVED" in audit_actions or "FINDING_WAIVED" in audit_actions

        # Scenario 22: Tenant / Organization Isolation
        # Org B Engineer cannot access or modify Org A reviews or attestations
        b_access_reviews = await client.get(
            f"/api/v1/jobs/{job_id}/reviews",
            headers=org_b_headers,
        )
        assert b_access_reviews.status_code in [403, 404]

        b_access_attestations = await client.get(
            f"/api/v1/jobs/{job_id}/attestations",
            headers=org_b_headers,
        )
        assert b_access_attestations.status_code in [403, 404]
