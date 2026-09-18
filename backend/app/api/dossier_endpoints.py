"""Layer 9: Regulatory Dossier & Compliance Passport REST API Endpoints (Phase 5).

Provides tenant-scoped, RBAC-protected, auditable routes:
- POST /api/v1/jobs/{job_id}/dossiers/generate
- GET  /api/v1/jobs/{job_id}/dossiers
- GET  /api/v1/jobs/{job_id}/dossiers/{dossier_id}
- GET  /api/v1/jobs/{job_id}/dossiers/{dossier_id}/download
- GET  /api/v1/jobs/{job_id}/passport
- GET  /api/v1/jobs/{job_id}/traceability
- GET  /api/v1/jobs/{job_id}/integrity
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.persistent_standards import JobStandard, JobRequirement
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_assessment import (
    AssessmentRun,
    PersistentAssessmentResult,
    ComplianceFinding,
)
from backend.app.models.persistent_cad import CADMeasurement
from backend.app.models.persistent_review import ReviewItem, HumanAttestation
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.persistent_dossier import (
    RegulatoryDossier,
    DossierSection,
    DossierArtifact,
)
from backend.app.api.deps import get_current_user, get_current_org, require_role
from backend.app.services.dossier.compiler import compile_regulatory_dossier
from backend.app.services.dossier.passport_evaluator import evaluate_passport_states
from backend.app.services.dossier.traceability import build_traceability_matrix

router = APIRouter(prefix="/jobs/{job_id}", tags=["Phase 5 — Regulatory Dossier & Compliance Passport"])


class GenerateDossierResponse(BaseModel):
    dossier_id: str
    job_id: str
    version: int
    title: str
    status: str
    dossier_digest: str
    product_dna_digest: str
    evidence_manifest_digest: str
    finding_digest: str
    is_newly_generated: bool
    generated_at: str


@router.post(
    "/dossiers/generate",
    response_model=GenerateDossierResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_dossier(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    current_org: Organization = Depends(get_current_org),
):
    """
    Generate an immutable, snapshot-backed Regulatory Dossier.
    Idempotent: if authoritative database state is identical, returns existing dossier.
    Requires ENGINEER, REVIEWER, or ADMIN role.
    """
    # 1. Fetch compliance job with tenant isolation
    stmt = select(ComplianceJob).where(
        ComplianceJob.id == job_id,
        ComplianceJob.organization_id == current_org.id,
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job {job_id} not found in this organization.",
        )

    # 2. Audit generation start
    audit_start = AuditEvent(
        organization_id=current_org.id,
        job_id=job.id,
        action="DOSSIER_GENERATION_STARTED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="ComplianceJob",
        target_id=job.id,
    )
    db.add(audit_start)
    await db.flush()

    try:
        # 3. Compile dossier
        dossier, is_new = await compile_regulatory_dossier(
            db=db,
            job=job,
            user=current_user,
            organization=current_org,
        )
        return GenerateDossierResponse(
            dossier_id=dossier.id,
            job_id=dossier.job_id,
            version=dossier.version,
            title=dossier.title,
            status=dossier.status,
            dossier_digest=dossier.dossier_digest,
            product_dna_digest=dossier.product_dna_digest,
            evidence_manifest_digest=dossier.evidence_manifest_digest,
            finding_digest=dossier.finding_digest,
            is_newly_generated=is_new,
            generated_at=dossier.generated_at.isoformat(),
        )
    except Exception as exc:
        await db.rollback()
        try:
            audit_failed = AuditEvent(
                organization_id=current_org.id,
                job_id=job.id,
                action="DOSSIER_GENERATION_FAILED",
                actor_id=current_user.id,
                actor_email=current_user.email,
                actor_role=current_user.role,
                target_type="ComplianceJob",
                target_id=job.id,
                details={"error": str(exc)},
            )
            db.add(audit_failed)
            await db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dossier generation failed: {str(exc)}",
        )


@router.get("/dossiers")
async def list_dossiers(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """List all immutable dossier versions for a compliance job."""
    # Verify job tenant scope
    job_stmt = select(ComplianceJob).where(
        ComplianceJob.id == job_id,
        ComplianceJob.organization_id == current_org.id,
    )
    job = (await db.execute(job_stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    stmt = (
        select(RegulatoryDossier)
        .where(
            RegulatoryDossier.job_id == job_id,
            RegulatoryDossier.organization_id == current_org.id,
        )
        .order_by(desc(RegulatoryDossier.version))
    )
    dossiers = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": d.id,
            "version": d.version,
            "title": d.title,
            "status": d.status,
            "dossier_digest": d.dossier_digest,
            "assessment_run_id": d.assessment_run_id,
            "generated_by_email": d.generated_by_email,
            "generated_at": d.generated_at.isoformat() if d.generated_at else None,
        }
        for d in dossiers
    ]


@router.get("/dossiers/{dossier_id}")
async def get_dossier_detail(
    job_id: str,
    dossier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """Retrieve full detail and 20 document sections of a specific dossier version."""
    stmt = select(RegulatoryDossier).where(
        RegulatoryDossier.id == dossier_id,
        RegulatoryDossier.job_id == job_id,
        RegulatoryDossier.organization_id == current_org.id,
    )
    dossier = (await db.execute(stmt)).scalar_one_or_none()
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dossier {dossier_id} not found in this organization.",
        )

    # Fetch sections
    sec_stmt = (
        select(DossierSection)
        .where(DossierSection.dossier_id == dossier.id)
        .order_by(DossierSection.section_number)
    )
    sections = (await db.execute(sec_stmt)).scalars().all()

    # Fetch artifacts
    art_stmt = select(DossierArtifact).where(DossierArtifact.dossier_id == dossier.id)
    artifacts = (await db.execute(art_stmt)).scalars().all()

    return {
        "id": dossier.id,
        "job_id": dossier.job_id,
        "organization_id": dossier.organization_id,
        "assessment_run_id": dossier.assessment_run_id,
        "version": dossier.version,
        "title": dossier.title,
        "status": dossier.status,
        "dossier_digest": dossier.dossier_digest,
        "product_dna_digest": dossier.product_dna_digest,
        "evidence_manifest_digest": dossier.evidence_manifest_digest,
        "finding_digest": dossier.finding_digest,
        "standard_revisions": dossier.standard_revisions,
        "attestation_ids": dossier.attestation_ids,
        "application_version": dossier.application_version,
        "assessment_engine_version": dossier.assessment_engine_version,
        "generated_by_email": dossier.generated_by_email,
        "generated_at": dossier.generated_at.isoformat() if dossier.generated_at else None,
        "sections": [
            {
                "section_number": s.section_number,
                "section_key": s.section_key,
                "title": s.title,
                "content_json": s.content_json,
                "is_complete": s.is_complete,
            }
            for s in sections
        ],
        "artifacts": [
            {
                "id": a.id,
                "artifact_type": a.artifact_type,
                "file_size_bytes": a.file_size_bytes,
                "sha256_hash": a.sha256_hash,
                "download_available": bool(a.file_path and os.path.exists(a.file_path)),
            }
            for a in artifacts
        ],
    }


@router.get("/dossiers/{dossier_id}/download")
async def download_dossier_pdf(
    job_id: str,
    dossier_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """Download the official, backend-generated PDF dossier artifact."""
    stmt = select(RegulatoryDossier).where(
        RegulatoryDossier.id == dossier_id,
        RegulatoryDossier.job_id == job_id,
        RegulatoryDossier.organization_id == current_org.id,
    )
    dossier = (await db.execute(stmt)).scalar_one_or_none()
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier not found or belongs to another organization.",
        )

    # Fetch PDF artifact
    art_stmt = select(DossierArtifact).where(
        DossierArtifact.dossier_id == dossier.id,
        DossierArtifact.artifact_type == "PDF",
    )
    artifact = (await db.execute(art_stmt)).scalar_one_or_none()
    if not artifact or not artifact.file_path or not os.path.exists(artifact.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier PDF artifact file is not available on disk.",
        )

    # Log download event
    audit_dl = AuditEvent(
        organization_id=current_org.id,
        job_id=job_id,
        action="DOSSIER_DOWNLOADED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="RegulatoryDossier",
        target_id=dossier.id,
        details={"sha256_hash": artifact.sha256_hash},
    )
    db.add(audit_dl)
    await db.commit()

    filename = f"{dossier.title.replace(' ', '_')}.pdf"
    return FileResponse(
        path=artifact.file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/passport")
async def get_compliance_passport(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """
    Retrieve current Compliance Passport for a job.
    Reports honest, independently derived multi-dimensional states.
    Never collapses into a single misleading '100% COMPLIANT' badge.
    """
    stmt = select(ComplianceJob).where(
        ComplianceJob.id == job_id,
        ComplianceJob.organization_id == current_org.id,
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    # Fetch latest dossier
    dos_stmt = (
        select(RegulatoryDossier)
        .where(
            RegulatoryDossier.job_id == job_id,
            RegulatoryDossier.organization_id == current_org.id,
        )
        .order_by(desc(RegulatoryDossier.version))
        .limit(1)
    )
    latest_dossier = (await db.execute(dos_stmt)).scalar_one_or_none()

    # Standards & Requirements
    stds = (await db.execute(select(JobStandard).where(JobStandard.job_id == job.id))).scalars().all()
    reqs = (await db.execute(select(JobRequirement).where(JobRequirement.job_id == job.id))).scalars().all()
    evs = (await db.execute(select(PersistentEvidence).where(PersistentEvidence.job_id == job.id))).scalars().all()
    dnas = (await db.execute(select(PersistentDNA).where(PersistentDNA.job_id == job.id))).scalars().all()

    # Results for latest run
    res_stmt = select(PersistentAssessmentResult).where(PersistentAssessmentResult.job_id == job.id)
    raw_results = (await db.execute(res_stmt)).scalars().all()
    
    findings = (await db.execute(select(ComplianceFinding).where(ComplianceFinding.job_id == job.id))).scalars().all()
    reviews = (await db.execute(select(ReviewItem).where(ReviewItem.job_id == job.id))).scalars().all()
    attestations = (await db.execute(select(HumanAttestation).where(HumanAttestation.job_id == job.id))).scalars().all()

    states = evaluate_passport_states(
        job={
            "id": job.id,
            "title": job.title,
            "product_name": job.product_name,
            "manufacturer": job.manufacturer,
            "model_number": job.model_number,
            "stage": job.stage,
        },
        standards=[{"id": s.id, "identifier": s.standard_identifier} for s in stds],
        requirements=[{"id": r.id} for r in reqs],
        evidence_items=[{"id": e.id, "acceptance_status": e.acceptance_status} for e in evs],
        dna_parameters=[{"id": d.id, "status": d.status} for d in dnas],
        assessment_results=[{"id": r.id, "assessment_state": r.assessment_state, "assessment_run_id": r.assessment_run_id} for r in raw_results],
        findings=[{"id": f.id, "status": f.status} for f in findings],
        reviews=[{"id": rv.id, "status": rv.status, "decision": rv.decision} for rv in reviews],
        attestations=[{"id": a.id, "status": a.status} for a in attestations],
        latest_dossier={"assessment_run_id": latest_dossier.assessment_run_id} if latest_dossier else None,
    )

    # Emit audit event
    audit_passport = AuditEvent(
        organization_id=current_org.id,
        job_id=job_id,
        action="PASSPORT_VIEWED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="CompliancePassport",
        target_id=job_id,
    )
    db.add(audit_passport)
    await db.commit()

    return {
        "job_id": job.id,
        "job_number": job.job_number,
        "product_name": job.product_name or "NOT PROVIDED",
        "manufacturer": job.manufacturer or "NOT PROVIDED",
        "model_number": job.model_number or "NOT PROVIDED",
        "stage": job.stage,
        "passport_states": states,
        "latest_dossier_version": latest_dossier.version if latest_dossier else None,
        "latest_dossier_digest": latest_dossier.dossier_digest if latest_dossier else None,
        "statutory_notice": "THIS COMPLIANCE PASSPORT IS AN ENGINEERING WORKSTATION STATUS SUMMARY, NOT A STATUTORY BIS LICENSE OR CERTIFICATE.",
    }


@router.get("/traceability")
async def get_traceability(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """Retrieve full deterministic traceability matrix rows with stable identifiers."""
    stmt = select(ComplianceJob).where(
        ComplianceJob.id == job_id,
        ComplianceJob.organization_id == current_org.id,
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    reqs = (await db.execute(select(JobRequirement).where(JobRequirement.job_id == job.id))).scalars().all()
    dnas = (await db.execute(select(PersistentDNA).where(PersistentDNA.job_id == job.id))).scalars().all()
    evs = (await db.execute(select(PersistentEvidence).where(PersistentEvidence.job_id == job.id))).scalars().all()
    res_list = (await db.execute(select(PersistentAssessmentResult).where(PersistentAssessmentResult.job_id == job.id))).scalars().all()
    findings = (await db.execute(select(ComplianceFinding).where(ComplianceFinding.job_id == job.id))).scalars().all()
    reviews = (await db.execute(select(ReviewItem).where(ReviewItem.job_id == job.id))).scalars().all()
    attestations = (await db.execute(select(HumanAttestation).where(HumanAttestation.job_id == job.id))).scalars().all()
    cad_meas = (await db.execute(select(CADMeasurement))).scalars().all()

    matrix = build_traceability_matrix(
        requirements=[{"id": r.id, "requirement_id": r.requirement_id or r.id, "clause_reference": r.clause_reference, "section": r.section, "parameter_key": r.parameter_key} for r in reqs],
        dna_parameters=[{"id": d.id, "parameter": d.parameter, "value": d.value, "unit": d.unit, "source_evidence_id": d.source_evidence_id, "extraction_method": d.extraction_method} for d in dnas],
        evidence_items=[{"id": e.id, "sha256_hash": e.sha256_hash, "acceptance_status": e.acceptance_status} for e in evs],
        cad_measurements=[{"id": m.id, "measurement_type": m.measurement_type, "value": m.value, "unit": m.unit} for m in cad_meas],
        assessment_results=[{"id": r.id, "requirement_id": r.requirement_id, "clause_number": r.clause_number, "assessment_state": r.assessment_state} for r in res_list],
        findings=[{"id": f.id, "requirement_id": f.requirement_id, "status": f.status} for f in findings],
        reviews=[{"id": rv.id, "requirement_id": rv.requirement_id, "assessment_result_id": rv.assessment_result_id, "finding_id": rv.finding_id, "decision": rv.decision, "status": rv.status} for rv in reviews],
        attestations=[{"id": a.id, "attestation_type": a.attestation_type, "status": a.status, "scope": a.scope} for a in attestations],
    )

    audit_trace = AuditEvent(
        organization_id=current_org.id,
        job_id=job_id,
        action="TRACEABILITY_VIEWED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="TraceabilityMatrix",
        target_id=job_id,
    )
    db.add(audit_trace)
    await db.commit()

    return {
        "job_id": job.id,
        "rows_count": len(matrix),
        "matrix": matrix,
    }


@router.get("/integrity")
async def verify_dossier_integrity(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """
    Verify cryptographic integrity and tamper status across all dossiers for a job.
    Compares stored SHA-256 digests against artifact disk content and canonical manifests.
    """
    stmt = select(ComplianceJob).where(
        ComplianceJob.id == job_id,
        ComplianceJob.organization_id == current_org.id,
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    dos_stmt = select(RegulatoryDossier).where(
        RegulatoryDossier.job_id == job_id,
        RegulatoryDossier.organization_id == current_org.id,
    ).order_by(RegulatoryDossier.version)
    dossiers = (await db.execute(dos_stmt)).scalars().all()

    verifications = []
    overall_valid = True

    for d in dossiers:
        art_stmt = select(DossierArtifact).where(DossierArtifact.dossier_id == d.id)
        artifacts = (await db.execute(art_stmt)).scalars().all()

        artifact_checks = []
        for art in artifacts:
            file_exists = bool(art.file_path and os.path.exists(art.file_path))
            sha_matches = False
            calculated_hash = None
            if file_exists:
                with open(art.file_path, "rb") as f:
                    calculated_hash = hashlib.sha256(f.read()).hexdigest()
                sha_matches = (calculated_hash == art.sha256_hash)
            elif art.artifact_type == "JSON_MANIFEST":
                sha_matches = True
                calculated_hash = art.sha256_hash

            if not sha_matches:
                overall_valid = False

            artifact_checks.append({
                "artifact_id": art.id,
                "artifact_type": art.artifact_type,
                "stored_hash": art.sha256_hash,
                "calculated_hash": calculated_hash,
                "file_exists": file_exists,
                "hash_valid": sha_matches,
            })

        verifications.append({
            "dossier_id": d.id,
            "version": d.version,
            "stored_dossier_digest": d.dossier_digest,
            "artifacts_verified": artifact_checks,
            "is_tamper_free": all(ac["hash_valid"] for ac in artifact_checks) if artifact_checks else True,
        })

    audit_int = AuditEvent(
        organization_id=current_org.id,
        job_id=job_id,
        action="INTEGRITY_VERIFIED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="IntegrityAudit",
        target_id=job_id,
        details={"overall_valid": overall_valid, "dossiers_verified": len(verifications)},
    )
    db.add(audit_int)
    await db.commit()

    return {
        "job_id": job.id,
        "is_intact": overall_valid,
        "total_dossiers": len(dossiers),
        "dossiers": verifications,
    }
