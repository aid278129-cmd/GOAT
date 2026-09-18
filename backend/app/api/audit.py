from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_current_org

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Regulatory Audit Ledger"])


def format_audit_dict(event: AuditEvent) -> dict:
    return {
        "id": event.id,
        "organization_id": event.organization_id,
        "job_id": event.job_id,
        "action": event.action,
        "actor_id": event.actor_id,
        "actor_email": event.actor_email,
        "actor_role": event.actor_role,
        "target_type": event.target_type,
        "target_id": event.target_id,
        "details": event.details or {},
        "ip_address": event.ip_address,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


@router.get("", response_model=List[dict])
async def list_organization_audit_events(
    limit: int = 100,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve organization-wide authoritative audit trail entries."""
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.organization_id == org.id)
        .order_by(desc(AuditEvent.created_at))
        .limit(limit)
    )
    events = result.scalars().all()
    return [format_audit_dict(e) for e in events]


@router.get("/jobs/{job_id}", response_model=List[dict])
async def list_job_audit_events(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve immutable audit events specific to a compliance job."""
    result = await db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.job_id == job_id,
            AuditEvent.organization_id == org.id,
        )
        .order_by(desc(AuditEvent.created_at))
    )
    events = result.scalars().all()
    return [format_audit_dict(e) for e in events]
