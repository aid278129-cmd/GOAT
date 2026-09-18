from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_evidence import PersistentEvidence, EvidenceLifecycleEvent
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_current_org, require_role
from backend.app.services.storage.service import storage_service

router = APIRouter(prefix="/jobs/{job_id}/evidence", tags=["Authoritative Evidence Ingestion & Review"])


class EvidenceReviewRequest(BaseModel):
    decision: str  # ACCEPTED | REJECTED | REQUIRES_REVIEW
    reason: Optional[str] = None


def format_evidence_dict(ev: PersistentEvidence) -> dict:
    return {
        "id": ev.id,
        "job_id": ev.job_id,
        "organization_id": ev.organization_id,
        "file_name": ev.file_name,
        "file_type": ev.file_type,
        "mime_type": ev.mime_type,
        "file_size_bytes": ev.file_size_bytes,
        "storage_path": ev.storage_path,
        "sha256_hash": ev.sha256_hash,
        "source": ev.source,
        "processing_status": ev.processing_status,
        "acceptance_status": ev.acceptance_status,
        "acceptance_reason": ev.acceptance_reason,
        "reviewed_by": ev.reviewed_by,
        "reviewed_at": ev.reviewed_at.isoformat() if ev.reviewed_at else None,
        "extracted_data": ev.extracted_data or {},
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
        "updated_at": ev.updated_at.isoformat() if ev.updated_at else None,
    }


async def _verify_job_ownership(job_id: str, org_id: str, db: AsyncSession) -> ComplianceJob:
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
            detail=f"Compliance job '{job_id}' not found in organization.",
        )
    return job


@router.get("", response_model=List[dict])
async def list_job_evidence(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all evidence artifacts for a compliance job."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(PersistentEvidence)
        .where(
            PersistentEvidence.job_id == job_id,
            PersistentEvidence.organization_id == org.id,
        )
        .order_by(desc(PersistentEvidence.created_at))
    )
    items = result.scalars().all()
    return [format_evidence_dict(i) for i in items]


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    job_id: str,
    file: UploadFile = File(...),
    source: Optional[str] = Form("Engineering Upload"),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Upload and persistently store an evidence artifact with server SHA-256 digest."""
    job = await _verify_job_ownership(job_id, org.id, db)

    # Stream to durable partition and calculate authoritative SHA-256
    stored = await storage_service.save_evidence_file(
        file=file,
        organization_id=org.id,
        job_id=job.id,
    )

    # Initial state: UPLOADED, gating requires review
    evidence = PersistentEvidence(
        organization_id=org.id,
        job_id=job.id,
        file_name=stored["file_name"],
        file_type=stored["file_type"],
        mime_type=stored["mime_type"],
        file_size_bytes=stored["file_size_bytes"],
        storage_path=stored["storage_path"],
        sha256_hash=stored["sha256_hash"],
        source=source or "Engineering Upload",
        processing_status="EXTRACTION_COMPLETE",
        acceptance_status="REQUIRES_REVIEW",
        extracted_data={
            "initial_scan": "completed",
            "file_size": stored["file_size_bytes"],
            "sha256": stored["sha256_hash"],
        },
    )
    db.add(evidence)
    await db.flush()

    # Append-only lifecycle event: Uploaded
    lifecycle_upload = EvidenceLifecycleEvent(
        evidence_id=evidence.id,
        event_type="UPLOADED",
        previous_status=None,
        new_status="UPLOADED",
        actor_id=current_user.id,
        actor_name=current_user.full_name or current_user.email,
        reason="Initial document ingestion",
        details={"sha256": evidence.sha256_hash, "size_bytes": evidence.file_size_bytes},
    )
    db.add(lifecycle_upload)

    # Append-only lifecycle event: Extraction Complete
    lifecycle_processed = EvidenceLifecycleEvent(
        evidence_id=evidence.id,
        event_type="EXTRACTION_COMPLETE",
        previous_status="UPLOADED",
        new_status="EXTRACTION_COMPLETE",
        actor_id=None,
        actor_name="Automated Ingestion Pipeline",
        reason="Metadata and digest computed; pending regulatory review",
        details={"sha256": evidence.sha256_hash},
    )
    db.add(lifecycle_processed)

    # Audit trail
    audit = AuditEvent(
        organization_id=org.id,
        job_id=job.id,
        action="EVIDENCE_UPLOADED",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="EVIDENCE",
        target_id=evidence.id,
        details={
            "file_name": evidence.file_name,
            "sha256": evidence.sha256_hash,
            "file_type": evidence.file_type,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(evidence)

    return format_evidence_dict(evidence)


@router.get("/{evidence_id}", response_model=dict)
async def get_evidence_detail(
    job_id: str,
    evidence_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed metadata and lifecycle event history for an evidence record."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(PersistentEvidence).where(
            PersistentEvidence.id == evidence_id,
            PersistentEvidence.job_id == job_id,
            PersistentEvidence.organization_id == org.id,
        )
    )
    ev = result.scalars().first()
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact '{evidence_id}' not found.",
        )

    # Fetch lifecycle events
    events_res = await db.execute(
        select(EvidenceLifecycleEvent)
        .where(EvidenceLifecycleEvent.evidence_id == ev.id)
        .order_by(EvidenceLifecycleEvent.created_at)
    )
    events = events_res.scalars().all()

    resp = format_evidence_dict(ev)
    resp["lifecycle_events"] = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "previous_status": e.previous_status,
            "new_status": e.new_status,
            "actor_id": e.actor_id,
            "actor_name": e.actor_name,
            "reason": e.reason,
            "details": e.details or {},
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
    return resp


@router.get("/{evidence_id}/download")
async def download_evidence_file(
    job_id: str,
    evidence_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Download the durable stored evidence file."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(PersistentEvidence).where(
            PersistentEvidence.id == evidence_id,
            PersistentEvidence.job_id == job_id,
            PersistentEvidence.organization_id == org.id,
        )
    )
    ev = result.scalars().first()
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence artifact not found.",
        )

    file_path = storage_service.resolve_storage_path(ev.storage_path)
    return FileResponse(
        path=str(file_path),
        filename=ev.file_name,
        media_type=ev.mime_type,
    )


@router.post("/{evidence_id}/review", response_model=dict)
async def review_evidence(
    job_id: str,
    evidence_id: str,
    payload: EvidenceReviewRequest,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Review and transition evidence acceptance status (ACCEPTED / REJECTED / REQUIRES_REVIEW)."""
    job = await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(PersistentEvidence).where(
            PersistentEvidence.id == evidence_id,
            PersistentEvidence.job_id == job_id,
            PersistentEvidence.organization_id == org.id,
        )
    )
    ev = result.scalars().first()
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence artifact not found.",
        )

    valid_statuses = {"ACCEPTED", "REJECTED", "REQUIRES_REVIEW"}
    decision = payload.decision.upper()
    if decision not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid acceptance status '{payload.decision}'. Allowed: {', '.join(valid_statuses)}",
        )

    old_status = ev.acceptance_status
    ev.acceptance_status = decision
    ev.acceptance_reason = payload.reason
    ev.reviewed_by = current_user.id
    ev.reviewed_at = datetime.now(timezone.utc)

    # Append-only lifecycle event
    lifecycle_event = EvidenceLifecycleEvent(
        evidence_id=ev.id,
        event_type=f"ACCEPTANCE_{decision}",
        previous_status=old_status,
        new_status=decision,
        actor_id=current_user.id,
        actor_name=current_user.full_name or current_user.email,
        reason=payload.reason,
        details={"decision": decision},
    )
    db.add(lifecycle_event)

    # Audit event
    audit_action = "EVIDENCE_ACCEPTED" if decision == "ACCEPTED" else (
        "EVIDENCE_REJECTED" if decision == "REJECTED" else "EVIDENCE_REVIEW_REQUESTED"
    )
    audit = AuditEvent(
        organization_id=org.id,
        job_id=job.id,
        action=audit_action,
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        target_type="EVIDENCE",
        target_id=ev.id,
        details={"decision": decision, "reason": payload.reason, "file_name": ev.file_name},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(ev)

    return format_evidence_dict(ev)
