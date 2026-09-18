from typing import List, Optional, Any, Union, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_standards import JobStandard, JobRequirement
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_current_org, require_role

router = APIRouter(prefix="/jobs/{job_id}/standards", tags=["Standards & Clause Intelligence"])


class StandardAssignRequest(BaseModel):
    standard_identifier: str  # e.g., IS 13252 (Part 1): 2010
    title: str
    revision_year: Optional[str] = ""
    applicability: Optional[str] = "MANDATORY"
    is_active_assessment_basis: Optional[bool] = True
    scope_summary: Optional[str] = None


class RequirementCreateRequest(BaseModel):
    clause_number: Optional[str] = None
    clause_reference: Optional[str] = None
    section: Optional[str] = "General"
    requirement_id: Optional[str] = None
    title: Optional[str] = None
    requirement_text: Optional[str] = None
    description: Optional[str] = ""
    requirement_type: Optional[str] = "NUMERIC"
    parameter_key: Optional[str] = None
    expected_unit: Optional[str] = None
    unit: Optional[str] = None
    comparison_operator: Optional[str] = ">="
    threshold_min: Optional[Any] = None
    threshold_max: Optional[Any] = None
    limit_min: Optional[str] = None
    limit_max: Optional[str] = None
    expected_value: Optional[Any] = None
    allowed_values: Optional[list] = None
    applicability_condition: Optional[str] = None
    evidence_requirement: Optional[str] = None
    verification_method: Optional[str] = "TYPE_TEST"
    source_reference: Optional[str] = None
    test_method: Optional[str] = None
    pass_criteria: Optional[str] = None


class RequirementUpdateRequest(BaseModel):
    status: Optional[str] = None  # PENDING, PASS, FAIL, NOT_APPLICABLE
    description: Optional[str] = None
    requirement_text: Optional[str] = None
    pass_criteria: Optional[str] = None
    expected_value: Optional[str] = None
    threshold_min: Optional[str] = None
    threshold_max: Optional[str] = None


def format_standard_dict(std: JobStandard) -> dict:
    return {
        "id": std.id,
        "job_id": std.job_id,
        "organization_id": std.organization_id,
        "standard_identifier": std.standard_identifier,
        "title": std.title,
        "revision_year": std.revision_year,
        "applicability": std.applicability,
        "is_active_assessment_basis": std.is_active_assessment_basis,
        "scope_summary": std.scope_summary,
        "created_at": std.created_at.isoformat() if std.created_at else None,
    }


def format_req_dict(req: JobRequirement) -> dict:
    return {
        "id": req.id,
        "standard_id": req.standard_id,
        "job_id": req.job_id,
        "requirement_id": req.requirement_id or f"REQ-{req.clause_reference or req.clause_number}",
        "clause_reference": req.clause_reference or req.clause_number,
        "clause_number": req.clause_number or req.clause_reference,
        "section": req.section,
        "title": req.title,
        "requirement_text": req.requirement_text or req.description,
        "description": req.description or req.requirement_text,
        "requirement_type": req.requirement_type,
        "parameter_key": req.parameter_key,
        "expected_unit": req.expected_unit or req.unit,
        "unit": req.unit or req.expected_unit,
        "comparison_operator": req.comparison_operator,
        "threshold_min": req.threshold_min or req.limit_min,
        "threshold_max": req.threshold_max or req.limit_max,
        "limit_min": req.limit_min or req.threshold_min,
        "limit_max": req.limit_max or req.threshold_max,
        "expected_value": req.expected_value,
        "allowed_values": req.allowed_values or [],
        "applicability_condition": req.applicability_condition,
        "evidence_requirement": req.evidence_requirement,
        "verification_method": req.verification_method,
        "source_reference": req.source_reference,
        "test_method": req.test_method,
        "pass_criteria": req.pass_criteria,
        "status": req.status,
        "created_at": req.created_at.isoformat() if req.created_at else None,
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


@router.get("", response_model=List[dict])
async def list_standards(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all standards assigned to a compliance job."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(JobStandard)
        .where(
            JobStandard.job_id == job_id,
            JobStandard.organization_id == org.id,
        )
        .order_by(JobStandard.created_at)
    )
    stds = result.scalars().all()
    return [format_standard_dict(s) for s in stds]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def assign_standard(
    job_id: str,
    payload: StandardAssignRequest,
    current_user: User = Depends(require_role("ENGINEER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Assign a standard to the compliance job."""
    job = await _verify_job(job_id, org.id, db)

    # If this is marked active, deactivate others
    if payload.is_active_assessment_basis:
        await db.execute(
            update(JobStandard)
            .where(JobStandard.job_id == job_id)
            .values(is_active_assessment_basis=False)
        )

    std = JobStandard(
        organization_id=org.id,
        job_id=job.id,
        standard_identifier=payload.standard_identifier,
        title=payload.title,
        revision_year=payload.revision_year or "",
        applicability=payload.applicability or "MANDATORY",
        is_active_assessment_basis=payload.is_active_assessment_basis if payload.is_active_assessment_basis is not None else True,
        scope_summary=payload.scope_summary,
    )
    db.add(std)
    await db.flush()

    audit = AuditEvent(
        organization_id=org.id,
        job_id=job.id,
        action="STANDARD_ASSIGNED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="STANDARD",
        target_id=std.id,
        details={"standard_identifier": std.standard_identifier, "title": std.title},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(std)

    return format_standard_dict(std)


@router.patch("/{standard_id}/activate", response_model=dict)
async def set_active_standard(
    job_id: str,
    standard_id: str,
    current_user: User = Depends(require_role("ENGINEER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Mark a standard as the active regulatory assessment basis for the job."""
    await _verify_job(job_id, org.id, db)

    # Deactivate all other standards for this job
    await db.execute(
        update(JobStandard)
        .where(JobStandard.job_id == job_id)
        .values(is_active_assessment_basis=False)
    )

    std_res = await db.execute(
        select(JobStandard).where(
            JobStandard.id == standard_id,
            JobStandard.job_id == job_id,
            JobStandard.organization_id == org.id,
        )
    )
    std = std_res.scalars().first()
    if not std:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard '{standard_id}' not found.",
        )

    std.is_active_assessment_basis = True
    audit = AuditEvent(
        organization_id=org.id,
        job_id=job_id,
        action="STANDARD_ACTIVATED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="STANDARD",
        target_id=std.id,
        details={"standard_identifier": std.standard_identifier},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(std)

    return format_standard_dict(std)


@router.delete("/{standard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_standard(
    job_id: str,
    standard_id: str,
    current_user: User = Depends(require_role("ENGINEER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Remove assigned standard from job."""
    await _verify_job(job_id, org.id, db)
    std_res = await db.execute(
        select(JobStandard).where(
            JobStandard.id == standard_id,
            JobStandard.job_id == job_id,
            JobStandard.organization_id == org.id,
        )
    )
    std = std_res.scalars().first()
    if not std:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard '{standard_id}' not found.",
        )

    await db.delete(std)
    audit = AuditEvent(
        organization_id=org.id,
        job_id=job_id,
        action="STANDARD_REMOVED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="STANDARD",
        target_id=standard_id,
        details={"standard_identifier": std.standard_identifier},
    )
    db.add(audit)
    await db.commit()


@router.get("/{standard_id}/requirements", response_model=List[dict])
async def list_requirements(
    job_id: str,
    standard_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all clause requirements for an assigned standard."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(JobRequirement)
        .where(
            JobRequirement.standard_id == standard_id,
            JobRequirement.job_id == job_id,
        )
        .order_by(JobRequirement.clause_number)
    )
    reqs = result.scalars().all()
    return [format_req_dict(r) for r in reqs]


@router.post("/{standard_id}/requirements", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_requirement(
    job_id: str,
    standard_id: str,
    payload: RequirementCreateRequest,
    current_user: User = Depends(require_role("ENGINEER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Add a clause requirement to an assigned standard."""
    await _verify_job(job_id, org.id, db)
    clause_num = payload.clause_number or payload.clause_reference or "General"
    clause_ref = payload.clause_reference or payload.clause_number or "General"
    t_min = float(payload.threshold_min) if payload.threshold_min is not None else None
    t_max = float(payload.threshold_max) if payload.threshold_max is not None else None

    req = JobRequirement(
        standard_id=standard_id,
        job_id=job_id,
        clause_number=clause_num,
        title=payload.title or clause_ref,
        requirement_type=payload.requirement_type or "SAFETY",
        description=payload.description or payload.requirement_text or "",
        limit_min=payload.limit_min or (str(t_min) if t_min is not None else None),
        limit_max=payload.limit_max or (str(t_max) if t_max is not None else None),
        unit=payload.unit or payload.expected_unit,
        test_method=payload.test_method,
        pass_criteria=payload.pass_criteria,
        status="PENDING",
        # Statutory 15 columns
        requirement_id=payload.requirement_id or f"REQ-{clause_num}",
        clause_reference=clause_ref,
        section=payload.section or "General",
        requirement_text=payload.requirement_text or payload.description or "",
        parameter_key=payload.parameter_key,
        expected_unit=payload.expected_unit or payload.unit,
        comparison_operator=payload.comparison_operator or ">=",
        threshold_min=t_min,
        threshold_max=t_max,
        expected_value=str(payload.expected_value) if payload.expected_value is not None else None,
        allowed_values=payload.allowed_values or [],
        applicability_condition=payload.applicability_condition,
        evidence_requirement=payload.evidence_requirement,
        verification_method=payload.verification_method or "TYPE_TEST",
        source_reference=payload.source_reference,
    )
    db.add(req)
    await db.flush()

    audit = AuditEvent(
        organization_id=org.id,
        job_id=job_id,
        action="REQUIREMENT_ADDED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="REQUIREMENT",
        target_id=req.id,
        details={"clause_number": req.clause_number, "title": req.title},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(req)

    return format_req_dict(req)
