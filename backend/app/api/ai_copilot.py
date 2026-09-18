"""FastAPI API endpoints for Zyntrix Phase 4A AI Engineering Copilot.

Enforces:
- Multi-tenant organization isolation and job scoping
- JWT authentication
- Explicit AI_PROVIDER_NOT_CONFIGURED (HTTP 503) when unconfigured
- Human gate confirmation and rejection for action proposals
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_ai import (
    AIConversation,
    AIMessage,
    AIExecution,
    AIActionProposal,
)
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_standards import JobRequirement
from backend.app.models.persistent_review import ReviewItem
from backend.app.api.deps import get_current_user, get_current_org, require_role
from backend.app.services.ai.provider import get_llm_provider, AIProviderNotConfiguredError
from backend.app.services.ai.orchestrator import ZyntrixAIOrchestrator

router = APIRouter(prefix="/ai", tags=["AI Engineering Copilot & LangGraph Orchestrator"])


class AIChatRequest(BaseModel):
    job_id: str
    message: str
    conversation_id: Optional[str] = None


class ProposalDecisionRequest(BaseModel):
    rejection_reason: Optional[str] = None


@router.get("/health", response_model=Dict[str, Any])
async def ai_health_check():
    """Health check for configured AI LLM provider."""
    try:
        provider = get_llm_provider()
        is_healthy = await provider.health_check()
        return {
            "status": "healthy" if is_healthy else "degraded",
            "provider": type(provider).__name__,
            "configured": True,
        }
    except AIProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "AI_PROVIDER_NOT_CONFIGURED", "message": str(exc)},
        )


@router.post("/chat", response_model=Dict[str, Any])
async def ai_chat(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Job-scoped conversational copilot execution."""
    # 1. Verify Job exists and belongs to current tenant
    job_stmt = select(ComplianceJob).where(ComplianceJob.id == req.job_id, ComplianceJob.organization_id == org.id)
    job_res = await db.execute(job_stmt)
    job = job_res.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job '{req.job_id}' not found in organization scope.",
        )

    # 2. Execute Copilot Orchestrator
    try:
        result = await ZyntrixAIOrchestrator.process_user_query(
            db=db,
            org_id=org.id,
            user_id=current_user.id,
            user_email=current_user.email,
            job_id=req.job_id,
            query=req.message,
            conversation_id=req.conversation_id,
        )
        return result
    except AIProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error_code": "AI_PROVIDER_NOT_CONFIGURED", "message": str(exc)},
        )


@router.get("/conversations/{job_id}", response_model=List[Dict[str, Any]])
async def list_conversations(
    job_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for a job within tenant scope."""
    stmt = (
        select(AIConversation)
        .where(AIConversation.job_id == job_id, AIConversation.organization_id == org.id)
        .order_by(desc(AIConversation.created_at))
    )
    res = await db.execute(stmt)
    convs = res.scalars().all()
    return [
        {
            "id": c.id,
            "job_id": c.job_id,
            "title": c.title,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in convs
    ]


@router.get("/conversations/{job_id}/{conversation_id}/messages", response_model=List[Dict[str, Any]])
async def get_conversation_messages(
    job_id: str,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve message history for a conversation within tenant scope."""
    # Verify conversation ownership
    c_stmt = select(AIConversation).where(
        AIConversation.id == conversation_id,
        AIConversation.job_id == job_id,
        AIConversation.organization_id == org.id,
    )
    c_res = await db.execute(c_stmt)
    conv = c_res.scalars().first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    m_stmt = select(AIMessage).where(AIMessage.conversation_id == conversation_id).order_by(AIMessage.created_at)
    m_res = await db.execute(m_stmt)
    messages = m_res.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "structured_payload": m.structured_payload,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


@router.get("/proposals/{job_id}", response_model=List[Dict[str, Any]])
async def list_action_proposals(
    job_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List pending AI action proposals requiring human confirmation."""
    stmt = (
        select(AIActionProposal)
        .where(AIActionProposal.job_id == job_id, AIActionProposal.organization_id == org.id)
        .order_by(desc(AIActionProposal.created_at))
    )
    res = await db.execute(stmt)
    proposals = res.scalars().all()
    return [
        {
            "id": p.id,
            "action_type": p.action_type,
            "target_id": p.target_id,
            "proposal_payload": p.proposal_payload,
            "reason": p.reason,
            "status": p.status,
            "created_by_agent": p.created_by_agent,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
        }
        for p in proposals
    ]


@router.post("/proposals/{proposal_id}/confirm", response_model=Dict[str, Any])
async def confirm_action_proposal(
    proposal_id: str,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Human Gate: Confirm an AI proposal and execute it with strict validation."""
    stmt = select(AIActionProposal).where(
        AIActionProposal.id == proposal_id,
        AIActionProposal.organization_id == org.id,
    )
    res = await db.execute(stmt)
    proposal = res.scalars().first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action proposal not found.")

    if proposal.status != "PROPOSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is already '{proposal.status}' and cannot be confirmed.",
        )

    now = datetime.now(timezone.utc)
    payload = proposal.proposal_payload or {}

    # Target & Evidence Gating Enforcement
    if proposal.action_type == "CREATE_DNA_CANDIDATE":
        source_evidence_id = payload.get("source_evidence_id") or proposal.target_id
        if not source_evidence_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DNA candidate proposal lacks mandatory source evidence reference.",
            )
        ev_res = await db.execute(
            select(PersistentEvidence).where(
                PersistentEvidence.id == source_evidence_id,
                PersistentEvidence.job_id == proposal.job_id,
                PersistentEvidence.organization_id == org.id,
            )
        )
        evidence = ev_res.scalars().first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked source evidence '{source_evidence_id}' does not exist for this job.",
            )
        if evidence.acceptance_status != "ACCEPTED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Evidence gating violation: Source evidence '{evidence.file_name}' has status "
                    f"'{evidence.acceptance_status}'. Only ACCEPTED evidence may contribute parameters to Product DNA."
                ),
            )
        # Authoritative creation of Product DNA record upon confirmed proposal
        dna_param = PersistentDNA(
            organization_id=org.id,
            job_id=proposal.job_id,
            category=payload.get("category", "General"),
            parameter=payload.get("parameter", "unspecified"),
            value=str(payload.get("value", "")),
            unit=payload.get("unit"),
            confidence=1.0,
            status="VERIFIED",
            source_evidence_id=evidence.id,
            source_file_name=evidence.file_name,
            extraction_method="AI_PROPOSAL_CONFIRMED",
            verified_by=current_user.id,
            verification_timestamp=now,
        )
        db.add(dna_param)

    elif proposal.action_type == "CREATE_REVIEW_REQUEST":
        target_ref = str(payload.get("requirement_id") or proposal.target_id or "")
        req_res = await db.execute(
            select(JobRequirement).where(
                (JobRequirement.id == target_ref) | (JobRequirement.requirement_id == target_ref),
                JobRequirement.job_id == proposal.job_id,
            )
        )
        req = req_res.scalars().first()
        req_fk = req.id if req else None

        review_item = ReviewItem(
            organization_id=org.id,
            job_id=proposal.job_id,
            review_type="ENGINEERING_JUDGEMENT",
            title=f"AI-Proposed Review: {target_ref}",
            description=proposal.reason,
            priority="MEDIUM",
            status="PENDING",
            requirement_id=req_fk,
            review_snapshot={"proposed_by": proposal.created_by_agent, "target_id": proposal.target_id},
        )
        db.add(review_item)

    proposal.status = "CONFIRMED"
    proposal.confirmed_by_user_id = current_user.id
    proposal.confirmed_at = now

    # Audit proposal confirmation
    db.add(
        AuditEvent(
            organization_id=org.id,
            job_id=proposal.job_id,
            action="AI_ACTION_PROPOSAL_CONFIRMED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="AI_ACTION_PROPOSAL",
            target_id=proposal.id,
            details={"action_type": proposal.action_type, "target_id": proposal.target_id},
        )
    )
    await db.commit()
    return {
        "status": "success",
        "proposal_id": proposal.id,
        "action_type": proposal.action_type,
        "proposal_status": proposal.status,
        "confirmed_by": current_user.email,
        "confirmed_at": now.isoformat(),
    }


@router.post("/proposals/{proposal_id}/reject", response_model=Dict[str, Any])
async def reject_action_proposal(
    proposal_id: str,
    payload: ProposalDecisionRequest,
    current_user: User = Depends(require_role("ENGINEER", "REVIEWER", "ADMIN")),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Human Gate: Reject an AI proposal."""
    stmt = select(AIActionProposal).where(
        AIActionProposal.id == proposal_id,
        AIActionProposal.organization_id == org.id,
    )
    res = await db.execute(stmt)
    proposal = res.scalars().first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action proposal not found.")

    if proposal.status != "PROPOSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is already '{proposal.status}' and cannot be rejected.",
        )

    now = datetime.now(timezone.utc)
    proposal.status = "REJECTED"
    proposal.rejection_reason = payload.rejection_reason or "Rejected by human reviewer."
    proposal.confirmed_by_user_id = current_user.id
    proposal.confirmed_at = now

    # Audit proposal rejection
    db.add(
        AuditEvent(
            organization_id=org.id,
            job_id=proposal.job_id,
            action="AI_ACTION_PROPOSAL_REJECTED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="AI_ACTION_PROPOSAL",
            target_id=proposal.id,
            details={"action_type": proposal.action_type, "reason": proposal.rejection_reason},
        )
    )
    await db.commit()
    return {
        "status": "rejected",
        "proposal_id": proposal.id,
        "proposal_status": proposal.status,
        "rejected_by": current_user.email,
        "rejection_reason": proposal.rejection_reason,
    }
