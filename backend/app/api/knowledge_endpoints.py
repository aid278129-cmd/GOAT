"""FastAPI Endpoints for Authoritative BIS Knowledge Repository (Phase 6).

Routes:
 GET /api/v1/knowledge/search                     - Hybrid search across standards, clauses, schemes
 GET /api/v1/knowledge/standards                  - List all published Indian Standards
 GET /api/v1/knowledge/standards/{id}             - Retrieve standard details, revisions, and related
 GET /api/v1/knowledge/standards/{id}/clauses     - List clauses for standard
 GET /api/v1/knowledge/schemes                    - Official BIS Conformity Assessment Schemes
 GET /api/v1/knowledge/services                   - BIS Services for industries & consumers
 GET /api/v1/knowledge/laboratories               - Recognized testing laboratories search
 GET /api/v1/knowledge/hallmarking                - Statutory hallmarking purity and HUID rules
 GET /api/v1/knowledge/sources/{id}               - Source provenance inspection
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.models.persistent_knowledge import (
    BISKnowledgeSource,
    BISDocument,
    BISDocumentVersion,
    BISStandard,
    BISStandardRevision,
    BISClause,
    BISScheme,
    BISService,
    BISLaboratory,
    BISHallmarkingReference,
    BISRelatedStandard,
)
from backend.app.models.persistent_audit import AuditEvent
from backend.app.api.deps import get_current_user, get_current_org
from backend.app.services.knowledge.retrieval import BISHybridRetrievalEngine

router = APIRouter(prefix="/knowledge", tags=["PS 26107 Authoritative BIS Knowledge"])


@router.get("/search", response_model=Dict[str, Any])
async def search_knowledge(
    q: str = Query(..., description="Search query string"),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Hybrid lexical and semantic retrieval over published BIS standards and clauses."""
    chunks = await BISHybridRetrievalEngine.hybrid_retrieve(db, q, top_k=top_k)
    standards = await BISHybridRetrievalEngine.search_standards(db, q, limit=3)
    schemes = await BISHybridRetrievalEngine.retrieve_schemes(db, q)

    db.add(
        AuditEvent(
            organization_id=org.id,
            action="KNOWLEDGE_RETRIEVAL",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="KNOWLEDGE_SEARCH",
            details={"query": q, "chunks_found": len(chunks), "standards_found": len(standards)},
        )
    )
    await db.commit()

    return {
        "query": q,
        "chunks": chunks,
        "standards": standards,
        "schemes": schemes[:2],
        "total_results": len(chunks) + len(standards),
    }


@router.get("/standards", response_model=List[Dict[str, Any]])
async def list_standards(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists published Indian Standards with scope and CRO references."""
    stmt = select(BISStandard).where(BISStandard.status == "ACTIVE").order_by(BISStandard.standard_number)
    if category:
        stmt = stmt.where(BISStandard.product_category == category)
    stds = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": s.id,
            "standard_number": s.standard_number,
            "title": s.title,
            "scope_summary": s.scope_summary,
            "product_category": s.product_category,
            "is_mandatory": s.is_mandatory,
            "cro_order_reference": s.cro_order_reference,
            "equivalent_international_standard": s.equivalent_international_standard,
        }
        for s in stds
    ]


@router.get("/standards/{standard_id}", response_model=Dict[str, Any])
async def get_standard_details(
    standard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves standard metadata, published revisions, and normative references."""
    # Find by ID or standard_number
    stmt = select(BISStandard).where((BISStandard.id == standard_id) | (BISStandard.standard_number == standard_id))
    std = (await db.execute(stmt)).scalars().first()
    if not std:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indian Standard not found")

    rev_stmt = (
        select(BISStandardRevision)
        .where(BISStandardRevision.standard_id == std.id)
        .order_by(desc(BISStandardRevision.revision_year))
    )
    revisions = (await db.execute(rev_stmt)).scalars().all()

    rel_stmt = (
        select(BISRelatedStandard, BISStandard)
        .join(BISStandard, BISRelatedStandard.related_standard_id == BISStandard.id)
        .where(BISRelatedStandard.primary_standard_id == std.id)
    )
    rel_rows = (await db.execute(rel_stmt)).all()

    return {
        "id": std.id,
        "standard_number": std.standard_number,
        "title": std.title,
        "scope_summary": std.scope_summary,
        "product_category": std.product_category,
        "is_mandatory": std.is_mandatory,
        "cro_order_reference": std.cro_order_reference,
        "equivalent_international_standard": std.equivalent_international_standard,
        "revisions": [
            {
                "id": r.id,
                "revision_year": r.revision_year,
                "status": r.status,
                "content_hash": r.content_hash,
                "effective_date": r.effective_date.isoformat() if r.effective_date else None,
            }
            for r in revisions
        ],
        "related_standards": [
            {
                "standard_number": r_std.standard_number,
                "title": r_std.title,
                "relationship_type": rel.relationship_type,
                "notes": rel.notes,
            }
            for rel, r_std in rel_rows
        ],
    }


@router.get("/standards/{standard_id}/clauses", response_model=List[Dict[str, Any]])
async def list_standard_clauses(
    standard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all codified clauses under the latest published revision of a standard."""
    std_stmt = select(BISStandard).where((BISStandard.id == standard_id) | (BISStandard.standard_number == standard_id))
    std = (await db.execute(std_stmt)).scalars().first()
    if not std:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indian Standard not found")

    rev_stmt = (
        select(BISStandardRevision)
        .where(BISStandardRevision.standard_id == std.id, BISStandardRevision.status == "PUBLISHED")
        .order_by(desc(BISStandardRevision.revision_year))
        .limit(1)
    )
    rev = (await db.execute(rev_stmt)).scalars().first()
    if not rev:
        return []

    c_stmt = select(BISClause).where(BISClause.standard_revision_id == rev.id).order_by(BISClause.clause_number)
    clauses = (await db.execute(c_stmt)).scalars().all()
    return [
        {
            "id": c.id,
            "clause_number": c.clause_number,
            "clause_title": c.clause_title,
            "clause_text": c.clause_text,
            "section_name": c.section_name,
            "page_number": c.page_number,
            "parameter_key": c.parameter_key,
            "expected_unit": c.expected_unit,
            "threshold_min": c.threshold_min,
            "threshold_max": c.threshold_max,
            "expected_value": c.expected_value,
            "content_hash": c.content_hash,
        }
        for c in clauses
    ]


@router.get("/schemes", response_model=List[Dict[str, Any]])
async def list_schemes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists official BIS conformity assessment schemes (ISI, CRS, Scheme IV)."""
    return await BISHybridRetrievalEngine.retrieve_schemes(db)


@router.get("/services", response_model=List[Dict[str, Any]])
async def list_services(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists official BIS services with step-by-step procedures and documentation requirements."""
    return await BISHybridRetrievalEngine.retrieve_services(db)


@router.get("/laboratories", response_model=List[Dict[str, Any]])
async def search_laboratories(
    standard: Optional[str] = Query(None, description="Standard number filter e.g. IS 16221"),
    city: Optional[str] = Query(None, description="City location filter"),
    state: Optional[str] = Query(None, description="State location filter"),
    q: Optional[str] = Query(None, description="General search term"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Searches recognized testing laboratories across India."""
    return await BISHybridRetrievalEngine.retrieve_laboratories(
        db, standard_number=standard, city=city, state=state, query=q
    )


@router.get("/hallmarking", response_model=Dict[str, Any])
async def get_hallmarking(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves statutory hallmarking standards, purity grades, and HUID consumer verification guidelines."""
    hm = await BISHybridRetrievalEngine.retrieve_hallmarking_guidance(db)
    if not hm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hallmarking reference data not found")
    return hm


@router.get("/sources/{source_id}", response_model=Dict[str, Any])
async def get_source_provenance(
    source_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Inspects provenance, document hash, and publication date of an authorized BIS source."""
    src = await db.get(BISKnowledgeSource, source_id)
    if not src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")

    db.add(
        AuditEvent(
            organization_id=org.id,
            action="SOURCE_INSPECTED",
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            target_type="KNOWLEDGE_SOURCE",
            target_id=src.id,
            details={"source_name": src.source_name, "source_type": src.source_type},
        )
    )
    await db.commit()

    return {
        "id": src.id,
        "source_name": src.source_name,
        "source_type": src.source_type,
        "source_url": src.source_url,
        "publisher": src.publisher,
        "jurisdiction": src.jurisdiction,
        "is_active": src.is_active,
        "publication_date": src.publication_date.isoformat() if src.publication_date else None,
        "last_verified_at": src.last_verified_at.isoformat() if src.last_verified_at else None,
        "metadata": src.metadata_json or {},
    }
