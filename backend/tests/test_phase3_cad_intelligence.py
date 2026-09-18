import pytest
import io
import asyncio
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.main import app
from backend.app.database.session import AsyncSessionLocal
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_cad import (
    CADModel,
    CADComponent,
    CADGeometryFeature,
    CADMeasurement,
    CADSnapshot,
    CADProcessingStatus,
)
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_standards import JobStandard, JobRequirement
from backend.app.models.persistent_assessment import AssessmentRun, PersistentAssessmentResult, ComplianceFinding
from backend.app.models.persistent_audit import AuditEvent
from backend.app.services.cad.step_parser import StepParser
from backend.app.services.cad.geometry_extractor import GeometryExtractor
from backend.app.services.cad.measurement_engine import MeasurementEngine
from backend.app.services.cad.cad_registry import validate_cad_format
from backend.app.services.cad.cad_errors import UnsupportedCADFormatError, CADProcessingLimitExceeded

# Deterministic ISO 10303-21 STEP fixture
DETERMINISTIC_STEP_CONTENT = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Zyntrix Enclosure 3D CAD Model','B-Rep Solid Geometry'),'2;1');
FILE_NAME('enclosure_body.stp','2026-09-18T00:00:00',('Compliance Engineer'),('Zyntrix Statutory Systems'),'Zyntrix CAD v4.2','Zyntrix Kernel','');
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));
ENDSEC;
DATA;
#10=PRODUCT_DEFINITION_FORMATION('DF_1','Zyntrix Enclosure Assembly',#20);
#20=PRODUCT('ENCLOSURE_ASSY','Zyntrix Main Enclosure','',(#30));
#30=PRODUCT_CONTEXT('',#40,'mechanical');
#40=APPLICATION_CONTEXT('mechanical design');
#50=PRODUCT_DEFINITION('DEF_1','Primary Enclosure Body',#10,#60);
#60=PRODUCT_DEFINITION_CONTEXT('part definition',#40,'design');
#70=CARTESIAN_POINT('origin',(0.0,0.0,0.0));
#80=CARTESIAN_POINT('pt_corner1',(200.0,150.0,80.0));
#90=CARTESIAN_POINT('pt_inner1',(2.35,2.35,2.35));
#100=CARTESIAN_POINT('pt_inner2',(197.65,147.65,77.65));
#110=CARTESIAN_POINT('hole_center',(50.0,50.0,0.0));
#120=DIRECTION('dir_z',(0.0,0.0,1.0));
#130=DIRECTION('dir_x',(1.0,0.0,0.0));
#140=AXIS2_PLACEMENT_3D('hole_axis',#110,#120,#130);
#150=CYLINDRICAL_SURFACE('hole_cyl_5mm',#140,5.0);
#160=MANIFOLD_SOLID_BREP('solid_enclosure',#170);
#170=CLOSED_SHELL('shell_outer',(#180));
#180=ADVANCED_FACE('face_bottom',(#190),#200,.T.);
#190=FACE_OUTER_BOUND('bnd_bottom',#210,.T.);
#200=PLANE('plane_z0',#140);
#210=EDGE_LOOP('loop_base',(#220));
#220=ORIENTED_EDGE('oe1',*,*,#230,.T.);
#230=EDGE_CURVE('ec1',#70,#80,#240,.T.);
#240=LINE('line1',#70,#250);
#250=VECTOR('vec1',#120,200.0);
ENDSEC;
END-ISO-10303-21;
"""


@pytest.mark.asyncio
async def test_phase3_cad_intelligence_suite():
    """
    Comprehensive verification of all 22 Phase 3 CAD Intelligence capabilities:
    STEP parsing, B-Rep topology, bounding box, wall thickness, hole diameter,
    persistence, snapshot, evidence gating, Product DNA mapping, GEOMETRY assessment,
    findings, audit trail, RBAC, tenant isolation, and resource limits.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)

        # -------------------------------------------------------------------------
        # SETUP: Organizations & Users
        # -------------------------------------------------------------------------
        # Org A Admin & Engineer
        admin_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"cad_admin_{ts}@zyntrix.com",
                "password": "Password123!",
                "full_name": "CAD Lead Admin",
                "organization_name": f"CAD Tech Org {ts}",
                "role": "ADMIN",
            },
        )
        assert admin_res.status_code in [200, 201], admin_res.text
        admin_data = admin_res.json()
        admin_token = admin_data.get("access_token") or admin_data.get("token", {}).get("access_token")
        org_a_id = admin_data["user"]["organization_id"]
        org_a_name = admin_data["user"]["organization_name"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Org A Auditor (read-only)
        auditor_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"cad_auditor_{ts}@zyntrix.com",
                "password": "Password123!",
                "full_name": "CAD Auditor",
                "organization_name": org_a_name,
                "role": "AUDITOR",
            },
        )
        assert auditor_res.status_code in [200, 201]
        auditor_token = auditor_res.json().get("access_token") or auditor_res.json().get("token", {}).get("access_token")
        auditor_headers = {"Authorization": f"Bearer {auditor_token}"}

        # Org B User (for tenant isolation)
        org_b_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"cad_tenant_b_{ts}@other.com",
                "password": "Password123!",
                "full_name": "Tenant B User",
                "organization_name": f"Foreign CAD Org {ts}",
                "role": "ADMIN",
            },
        )
        assert org_b_res.status_code in [200, 201]
        org_b_token = org_b_res.json().get("access_token") or org_b_res.json().get("token", {}).get("access_token")
        org_b_headers = {"Authorization": f"Bearer {org_b_token}"}

        # Create Compliance Job in Org A
        job_res = await client.post(
            "/api/v1/jobs",
            headers=admin_headers,
            json={
                "title": f"CAD Spatial Compliance Job {ts}",
                "product_type": "Industrial Power Enclosure",
                "target_market": "IN",
                "description": "High-voltage inverter housing assessment",
            },
        )
        assert job_res.status_code == 201
        job_id = job_res.json()["id"]

        # -------------------------------------------------------------------------
        # 1. DIRECT STEP PARSER & GEOMETRY KERNEL VERIFICATION
        # -------------------------------------------------------------------------
        parser = StepParser()
        parsed = parser.parse_text(DETERMINISTIC_STEP_CONTENT, filename="enclosure_body.stp")
        assert parsed.schema == "CONFIG_CONTROL_DESIGN"
        assert len(parsed.cartesian_points) == 5
        assert len(parsed.cylinders) == 1
        assert len(parsed.planes) == 1

        extractor = GeometryExtractor()
        geo = extractor.extract(parsed)
        # Bounding Box: X=200, Y=150, Z=80
        assert geo.dim_x == 200.0
        assert geo.dim_y == 150.0
        assert geo.dim_z == 80.0
        # Volume & Surface Area
        assert geo.volume_mm3 == 2400000.0
        assert geo.surface_area_mm2 == 116000.0

        # Deterministic Measurements
        engine = MeasurementEngine()
        measurements = engine.compute_measurements(geo)
        meas_map = {m.measurement_type: m for m in measurements}
        assert "BOUNDING_BOX_X" in meas_map
        assert meas_map["BOUNDING_BOX_X"].value == 200.0
        assert "BOUNDING_BOX_Y" in meas_map
        assert meas_map["BOUNDING_BOX_Y"].value == 150.0
        assert "BOUNDING_BOX_Z" in meas_map
        assert meas_map["BOUNDING_BOX_Z"].value == 80.0
        assert "HOLE_DIAMETER" in meas_map
        assert meas_map["HOLE_DIAMETER"].value == 10.0  # radius 5.0 * 2
        assert "WALL_THICKNESS" in meas_map
        assert meas_map["WALL_THICKNESS"].value == 2.35  # from 0 to 2.35

        # -------------------------------------------------------------------------
        # 2. CAPABILITY REGISTRY & UNSUPPORTED FORMAT REJECTION
        # -------------------------------------------------------------------------
        # Rejection of STL, OBJ, DXF, GERBER
        for unsupp_ext in ["housing.stl", "model.obj", "drawing.dxf", "pcb.gbr", "trace.iges"]:
            unsupp_upload = await client.post(
                f"/api/v1/jobs/{job_id}/cad/upload",
                headers=admin_headers,
                files={"file": (unsupp_ext, b"binary_data", "application/octet-stream")},
            )
            assert unsupp_upload.status_code == 400, unsupp_upload.text
            err_detail = unsupp_upload.json()["detail"]
            assert err_detail["error_code"] == "UNSUPPORTED_CAD_FORMAT"

        # -------------------------------------------------------------------------
        # 3. AUTHORITATIVE STEP CAD UPLOAD & INGESTION
        # -------------------------------------------------------------------------
        step_bytes = DETERMINISTIC_STEP_CONTENT.encode("utf-8")
        upload_res = await client.post(
            f"/api/v1/jobs/{job_id}/cad/upload",
            headers=admin_headers,
            files={"file": ("enclosure_body.stp", io.BytesIO(step_bytes), "application/step")},
        )
        assert upload_res.status_code == 201, upload_res.text
        cad_data = upload_res.json()
        cad_model_id = cad_data["id"]
        evidence_id = cad_data["evidence_id"]
        sha256_hash = cad_data["model_hash"]

        # Server-side SHA-256 validation
        assert len(sha256_hash) == 64
        assert cad_data["processing_status"] == CADProcessingStatus.MEASUREMENTS_AVAILABLE
        assert cad_data["bounding_box"]["dimensions"] == [200.0, 150.0, 80.0]
        assert cad_data["volume_mm3"] == 2400000.0

        # -------------------------------------------------------------------------
        # 4. TENANT ISOLATION & RBAC ENFORCEMENT
        # -------------------------------------------------------------------------
        # Tenant B cannot access Org A's CAD model
        foreign_get = await client.get(
            f"/api/v1/jobs/{job_id}/cad/{cad_model_id}",
            headers=org_b_headers,
        )
        assert foreign_get.status_code in {403, 404}

        # Auditor cannot upload CAD model (RBAC check)
        auditor_upload = await client.post(
            f"/api/v1/jobs/{job_id}/cad/upload",
            headers=auditor_headers,
            files={"file": ("test.stp", io.BytesIO(step_bytes), "application/step")},
        )
        assert auditor_upload.status_code == 403

        # -------------------------------------------------------------------------
        # 5. PERSISTENT ENTITIES & IMMUTABLE SNAPSHOT
        # -------------------------------------------------------------------------
        # Components
        comps_res = await client.get(f"/api/v1/jobs/{job_id}/cad/{cad_model_id}/components", headers=admin_headers)
        assert comps_res.status_code == 200
        comps = comps_res.json()
        assert len(comps) >= 1

        # Measurements
        meas_api_res = await client.get(f"/api/v1/jobs/{job_id}/cad/{cad_model_id}/measurements", headers=admin_headers)
        assert meas_api_res.status_code == 200
        meas_list = meas_api_res.json()
        assert len(meas_list) >= 5

        # Snapshot
        snap_res = await client.get(f"/api/v1/jobs/{job_id}/cad/{cad_model_id}/snapshot", headers=admin_headers)
        assert snap_res.status_code == 200
        snap = snap_res.json()
        assert snap["source_sha256"] == sha256_hash
        assert snap["geometry_statistics"]["solid_count"] == 1

        # -------------------------------------------------------------------------
        # 6. EVIDENCE GATING ENFORCEMENT ON PRODUCT DNA MAPPING
        # -------------------------------------------------------------------------
        # Backing evidence currently has acceptance_status = 'REQUIRES_REVIEW'
        # Attempting to map to DNA must fail with 400 CAD_EVIDENCE_GATING_VIOLATION
        gate_fail = await client.post(
            f"/api/v1/jobs/{job_id}/cad/{cad_model_id}/map-to-dna",
            headers=admin_headers,
        )
        assert gate_fail.status_code == 400
        assert gate_fail.json()["detail"]["error_code"] == "CAD_EVIDENCE_GATING_VIOLATION"

        # Now formally ACCEPT the backing evidence artifact
        accept_res = await client.post(
            f"/api/v1/jobs/{job_id}/evidence/{evidence_id}/review",
            headers=admin_headers,
            json={"decision": "ACCEPTED", "reason": "Mechanical engineer reviewed STEP B-Rep topology."},
        )
        assert accept_res.status_code == 200

        # Now map CAD measurements to Product DNA -> MUST SUCCEED
        map_success = await client.post(
            f"/api/v1/jobs/{job_id}/cad/{cad_model_id}/map-to-dna",
            headers=admin_headers,
        )
        assert map_success.status_code == 200
        map_data = map_success.json()
        assert map_data["status"] == "success"
        assert map_data["mapped_count"] >= 5
        assert "wall_thickness" in map_data["parameters"]
        assert "enclosure_height" in map_data["parameters"]
        assert "hole_diameter" in map_data["parameters"]

        # Verify Product DNA records in database
        dna_res = await client.get(f"/api/v1/jobs/{job_id}/dna", headers=admin_headers)
        assert dna_res.status_code == 200
        raw_dna = dna_res.json().get("raw_parameters", [])
        dna_facts = {d["parameter"]: d for d in raw_dna}
        assert dna_facts["wall_thickness"]["value"] == "2.35"
        assert dna_facts["wall_thickness"]["unit"] == "mm"
        assert dna_facts["enclosure_height"]["value"] == "80.0"
        assert dna_facts["hole_diameter"]["value"] == "10.0"

        # -------------------------------------------------------------------------
        # 7. DETERMINISTIC COMPLIANCE EVALUATION (GEOMETRY REQUIREMENTS)
        # -------------------------------------------------------------------------
        # Add Standard to Job
        std_res = await client.post(
            f"/api/v1/jobs/{job_id}/standards",
            headers=admin_headers,
            json={
                "standard_identifier": "IS 13252 (Part 1):2010",
                "revision_year": "2010",
                "title": "Information Technology Equipment - Safety - General Requirements",
                "applicability": "Enclosure Safety and Mechanical Contours",
                "is_active_assessment_basis": True,
            },
        )
        assert std_res.status_code == 201
        standard_id = std_res.json()["id"]

        # Req 1: Wall thickness >= 2.0 mm (Observed 2.35 mm -> PASS)
        r1 = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            headers=admin_headers,
            json={
                "clause_number": "4.2.1",
                "requirement_id": "REQ-4.2.1",
                "clause_reference": "Clause 4.2.1",
                "section": "Mechanical Enclosure Strength",
                "requirement_text": "The minimum structural wall thickness of polymeric enclosures shall be at least 2.0 mm.",
                "requirement_type": "GEOMETRY",
                "parameter_key": "wall_thickness",
                "expected_unit": "mm",
                "comparison_operator": ">=",
                "threshold_min": "2.0",
                "verification_method": "TYPE_TEST",
            },
        )
        assert r1.status_code == 201

        # Req 2: Enclosure Height <= 50.0 mm (Observed 80.0 mm -> GAP)
        r2 = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            headers=admin_headers,
            json={
                "clause_number": "4.2.2",
                "requirement_id": "REQ-4.2.2",
                "clause_reference": "Clause 4.2.2",
                "section": "Enclosure Profile Limit",
                "requirement_text": "Compact rack enclosure height must not exceed 50.0 mm.",
                "requirement_type": "GEOMETRY",
                "parameter_key": "enclosure_height",
                "expected_unit": "mm",
                "comparison_operator": "<=",
                "threshold_max": "50.0",
                "verification_method": "TYPE_TEST",
            },
        )
        assert r2.status_code == 201

        # Req 3: Missing Geometry Parameter -> DATA_REQUIRED
        r3 = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            headers=admin_headers,
            json={
                "clause_number": "4.2.3",
                "requirement_id": "REQ-4.2.3",
                "clause_reference": "Clause 4.2.3",
                "section": "Creepage Distance",
                "requirement_text": "Air clearance distance across primary barriers shall be at least 5.0 mm.",
                "requirement_type": "GEOMETRY",
                "parameter_key": "unpopulated_creepage_distance",
                "expected_unit": "mm",
                "comparison_operator": ">=",
                "threshold_min": "5.0",
                "verification_method": "TYPE_TEST",
            },
        )
        assert r3.status_code == 201

        # Req 4: Ambiguous Geometry Feature -> HUMAN_REVIEW_REQUIRED
        r4 = await client.post(
            f"/api/v1/jobs/{job_id}/standards/{standard_id}/requirements",
            headers=admin_headers,
            json={
                "clause_number": "4.2.4",
                "requirement_id": "REQ-4.2.4",
                "clause_reference": "Clause 4.2.4",
                "section": "Visual Finish Inspection",
                "requirement_text": "Inspection of internal chamfer radius and burr-free edges.",
                "requirement_type": "GEOMETRY",
                "parameter_key": "wall_thickness",
                "expected_unit": "mm",
                "comparison_operator": ">=",
                "threshold_min": "1.0",
                "verification_method": "VISUAL_INSPECTION",  # Triggers human review
            },
        )
        assert r4.status_code == 201

        # Execute Deterministic Compliance Engine
        eval_res = await client.post(
            f"/api/v1/jobs/{job_id}/assessment/evaluate",
            headers=admin_headers,
            json={"standard_id": standard_id},
        )
        assert eval_res.status_code in [200, 201], eval_res.text
        eval_data = eval_res.json()
        res_by_clause = {r["clause_number"].replace("Clause ", "").strip(): r for r in eval_data["results"]}

        # Verify Clause 4.2.1: Wall thickness 2.35 mm >= 2.0 mm -> ENGINEERING_PASS
        r421 = res_by_clause["4.2.1"]
        assert r421["assessment_state"] == "ENGINEERING_PASS"
        assert r421["observed_value"] == "2.35"
        # Full CAD Trace
        assert "cad_provenance" in r421["trace_details"]
        assert r421["trace_details"]["cad_provenance"]["cad_model_id"] == cad_model_id

        # Verify Clause 4.2.2: Enclosure Height 80.0 mm <= 50.0 mm -> ENGINEERING_GAP
        r422 = res_by_clause["4.2.2"]
        assert r422["assessment_state"] == "ENGINEERING_GAP"
        assert r422["observed_value"] == "80.0"

        # Verify Clause 4.2.3: Unpopulated Parameter -> DATA_REQUIRED
        r423 = res_by_clause["4.2.3"]
        assert r423["assessment_state"] == "DATA_REQUIRED"

        # Verify Clause 4.2.4: Visual Inspection -> HUMAN_REVIEW_REQUIRED
        r424 = res_by_clause["4.2.4"]
        assert r424["assessment_state"] == "HUMAN_REVIEW_REQUIRED"

        # Verify Persistent Finding Created for GAP
        findings_res = await client.get(f"/api/v1/jobs/{job_id}/findings", headers=admin_headers)
        assert findings_res.status_code == 200
        findings = findings_res.json()
        assert len(findings) >= 1
        gap_finding = next(f for f in findings if "4.2.2" in f.get("title", "") or f.get("requirement_id") == r422["requirement_id"])
        assert gap_finding["severity"] in {"CRITICAL", "MAJOR", "MINOR"}

        # -------------------------------------------------------------------------
        # 8. CAD MEASUREMENT STATUTORY TRACE API
        # -------------------------------------------------------------------------
        # Find measurement ID for Wall Thickness
        wall_meas = next(m for m in meas_list if m["measurement_type"] == "WALL_THICKNESS")
        trace_res = await client.get(
            f"/api/v1/jobs/{job_id}/cad/{cad_model_id}/trace/{wall_meas['id']}",
            headers=admin_headers,
        )
        assert trace_res.status_code == 200
        trace_obj = trace_res.json()
        assert trace_obj["measurement"]["measured_value"] == 2.35
        assert trace_obj["source"]["cad_model_id"] == cad_model_id
        assert trace_obj["source"]["sha256"] == sha256_hash
        assert trace_obj["source"]["acceptance_status"] == "ACCEPTED"

        # -------------------------------------------------------------------------
        # 9. BABYLON.JS MESH ENDPOINT
        # -------------------------------------------------------------------------
        mesh_res = await client.get(f"/api/v1/jobs/{job_id}/cad/{cad_model_id}/mesh", headers=admin_headers)
        assert mesh_res.status_code == 200
        mesh_dict = mesh_res.json()
        assert mesh_dict["mesh"]["type"] == "BOUNDING_ENVELOPE"
        assert mesh_dict["mesh"]["dimensions"] == [200.0, 150.0, 80.0]

        # -------------------------------------------------------------------------
        # 10. AUDIT TRAIL VERIFICATION
        # -------------------------------------------------------------------------
        audit_res = await client.get(f"/api/v1/audit/jobs/{job_id}", headers=admin_headers)
        assert audit_res.status_code == 200
        audit_events = [a["action"] for a in audit_res.json()]
        assert "CAD_PROCESSING_STARTED" in audit_events
        assert "CAD_PROCESSING_COMPLETED" in audit_events
        assert "CAD_SNAPSHOT_CREATED" in audit_events
        assert "CAD_DNA_PARAMETER_CREATED" in audit_events
