"""FastAPI Endpoints for PS 26107 BIS Intelligent Assistant (Phase 6).

Routes:
 POST /api/v1/assistant/chat                     - Conversational intelligence with citations
 GET  /api/v1/assistant/conversations            - List conversations
 GET  /api/v1/assistant/conversations/{id}       - Retrieve conversation with messages and citations
 POST /api/v1/assistant/recommend-standard       - Recommend standards from product description
 POST /api/v1/assistant/compare-standards        - Compare two Indian standards
 POST /api/v1/assistant/explain-clause           - Plain-language explanation of a clause
 POST /api/v1/assistant/start-workstation-job    - Engineering Workstation handoff (Layer A -> Layer B)
"""

import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_standards import JobStandard, JobRequirement
from backend.app.models.persistent_knowledge import (
    BISStandard,
    BISClause,
    BISStandardRevision,
    KnowledgeCitation,
)
from backend.app.models.persistent_ai import AIConversation, AIMessage
from backend.app.models.persistent_audit import AuditEvent
from backend.app.api.deps import get_current_user, get_current_org
from backend.app.services.ai.assistant import BISAssistantService
from backend.app.services.knowledge.recommender import BISProductStandardRecommender
from backend.app.services.knowledge.retrieval import BISHybridRetrievalEngine

router = APIRouter(prefix="/assistant", tags=["PS 26107 BIS Intelligent Assistant"])


class AssistantChatRequest(BaseModel):
    message: str = Field(..., description="User query or question about Indian standards, schemes, or services")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID to continue dialog")
    language: Optional[str] = Field(None, description="Preferred language: en | hi | ta")


class RecommendStandardRequest(BaseModel):
    product_description: str = Field(..., description="Detailed description of product, intended use, and electrical rating")
    limit: int = Field(4, ge=1, le=10)


class CompareStandardsRequest(BaseModel):
    standard_a: str = Field(..., description="First standard number e.g. IS 16221 (Part 2)")
    standard_b: str = Field(..., description="Second standard number e.g. IS 13252 (Part 1)")


class ExplainClauseRequest(BaseModel):
    standard_number: str = Field(..., description="e.g. IS 16221 (Part 2)")
    clause_number: str = Field(..., description="e.g. 5.3")


class StartWorkstationJobRequest(BaseModel):
    title: str = Field(..., description="Job title")
    product_name: str = Field(..., description="Name of product")
    target_standard_number: str = Field(..., description="Standard selected for evaluation e.g. IS 16221 (Part 2)")
    product_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted product characteristics")


@router.post("/chat", response_model=Dict[str, Any])
@router.post("/query", response_model=Dict[str, Any])
async def assistant_chat(
    req: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Processes natural language questions about Indian Standards and BIS services."""
    res = await BISAssistantService.process_chat_query(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        org_id=org.id,
        message=req.message,
        conversation_id=req.conversation_id,
        language=req.language,
    )

    # Emit audit event
    db.add(
        AuditEvent(
            organization_id=org.id,
            action="AI_QUERY",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="AI_CONVERSATION",
            target_id=res.get("conversation_id"),
            details={
                "intent": res.get("intent"),
                "agent": res.get("agent"),
                "citations_count": len(res.get("citations", [])),
                "language": res.get("language"),
            },
        )
    )
    await db.commit()
    return res


@router.get("/conversations", response_model=List[Dict[str, Any]])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Lists user conversations with the BIS assistant."""
    stmt = (
        select(AIConversation)
        .where(AIConversation.organization_id == org.id, AIConversation.user_id == current_user.id)
        .order_by(desc(AIConversation.updated_at))
    )
    convs = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves conversation history along with validated citations."""
    conv = await db.get(AIConversation, conversation_id)
    if not conv or conv.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    msg_stmt = (
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at)
    )
    messages = (await db.execute(msg_stmt)).scalars().all()

    cite_stmt = (
        select(KnowledgeCitation)
        .where(KnowledgeCitation.conversation_id == conversation_id)
        .order_by(KnowledgeCitation.created_at)
    )
    citations = (await db.execute(cite_stmt)).scalars().all()

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "citations": [
            {
                "id": c.id,
                "label": c.citation_label,
                "claim": c.claim_text,
                "source_type": c.source_type,
                "page": c.page_number,
                "content_hash": c.content_hash,
                "is_validated": c.is_validated,
            }
            for c in citations
        ],
    }


@router.post("/recommend-standard", response_model=Dict[str, Any])
async def recommend_standard(
    req: RecommendStandardRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Recommends applicable Indian Standards based on natural language product specifications."""
    rec = await BISProductStandardRecommender.recommend_standards_for_product(
        db, req.product_description, limit=req.limit
    )

    db.add(
        AuditEvent(
            organization_id=org.id,
            action="STANDARD_RECOMMENDATION",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="RECOMMENDATION",
            details={
                "detected_categories": rec["product_context"]["detected_categories"],
                "candidates_count": len(rec["potentially_relevant_standards"]),
            },
        )
    )
    await db.commit()
    return rec


@router.post("/compare-standards", response_model=Dict[str, Any])
async def compare_standards(
    req: CompareStandardsRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Technical comparative breakdown between two Indian Standards."""
    stds = await BISHybridRetrievalEngine.search_standards(db, f"{req.standard_a} {req.standard_b}", limit=5)
    std_a = next((s for s in stds if req.standard_a.upper() in s["standard_number"].upper()), None)
    std_b = next((s for s in stds if req.standard_b.upper() in s["standard_number"].upper()), None)

    if not std_a or not std_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both standards could not be verified in the authorized BIS repository.",
        )

    comparison_summary = (
        f"Comparison between {std_a['standard_number']} ({std_a['product_category']}) and "
        f"{std_b['standard_number']} ({std_b['product_category']}). "
        f"Both standards apply under separate statutory regulatory quality control orders."
    )

    try:
        from backend.app.services.ai.provider import get_llm_provider, TestConfigurableProvider
        provider = get_llm_provider()
        if not isinstance(provider, TestConfigurableProvider):
            prompt = (
                f"Compare Indian Standard {std_a['standard_number']} ({std_a.get('title')}) "
                f"with {std_b['standard_number']} ({std_b.get('title')}).\n"
                f"Scope A: {std_a.get('scope_summary')}\n"
                f"Scope B: {std_b.get('scope_summary')}\n"
                f"Highlight key differences in scope, testing requirements, safety thresholds, and applicability."
            )
            llm_summary = await provider.generate(
                prompt=prompt,
                system_prompt="You are a BIS regulatory standards analyst. Provide a clear, technical comparison in 3-4 concise paragraphs with bullet points.",
                max_tokens=600,
                temperature=0.1,
            )
            if llm_summary and len(llm_summary.strip()) > 50:
                comparison_summary = llm_summary.strip()
    except Exception:
        pass

    return {
        "standard_a": std_a,
        "standard_b": std_b,
        "comparison_summary": comparison_summary,
        "source": "Bureau of Indian Standards Official Catalogue",
    }


@router.post("/explain-clause", response_model=Dict[str, Any])
async def explain_clause(
    req: ExplainClauseRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Plain-language explanation and verification thresholds of a specific standard clause."""
    # 1. Direct query on authoritative BIS knowledge base
    stmt = (
        select(BISClause, BISStandard)
        .join(BISStandardRevision, BISClause.standard_revision_id == BISStandardRevision.id)
        .join(BISStandard, BISStandardRevision.standard_id == BISStandard.id)
        .where(
            BISClause.clause_number == req.clause_number.strip(),
            or_(
                BISStandard.standard_number == req.standard_number.strip(),
                BISStandard.standard_number.ilike(f"%{req.standard_number.strip()}%"),
            ),
        )
    )
    result = (await db.execute(stmt)).first()

    if result:
        clause, std = result
        std_num = std.standard_number
        clause_num = clause.clause_number
        clause_title = clause.clause_title
        section = clause.section_name
        page = clause.page_number
        original_text = clause.clause_text
        param_key = clause.parameter_key
        exp_unit = clause.expected_unit
        thresh_min = clause.threshold_min
        thresh_max = clause.threshold_max
        expected_val = clause.expected_value
    else:
        # Fallback to hybrid retrieve
        q = f"{req.standard_number} Clause {req.clause_number}"
        chunks = await BISHybridRetrievalEngine.hybrid_retrieve(db, q, top_k=5)
        matching_chunk = None
        for chk in chunks:
            if chk.get("clause_number") == req.clause_number.strip():
                matching_chunk = chk
                break
        if not matching_chunk and chunks:
            matching_chunk = chunks[0]
        if not matching_chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Clause {req.clause_number} under {req.standard_number} could not be verified in authorized sources.",
            )
        c = matching_chunk
        std_num = c["standard_number"]
        clause_num = c["clause_number"]
        clause_title = c["clause_title"]
        section = c.get("section_name", "General Requirements")
        page = c.get("page_number", 1)
        original_text = c.get("text", "")
        param_key = c.get("parameter_key")
        exp_unit = c.get("expected_unit")
        thresh_min = None
        thresh_max = None
        expected_val = None

    threshold_desc = ""
    if thresh_min and thresh_max:
        threshold_desc = f" (Threshold range: {thresh_min} to {thresh_max} {exp_unit or ''})"
    elif thresh_min:
        threshold_desc = f" (Minimum requirement: >= {thresh_min} {exp_unit or ''})"
    elif thresh_max:
        threshold_desc = f" (Maximum permissible limit: <= {thresh_max} {exp_unit or ''})"
    elif expected_val:
        threshold_desc = f" (Required value: {expected_val})"

    plain_summary = (
        f"Under {std_num}, Clause {clause_num} ('{clause_title}') mandates: {original_text}{threshold_desc} "
        f"Compliance must be demonstrated through accredited laboratory testing."
    )
    why_matters = (
        f"This requirement ensures statutory safety, insulation integrity, and operational resilience for {std_num} equipment, "
        f"protecting end-users against electric shock, fire hazards, and premature component degradation."
    )
    testing_proc = (
        f"Type testing according to {std_num} Clause {clause_num} using calibrated laboratory apparatus "
        f"in a BIS-recognized or NABL-accredited test laboratory. Verification is documented in an authoritative test report."
    )
    consequence_failure = (
        f"Non-conformance to Clause {clause_num} results in test report failure, denial or suspension of BIS licence/CRS registration, "
        f"and statutory recall of non-compliant batches under the Bureau of Indian Standards Act, 2016."
    )

    try:
        from backend.app.services.ai.provider import get_llm_provider, TestConfigurableProvider
        provider = get_llm_provider()
        if not isinstance(provider, TestConfigurableProvider):
            prompt = (
                f"Explain Clause {clause_num} ('{clause_title}') of Indian Standard {std_num}.\n"
                f"Statutory text: \"{original_text}\"\n"
                f"Threshold/Parameter: {threshold_desc}\n"
                f"Provide a plain-language summary, why this requirement matters for public safety, the typical lab testing procedure, and consequences of test failure."
            )
            llm_exp = await provider.generate(
                prompt=prompt,
                system_prompt="You are an expert electrical and safety compliance engineer. Explain this BIS standard clause clearly and practically.",
                max_tokens=600,
                temperature=0.1,
            )
            if llm_exp and len(llm_exp.strip()) > 50:
                plain_summary = llm_exp.strip()
    except Exception:
        pass

    return {
        "standard_number": std_num,
        "clause_number": clause_num,
        "clause_title": clause_title,
        "section_name": section,
        "page_number": page,
        "original_text": original_text,
        "parameter_key": param_key,
        "source_type": "AUTHORITATIVE_BIS",
        "citation": f"[{std_num} — Clause {clause_num} — Page {page or 1}]",
        "plain_language_summary": plain_summary,
        "plain_language_explanation": plain_summary,
        "why_it_matters": why_matters,
        "testing_procedure": testing_proc,
        "consequence_of_failure": consequence_failure,
    }


@router.post("/start-workstation-job", response_model=Dict[str, Any])
async def start_workstation_job(
    req: StartWorkstationJobRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Seamlessly hands off product context from Assistant (Layer A) to Engineering Workstation (Layer B)."""
    # 1. Create new ComplianceJob
    job_number = f"JOB-2026-{uuid.uuid4().hex[:6].upper()}"
    job = ComplianceJob(
        organization_id=org.id,
        created_by_user_id=current_user.id,
        job_number=job_number,
        title=req.title,
        product_name=req.product_name,
        target_standard=req.target_standard_number,
        status="PENDING_EVIDENCE",
        metadata_json={
            "source_origin": "PS_26107_AI_ASSISTANT_HANDOFF",
            "product_context": req.product_context or {},
        },
    )
    db.add(job)
    await db.flush()

    # 2. Lookup standard from BIS knowledge base
    std_stmt = select(BISStandard).where(BISStandard.standard_number == req.target_standard_number)
    bis_std = (await db.execute(std_stmt)).scalars().first()

    if bis_std:
        job_std = JobStandard(
            organization_id=org.id,
            job_id=job.id,
            standard_identifier=bis_std.standard_number,
            title=bis_std.title,
            revision_year="CURRENT",
            applicability="MANDATORY" if bis_std.is_mandatory else "VOLUNTARY",
            scope_summary=bis_std.scope_summary,
        )
        db.add(job_std)
        await db.flush()

        # Import authoritative clauses from latest published revision
        rev_stmt = (
            select(BISStandardRevision)
            .where(BISStandardRevision.standard_id == bis_std.id, BISStandardRevision.status == "PUBLISHED")
            .order_by(desc(BISStandardRevision.revision_year))
            .limit(1)
        )
        rev = (await db.execute(rev_stmt)).scalars().first()
        if rev:
            c_stmt = select(BISClause).where(BISClause.standard_revision_id == rev.id).order_by(BISClause.clause_number)
            clauses = (await db.execute(c_stmt)).scalars().all()
            for c in clauses:
                db.add(
                    JobRequirement(
                        standard_id=job_std.id,
                        job_id=job.id,
                        clause_number=c.clause_number,
                        clause_reference=c.clause_number,
                        requirement_id=f"REQ-{c.clause_number}",
                        section=c.section_name,
                        title=c.clause_title,
                        description=c.clause_text,
                        requirement_text=c.clause_text,
                        parameter_key=c.parameter_key,
                        expected_unit=c.expected_unit,
                        comparison_operator=c.comparison_operator or ">=",
                        threshold_min=c.threshold_min,
                        threshold_max=c.threshold_max,
                        expected_value=c.expected_value,
                        verification_method="LABORATORY_TEST",
                    )
                )

    # 3. Emit Audit Event
    db.add(
        AuditEvent(
            organization_id=org.id,
            job_id=job.id,
            action="WORKSTATION_HANDOFF",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="COMPLIANCE_JOB",
            target_id=job.id,
            details={
                "job_number": job.job_number,
                "target_standard": req.target_standard_number,
                "origin": "AI_ASSISTANT",
            },
        )
    )
    await db.commit()

    return {
        "job_id": job.id,
        "job_number": job.job_number,
        "title": job.title,
        "product_name": job.product_name,
        "target_standard": req.target_standard_number,
        "status": job.status,
        "message": "Compliance job initiated in Engineering Workstation with verified standard clauses.",
    }
