from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_assessment import (
    AssessmentRun,
    PersistentAssessmentResult,
    ComplianceFinding,
)
from backend.app.models.persistent_standards import JobRequirement, JobStandard
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_review import ReviewItem
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.user import User


class ReviewType(str, Enum):
    EVIDENCE_REVIEW = "EVIDENCE_REVIEW"
    DNA_CONFLICT_REVIEW = "DNA_CONFLICT_REVIEW"
    DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
    TEXT_REVIEW = "TEXT_REVIEW"
    GEOMETRY_REVIEW = "GEOMETRY_REVIEW"
    ENGINEERING_JUDGEMENT = "ENGINEERING_JUDGEMENT"
    FINDING_REVIEW = "FINDING_REVIEW"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class ReviewPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN = "RETURN"


async def build_review_snapshot(
    db: AsyncSession,
    job_id: str,
    assessment_run_id: Optional[str] = None,
    requirement_id: Optional[str] = None,
    assessment_result_id: Optional[str] = None,
    finding_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Capture an immutable snapshot of all contextual data at review initiation."""
    snapshot: Dict[str, Any] = {
        "job_id": job_id,
        "assessment_run_id": assessment_run_id,
        "requirement_id": requirement_id,
        "assessment_result_id": assessment_result_id,
        "finding_id": finding_id,
        "snapshot_timestamp": datetime.now(timezone.utc).isoformat(),
        "requirement": {},
        "result": {},
        "finding": {},
        "evidence_references": [],
        "dna_parameters": [],
    }

    # Fetch Requirement Details
    if requirement_id:
        req_res = await db.execute(select(JobRequirement).where(JobRequirement.id == requirement_id))
        req = req_res.scalars().first()
        if req:
            snapshot["requirement"] = {
                "clause_reference": req.clause_reference,
                "section": req.section,
                "requirement_text": req.requirement_text,
                "parameter_key": req.parameter_key,
                "expected_value": req.expected_value,
                "threshold_min": req.threshold_min,
                "threshold_max": req.threshold_max,
                "comparison_operator": req.comparison_operator,
                "expected_unit": req.expected_unit,
                "verification_method": req.verification_method,
            }

    # Fetch Assessment Result Details
    if assessment_result_id:
        res_stmt = await db.execute(
            select(PersistentAssessmentResult).where(PersistentAssessmentResult.id == assessment_result_id)
        )
        res = res_stmt.scalars().first()
        if res:
            td = res.trace_details or {}
            snapshot["result"] = {
                "clause_number": res.clause_number,
                "parameter_key": res.parameter_key,
                "assessment_state": res.assessment_state,
                "applicability_state": res.applicability_state,
                "observed_value": res.observed_value,
                "observed_unit": res.observed_unit,
                "normalized_value": res.normalized_value,
                "normalized_unit": res.normalized_unit,
                "expected_value": res.expected_value,
                "expected_unit": res.expected_unit,
                "comparison_operator": res.comparison_operator,
                "evaluation_expression": res.evaluation_expression,
                "explanation": res.explanation,
                "engine_version": res.engine_version,
                "evaluated_at": res.evaluated_at.isoformat() if res.evaluated_at else None,
            }
            if isinstance(td, dict) and "evidence_artifact" in td:
                ev_art = td["evidence_artifact"]
                snapshot["evidence_references"].append({
                    "evidence_id": ev_art.get("id") or res.source_evidence_id,
                    "file_name": ev_art.get("file_name"),
                    "sha256": ev_art.get("sha256"),
                    "acceptance_status": "ACCEPTED",
                })

    # Fetch Finding Details
    if finding_id:
        f_res = await db.execute(select(ComplianceFinding).where(ComplianceFinding.id == finding_id))
        f = f_res.scalars().first()
        if f:
            snapshot["finding"] = {
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "observed_value": f.observed_value,
                "expected_value": f.expected_value,
                "status": f.status,
            }

    # If no specific evidence captured yet, query accepted evidence from job
    if not snapshot["evidence_references"]:
        ev_query = await db.execute(
            select(PersistentEvidence).where(
                PersistentEvidence.job_id == job_id,
                PersistentEvidence.acceptance_status == "ACCEPTED",
            )
        )
        for ev in ev_query.scalars().all():
            snapshot["evidence_references"].append({
                "evidence_id": ev.id,
                "file_name": ev.file_name,
                "file_type": ev.file_type,
                "sha256": ev.sha256_hash,
                "acceptance_status": ev.acceptance_status,
                "uploaded_at": ev.created_at.isoformat() if ev.created_at else None,
            })

    # Capture DNA parameters for job
    dna_query = await db.execute(select(PersistentDNA).where(PersistentDNA.job_id == job_id))
    for dna in dna_query.scalars().all():
        snapshot["dna_parameters"].append({
            "id": dna.id,
            "parameter_key": dna.parameter,
            "category": dna.category,
            "value": dna.value,
            "unit": dna.unit,
            "confidence": dna.confidence,
            "status": dna.status,
            "source_evidence_id": dna.source_evidence_id,
        })

    return snapshot


async def create_review_item(
    db: AsyncSession,
    org_id: str,
    job_id: str,
    review_type: str,
    title: str,
    description: str,
    priority: str = "MEDIUM",
    assessment_run_id: Optional[str] = None,
    requirement_id: Optional[str] = None,
    assessment_result_id: Optional[str] = None,
    finding_id: Optional[str] = None,
    current_user: Optional[User] = None,
) -> ReviewItem:
    """Create a persistent review item with captured immutable snapshot and audit logging."""
    snapshot = await build_review_snapshot(
        db=db,
        job_id=job_id,
        assessment_run_id=assessment_run_id,
        requirement_id=requirement_id,
        assessment_result_id=assessment_result_id,
        finding_id=finding_id,
    )

    review_item = ReviewItem(
        organization_id=org_id,
        job_id=job_id,
        assessment_run_id=assessment_run_id,
        requirement_id=requirement_id,
        assessment_result_id=assessment_result_id,
        finding_id=finding_id,
        review_type=review_type,
        status=ReviewStatus.PENDING.value,
        priority=priority,
        title=title,
        description=description,
        review_snapshot=snapshot,
    )
    db.add(review_item)
    await db.flush()

    # Emit audit event
    db.add(
        AuditEvent(
            organization_id=org_id,
            job_id=job_id,
            action="REVIEW_CREATED",
            actor_id=current_user.id if current_user else None,
            actor_email=current_user.email if current_user else None,
            actor_role=current_user.role if current_user else None,
            target_type="REVIEW_ITEM",
            target_id=review_item.id,
            details={
                "review_type": review_type,
                "priority": priority,
                "title": title,
                "assessment_run_id": assessment_run_id,
                "requirement_id": requirement_id,
                "assessment_result_id": assessment_result_id,
            },
        )
    )

    return review_item


async def auto_populate_reviews_from_assessment(
    db: AsyncSession,
    org_id: str,
    job_id: str,
    assessment_run_id: str,
    current_user: User,
) -> List[ReviewItem]:
    """Auto-populate review queue from assessment items requiring human review or resolution."""
    run_res = await db.execute(
        select(AssessmentRun).where(
            AssessmentRun.id == assessment_run_id,
            AssessmentRun.organization_id == org_id,
        )
    )
    run = run_res.scalars().first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment run '{assessment_run_id}' not found.",
        )

    # Fetch existing review items for this assessment run to avoid duplicates
    existing_items_res = await db.execute(
        select(ReviewItem).where(
            ReviewItem.assessment_run_id == assessment_run_id,
            ReviewItem.organization_id == org_id,
        )
    )
    existing_by_result_id = {
        item.assessment_result_id: item
        for item in existing_items_res.scalars().all()
        if item.assessment_result_id
    }

    # Fetch assessment results
    results_stmt = await db.execute(
        select(PersistentAssessmentResult).where(
            PersistentAssessmentResult.assessment_run_id == assessment_run_id
        )
    )
    results = results_stmt.scalars().all()

    created_reviews: List[ReviewItem] = []

    for res in results:
        if res.id in existing_by_result_id:
            continue

        if res.assessment_state == "HUMAN_REVIEW_REQUIRED":
            rev_type = ReviewType.ENGINEERING_JUDGEMENT.value
            title = f"Engineering Judgement Required: Clause {res.clause_number}"
            desc = res.explanation or f"Human engineering review required for clause {res.clause_number}."
            item = await create_review_item(
                db=db,
                org_id=org_id,
                job_id=job_id,
                review_type=rev_type,
                title=title,
                description=desc,
                priority=ReviewPriority.HIGH.value,
                assessment_run_id=assessment_run_id,
                requirement_id=res.requirement_id,
                assessment_result_id=res.id,
                current_user=current_user,
            )
            created_reviews.append(item)

        elif res.assessment_state == "CONFLICT":
            rev_type = ReviewType.DNA_CONFLICT_REVIEW.value
            title = f"DNA Parameter Conflict: Clause {res.clause_number} ({res.parameter_key})"
            desc = res.explanation or f"Conflicting values detected for {res.parameter_key} in Product DNA."
            item = await create_review_item(
                db=db,
                org_id=org_id,
                job_id=job_id,
                review_type=rev_type,
                title=title,
                description=desc,
                priority=ReviewPriority.CRITICAL.value,
                assessment_run_id=assessment_run_id,
                requirement_id=res.requirement_id,
                assessment_result_id=res.id,
                current_user=current_user,
            )
            created_reviews.append(item)

        elif res.assessment_state == "ENGINEERING_GAP":
            rev_type = ReviewType.FINDING_REVIEW.value
            title = f"Engineering Non-Conformance Review: Clause {res.clause_number}"
            desc = res.explanation or f"Statutory requirement unmet for clause {res.clause_number}."
            item = await create_review_item(
                db=db,
                org_id=org_id,
                job_id=job_id,
                review_type=rev_type,
                title=title,
                description=desc,
                priority=ReviewPriority.HIGH.value,
                assessment_run_id=assessment_run_id,
                requirement_id=res.requirement_id,
                assessment_result_id=res.id,
                current_user=current_user,
            )
            created_reviews.append(item)

        elif res.assessment_state == "DATA_REQUIRED":
            rev_type = ReviewType.EVIDENCE_REVIEW.value
            title = f"Evidence Verification Required: Clause {res.clause_number}"
            desc = res.explanation or f"Missing evidence data for parameter {res.parameter_key} in clause {res.clause_number}."
            item = await create_review_item(
                db=db,
                org_id=org_id,
                job_id=job_id,
                review_type=rev_type,
                title=title,
                description=desc,
                priority=ReviewPriority.MEDIUM.value,
                assessment_run_id=assessment_run_id,
                requirement_id=res.requirement_id,
                assessment_result_id=res.id,
                current_user=current_user,
            )
            created_reviews.append(item)

    return created_reviews


async def assign_review_item(
    db: AsyncSession,
    review_item: ReviewItem,
    reviewer: User,
    current_user: User,
) -> ReviewItem:
    """Assign a review item to an authorized reviewer."""
    if reviewer.role not in ["REVIEWER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{reviewer.email}' with role '{reviewer.role}' cannot be assigned reviews. Must be REVIEWER or ADMIN.",
        )

    review_item.assigned_reviewer_id = reviewer.id
    review_item.assigned_reviewer_email = reviewer.email
    review_item.assigned_at = datetime.now(timezone.utc)
    review_item.status = ReviewStatus.ASSIGNED.value

    db.add(
        AuditEvent(
            organization_id=review_item.organization_id,
            job_id=review_item.job_id,
            action="REVIEW_ASSIGNED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="REVIEW_ITEM",
            target_id=review_item.id,
            details={
                "assigned_reviewer_id": reviewer.id,
                "assigned_reviewer_email": reviewer.email,
                "assigned_by": current_user.email,
            },
        )
    )
    return review_item


async def start_review_item(
    db: AsyncSession,
    review_item: ReviewItem,
    current_user: User,
) -> ReviewItem:
    """Mark a review item as actively under review."""
    review_item.status = ReviewStatus.IN_REVIEW.value
    review_item.reviewed_by = current_user.id
    review_item.reviewed_by_email = current_user.email

    db.add(
        AuditEvent(
            organization_id=review_item.organization_id,
            job_id=review_item.job_id,
            action="REVIEW_STARTED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="REVIEW_ITEM",
            target_id=review_item.id,
            details={"started_by": current_user.email},
        )
    )
    return review_item


async def submit_review_decision(
    db: AsyncSession,
    review_item: ReviewItem,
    decision: str,
    decision_notes: Optional[str],
    current_user: User,
) -> ReviewItem:
    """Submit a formal human review decision (APPROVE, REJECT, RETURN)."""
    # Strict RBAC check: only REVIEWER or ADMIN can decide
    if current_user.role not in ["REVIEWER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to submit review decisions. Must be REVIEWER or ADMIN.",
        )

    decision_upper = decision.upper()
    if decision_upper not in [ReviewDecision.APPROVE.value, ReviewDecision.REJECT.value, ReviewDecision.RETURN.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review decision '{decision}'. Must be APPROVE, REJECT, or RETURN.",
        )

    # Mandatory notes for REJECT or RETURN
    if decision_upper in [ReviewDecision.REJECT.value, ReviewDecision.RETURN.value]:
        if not decision_notes or not decision_notes.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review decision '{decision_upper}' strictly requires substantive decision notes / engineering rationale.",
            )

    review_item.decision = decision_upper
    review_item.decision_notes = decision_notes.strip() if decision_notes else ""
    review_item.reviewed_by = current_user.id
    review_item.reviewed_by_email = current_user.email
    review_item.completed_at = datetime.now(timezone.utc)

    if decision_upper == ReviewDecision.APPROVE.value:
        review_item.status = ReviewStatus.APPROVED.value
        audit_action = "REVIEW_APPROVED"
    elif decision_upper == ReviewDecision.REJECT.value:
        review_item.status = ReviewStatus.REJECTED.value
        audit_action = "REVIEW_REJECTED"
    else:
        review_item.status = ReviewStatus.RETURNED.value
        audit_action = "REVIEW_RETURNED"

    # If linked to a finding and approved, mark finding resolved
    if review_item.finding_id and decision_upper == ReviewDecision.APPROVE.value:
        f_res = await db.execute(
            select(ComplianceFinding).where(ComplianceFinding.id == review_item.finding_id)
        )
        finding = f_res.scalars().first()
        if finding:
            finding.status = "RESOLVED"
            finding.reviewed_by = current_user.id
            finding.reviewed_at = datetime.now(timezone.utc)
            finding.review_notes = f"Resolved via human review {review_item.id}: {decision_notes}"
            db.add(
                AuditEvent(
                    organization_id=review_item.organization_id,
                    job_id=review_item.job_id,
                    action="FINDING_RESOLVED",
                    actor_id=current_user.id,
                    actor_email=current_user.email,
                    actor_role=current_user.role,
                    target_type="COMPLIANCE_FINDING",
                    target_id=finding.id,
                    details={"review_id": review_item.id, "decision_notes": decision_notes},
                )
            )

    db.add(
        AuditEvent(
            organization_id=review_item.organization_id,
            job_id=review_item.job_id,
            action=audit_action,
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="REVIEW_ITEM",
            target_id=review_item.id,
            details={
                "decision": decision_upper,
                "decision_notes": decision_notes,
                "reviewed_by": current_user.email,
                "status": review_item.status,
            },
        )
    )

    return review_item
