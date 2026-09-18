from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_standards import JobStandard, JobRequirement
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_assessment import (
    AssessmentRun,
    PersistentAssessmentResult,
    ComplianceFinding,
)
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_current_org, require_role
from backend.app.services.compliance.evaluator import (
    DeterministicComplianceEvaluator,
    AssessmentState,
)

router = APIRouter(prefix="/jobs/{job_id}", tags=["Real Compliance Assessment Engine"])


class EvaluateAssessmentRequest(BaseModel):
    standard_id: Optional[str] = None


class FindingUpdateRequest(BaseModel):
    status: str  # OPEN | UNDER_REVIEW | RESOLVED | WAIVED
    review_notes: Optional[str] = None


def format_result_dict(res: PersistentAssessmentResult) -> dict:
    td = res.trace_details or {}
    ev_artifact = td.get("evidence_artifact", {}) if isinstance(td, dict) else {}
    return {
        "id": res.id,
        "assessment_run_id": res.assessment_run_id,
        "job_id": res.job_id,
        "requirement_id": res.requirement_id,
        "clause_number": res.clause_number,
        "parameter_key": res.parameter_key,
        "applicability_state": res.applicability_state,
        "applicability_reason": res.applicability_reason,
        "assessment_state": res.assessment_state,
        "observed_value": res.observed_value,
        "observed_unit": res.observed_unit,
        "normalized_value": res.normalized_value,
        "normalized_unit": res.normalized_unit,
        "expected_value": res.expected_value,
        "expected_unit": res.expected_unit,
        "threshold_min": res.threshold_min,
        "threshold_max": res.threshold_max,
        "comparison_operator": res.comparison_operator,
        "evaluation_expression": res.evaluation_expression,
        "source_evidence_id": res.source_evidence_id,
        "source_dna_id": res.source_dna_id,
        "source_file_name": ev_artifact.get("file_name"),
        "source_sha256": ev_artifact.get("sha256"),
        "explanation": res.explanation,
        "trace_details": td,
        "engine_version": res.engine_version,
        "evaluated_at": res.evaluated_at.isoformat() if res.evaluated_at else None,
        "evaluated_by": res.evaluated_by,
    }


def format_finding_dict(f: ComplianceFinding) -> dict:
    return {
        "id": f.id,
        "organization_id": f.organization_id,
        "job_id": f.job_id,
        "assessment_run_id": f.assessment_run_id,
        "requirement_id": f.requirement_id,
        "severity": f.severity,
        "title": f.title,
        "description": f.description,
        "observed_value": f.observed_value,
        "expected_value": f.expected_value,
        "evidence_reference": f.evidence_reference,
        "status": f.status,
        "review_notes": f.review_notes,
        "reviewed_by": f.reviewed_by,
        "reviewed_at": f.reviewed_at.isoformat() if f.reviewed_at else None,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


async def _verify_job(job_id: str, org_id: str, db: AsyncSession) -> ComplianceJob:
    result = await db.execute(
        select(ComplianceJob).where(
            ComplianceJob.id == job_id,
            ComplianceJob.organization_id == org_id,
        )
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job '{job_id}' not found.",
        )
    return job


@router.post("/assessment/evaluate", response_model=dict, status_code=status.HTTP_201_CREATED)
async def evaluate_compliance_job(
    job_id: str,
    payload: Optional[EvaluateAssessmentRequest] = None,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Execute authoritative deterministic compliance assessment on backend and persist results."""
    job = await _verify_job(job_id, org.id, db)

    # Resolve Standard: either from payload or active assessment basis
    standard_id = payload.standard_id if payload else None
    if standard_id:
        std_res = await db.execute(
            select(JobStandard).where(
                JobStandard.id == standard_id,
                JobStandard.job_id == job_id,
                JobStandard.organization_id == org.id,
            )
        )
        standard = std_res.scalars().first()
        if not standard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Standard '{standard_id}' not found for job.",
            )
    else:
        std_res = await db.execute(
            select(JobStandard).where(
                JobStandard.job_id == job_id,
                JobStandard.organization_id == org.id,
                JobStandard.is_active_assessment_basis == True,
            )
        )
        standard = std_res.scalars().first()
        if not standard:
            # Fallback to first assigned standard
            std_fallback = await db.execute(
                select(JobStandard)
                .where(
                    JobStandard.job_id == job_id,
                    JobStandard.organization_id == org.id,
                )
                .order_by(JobStandard.created_at)
            )
            standard = std_fallback.scalars().first()

    if not standard:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No statutory standard assigned to this compliance job. Assign a standard before evaluation.",
        )

    # Audit log: Assessment Started
    db.add(
        AuditEvent(
            organization_id=org.id,
            job_id=job.id,
            action="ASSESSMENT_STARTED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="ASSESSMENT_RUN",
            target_id=None,
            details={"standard_identifier": standard.standard_identifier, "engine": DeterministicComplianceEvaluator.ENGINE_VERSION},
        )
    )

    # Fetch Requirements for Standard
    req_res = await db.execute(
        select(JobRequirement)
        .where(
            JobRequirement.standard_id == standard.id,
            JobRequirement.job_id == job_id,
        )
        .order_by(JobRequirement.clause_reference)
    )
    requirements = req_res.scalars().all()

    # Fetch Product DNA
    dna_res = await db.execute(
        select(PersistentDNA).where(
            PersistentDNA.job_id == job_id,
            PersistentDNA.organization_id == org.id,
        )
    )
    dna_items = dna_res.scalars().all()
    dna_map = {
        item.parameter: {
            "id": item.id,
            "parameter": item.parameter,
            "value": item.value,
            "unit": item.unit,
            "confidence": item.confidence,
            "status": item.status,
            "source_evidence_id": item.source_evidence_id,
            "source_file_name": item.source_file_name,
            "page_or_sheet": item.page_or_sheet,
            "extraction_method": item.extraction_method,
            "verification_timestamp": item.verification_timestamp.isoformat() if item.verification_timestamp else None,
            "metadata_json": item.metadata_json or {},
        }
        for item in dna_items
    }

    # Fetch Evidence Map
    ev_res = await db.execute(
        select(PersistentEvidence).where(
            PersistentEvidence.job_id == job_id,
            PersistentEvidence.organization_id == org.id,
        )
    )
    ev_items = ev_res.scalars().all()
    evidence_map = {
        ev.id: {
            "id": ev.id,
            "file_name": ev.file_name,
            "file_type": ev.file_type,
            "mime_type": ev.mime_type,
            "sha256_hash": ev.sha256_hash,
            "acceptance_status": ev.acceptance_status,
            "processing_status": ev.processing_status,
        }
        for ev in ev_items
    }

    # Initialize Assessment Run Entity
    summary_counts = {
        "total": len(requirements),
        "engineering_pass": 0,
        "engineering_gap": 0,
        "data_required": 0,
        "conflict": 0,
        "not_applicable": 0,
        "human_review_required": 0,
    }

    assessment_run = AssessmentRun(
        organization_id=org.id,
        job_id=job.id,
        standard_id=standard.id,
        engine_version=DeterministicComplianceEvaluator.ENGINE_VERSION,
        standard_revision=standard.revision_year or standard.standard_identifier,
        dna_snapshot=dna_map,
        summary=summary_counts,
        created_by=current_user.id,
    )
    db.add(assessment_run)
    await db.flush()

    evaluated_results: List[PersistentAssessmentResult] = []
    generated_findings: List[ComplianceFinding] = []

    for req in requirements:
        req_dict = {
            "id": req.id,
            "standard_id": req.standard_id,
            "job_id": req.job_id,
            "clause_reference": req.clause_reference or req.clause_number,
            "clause_number": req.clause_number or req.clause_reference,
            "section": req.section,
            "requirement_id": req.requirement_id,
            "title": req.title,
            "requirement_text": req.requirement_text or req.description,
            "requirement_type": req.requirement_type,
            "parameter_key": req.parameter_key,
            "expected_unit": req.expected_unit or req.unit,
            "comparison_operator": req.comparison_operator,
            "threshold_min": req.threshold_min or req.limit_min,
            "threshold_max": req.threshold_max or req.limit_max,
            "expected_value": req.expected_value,
            "allowed_values": req.allowed_values,
            "applicability_condition": req.applicability_condition,
            "evidence_requirement": req.evidence_requirement,
            "verification_method": req.verification_method,
            "source_reference": req.source_reference,
        }

        eval_output = DeterministicComplianceEvaluator.evaluate_requirement(
            requirement=req_dict,
            product_dna_facts=dna_map,
            evidence_map=evidence_map,
            conflicts=[],
            evaluated_by=current_user.email,
        )

        st = eval_output["assessment_state"]
        if st == AssessmentState.ENGINEERING_PASS:
            summary_counts["engineering_pass"] += 1
        elif st == AssessmentState.ENGINEERING_GAP:
            summary_counts["engineering_gap"] += 1
        elif st == AssessmentState.DATA_REQUIRED:
            summary_counts["data_required"] += 1
        elif st == AssessmentState.CONFLICT:
            summary_counts["conflict"] += 1
        elif st == AssessmentState.NOT_APPLICABLE:
            summary_counts["not_applicable"] += 1
        elif st == AssessmentState.HUMAN_REVIEW_REQUIRED:
            summary_counts["human_review_required"] += 1

        db_result = PersistentAssessmentResult(
            assessment_run_id=assessment_run.id,
            job_id=job.id,
            requirement_id=req.id,
            clause_number=eval_output["clause_number"],
            parameter_key=eval_output["parameter_key"],
            applicability_state=eval_output["applicability_state"],
            applicability_reason=eval_output["applicability_reason"],
            assessment_state=st,
            observed_value=eval_output["observed_value"],
            observed_unit=eval_output["observed_unit"],
            normalized_value=eval_output["normalized_value"],
            normalized_unit=eval_output["normalized_unit"],
            expected_value=eval_output["expected_value"],
            expected_unit=eval_output["expected_unit"],
            threshold_min=eval_output["threshold_min"],
            threshold_max=eval_output["threshold_max"],
            comparison_operator=eval_output["comparison_operator"],
            evaluation_expression=eval_output["evaluation_expression"],
            source_evidence_id=eval_output["source_evidence_id"],
            source_dna_id=eval_output["source_dna_id"],
            explanation=eval_output["explanation"],
            trace_details=eval_output["trace_details"],
            engine_version=eval_output["engine_version"],
            evaluated_at=eval_output["evaluated_at"],
            evaluated_by=eval_output["evaluated_by"],
        )
        db.add(db_result)
        evaluated_results.append(db_result)

        # Audit requirement evaluated
        db.add(
            AuditEvent(
                organization_id=org.id,
                job_id=job.id,
                action="REQUIREMENT_EVALUATED",
                actor_id=current_user.id,
                actor_email=current_user.email,
                actor_role=current_user.role,
                target_type="REQUIREMENT",
                target_id=req.id,
                details={
                    "clause_number": eval_output["clause_number"],
                    "state": st,
                    "parameter_key": eval_output["parameter_key"],
                },
            )
        )

        # Generate persistent finding for ENGINEERING_GAP
        if st == AssessmentState.ENGINEERING_GAP:
            finding = ComplianceFinding(
                organization_id=org.id,
                job_id=job.id,
                assessment_run_id=assessment_run.id,
                requirement_id=req.id,
                severity="MAJOR",
                title=f"Statutory Gap: Clause {eval_output['clause_number']} ({req.title})",
                description=eval_output["explanation"] or f"Value violates statutory threshold for clause {eval_output['clause_number']}",
                observed_value=eval_output["observed_value"],
                expected_value=eval_output["expected_value"],
                evidence_reference=evidence_map.get(eval_output.get("source_evidence_id", ""), {}).get("file_name"),
                status="OPEN",
            )
            db.add(finding)
            generated_findings.append(finding)

            db.add(
                AuditEvent(
                    organization_id=org.id,
                    job_id=job.id,
                    action="FINDING_CREATED",
                    actor_id=current_user.id,
                    actor_email=current_user.email,
                    actor_role=current_user.role,
                    target_type="COMPLIANCE_FINDING",
                    target_id=finding.id,
                    details={
                        "clause_number": eval_output["clause_number"],
                        "observed_value": eval_output["observed_value"],
                        "expected_value": eval_output["expected_value"],
                    },
                )
            )

    assessment_run.summary = summary_counts

    # Audit log: Assessment Completed
    db.add(
        AuditEvent(
            organization_id=org.id,
            job_id=job.id,
            action="ASSESSMENT_COMPLETED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="ASSESSMENT_RUN",
            target_id=assessment_run.id,
            details=summary_counts,
        )
    )

    await db.commit()
    await db.refresh(assessment_run)

    return {
        "assessment_run_id": assessment_run.id,
        "job_id": job.id,
        "standard_identifier": standard.standard_identifier,
        "summary": summary_counts,
        "results": [format_result_dict(r) for r in evaluated_results],
        "findings": [format_finding_dict(f) for f in generated_findings],
        "timestamp": assessment_run.created_at.isoformat() if assessment_run.created_at else datetime.now(timezone.utc).isoformat(),
        "engine_version": assessment_run.engine_version,
    }


@router.get("/assessment/latest", response_model=dict)
async def get_latest_assessment(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the latest persistent assessment run and its evaluated results for a job."""
    await _verify_job(job_id, org.id, db)

    run_res = await db.execute(
        select(AssessmentRun)
        .where(
            AssessmentRun.job_id == job_id,
            AssessmentRun.organization_id == org.id,
        )
        .order_by(desc(AssessmentRun.created_at))
        .limit(1)
    )
    latest_run = run_res.scalars().first()
    if not latest_run:
        return {
            "status": "no_assessment_run",
            "message": "No assessment run available.",
            "job_id": job_id,
            "summary": {
                "total": 0,
                "engineering_pass": 0,
                "engineering_gap": 0,
                "data_required": 0,
                "conflict": 0,
                "not_applicable": 0,
                "human_review_required": 0,
            },
            "results": [],
        }

    results_res = await db.execute(
        select(PersistentAssessmentResult)
        .where(PersistentAssessmentResult.assessment_run_id == latest_run.id)
        .order_by(PersistentAssessmentResult.clause_number)
    )
    results = results_res.scalars().all()

    findings_res = await db.execute(
        select(ComplianceFinding).where(ComplianceFinding.assessment_run_id == latest_run.id)
    )
    findings = findings_res.scalars().all()

    return {
        "assessment_run_id": latest_run.id,
        "job_id": job_id,
        "standard_id": latest_run.standard_id,
        "standard_revision": latest_run.standard_revision,
        "engine_version": latest_run.engine_version,
        "summary": latest_run.summary,
        "results": [format_result_dict(r) for r in results],
        "findings": [format_finding_dict(f) for f in findings],
        "timestamp": latest_run.created_at.isoformat() if latest_run.created_at else None,
    }


@router.get("/assessment/runs", response_model=List[dict])
async def list_assessment_runs(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List historical reproducible assessment runs for a job."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(AssessmentRun)
        .where(
            AssessmentRun.job_id == job_id,
            AssessmentRun.organization_id == org.id,
        )
        .order_by(desc(AssessmentRun.created_at))
    )
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "job_id": r.job_id,
            "standard_id": r.standard_id,
            "standard_revision": r.standard_revision,
            "engine_version": r.engine_version,
            "summary": r.summary,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/assessment/runs/{run_id}", response_model=dict)
async def get_assessment_run(
    job_id: str,
    run_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve an immutable historical assessment run with its exact snapshot and results."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(AssessmentRun).where(
            AssessmentRun.id == run_id,
            AssessmentRun.job_id == job_id,
            AssessmentRun.organization_id == org.id,
        )
    )
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment run '{run_id}' not found.")

    res_items = await db.execute(
        select(PersistentAssessmentResult)
        .where(PersistentAssessmentResult.assessment_run_id == run.id)
        .order_by(PersistentAssessmentResult.clause_number)
    )
    results = res_items.scalars().all()

    findings_items = await db.execute(
        select(ComplianceFinding).where(ComplianceFinding.assessment_run_id == run.id)
    )
    findings = findings_items.scalars().all()

    return {
        "assessment_run_id": run.id,
        "job_id": job_id,
        "standard_id": run.standard_id,
        "standard_revision": run.standard_revision,
        "engine_version": run.engine_version,
        "dna_snapshot": run.dna_snapshot,
        "summary": run.summary,
        "results": [format_result_dict(r) for r in results],
        "findings": [format_finding_dict(f) for f in findings],
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.get("/findings", response_model=List[dict])
async def list_job_findings(
    job_id: str,
    status_filter: Optional[str] = None,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List persistent compliance findings for a job."""
    await _verify_job(job_id, org.id, db)
    stmt = select(ComplianceFinding).where(
        ComplianceFinding.job_id == job_id,
        ComplianceFinding.organization_id == org.id,
    )
    if status_filter:
        stmt = stmt.where(ComplianceFinding.status == status_filter.upper())
    stmt = stmt.order_by(desc(ComplianceFinding.created_at))

    result = await db.execute(stmt)
    findings = result.scalars().all()
    return [format_finding_dict(f) for f in findings]


@router.patch("/findings/{finding_id}", response_model=dict)
async def update_finding_status(
    job_id: str,
    finding_id: str,
    payload: FindingUpdateRequest,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Review and update the status of a statutory compliance gap finding."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(ComplianceFinding).where(
            ComplianceFinding.id == finding_id,
            ComplianceFinding.job_id == job_id,
            ComplianceFinding.organization_id == org.id,
        )
    )
    finding = result.scalars().first()
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance finding '{finding_id}' not found.",
        )

    valid_statuses = {"OPEN", "UNDER_REVIEW", "RESOLVED", "WAIVED"}
    new_status = payload.status.upper()
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid finding status '{payload.status}'. Allowed: {', '.join(valid_statuses)}",
        )

    finding.status = new_status
    if payload.review_notes:
        finding.review_notes = payload.review_notes
    finding.reviewed_by = current_user.id
    finding.reviewed_at = datetime.now(timezone.utc)

    db.add(
        AuditEvent(
            organization_id=org.id,
            job_id=job_id,
            action="FINDING_STATUS_UPDATED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="COMPLIANCE_FINDING",
            target_id=finding.id,
            details={"status": new_status, "review_notes": payload.review_notes},
        )
    )

    await db.commit()
    await db.refresh(finding)

    return format_finding_dict(finding)
