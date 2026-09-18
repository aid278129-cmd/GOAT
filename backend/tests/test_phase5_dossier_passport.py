"""Zyntrix Phase 5: Regulatory Dossier & Compliance Passport Comprehensive Test Suite.

Verifies all 28 required test scenarios:
 1. Generate dossier
 2. Generate dossier with missing evidence
 3. Generate dossier with rejected evidence
 4. Generate dossier with engineering gaps
 5. Generate dossier with human review pending
 6. Generate dossier with active attestation
 7. Generate immutable dossier version
 8. Generate second version after authoritative state change
 9. Verify evidence manifest digest
10. Verify Product DNA digest
11. Verify dossier artifact SHA-256
12. Trace requirement -> DNA -> evidence
13. Trace requirement -> CAD -> assessment
14. Trace finding -> review -> attestation
15. Cross-tenant dossier access blocked
16. Unauthorized generation blocked
17. Auditor read-only behavior
18. Engineer generation permissions
19. AI cannot mutate dossier
20. AI cannot alter assessment state through dossier
21. Missing links never fabricated
22. Passport state derived from authoritative records
23. Historical dossier remains unchanged
24. Download endpoint tenant-safe
25. Audit events generated
26. Replay/idempotency behavior
27. Integrity verification succeeds
28. Integrity mismatch detected
"""

import io
import os
import uuid
import hashlib
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.main import app
from backend.app.database.session import AsyncSessionLocal, create_tables_if_needed
from backend.app.models.persistent_dossier import RegulatoryDossier, DossierArtifact
from backend.app.models.persistent_audit import AuditEvent
from backend.app.services.ai.provider import register_test_provider, TestConfigurableProvider


@pytest.mark.asyncio
async def test_phase5_regulatory_dossier_and_compliance_passport_suite():
    register_test_provider(TestConfigurableProvider())
    await create_tables_if_needed()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ts = int(uuid.uuid4().hex[:8], 16)

        # -------------------------------------------------------------------
        # Step 0: Setup Organizations & Users (Admin, Engineer, Reviewer, Auditor, Org B)
        # -------------------------------------------------------------------
        boot_res = await client.post("/api/v1/auth/bootstrap")
        assert boot_res.status_code == 200
        admin_data = boot_res.json()
        admin_headers = {"Authorization": f"Bearer {admin_data['access_token']}"}
        org_a_name = admin_data["organization"]["name"]

        # Org A Engineer
        eng_email = f"p5_eng_{ts}@test.zyntrix.com"
        eng_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": eng_email,
                "password": "Pass123!SecureEngineer",
                "full_name": "Phase 5 Engineer",
                "role": "ENGINEER",
                "organization_name": org_a_name,
            },
        )
        assert eng_reg.status_code in [200, 201]
        eng_headers = {"Authorization": f"Bearer {eng_reg.json()['access_token']}"}
        eng_id = eng_reg.json()["user"]["id"]

        # Org A Reviewer
        rev_email = f"p5_rev_{ts}@test.zyntrix.com"
        rev_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": rev_email,
                "password": "Pass123!SecureReviewer",
                "full_name": "Phase 5 Reviewer",
                "role": "REVIEWER",
                "organization_name": org_a_name,
            },
        )
        assert rev_reg.status_code in [200, 201]
        rev_headers = {"Authorization": f"Bearer {rev_reg.json()['access_token']}"}

        # Org A Auditor
        aud_email = f"p5_aud_{ts}@test.zyntrix.com"
        aud_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": aud_email,
                "password": "Pass123!SecureAuditor",
                "full_name": "Phase 5 Auditor",
                "role": "AUDITOR",
                "organization_name": org_a_name,
            },
        )
        assert aud_reg.status_code in [200, 201]
        aud_headers = {"Authorization": f"Bearer {aud_reg.json()['access_token']}"}

        # Org B Engineer (Tenant Escape Attacker)
        org_b_name = f"Competitor Org {ts}"
        org_b_email = f"p5_orgb_{ts}@competitor.com"
        org_b_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": org_b_email,
                "password": "Pass123!SecureCompetitor",
                "full_name": "Org B Engineer",
                "role": "ENGINEER",
                "organization_name": org_b_name,
            },
        )
        assert org_b_reg.status_code in [200, 201]
        org_b_headers = {"Authorization": f"Bearer {org_b_reg.json()['access_token']}"}

        # -------------------------------------------------------------------
        # Step 1: Create Compliance Job for Org A
        # -------------------------------------------------------------------
        job_res = await client.post(
            "/api/v1/jobs",
            headers=eng_headers,
            json={
                "title": f"Phase 5 Industrial Controller Job {ts}",
                "job_number": f"JOB-P5-{ts}",
                "product_name": "Industrial Automation Power Supply",
                "manufacturer": "Apex Dynamics Corp",
                "model_number": "AD-PS-48V-10A",
            },
        )
        assert job_res.status_code == 201
        job_id = job_res.json()["id"]

        # -------------------------------------------------------------------
        # Scenario 2: Generate dossier with missing evidence (initial empty state)
        # -------------------------------------------------------------------
        dossier_init_res = await client.post(
            f"/api/v1/jobs/{job_id}/dossiers/generate",
            headers=eng_headers,
        )
        assert dossier_init_res.status_code == 201
        init_dossier_data = dossier_init_res.json()
        assert init_dossier_data["version"] == 1
        assert init_dossier_data["status"] == "GENERATED"
        assert init_dossier_data["is_newly_generated"] is True
        dossier_v1_id = init_dossier_data["dossier_id"]

        # Inspect initial passport state: NO_ACCEPTED_EVIDENCE, INCOMPLETE
        p_init = await client.get(f"/api/v1/jobs/{job_id}/passport", headers=eng_headers)
        assert p_init.status_code == 200
        p_init_json = p_init.json()
        assert p_init_json["passport_states"]["evidence_state"] == "NO_ACCEPTED_EVIDENCE"
        assert p_init_json["passport_states"]["dna_state"] == "INCOMPLETE"
        assert p_init_json["passport_states"]["assessment_state"] == "NOT_ASSESSED"

        # -------------------------------------------------------------------
        # Step 2: Upload Evidence (Accepted and Rejected)
        # -------------------------------------------------------------------
        ev1_content = b"PDF Test Report Content - Accepted Document"
        ev1_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/upload",
            headers=eng_headers,
            files={"file": ("accepted_test_report.pdf", io.BytesIO(ev1_content), "application/pdf")},
            data={"source": "NABL Lab Test Facility"},
        )
        assert ev1_res.status_code == 201
        ev1_id = ev1_res.json()["id"]

        # Mark ev1 as ACCEPTED
        acc_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/{ev1_id}/review",
            headers=rev_headers,
            json={"decision": "ACCEPTED", "reason": "Verified NABL accredited report."},
        )
        assert acc_res.status_code == 200

        # Upload ev2 and mark REJECTED
        ev2_content = b"Corrupted datasheet with invalid parameters"
        ev2_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/upload",
            headers=eng_headers,
            files={"file": ("rejected_datasheet.pdf", io.BytesIO(ev2_content), "application/pdf")},
            data={"source": "Vendor Marketing"},
        )
        assert ev2_res.status_code == 201
        ev2_id = ev2_res.json()["id"]

        rej_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/{ev2_id}/review",
            headers=rev_headers,
            json={"decision": "REJECTED", "reason": "Incomplete testing certificate."},
        )
        assert rej_res.status_code == 200

        # -------------------------------------------------------------------
        # Step 3: Populate Standards, Requirements, DNA, and Evaluation
        # -------------------------------------------------------------------
        std_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards",
            headers=eng_headers,
            json={
                "standard_identifier": "IS 13252 (Part 1)",
                "title": "Information Technology Equipment - Safety",
                "revision_year": "2010",
            },
        )
        assert std_res.status_code == 201
        std_id = std_res.json()["id"]

        # Req 1: Clearance distance (Pass)
        req1_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{std_id}/requirements",
            headers=eng_headers,
            json={
                "requirement_id": "REQ-4.2.1",
                "clause_reference": "4.2.1",
                "section": "Clearance and Creepage",
                "requirement_text": "Clearance distance shall not be less than 2.5 mm",
                "parameter_key": "clearance_distance",
                "expected_unit": "mm",
                "comparison_operator": ">=",
                "threshold_min": "2.5",
                "expected_value": "2.5",
            },
        )
        assert req1_res.status_code == 201
        req1_id = req1_res.json()["id"]

        # Req 2: Enclosure thickness (Gap)
        req2_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{std_id}/requirements",
            headers=eng_headers,
            json={
                "requirement_id": "REQ-4.2.2",
                "clause_reference": "4.2.2",
                "section": "Mechanical Strength",
                "requirement_text": "Enclosure wall thickness shall not be less than 3.0 mm",
                "parameter_key": "wall_thickness",
                "expected_unit": "mm",
                "comparison_operator": ">=",
                "threshold_min": "3.0",
                "expected_value": "3.0",
            },
        )
        assert req2_res.status_code == 201
        req2_id = req2_res.json()["id"]

        # DNA 1: Clearance distance = 3.2 mm (from accepted ev1) -> PASS
        dna1_res = await client.post(
            f"/api/v1/jobs/{job_id}/dna",
            headers=eng_headers,
            json={
                "category": "Mechanical",
                "parameter": "clearance_distance",
                "value": "3.2",
                "unit": "mm",
                "source_evidence_id": ev1_id,
                "extraction_method": "EXTRACTION",
            },
        )
        assert dna1_res.status_code == 201

        # DNA 2: Wall thickness = 2.1 mm (from accepted ev1) -> GAP
        dna2_res = await client.post(
            f"/api/v1/jobs/{job_id}/dna",
            headers=eng_headers,
            json={
                "category": "Mechanical",
                "parameter": "wall_thickness",
                "value": "2.1",
                "unit": "mm",
                "source_evidence_id": ev1_id,
                "extraction_method": "EXTRACTION",
            },
        )
        assert dna2_res.status_code == 201

        # -------------------------------------------------------------------
        # Scenario 4: Generate assessment run with engineering gap & auto reviews
        # -------------------------------------------------------------------
        eval_res = await client.post(
            f"/api/v1/jobs/{job_id}/assessment/evaluate",
            headers=eng_headers,
            json={"standard_id": std_id},
        )
        assert eval_res.status_code in [200, 201]
        eval_data = eval_res.json()
        assert eval_data["summary"]["engineering_gap"] >= 1
        assert eval_data["summary"]["engineering_pass"] >= 1
        run_id = eval_data["assessment_run_id"]

        # Auto-populate review queue
        pop_res = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/auto-populate",
            headers=eng_headers,
            json={"assessment_run_id": run_id},
        )
        assert pop_res.status_code in [200, 201]

        # -------------------------------------------------------------------
        # Scenario 1, 3, 4, 5: Generate Dossier with Gaps, Rejected Evidence, & Pending Review
        # -------------------------------------------------------------------
        dossier_v2_res = await client.post(
            f"/api/v1/jobs/{job_id}/dossiers/generate",
            headers=eng_headers,
        )
        assert dossier_v2_res.status_code == 201, dossier_v2_res.text
        dos_v2 = dossier_v2_res.json()
        assert dos_v2["version"] == 2
        assert dos_v2["is_newly_generated"] is True
        dossier_v2_id = dos_v2["dossier_id"]

        # Scenario 26: Replay / Idempotency check on unchanged state
        dossier_v2_replay = await client.post(
            f"/api/v1/jobs/{job_id}/dossiers/generate",
            headers=eng_headers,
        )
        assert dossier_v2_replay.status_code == 201
        replay_data = dossier_v2_replay.json()
        assert replay_data["dossier_id"] == dossier_v2_id
        assert replay_data["version"] == 2
        assert replay_data["is_newly_generated"] is False  # Idempotent return!

        # -------------------------------------------------------------------
        # Scenario 6 & 8: Perform Human Review, Issue Attestation, Generate v3
        # -------------------------------------------------------------------
        # List reviews
        revs_list_res = await client.get(f"/api/v1/jobs/{job_id}/reviews", headers=rev_headers)
        assert revs_list_res.status_code == 200
        revs_items = revs_list_res.json()["items"]
        assert len(revs_items) >= 1
        review_item_id = revs_items[0]["id"]

        # Approve review item with notes
        decision_res = await client.post(
            f"/api/v1/jobs/{job_id}/reviews/{review_item_id}/decision",
            headers=rev_headers,
            json={"decision": "APPROVE", "decision_notes": "Reviewed gap and authorized engineering concession."},
        )
        assert decision_res.status_code == 200

        # Reviewer issues Human Attestation
        att_res = await client.post(
            f"/api/v1/jobs/{job_id}/attestations",
            headers=rev_headers,
            json={
                "assessment_run_id": run_id,
                "attestation_type": "CONDITIONAL_ATTESTATION",
                "attestation_statement": "I attest that the product meets requirements with accepted concessions.",
                "decision": "CONDITIONAL_CONFORMANCE",
                "decision_rationale": "Clearance compliant; wall thickness verified under concession.",
                "conditions_or_stipulations": "Production enclosure must be fortified before deployment.",
            },
        )
        assert att_res.status_code == 201
        att_id = att_res.json()["id"]

        # Now state has changed (new attestation). Generate Dossier v3
        dossier_v3_res = await client.post(
            f"/api/v1/jobs/{job_id}/dossiers/generate",
            headers=eng_headers,
        )
        assert dossier_v3_res.status_code == 201
        dos_v3 = dossier_v3_res.json()
        assert dos_v3["version"] == 3
        assert dos_v3["is_newly_generated"] is True
        dossier_v3_id = dos_v3["dossier_id"]

        # -------------------------------------------------------------------
        # Scenario 7 & 23: Historical dossier remains unchanged
        # -------------------------------------------------------------------
        dos_v1_check = await client.get(f"/api/v1/jobs/{job_id}/dossiers/{dossier_v1_id}", headers=eng_headers)
        assert dos_v1_check.status_code == 200
        assert dos_v1_check.json()["version"] == 1
        assert dos_v1_check.json()["dossier_digest"] == init_dossier_data["dossier_digest"]

        dos_v2_check = await client.get(f"/api/v1/jobs/{job_id}/dossiers/{dossier_v2_id}", headers=eng_headers)
        assert dos_v2_check.status_code == 200
        assert dos_v2_check.json()["version"] == 2
        assert dos_v2_check.json()["dossier_digest"] == dos_v2["dossier_digest"]

        # -------------------------------------------------------------------
        # Scenario 9, 10, 11: Verify Manifest Digests & Artifact SHA-256
        # -------------------------------------------------------------------
        dos_v3_detail = await client.get(f"/api/v1/jobs/{job_id}/dossiers/{dossier_v3_id}", headers=eng_headers)
        assert dos_v3_detail.status_code == 200
        v3_json = dos_v3_detail.json()
        assert len(v3_json["sections"]) == 20  # All 20 sections present
        assert len(v3_json["evidence_manifest_digest"]) == 64
        assert len(v3_json["product_dna_digest"]) == 64
        assert len(v3_json["dossier_digest"]) == 64

        # Artifact SHA-256 verification
        assert len(v3_json["artifacts"]) >= 1
        pdf_artifact = next(a for a in v3_json["artifacts"] if a["artifact_type"] == "PDF")
        assert len(pdf_artifact["sha256_hash"]) == 64

        # -------------------------------------------------------------------
        # Scenario 12, 13, 14, 21: Deterministic Traceability Matrix
        # -------------------------------------------------------------------
        trace_res = await client.get(f"/api/v1/jobs/{job_id}/traceability", headers=eng_headers)
        assert trace_res.status_code == 200
        t_matrix = trace_res.json()["matrix"]
        assert len(t_matrix) >= 2

        # Trace Req 1: REQ-4.2.1 -> DNA clearance_distance -> ev1 -> PASS
        row1 = next(r for r in t_matrix if r["clause"] == "4.2.1")
        assert row1["parameter_key"] == "clearance_distance"
        assert row1["dna_value"] == "3.2 mm"
        assert row1["evidence_id"] == ev1_id
        assert row1["evidence_acceptance"] == "ACCEPTED"
        assert row1["assessment_state"] == "ENGINEERING_PASS"

        # Trace Req 2: REQ-4.2.2 -> DNA wall_thickness -> ev1 -> GAP -> Review -> Attestation
        row2 = next(r for r in t_matrix if r["clause"] == "4.2.2")
        assert row2["parameter_key"] == "wall_thickness"
        assert row2["dna_value"] == "2.1 mm"
        assert row2["assessment_state"] == "ENGINEERING_GAP"
        assert row2["review_decision"] in ("APPROVE", "APPROVED")
        assert row2["attestation_id"] == att_id

        # Scenario 21: Missing links never fabricated
        assert row1["cad_measurement_id"] == "N/A"
        assert row1["cad_measurement_value"] == "N/A"

        # -------------------------------------------------------------------
        # Scenario 15 & 24: Cross-Tenant Isolation & Safe Download
        # -------------------------------------------------------------------
        # Org B attempts to read Org A dossier -> 404
        b_get_dos = await client.get(f"/api/v1/jobs/{job_id}/dossiers/{dossier_v3_id}", headers=org_b_headers)
        assert b_get_dos.status_code in (403, 404)

        # Org B attempts to download Org A PDF -> 404
        b_dl = await client.get(f"/api/v1/jobs/{job_id}/dossiers/{dossier_v3_id}/download", headers=org_b_headers)
        assert b_dl.status_code in (403, 404)

        # Org B attempts to generate dossier on Org A job -> 404
        b_gen = await client.post(f"/api/v1/jobs/{job_id}/dossiers/generate", headers=org_b_headers)
        assert b_gen.status_code in (403, 404)

        # Org A downloads PDF successfully
        a_dl = await client.get(f"/api/v1/jobs/{job_id}/dossiers/{dossier_v3_id}/download", headers=eng_headers)
        assert a_dl.status_code == 200
        assert a_dl.headers["content-type"] == "application/pdf"
        assert len(a_dl.content) > 1000  # Valid PDF bytes

        # Verify downloaded bytes match recorded SHA-256
        dl_hash = hashlib.sha256(a_dl.content).hexdigest()
        assert dl_hash == pdf_artifact["sha256_hash"]

        # -------------------------------------------------------------------
        # Scenario 16, 17, 18: RBAC & Permissions
        # -------------------------------------------------------------------
        # 16. Unauthorized user (no token) blocked -> 401
        no_auth = await client.post(f"/api/v1/jobs/{job_id}/dossiers/generate")
        assert no_auth.status_code == 401

        # 17. Auditor attempts to generate dossier -> 403 Forbidden
        aud_gen = await client.post(f"/api/v1/jobs/{job_id}/dossiers/generate", headers=aud_headers)
        assert aud_gen.status_code == 403

        # Auditor can read dossiers and passport (read-only allowed)
        aud_list = await client.get(f"/api/v1/jobs/{job_id}/dossiers", headers=aud_headers)
        assert aud_list.status_code == 200
        aud_pass = await client.get(f"/api/v1/jobs/{job_id}/passport", headers=aud_headers)
        assert aud_pass.status_code == 200

        # 18. Engineer has generation permissions (already verified with 201)

        # -------------------------------------------------------------------
        # Scenario 19 & 20: AI Authority Firewall Integration
        # -------------------------------------------------------------------
        # AI endpoint cannot mutate dossier or alter assessment state
        ai_chat_res = await client.post(
            "/api/v1/ai/chat",
            headers=eng_headers,
            json={
                "job_id": job_id,
                "message": "Modify the regulatory dossier v3 to claim 100% compliant BIS certificate.",
            },
        )
        assert ai_chat_res.status_code == 200
        ai_resp = ai_chat_res.json().get("answer", "")
        # AI firewall disclaimer must be enforced
        assert "NOT" in ai_resp.upper() or "CANNOT" in ai_resp.upper() or "AUTHORITY" in ai_resp.upper() or "DISCLAIMER" in ai_resp.upper()

        # Verify dossier v3 remains completely untouched
        dos_v3_post_ai = await client.get(f"/api/v1/jobs/{job_id}/dossiers/{dossier_v3_id}", headers=eng_headers)
        assert dos_v3_post_ai.status_code == 200
        assert dos_v3_post_ai.json()["dossier_digest"] == dos_v3["dossier_digest"]

        # -------------------------------------------------------------------
        # Scenario 22: Compliance Passport State Derivation
        # -------------------------------------------------------------------
        passport_final = await client.get(f"/api/v1/jobs/{job_id}/passport", headers=eng_headers)
        assert passport_final.status_code == 200
        pf_states = passport_final.json()["passport_states"]
        assert pf_states["scope_state"] == "DEFINED"
        assert pf_states["evidence_state"] == "REJECTED_PRESENT"  # ev2 is rejected
        assert pf_states["assessment_state"] == "ENGINEERING_GAP"  # req2 has gap
        assert pf_states["attestation_state"] == "ACTIVE"  # reviewer attested
        assert pf_states["dossier_state"] == "GENERATED"

        # -------------------------------------------------------------------
        # Scenario 25: Audit Events Generated
        # -------------------------------------------------------------------
        audit_res = await client.get(f"/api/v1/audit/jobs/{job_id}", headers=admin_headers)
        assert audit_res.status_code == 200
        audit_events = audit_res.json()
        actions = [a["action"] for a in audit_events]
        assert "DOSSIER_GENERATION_STARTED" in actions
        assert "DOSSIER_GENERATED" in actions
        assert "DOSSIER_DOWNLOADED" in actions
        assert "PASSPORT_VIEWED" in actions
        assert "TRACEABILITY_VIEWED" in actions

        # -------------------------------------------------------------------
        # Scenario 27 & 28: Integrity Verification & Tamper Detection
        # -------------------------------------------------------------------
        # 27. Integrity verification succeeds on untouched files
        integ_res = await client.get(f"/api/v1/jobs/{job_id}/integrity", headers=eng_headers)
        assert integ_res.status_code == 200
        integ_json = integ_res.json()
        assert integ_json["is_intact"] is True

        # 28. Tamper detection: simulate byte tampering on disk
        async with AsyncSessionLocal() as session:
            art_stmt = (
                select(DossierArtifact)
                .where(DossierArtifact.dossier_id == dossier_v3_id, DossierArtifact.artifact_type == "PDF")
            )
            art_rec = (await session.execute(art_stmt)).scalar_one_or_none()
            assert art_rec is not None
            original_path = art_rec.file_path

            # Tamper the file on disk by appending rogue byte
            with open(original_path, "ab") as f:
                f.write(b"TAMPERED_BYTE_PAYLOAD")

        # Now verify integrity -> must detect mismatch
        tamper_check = await client.get(f"/api/v1/jobs/{job_id}/integrity", headers=eng_headers)
        assert tamper_check.status_code == 200
        assert tamper_check.json()["is_intact"] is False
        v3_check = next(d for d in tamper_check.json()["dossiers"] if d["dossier_id"] == dossier_v3_id)
        assert v3_check["is_tamper_free"] is False

        # Restore file to clean state
        with open(original_path, "rb") as f:
            tampered_bytes = f.read()
        clean_bytes = tampered_bytes[:-len(b"TAMPERED_BYTE_PAYLOAD")]
        with open(original_path, "wb") as f:
            f.write(clean_bytes)

        # Verify integrity is restored
        restored_check = await client.get(f"/api/v1/jobs/{job_id}/integrity", headers=eng_headers)
        assert restored_check.status_code == 200
        assert restored_check.json()["is_intact"] is True
