from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_review import ReviewItem, HumanAttestation
from backend.app.models.persistent_assessment import ComplianceFinding
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_current_org, require_role
from backend.app.services.review import (
    ReviewType,
    ReviewStatus,
    ReviewPriority,
    ReviewDecision,
    create_review_item,
    auto_populate_reviews_from_assessment,
    assign_review_item,
    start_review_item,
    submit_review_decision,
    create_human_attestation,
    supersede_human_attestation,
    revoke_human_attestation,
)

router = APIRouter(prefix="/jobs/{job_id}", tags=["Human Review and Attestation Workflow"])


# Pydantic Schemas
class CreateReviewItemRequest(BaseModel):
    review_type: str = Field(..., description="EVIDENCE_REVIEW | DNA_CONFLICT_REVIEW | DOCUMENT_REVIEW | TEXT_REVIEW | GEOMETRY_REVIEW | ENGINEERING_JUDGEMENT | FINDING_REVIEW")
    title: str
    description: str
    priority: Optional[str] = "MEDIUM"
    assessment_run_id: Optional[str] = None
    requirement_id: Optional[str] = None
    assessment_result_id: Optional[str] = None
    finding_id: Optional[str] = None


class AutoPopulateReviewsRequest(BaseModel):
    assessment_run_id: str


class AssignReviewRequest(BaseModel):
    reviewer_id: str


class ReviewDecisionRequest(BaseModel):
    decision: str  # APPROVE | REJECT | RETURN
    decision_notes: Optional[str] = None


class CreateAttestationRequest(BaseModel):
    assessment_run_id: str
    attestation_type: Optional[str] = "STANDARDS_CONFORMANCE"
    attestation_statement: str
    decision: str  # CONFORMANT | NON_CONFORMANT | CONDITIONAL_CONFORMANCE | WAIVER_GRANTED
    decision_rationale: str
    review_id: Optional[str] = None
    conditions_or_stipulations: Optional[str] = None
    admin_override: Optional[bool] = False


class SupersedeAttestationRequest(BaseModel):
    attestation_statement: str
    decision: str
    decision_rationale: str
    conditions_or_stipulations: Optional[str] = None


class RevokeAttestationRequest(BaseModel):
    revocation_reason: str


class FindingReviewRequest(BaseModel):
    status: str  # RESOLVED | WAIVED | UNDER_REVIEW
    review_notes: str


# Helper formatters
def format_review_dict(item: ReviewItem) -> dict:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "job_id": item.job_id,
        "assessment_run_id": item.assessment_run_id,
        "requirement_id": item.requirement_id,
        "assessment_result_id": item.assessment_result_id,
        "finding_id": item.finding_id,
        "review_type": item.review_type,
        "status": item.status,
        "priority": item.priority,
        "title": item.title,
        "description": item.description,
        "assigned_reviewer_id": item.assigned_reviewer_id,
        "assigned_reviewer_email": item.assigned_reviewer_email,
        "assigned_at": item.assigned_at.isoformat() if item.assigned_at else None,
        "decision": item.decision,
        "decision_notes": item.decision_notes,
        "reviewed_by": item.reviewed_by,
        "reviewed_by_email": item.reviewed_by_email,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "review_snapshot": item.review_snapshot or {},
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def format_attestation_dict(att: HumanAttestation) -> dict:
    return {
        "id": att.id,
        "organization_id": att.organization_id,
        "job_id": att.job_id,
        "assessment_run_id": att.assessment_run_id,
        "review_id": att.review_id,
        "attestor_id": att.attestor_id,
        "attestor_email": att.attestor_email,
        "attestor_role": att.attestor_role,
        "attestation_type": att.attestation_type,
        "attestation_statement": att.attestation_statement,
        "scope": att.scope or {},
        "decision": att.decision,
        "decision_rationale": att.decision_rationale,
        "conditions_or_stipulations": att.conditions_or_stipulations,
        "attested_at": att.attested_at.isoformat() if att.attested_at else None,
        "status": att.status,
        "supersedes_attestation_id": att.supersedes_attestation_id,
        "revoked_at": att.revoked_at.isoformat() if att.revoked_at else None,
        "revoked_by": att.revoked_by,
        "revocation_reason": att.revocation_reason,
        "created_at": att.created_at.isoformat() if att.created_at else None,
        "updated_at": att.updated_at.isoformat() if att.updated_at else None,
    }


async def _verify_job(job_id: str, org_id: str, db: AsyncSession) -> ComplianceJob:
    res = await db.execute(
        select(ComplianceJob).where(
            ComplianceJob.id == job_id,
            ComplianceJob.organization_id == org_id,
        )
    )
    job = res.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job '{job_id}' not found.",
        )
    return job


# ----------------------------------------------------
# Review Queue & Items
# ----------------------------------------------------
@router.get("/reviews", response_model=dict)
async def list_review_items(
    job_id: str,
    review_status: Optional[str] = Query(None, alias="status"),
    review_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "AUDITOR", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List review items for a compliance job with optional filtering."""
    job = await _verify_job(job_id, org.id, db)

    query = select(ReviewItem).where(
        ReviewItem.job_id == job.id,
        ReviewItem.organization_id == org.id,
    )

    if review_status:
        query = query.where(ReviewItem.status == review_status.upper())
    if review_type:
        query = query.where(ReviewItem.review_type == review_type.upper())
    if priority:
        query = query.where(ReviewItem.priority == priority.upper())

    query = query.order_by(desc(ReviewItem.created_at))
    res = await db.execute(query)
    items = res.scalars().all()

    return {
        "job_id": job.id,
        "count": len(items),
        "items": [format_review_dict(item) for item in items],
    }


@router.post("/reviews", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_new_review_item(
    job_id: str,
    payload: CreateReviewItemRequest,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Manually create a new review item linked to an assessment result, requirement, or finding."""
    job = await _verify_job(job_id, org.id, db)

    item = await create_review_item(
        db=db,
        org_id=org.id,
        job_id=job.id,
        review_type=payload.review_type.upper(),
        title=payload.title,
        description=payload.description,
        priority=payload.priority.upper() if payload.priority else "MEDIUM",
        assessment_run_id=payload.assessment_run_id,
        requirement_id=payload.requirement_id,
        assessment_result_id=payload.assessment_result_id,
        finding_id=payload.finding_id,
        current_user=current_user,
    )
    return format_review_dict(item)


@router.post("/reviews/auto-populate", response_model=dict, status_code=status.HTTP_201_CREATED)
async def auto_populate_review_queue(
    job_id: str,
    payload: AutoPopulateReviewsRequest,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Auto-populate the review queue from assessment results requiring human judgement, conflicts, or gaps."""
    job = await _verify_job(job_id, org.id, db)

    items = await auto_populate_reviews_from_assessment(
        db=db,
        org_id=org.id,
        job_id=job.id,
        assessment_run_id=payload.assessment_run_id,
        current_user=current_user,
    )
    return {
        "job_id": job.id,
        "assessment_run_id": payload.assessment_run_id,
        "created_count": len(items),
        "items": [format_review_dict(i) for i in items],
    }


@router.get("/reviews/{review_id}", response_model=dict)
async def get_review_item(
    job_id: str,
    review_id: str,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "AUDITOR", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a specific review item including its captured immutable snapshot."""
    job = await _verify_job(job_id, org.id, db)

    res = await db.execute(
        select(ReviewItem).where(
            ReviewItem.id == review_id,
            ReviewItem.job_id == job.id,
            ReviewItem.organization_id == org.id,
        )
    )
    item = res.scalars().first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item '{review_id}' not found.",
        )

    return format_review_dict(item)


@router.post("/reviews/{review_id}/assign", response_model=dict)
async def assign_reviewer(
    job_id: str,
    review_id: str,
    payload: AssignReviewRequest,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Assign an authorized reviewer to a review item."""
    job = await _verify_job(job_id, org.id, db)

    # Fetch reviewer user
    u_res = await db.execute(
        select(User).where(
            User.id == payload.reviewer_id,
            User.organization_id == org.id,
        )
    )
    reviewer = u_res.scalars().first()
    if not reviewer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reviewer user '{payload.reviewer_id}' not found in organization.",
        )

    res = await db.execute(
        select(ReviewItem).where(
            ReviewItem.id == review_id,
            ReviewItem.job_id == job.id,
            ReviewItem.organization_id == org.id,
        )
    )
    item = res.scalars().first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item '{review_id}' not found.",
        )

    updated = await assign_review_item(db, item, reviewer, current_user)
    return format_review_dict(updated)


@router.post("/reviews/{review_id}/start", response_model=dict)
async def start_review(
    job_id: str,
    review_id: str,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Transition a review item to IN_REVIEW status."""
    job = await _verify_job(job_id, org.id, db)

    res = await db.execute(
        select(ReviewItem).where(
            ReviewItem.id == review_id,
            ReviewItem.job_id == job.id,
            ReviewItem.organization_id == org.id,
        )
    )
    item = res.scalars().first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item '{review_id}' not found.",
        )

    updated = await start_review_item(db, item, current_user)
    return format_review_dict(updated)


@router.post("/reviews/{review_id}/decision", response_model=dict)
async def record_review_decision(
    job_id: str,
    review_id: str,
    payload: ReviewDecisionRequest,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Record an authoritative human review decision (APPROVE, REJECT, RETURN)."""
    job = await _verify_job(job_id, org.id, db)

    res = await db.execute(
        select(ReviewItem).where(
            ReviewItem.id == review_id,
            ReviewItem.job_id == job.id,
            ReviewItem.organization_id == org.id,
        )
    )
    item = res.scalars().first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item '{review_id}' not found.",
        )

    updated = await submit_review_decision(
        db=db,
        review_item=item,
        decision=payload.decision,
        decision_notes=payload.decision_notes,
        current_user=current_user,
    )
    return format_review_dict(updated)


# ----------------------------------------------------
# Findings Review
# ----------------------------------------------------
@router.post("/findings/{finding_id}/review", response_model=dict)
async def review_compliance_finding(
    job_id: str,
    finding_id: str,
    payload: FindingReviewRequest,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly review, resolve, or waive a compliance finding with statutory justification."""
    job = await _verify_job(job_id, org.id, db)

    res = await db.execute(
        select(ComplianceFinding).where(
            ComplianceFinding.id == finding_id,
            ComplianceFinding.job_id == job.id,
            ComplianceFinding.organization_id == org.id,
        )
    )
    finding = res.scalars().first()
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding '{finding_id}' not found.",
        )

    target_status = payload.status.upper()
    if target_status not in ["RESOLVED", "WAIVED", "UNDER_REVIEW"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid finding status '{payload.status}'. Must be RESOLVED, WAIVED, or UNDER_REVIEW.",
        )

    if target_status in ["RESOLVED", "WAIVED"] and not payload.review_notes.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Review notes / engineering justification are strictly mandatory when status is '{target_status}'.",
        )

    finding.status = target_status
    finding.review_notes = payload.review_notes.strip()
    finding.reviewed_by = current_user.id
    finding.reviewed_at = datetime.now(timezone.utc)

    audit_action = "FINDING_RESOLVED" if target_status == "RESOLVED" else (
        "FINDING_WAIVED" if target_status == "WAIVED" else "FINDING_UNDER_REVIEW"
    )

    db.add(
        AuditEvent(
            organization_id=org.id,
            job_id=job.id,
            action=audit_action,
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="COMPLIANCE_FINDING",
            target_id=finding.id,
            details={
                "status": target_status,
                "review_notes": payload.review_notes.strip(),
                "severity": finding.severity,
                "title": finding.title,
            },
        )
    )

    return {
        "id": finding.id,
        "job_id": finding.job_id,
        "severity": finding.severity,
        "title": finding.title,
        "status": finding.status,
        "review_notes": finding.review_notes,
        "reviewed_by": current_user.email,
        "reviewed_at": finding.reviewed_at.isoformat(),
    }


# ----------------------------------------------------
# Human Attestation Management
# ----------------------------------------------------
@router.get("/attestations", response_model=dict)
async def list_human_attestations(
    job_id: str,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "AUDITOR", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all human compliance attestations associated with a compliance job."""
    job = await _verify_job(job_id, org.id, db)

    res = await db.execute(
        select(HumanAttestation)
        .where(
            HumanAttestation.job_id == job.id,
            HumanAttestation.organization_id == org.id,
        )
        .order_by(desc(HumanAttestation.attested_at))
    )
    attestations = res.scalars().all()

    return {
        "job_id": job.id,
        "count": len(attestations),
        "attestations": [format_attestation_dict(a) for a in attestations],
    }


@router.post("/attestations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submit_human_attestation(
    job_id: str,
    payload: CreateAttestationRequest,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Submit a formal human compliance attestation with strict separation of duties and bounded scope."""
    job = await _verify_job(job_id, org.id, db)

    attestation = await create_human_attestation(
        db=db,
        org_id=org.id,
        job_id=job.id,
        assessment_run_id=payload.assessment_run_id,
        attestation_type=payload.attestation_type or "STANDARDS_CONFORMANCE",
        attestation_statement=payload.attestation_statement,
        decision=payload.decision,
        decision_rationale=payload.decision_rationale,
        current_user=current_user,
        review_id=payload.review_id,
        conditions_or_stipulations=payload.conditions_or_stipulations,
        admin_override=payload.admin_override or False,
    )
    return format_attestation_dict(attestation)


@router.get("/attestations/{attestation_id}", response_model=dict)
async def get_human_attestation(
    job_id: str,
    attestation_id: str,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "AUDITOR", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get full details of a specific human attestation including scope and cryptographic references."""
    job = await _verify_job(job_id, org.id, db)

    res = await db.execute(
        select(HumanAttestation).where(
            HumanAttestation.id == attestation_id,
            HumanAttestation.job_id == job.id,
            HumanAttestation.organization_id == org.id,
        )
    )
    att = res.scalars().first()
    if not att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attestation '{attestation_id}' not found.",
        )

    return format_attestation_dict(att)


@router.post("/attestations/{attestation_id}/supersede", response_model=dict)
async def supersede_attestation(
    job_id: str,
    attestation_id: str,
    payload: SupersedeAttestationRequest,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Supersede an existing active attestation with an updated one (immutability enforcement)."""
    job = await _verify_job(job_id, org.id, db)

    new_att = await supersede_human_attestation(
        db=db,
        org_id=org.id,
        old_attestation_id=attestation_id,
        new_statement=payload.attestation_statement,
        new_decision=payload.decision,
        new_rationale=payload.decision_rationale,
        current_user=current_user,
        conditions_or_stipulations=payload.conditions_or_stipulations,
    )
    return format_attestation_dict(new_att)


@router.post("/attestations/{attestation_id}/revoke", response_model=dict)
async def revoke_attestation(
    job_id: str,
    attestation_id: str,
    payload: RevokeAttestationRequest,
    current_user: User = Depends(require_role("REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an active attestation with a mandatory revocation reason."""
    job = await _verify_job(job_id, org.id, db)

    revoked_att = await revoke_human_attestation(
        db=db,
        org_id=org.id,
        attestation_id=attestation_id,
        revocation_reason=payload.revocation_reason,
        current_user=current_user,
    )
    return format_attestation_dict(revoked_att)
