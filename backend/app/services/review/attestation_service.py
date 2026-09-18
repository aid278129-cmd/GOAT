from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_assessment import AssessmentRun, PersistentAssessmentResult
from backend.app.models.persistent_standards import JobStandard
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_review import ReviewItem, HumanAttestation
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.user import User


class AttestationType(str, Enum):
    STANDARDS_CONFORMANCE = "STANDARDS_CONFORMANCE"
    CLAUSE_COMPLIANCE = "CLAUSE_COMPLIANCE"
    JOB_COMPLIANCE = "JOB_COMPLIANCE"
    EVIDENCE_SUFFICIENCY = "EVIDENCE_SUFFICIENCY"
    DEVIATION_APPROVAL = "DEVIATION_APPROVAL"


class AttestationDecision(str, Enum):
    CONFORMANT = "CONFORMANT"
    NON_CONFORMANT = "NON_CONFORMANT"
    CONDITIONAL_CONFORMANCE = "CONDITIONAL_CONFORMANCE"
    WAIVER_GRANTED = "WAIVER_GRANTED"


class AttestationStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


async def build_attestation_scope(
    db: AsyncSession,
    job_id: str,
    assessment_run_id: str,
) -> Dict[str, Any]:
    """Construct bounded cryptographic and regulatory scope for the attestation."""
    # Fetch assessment run
    run_res = await db.execute(select(AssessmentRun).where(AssessmentRun.id == assessment_run_id))
    run = run_res.scalars().first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment run '{assessment_run_id}' not found.",
        )

    # Fetch standard
    std_ident = ""
    std_rev = run.standard_revision or ""
    if run.standard_id:
        std_res = await db.execute(select(JobStandard).where(JobStandard.id == run.standard_id))
        std = std_res.scalars().first()
        if std:
            std_ident = std.standard_identifier
            std_rev = std.revision_year or std_rev

    # Fetch covered clauses
    clauses_stmt = await db.execute(
        select(PersistentAssessmentResult.clause_number)
        .where(PersistentAssessmentResult.assessment_run_id == assessment_run_id)
        .distinct()
    )
    clauses_covered = sorted([c for (c,) in clauses_stmt.fetchall() if c])

    # Fetch cryptographic hashes of accepted evidence
    ev_stmt = await db.execute(
        select(PersistentEvidence.id, PersistentEvidence.file_name, PersistentEvidence.sha256_hash)
        .where(
            PersistentEvidence.job_id == job_id,
            PersistentEvidence.acceptance_status == "ACCEPTED",
        )
    )
    evidence_items = [
        {"evidence_id": eid, "file_name": fn, "sha256": hsh}
        for (eid, fn, hsh) in ev_stmt.fetchall()
        if hsh
    ]
    evidence_hashes = sorted(list({item["sha256"] for item in evidence_items}))

    return {
        "job_id": job_id,
        "assessment_run_id": assessment_run_id,
        "standard_id": run.standard_id,
        "standard_identifier": std_ident,
        "standard_revision": std_rev,
        "clauses_covered": clauses_covered,
        "clause_count": len(clauses_covered),
        "evidence_hashes": evidence_hashes,
        "evidence_items": evidence_items,
        "scope_generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def create_human_attestation(
    db: AsyncSession,
    org_id: str,
    job_id: str,
    assessment_run_id: str,
    attestation_type: str,
    attestation_statement: str,
    decision: str,
    decision_rationale: str,
    current_user: User,
    review_id: Optional[str] = None,
    conditions_or_stipulations: Optional[str] = None,
    status_state: str = "ACTIVE",
    admin_override: bool = False,
) -> HumanAttestation:
    """Create authoritative human attestation with RBAC, separation of duties, and audit logging."""
    # 1. RBAC check: only REVIEWER or ADMIN
    if current_user.role not in ["REVIEWER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to attest compliance. Must be REVIEWER or ADMIN.",
        )

    # 2. Fetch assessment run
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

    # 3. Strict Separation of Duties Check:
    # An engineer cannot attest their own assessment run
    if run.created_by and run.created_by == current_user.id:
        if not (current_user.role == "ADMIN" and admin_override):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Separation of duties violation: The engineer who created or executed the compliance assessment cannot attest their own assessment run.",
            )

    # 4. Validate statement & decision
    if not attestation_statement or not attestation_statement.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attestation statement cannot be empty. A formal regulatory declaration is required.",
        )

    if not decision_rationale or not decision_rationale.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision rationale cannot be empty. Professional engineering rationale is required.",
        )

    decision_upper = decision.upper()
    valid_decisions = [
        AttestationDecision.CONFORMANT.value,
        AttestationDecision.NON_CONFORMANT.value,
        AttestationDecision.CONDITIONAL_CONFORMANCE.value,
        AttestationDecision.WAIVER_GRANTED.value,
    ]
    if decision_upper not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid attestation decision '{decision}'. Must be one of: {valid_decisions}",
        )

    # 5. Build Bounded Scope
    scope = await build_attestation_scope(db, job_id, assessment_run_id)

    # 6. Instantiate Attestation
    attestation = HumanAttestation(
        organization_id=org_id,
        job_id=job_id,
        assessment_run_id=assessment_run_id,
        review_id=review_id,
        attestor_id=current_user.id,
        attestor_email=current_user.email,
        attestor_role=current_user.role,
        attestation_type=attestation_type,
        attestation_statement=attestation_statement.strip(),
        scope=scope,
        decision=decision_upper,
        decision_rationale=decision_rationale.strip(),
        conditions_or_stipulations=conditions_or_stipulations.strip() if conditions_or_stipulations else None,
        attested_at=datetime.now(timezone.utc),
        status=status_state.upper(),
    )
    db.add(attestation)
    await db.flush()

    # 7. Emit Audit Event
    audit_action = "ATTESTATION_ACTIVATED" if attestation.status == "ACTIVE" else "ATTESTATION_CREATED"
    db.add(
        AuditEvent(
            organization_id=org_id,
            job_id=job_id,
            action=audit_action,
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="HUMAN_ATTESTATION",
            target_id=attestation.id,
            details={
                "attestation_type": attestation_type,
                "decision": decision_upper,
                "assessment_run_id": assessment_run_id,
                "scope_clauses_count": len(scope.get("clauses_covered", [])),
                "scope_evidence_hashes_count": len(scope.get("evidence_hashes", [])),
                "status": attestation.status,
            },
        )
    )

    return attestation


async def supersede_human_attestation(
    db: AsyncSession,
    org_id: str,
    old_attestation_id: str,
    new_statement: str,
    new_decision: str,
    new_rationale: str,
    current_user: User,
    conditions_or_stipulations: Optional[str] = None,
) -> HumanAttestation:
    """Supersede an existing active attestation with an updated one (immutability pattern)."""
    # Strict RBAC
    if current_user.role not in ["REVIEWER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to supersede attestations.",
        )

    old_res = await db.execute(
        select(HumanAttestation).where(
            HumanAttestation.id == old_attestation_id,
            HumanAttestation.organization_id == org_id,
        )
    )
    old_att = old_res.scalars().first()
    if not old_att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attestation '{old_attestation_id}' not found.",
        )

    if old_att.status != AttestationStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot supersede an attestation that is not ACTIVE (current status: {old_att.status}).",
        )

    # Transition old to SUPERSEDED
    old_att.status = AttestationStatus.SUPERSEDED.value

    # Create new attestation
    new_att = await create_human_attestation(
        db=db,
        org_id=org_id,
        job_id=old_att.job_id,
        assessment_run_id=old_att.assessment_run_id,
        attestation_type=old_att.attestation_type,
        attestation_statement=new_statement,
        decision=new_decision,
        decision_rationale=new_rationale,
        current_user=current_user,
        review_id=old_att.review_id,
        conditions_or_stipulations=conditions_or_stipulations,
        status_state=AttestationStatus.ACTIVE.value,
    )
    new_att.supersedes_attestation_id = old_att.id

    # Audit event for superseded
    db.add(
        AuditEvent(
            organization_id=org_id,
            job_id=old_att.job_id,
            action="ATTESTATION_SUPERSEDED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="HUMAN_ATTESTATION",
            target_id=old_att.id,
            details={
                "superseded_by_attestation_id": new_att.id,
                "previous_decision": old_att.decision,
                "new_decision": new_att.decision,
            },
        )
    )

    return new_att


async def revoke_human_attestation(
    db: AsyncSession,
    org_id: str,
    attestation_id: str,
    revocation_reason: str,
    current_user: User,
) -> HumanAttestation:
    """Revoke an active attestation with mandatory revocation reason."""
    if current_user.role not in ["REVIEWER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' is not authorized to revoke attestations.",
        )

    if not revocation_reason or not revocation_reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Revocation reason is strictly mandatory.",
        )

    res = await db.execute(
        select(HumanAttestation).where(
            HumanAttestation.id == attestation_id,
            HumanAttestation.organization_id == org_id,
        )
    )
    att = res.scalars().first()
    if not att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attestation '{attestation_id}' not found.",
        )

    if att.status != AttestationStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revoke an attestation with status '{att.status}'. Must be ACTIVE.",
        )

    att.status = AttestationStatus.REVOKED.value
    att.revoked_at = datetime.now(timezone.utc)
    att.revoked_by = current_user.id
    att.revocation_reason = revocation_reason.strip()

    db.add(
        AuditEvent(
            organization_id=org_id,
            job_id=att.job_id,
            action="ATTESTATION_REVOKED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="HUMAN_ATTESTATION",
            target_id=att.id,
            details={
                "revoked_by": current_user.email,
                "revocation_reason": revocation_reason.strip(),
            },
        )
    )

    return att
