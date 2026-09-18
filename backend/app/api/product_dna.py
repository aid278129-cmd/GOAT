from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_current_org, require_role

router = APIRouter(prefix="/jobs/{job_id}/dna", tags=["Product DNA & Structured Parameters"])


class DNAParameterCreate(BaseModel):
    category: str  # Identity, Electrical, Mechanical, Safety, Environmental, Components, Materials, Interfaces, Regulatory
    parameter: str
    value: str
    unit: Optional[str] = None
    confidence: Optional[float] = 1.0
    status: Optional[str] = "VERIFIED"  # VERIFIED, CONFLICT, UNVERIFIED
    source_evidence_id: Optional[str] = None
    page_or_sheet: Optional[str] = None
    bounding_box: Optional[dict] = None
    extraction_method: Optional[str] = "ENGINEERING_VERIFIED"


class DNAParameterUpdate(BaseModel):
    value: Optional[str] = None
    unit: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = None
    page_or_sheet: Optional[str] = None
    extraction_method: Optional[str] = None


def format_dna_dict(param: PersistentDNA) -> dict:
    return {
        "id": param.id,
        "job_id": param.job_id,
        "organization_id": param.organization_id,
        "category": param.category,
        "parameter": param.parameter,
        "value": param.value,
        "unit": param.unit,
        "confidence": param.confidence,
        "status": param.status,
        "source_evidence_id": param.source_evidence_id,
        "source_file_name": param.source_file_name,
        "page_or_sheet": param.page_or_sheet,
        "bounding_box": param.bounding_box,
        "extraction_method": param.extraction_method,
        "verified_by": param.verified_by,
        "verification_timestamp": param.verification_timestamp.isoformat() if param.verification_timestamp else None,
        "created_at": param.created_at.isoformat() if param.created_at else None,
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


@router.get("", response_model=Dict[str, Any])
async def get_product_dna(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve structured Product DNA parameters grouped by engineering category."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(PersistentDNA)
        .where(
            PersistentDNA.job_id == job_id,
            PersistentDNA.organization_id == org.id,
        )
        .order_by(PersistentDNA.category, PersistentDNA.parameter)
    )
    params = result.scalars().all()

    # Pre-structure standard categories
    categories = [
        "Product Identity",
        "Electrical Characteristics",
        "Mechanical Characteristics",
        "Safety Characteristics",
        "Environmental Characteristics",
        "Components",
        "Materials",
        "Interfaces",
        "Regulatory Metadata",
    ]
    grouped = {cat: [] for cat in categories}

    for p in params:
        cat_key = p.category
        if cat_key not in grouped:
            grouped[cat_key] = []
        grouped[cat_key].append(format_dna_dict(p))

    return {
        "job_id": job_id,
        "total_parameters": len(params),
        "categories": grouped,
        "raw_parameters": [format_dna_dict(p) for p in params],
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_dna_parameter(
    job_id: str,
    payload: DNAParameterCreate,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Add a structured parameter to Product DNA with strict evidence gating and provenance."""
    job = await _verify_job(job_id, org.id, db)

    source_file_name = None
    # Strict Evidence Gating: If evidence is linked, must be ACCEPTED
    if payload.source_evidence_id:
        ev_res = await db.execute(
            select(PersistentEvidence).where(
                PersistentEvidence.id == payload.source_evidence_id,
                PersistentEvidence.job_id == job_id,
                PersistentEvidence.organization_id == org.id,
            )
        )
        evidence = ev_res.scalars().first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked source evidence '{payload.source_evidence_id}' does not exist for this job.",
            )

        if evidence.acceptance_status != "ACCEPTED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Evidence gating violation: Source evidence '{evidence.file_name}' has status "
                    f"'{evidence.acceptance_status}'. Only ACCEPTED evidence may contribute parameters to Product DNA."
                ),
            )
        source_file_name = evidence.file_name

    if payload.extraction_method == "CAD_MEASUREMENT" and not payload.source_evidence_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAD_MEASUREMENT extraction method strictly requires a linked source CAD evidence artifact.",
        )

    param = PersistentDNA(
        organization_id=org.id,
        job_id=job.id,
        category=payload.category,
        parameter=payload.parameter,
        value=payload.value,
        unit=payload.unit,
        confidence=payload.confidence or 1.0,
        status=payload.status or "VERIFIED",
        source_evidence_id=payload.source_evidence_id,
        source_file_name=source_file_name,
        page_or_sheet=payload.page_or_sheet,
        bounding_box=payload.bounding_box,
        extraction_method=payload.extraction_method or "MANUAL_VERIFIED",
        verified_by=current_user.id,
        verification_timestamp=datetime.now(timezone.utc),
    )
    db.add(param)
    await db.flush()

    # Audit log
    audit = AuditEvent(
        organization_id=org.id,
        job_id=job.id,
        action="DNA_PARAM_ADDED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="PRODUCT_DNA",
        target_id=param.id,
        details={
            "parameter": param.parameter,
            "category": param.category,
            "value": param.value,
            "source_evidence_id": param.source_evidence_id,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(param)

    return format_dna_dict(param)


@router.patch("/{param_id}", response_model=dict)
async def update_dna_parameter(
    job_id: str,
    param_id: str,
    payload: DNAParameterUpdate,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Update or resolve conflicts for a Product DNA parameter."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(PersistentDNA).where(
            PersistentDNA.id == param_id,
            PersistentDNA.job_id == job_id,
            PersistentDNA.organization_id == org.id,
        )
    )
    param = result.scalars().first()
    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DNA parameter '{param_id}' not found.",
        )

    for attr in ["value", "unit", "confidence", "status", "page_or_sheet", "extraction_method"]:
        val = getattr(payload, attr)
        if val is not None:
            setattr(param, attr, val)

    param.verified_by = current_user.id
    param.verification_timestamp = datetime.now(timezone.utc)

    audit = AuditEvent(
        organization_id=org.id,
        job_id=job_id,
        action="DNA_PARAM_UPDATED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="PRODUCT_DNA",
        target_id=param.id,
        details={"parameter": param.parameter, "updated_fields": payload.model_dump(exclude_none=True)},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(param)

    return format_dna_dict(param)


@router.delete("/{param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dna_parameter(
    job_id: str,
    param_id: str,
    current_user: User = Depends(require_role("ENGINEER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Remove a parameter from Product DNA."""
    await _verify_job(job_id, org.id, db)
    result = await db.execute(
        select(PersistentDNA).where(
            PersistentDNA.id == param_id,
            PersistentDNA.job_id == job_id,
            PersistentDNA.organization_id == org.id,
        )
    )
    param = result.scalars().first()
    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DNA parameter '{param_id}' not found.",
        )

    await db.delete(param)
    audit = AuditEvent(
        organization_id=org.id,
        job_id=job_id,
        action="DNA_PARAM_DELETED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="PRODUCT_DNA",
        target_id=param_id,
        details={"parameter": param.parameter},
    )
    db.add(audit)
    await db.commit()
