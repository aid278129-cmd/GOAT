import io
import hashlib
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_phase1_complete_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        # 1. Bootstrap default organization and admin
        boot_resp = await async_client.post("/api/v1/auth/bootstrap")
        assert boot_resp.status_code == 200, boot_resp.text
        boot_data = boot_resp.json()
        assert "access_token" in boot_data
        token = boot_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get /me
        me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == "engineer@zyntrix.io"
        org_id = me_data["organization_id"]
        assert org_id is not None

        # 3. Create a Compliance Job
        job_payload = {
            "title": "Industrial Power Supply Model X-500",
            "product_name": "Power Converter 500W",
            "manufacturer": "Apex Power Systems Ltd",
            "model_number": "APX-500-24",
            "stage": "01_EVIDENCE_INGESTION",
        }
        create_job_resp = await async_client.post("/api/v1/jobs", json=job_payload, headers=headers)
        assert create_job_resp.status_code == 201, create_job_resp.text
        job = create_job_resp.json()
        job_id = job["id"]
        assert job["job_number"].startswith("JOB-2026-")
        assert job["organization_id"] == org_id

        # 4. Upload Evidence Artifact with Server-side SHA-256
        file_bytes = b"%PDF-1.4 Mock Laboratory Test Report Content for BIS IS 13252 Testing\nData: Pass\n"
        expected_hash = hashlib.sha256(file_bytes).hexdigest()

        files = {"file": ("test_report.pdf", io.BytesIO(file_bytes), "application/pdf")}
        data = {"source": "NABL Accredited Test Lab"}
        upload_resp = await async_client.post(
            f"/api/v1/jobs/{job_id}/evidence/upload",
            files=files,
            data=data,
            headers=headers,
        )
        assert upload_resp.status_code == 201, upload_resp.text
        evidence = upload_resp.json()
        evidence_id = evidence["id"]
        assert evidence["sha256_hash"] == expected_hash
        assert evidence["file_type"] == "pdf"
        assert evidence["acceptance_status"] == "REQUIRES_REVIEW"
        assert evidence["processing_status"] == "EXTRACTION_COMPLETE"

        # 5. Check Evidence Detail and Lifecycle Events
        ev_detail_resp = await async_client.get(
            f"/api/v1/jobs/{job_id}/evidence/{evidence_id}",
            headers=headers,
        )
        assert ev_detail_resp.status_code == 200
        ev_detail = ev_detail_resp.json()
        assert len(ev_detail["lifecycle_events"]) >= 2
        assert ev_detail["lifecycle_events"][0]["event_type"] == "UPLOADED"

        # 6. Verify Evidence Gating: Unaccepted evidence MUST NOT populate Product DNA
        dna_attempt = {
            "category": "Electrical Characteristics",
            "parameter": "Rated Input Voltage",
            "value": "230 V",
            "unit": "V",
            "source_evidence_id": evidence_id,
        }
        blocked_dna_resp = await async_client.post(
            f"/api/v1/jobs/{job_id}/dna",
            json=dna_attempt,
            headers=headers,
        )
        assert blocked_dna_resp.status_code == 400
        assert "Evidence gating violation" in blocked_dna_resp.json()["detail"]

        # 7. Accept Evidence via Review Endpoint
        review_resp = await async_client.post(
            f"/api/v1/jobs/{job_id}/evidence/{evidence_id}/review",
            json={"decision": "ACCEPTED", "reason": "Verified calibration and NABL lab seal"},
            headers=headers,
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["acceptance_status"] == "ACCEPTED"

        # 8. Add Product DNA Parameter with Accepted Evidence (Now permitted)
        dna_allowed_resp = await async_client.post(
            f"/api/v1/jobs/{job_id}/dna",
            json=dna_attempt,
            headers=headers,
        )
        assert dna_allowed_resp.status_code == 201, dna_allowed_resp.text
        dna_param = dna_allowed_resp.json()
        assert dna_param["parameter"] == "Rated Input Voltage"
        assert dna_param["source_evidence_id"] == evidence_id
        assert dna_param["source_file_name"] == "test_report.pdf"

        # 9. Query Product DNA Structured View
        get_dna_resp = await async_client.get(f"/api/v1/jobs/{job_id}/dna", headers=headers)
        assert get_dna_resp.status_code == 200
        dna_view = get_dna_resp.json()
        assert dna_view["total_parameters"] == 1
        assert len(dna_view["categories"]["Electrical Characteristics"]) == 1

        # 10. Standards & Clause Intelligence: Assign Standard
        std_payload = {
            "standard_identifier": "IS 13252 (Part 1): 2010",
            "title": "Information Technology Equipment - Safety",
            "revision_year": "2010",
            "applicability": "MANDATORY",
            "is_active_assessment_basis": True,
        }
        assign_std_resp = await async_client.post(
            f"/api/v1/jobs/{job_id}/standards",
            json=std_payload,
            headers=headers,
        )
        assert assign_std_resp.status_code == 201
        assigned_std = assign_std_resp.json()
        std_id = assigned_std["id"]
        assert assigned_std["standard_identifier"] == "IS 13252 (Part 1): 2010"

        # 11. Add Clause Requirement
        req_payload = {
            "clause_number": "1.5.1",
            "title": "General Components Requirements",
            "requirement_type": "ELECTRICAL_SAFETY",
            "description": "Components shall comply with safety requirements of this standard.",
        }
        add_req_resp = await async_client.post(
            f"/api/v1/jobs/{job_id}/standards/{std_id}/requirements",
            json=req_payload,
            headers=headers,
        )
        assert add_req_resp.status_code == 201
        req_data = add_req_resp.json()
        assert req_data["clause_number"] == "1.5.1"

        # 12. Tamper-Evident Regulatory Audit Ledger
        audit_resp = await async_client.get(f"/api/v1/audit/jobs/{job_id}", headers=headers)
        assert audit_resp.status_code == 200
        audit_trail = audit_resp.json()
        actions = [a["action"] for a in audit_trail]
        assert "JOB_CREATED" in actions
        assert "EVIDENCE_UPLOADED" in actions
        assert "EVIDENCE_ACCEPTED" in actions
        assert "DNA_PARAM_ADDED" in actions
        assert "STANDARD_ASSIGNED" in actions
        assert "REQUIREMENT_ADDED" in actions


@pytest.mark.asyncio
async def test_tenant_isolation():
    import uuid
    run_id = uuid.uuid4().hex[:6]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        # Org 1: Alpha Corp
        alpha_reg = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"alpha_{run_id}@alpha-corp.io",
                "password": "AlphaPassword2026!",
                "full_name": "Alpha Lead Engineer",
                "role": "ENGINEER",
                "organization_name": f"Alpha Corp Technologies {run_id}",
            },
        )
        assert alpha_reg.status_code == 200, alpha_reg.text
        alpha_token = alpha_reg.json()["access_token"]
        alpha_headers = {"Authorization": f"Bearer {alpha_token}"}

        # Alpha creates a job
        alpha_job = await async_client.post(
            "/api/v1/jobs",
            json={"title": f"Alpha Confidential Battery Pack {run_id}"},
            headers=alpha_headers,
        )
        assert alpha_job.status_code == 201
        alpha_job_id = alpha_job.json()["id"]

        # Org 2: Beta Corp
        beta_reg = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"beta_{run_id}@beta-corp.io",
                "password": "BetaPassword2026!",
                "full_name": "Beta Lead Engineer",
                "role": "ENGINEER",
                "organization_name": f"Beta Corp Global {run_id}",
            },
        )
        assert beta_reg.status_code == 200, beta_reg.text
        beta_token = beta_reg.json()["access_token"]
        beta_headers = {"Authorization": f"Bearer {beta_token}"}

        # Beta attempts to access Alpha's job -> MUST be 404
        cross_job_resp = await async_client.get(
            f"/api/v1/jobs/{alpha_job_id}",
            headers=beta_headers,
        )
        assert cross_job_resp.status_code == 404

        # Beta lists jobs -> Alpha's job MUST NOT appear in Beta's list
        beta_jobs_resp = await async_client.get("/api/v1/jobs", headers=beta_headers)
        assert beta_jobs_resp.status_code == 200
        beta_job_ids = [j["id"] for j in beta_jobs_resp.json()]
        assert alpha_job_id not in beta_job_ids
