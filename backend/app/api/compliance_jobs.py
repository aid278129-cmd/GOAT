from typing import List, Optional
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.persistent_audit import AuditEvent
from backend.app.api.deps import get_current_user, get_current_org

router = APIRouter(prefix="/jobs", tags=["Compliance Jobs"])


class JobCreateRequest(BaseModel):
    title: str
    product_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    stage: Optional[str] = "01_EVIDENCE_INGESTION"


class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    product_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    compliance_score: Optional[float] = None
    metadata_json: Optional[dict] = None


def format_job_dict(job: ComplianceJob) -> dict:
    return {
        "id": job.id,
        "organization_id": job.organization_id,
        "job_number": job.job_number,
        "title": job.title,
        "product_name": job.product_name,
        "manufacturer": job.manufacturer,
        "model_number": job.model_number,
        "stage": job.stage,
        "status": job.status,
        "compliance_score": job.compliance_score,
        "created_by": job.created_by,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "metadata": job.metadata_json or {},
    }


@router.get("", response_model=List[dict])
async def list_jobs(
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all authoritative compliance jobs within the user's organization."""
    result = await db.execute(
        select(ComplianceJob)
        .where(ComplianceJob.organization_id == org.id)
        .order_by(desc(ComplianceJob.created_at))
    )
    jobs = result.scalars().all()
    return [format_job_dict(j) for j in jobs]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreateRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Create a new compliance job bound to the organization."""
    job_code = f"JOB-2026-{secrets.token_hex(3).upper()}"
    job = ComplianceJob(
        organization_id=org.id,
        job_number=job_code,
        title=payload.title,
        product_name=payload.product_name,
        manufacturer=payload.manufacturer,
        model_number=payload.model_number,
        stage=payload.stage or "01_EVIDENCE_INGESTION",
        status="IN_PROGRESS",
        compliance_score=0.0,
        created_by=current_user.id,
    )
    db.add(job)
    await db.flush()

    audit = AuditEvent(
        organization_id=org.id,
        job_id=job.id,
        action="JOB_CREATED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="COMPLIANCE_JOB",
        target_id=job.id,
        details={"job_number": job.job_number, "title": job.title},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(job)

    return format_job_dict(job)


@router.get("/{job_id}", response_model=dict)
async def get_job(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a specific compliance job with tenant verification."""
    result = await db.execute(
        select(ComplianceJob).where(
            ComplianceJob.id == job_id,
            ComplianceJob.organization_id == org.id,
        )
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job '{job_id}' not found in organization.",
        )
    return format_job_dict(job)


@router.patch("/{job_id}", response_model=dict)
async def update_job(
    job_id: str,
    payload: JobUpdateRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Update job properties, stage progression, or status."""
    result = await db.execute(
        select(ComplianceJob).where(
            ComplianceJob.id == job_id,
            ComplianceJob.organization_id == org.id,
        )
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job '{job_id}' not found.",
        )

    updated_fields = {}
    for attr in ["title", "product_name", "manufacturer", "model_number", "stage", "status", "compliance_score"]:
        val = getattr(payload, attr)
        if val is not None:
            setattr(job, attr, val)
            updated_fields[attr] = val

    if payload.metadata_json is not None:
        merged = (job.metadata_json or {}).copy()
        merged.update(payload.metadata_json)
        job.metadata_json = merged
        updated_fields["metadata"] = payload.metadata_json

    audit = AuditEvent(
        organization_id=org.id,
        job_id=job.id,
        action="JOB_UPDATED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="COMPLIANCE_JOB",
        target_id=job.id,
        details=updated_fields,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(job)

    return format_job_dict(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Delete a compliance job and all associated artifacts."""
    result = await db.execute(
        select(ComplianceJob).where(
            ComplianceJob.id == job_id,
            ComplianceJob.organization_id == org.id,
        )
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job '{job_id}' not found.",
        )

    await db.delete(job)
    audit = AuditEvent(
        organization_id=org.id,
        job_id=None,
        action="JOB_DELETED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="COMPLIANCE_JOB",
        target_id=job_id,
        details={"job_number": job.job_number},
    )
    db.add(audit)
    await db.commit()
