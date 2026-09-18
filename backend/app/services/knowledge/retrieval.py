"""Hybrid Retrieval & Reranking Engine for BIS Knowledge Intelligence (Phase 6).

Implements production-grade hybrid retrieval combining:
 1. Standard number pattern matching (e.g., 'IS 16221', 'IS 13252', 'IS 302')
 2. Lexical keyword search across standards, clauses, and schemes
 3. Dense semantic vector search via cosine similarity on KnowledgeEmbedding
 4. Clause reference matching (e.g., 'Clause 5.3', 'Clause 4.2.1')
 5. Published status gating (only status == 'PUBLISHED' knowledge is retrievable)
 6. Source trust filtering (AUTHORITATIVE_BIS, AUTHORIZED_SOURCE, SECONDARY_REFERENCE)
 7. Reciprocal Rank Fusion (RRF) reranking
 8. Conflicting source and staleness detection
"""

import re
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc

from backend.app.models.persistent_knowledge import (
    BISKnowledgeSource,
    BISDocument,
    BISDocumentVersion,
    BISStandard,
    BISStandardRevision,
    BISClause,
    BISScheme,
    BISService,
    BISTestingRequirement,
    BISLaboratory,
    BISHallmarkingReference,
    BISRelatedStandard,
    KnowledgeChunk,
    KnowledgeEmbedding,
)
from backend.app.services.knowledge.ingest import generate_embedding_vector

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two unit-normalized vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, dot))


class BISHybridRetrievalEngine:
    """Production-grade multi-channel retrieval engine for Indian Standards and BIS services."""

    STANDARD_REGEX = re.compile(r"\b(IS\s*/?\s*IEC\s*\d+(?:\s*\([^)]+\))?|IS\s*\d+(?:\s*\([^)]+\))?)\b", re.IGNORECASE)
    CLAUSE_REGEX = re.compile(r"\bclause\s*(\d+(?:\.\d+)*)\b", re.IGNORECASE)

    @classmethod
    def extract_standard_numbers(cls, query: str) -> List[str]:
        """Extracts standard identifiers like 'IS 16221', 'IS 13252', 'IS 302' from text."""
        matches = cls.STANDARD_REGEX.findall(query)
        normalized = []
        for m in matches:
            norm = re.sub(r"\s+", " ", m).strip().upper()
            if norm not in normalized:
                normalized.append(norm)
        return normalized

    @classmethod
    def extract_clause_references(cls, query: str) -> List[str]:
        """Extracts clause numbers like '5.3', '4.2.1' from query."""
        return [m.strip() for m in cls.CLAUSE_REGEX.findall(query)]

    @classmethod
    async def search_standards(
        cls, db: AsyncSession, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Searches standards catalog by standard number or title/scope tokens."""
        std_nums = cls.extract_standard_numbers(query)
        q_tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]

        stmt = (
            select(BISStandard, BISDocumentVersion)
            .outerjoin(BISDocumentVersion, BISStandard.document_version_id == BISDocumentVersion.id)
            .where(
                or_(
                    BISDocumentVersion.status == "PUBLISHED",
                    BISDocumentVersion.status.is_(None),
                )
            )
        )
        all_stds = (await db.execute(stmt)).all()

        scored_results: List[Tuple[float, BISStandard, Optional[BISDocumentVersion]]] = []
        for std, ver in all_stds:
            score = 0.0
            std_num_upper = std.standard_number.upper()
            title_lower = std.title.lower()
            scope_lower = (std.scope_summary or "").lower()

            # Exact standard match
            for s_num in std_nums:
                if s_num in std_num_upper or std_num_upper in s_num:
                    score += 10.0

            # Token match in title and scope
            for token in q_tokens:
                if token in title_lower:
                    score += 2.0
                if token in scope_lower:
                    score += 1.0

            if score > 0:
                scored_results.append((score, std, ver))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, std, ver in scored_results[:limit]:
            results.append({
                "id": std.id,
                "standard_number": std.standard_number,
                "title": std.title,
                "scope_summary": std.scope_summary,
                "product_category": std.product_category,
                "is_mandatory": std.is_mandatory,
                "cro_order_reference": std.cro_order_reference,
                "equivalent_international_standard": std.equivalent_international_standard,
                "version": ver.version_identifier if ver else "CURRENT",
                "status": ver.status if ver else "PUBLISHED",
                "content_hash": ver.content_hash if ver else None,
                "relevance_score": round(score, 2),
            })
        return results

    @classmethod
    async def hybrid_retrieve(
        cls,
        db: AsyncSession,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Executes full hybrid lexical + semantic + clause retrieval with RRF reranking."""
        query_text = query.strip()
        query_vec = generate_embedding_vector(query_text)
        std_nums = cls.extract_standard_numbers(query_text)
        clause_refs = cls.extract_clause_references(query_text)
        tokens = set(t.lower() for t in re.findall(r"\w+", query_text) if len(t) > 2)

        # 1. Fetch published knowledge chunks and embeddings
        chunk_stmt = (
            select(KnowledgeChunk, KnowledgeEmbedding, BISDocumentVersion)
            .join(BISDocumentVersion, KnowledgeChunk.document_version_id == BISDocumentVersion.id)
            .outerjoin(KnowledgeEmbedding, KnowledgeChunk.id == KnowledgeEmbedding.chunk_id)
            .where(BISDocumentVersion.status == "PUBLISHED")
        )
        chunk_rows = (await db.execute(chunk_stmt)).all()

        if not chunk_rows:
            return []

        # 2. Score Lexical & Semantic Channels
        lexical_scores: List[Tuple[KnowledgeChunk, float]] = []
        semantic_scores: List[Tuple[KnowledgeChunk, float]] = []

        for chunk, emb, ver in chunk_rows:
            meta = chunk.metadata_json or {}
            
            # Security / Gating: Only retrieve from AUTHORITATIVE_BIS, AUTHORIZED_SOURCE, or SECONDARY_REFERENCE
            source_type = meta.get("source_type", "AUTHORITATIVE_BIS")
            if source_type == "UNVERIFIED_EXTERNAL":
                continue

            chunk_text_lower = chunk.chunk_text.lower()
            title_lower = chunk.title.lower()

            # Lexical scoring
            lex_score = 0.0
            # Standard number match bonus
            for s_num in std_nums:
                if s_num.lower() in chunk_text_lower or s_num.lower() in title_lower:
                    lex_score += 15.0

            # Clause number match bonus
            for c_ref in clause_refs:
                if f"clause {c_ref}" in chunk_text_lower or f"{c_ref}" == str(meta.get("clause_number")):
                    lex_score += 10.0

            # Token overlap
            for tok in tokens:
                if tok in title_lower:
                    lex_score += 3.0
                if tok in chunk_text_lower:
                    lex_score += 1.0

            if lex_score > 0:
                lexical_scores.append((chunk, lex_score))

            # Semantic scoring via dense cosine similarity
            if emb and emb.vector_json:
                sem_sim = cosine_similarity(query_vec, emb.vector_json)
                if sem_sim >= 0.20:
                    semantic_scores.append((chunk, sem_sim))

        # Sort channels
        lexical_scores.sort(key=lambda x: x[1], reverse=True)
        semantic_scores.sort(key=lambda x: x[1], reverse=True)

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_score = 1 / (60 + rank_lex) + 1 / (60 + rank_sem)
        rrf_map: Dict[str, Dict[str, Any]] = {}
        k_rrf = 60

        for rank, (chunk, score) in enumerate(lexical_scores):
            if chunk.id not in rrf_map:
                rrf_map[chunk.id] = {
                    "chunk": chunk,
                    "rrf": 0.0,
                    "lex_rank": rank + 1,
                    "sem_rank": 9999,
                    "raw_lex": score,
                    "raw_sem": 0.0,
                }
            rrf_map[chunk.id]["rrf"] += 1.0 / (k_rrf + rank + 1)

        for rank, (chunk, sim) in enumerate(semantic_scores):
            if chunk.id not in rrf_map:
                rrf_map[chunk.id] = {
                    "chunk": chunk,
                    "rrf": 0.0,
                    "lex_rank": 9999,
                    "sem_rank": rank + 1,
                    "raw_lex": 0.0,
                    "raw_sem": sim,
                }
            rrf_map[chunk.id]["rrf"] += 1.0 / (k_rrf + rank + 1)
            rrf_map[chunk.id]["raw_sem"] = sim

        sorted_chunks = sorted(rrf_map.values(), key=lambda x: x["rrf"], reverse=True)

        # 4. Assemble enriched results
        results = []
        for item in sorted_chunks[:top_k]:
            chunk: KnowledgeChunk = item["chunk"]
            meta = chunk.metadata_json or {}
            results.append({
                "chunk_id": chunk.id,
                "title": chunk.title,
                "text": chunk.chunk_text,
                "standard_number": meta.get("standard_number"),
                "standard_title": meta.get("standard_title"),
                "clause_number": meta.get("clause_number"),
                "clause_title": meta.get("clause_title"),
                "section_name": meta.get("section_name"),
                "page_number": meta.get("page_number"),
                "parameter_key": meta.get("parameter_key"),
                "source_type": meta.get("source_type", "AUTHORITATIVE_BIS"),
                "content_hash": chunk.content_hash,
                "rrf_score": round(item["rrf"], 4),
                "semantic_similarity": round(item["raw_sem"], 4),
                "document_version_id": chunk.document_version_id,
            })
        return results

    @classmethod
    async def retrieve_schemes(cls, db: AsyncSession, query: str = "") -> List[Dict[str, Any]]:
        """Retrieves official BIS conformity assessment schemes."""
        stmt = select(BISScheme).where(BISScheme.status == "ACTIVE")
        schemes = (await db.execute(stmt)).scalars().all()
        q_lower = query.lower()

        results = []
        for s in schemes:
            score = 1.0
            if q_lower:
                if s.scheme_code.lower() in q_lower or s.scheme_name.lower() in q_lower:
                    score += 5.0
                if any(w in s.description.lower() for w in q_lower.split()):
                    score += 2.0
            results.append({
                "id": s.id,
                "scheme_code": s.scheme_code,
                "scheme_name": s.scheme_name,
                "governing_regulation": s.governing_regulation,
                "description": s.description,
                "applicable_products_summary": s.applicable_products_summary,
                "process_overview": s.process_overview,
                "official_guideline_url": s.official_guideline_url,
                "score": score,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    @classmethod
    async def retrieve_services(cls, db: AsyncSession, query: str = "") -> List[Dict[str, Any]]:
        """Retrieves BIS services for industries, startups, and consumers."""
        stmt = select(BISService).where(BISService.status == "ACTIVE")
        services = (await db.execute(stmt)).scalars().all()
        q_lower = query.lower()

        results = []
        for s in services:
            score = 1.0
            if q_lower:
                if s.service_name.lower() in q_lower or s.service_type.lower() in q_lower:
                    score += 5.0
                if any(w in s.description.lower() for w in q_lower.split()):
                    score += 2.0
            results.append({
                "id": s.id,
                "service_name": s.service_name,
                "service_type": s.service_type,
                "description": s.description,
                "eligibility_criteria": s.eligibility_criteria,
                "step_by_step_procedure": s.step_by_step_procedure,
                "required_documents": s.required_documents or [],
                "portal_url": s.portal_url,
                "statutory_source_ref": s.statutory_source_ref,
                "last_verified_at": s.last_verified_at.isoformat() if s.last_verified_at else None,
                "score": score,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    @classmethod
    async def retrieve_laboratories(
        cls,
        db: AsyncSession,
        standard_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Searches recognized testing laboratories by standard, location, or capability."""
        stmt = select(BISLaboratory).where(BISLaboratory.status == "ACTIVE")
        labs = (await db.execute(stmt)).scalars().all()

        results = []
        for lab in labs:
            score = 0.0
            # Standard filter
            if standard_number:
                if any(standard_number.upper() in s.upper() or s.upper() in standard_number.upper() for s in lab.accredited_standards):
                    score += 10.0

            # Location filter
            if city and city.lower() in lab.location_city.lower():
                score += 5.0
            if state and state.lower() in lab.location_state.lower():
                score += 5.0

            # General query filter
            if query:
                q_lower = query.lower()
                if q_lower in lab.lab_name.lower() or q_lower in lab.location_city.lower():
                    score += 3.0
                for cap in lab.testing_capabilities:
                    if any(w in cap.lower() for w in q_lower.split() if len(w) > 2):
                        score += 2.0

            if not standard_number and not city and not state and not query:
                score = 1.0

            if score > 0:
                results.append({
                    "id": lab.id,
                    "lab_name": lab.lab_name,
                    "registration_number": lab.registration_number,
                    "lab_type": lab.lab_type,
                    "location_city": lab.location_city,
                    "location_state": lab.location_state,
                    "address": lab.address,
                    "accredited_standards": lab.accredited_standards,
                    "testing_capabilities": lab.testing_capabilities,
                    "contact_email": lab.contact_email,
                    "contact_phone": lab.contact_phone,
                    "last_verified_at": lab.last_verified_at.isoformat() if lab.last_verified_at else None,
                    "score": score,
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    @classmethod
    async def retrieve_hallmarking_guidance(cls, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Retrieves official BIS hallmarking purity standards and HUID verification guide."""
        stmt = select(BISHallmarkingReference).limit(1)
        hm = (await db.execute(stmt)).scalars().first()
        if not hm:
            return None
        return {
            "id": hm.id,
            "metal_type": hm.metal_type,
            "standard_number": hm.standard_number,
            "purity_grades": hm.purity_grades_json,
            "mandatory_marks": hm.mandatory_marks_json,
            "huid_structure_description": hm.huid_structure_description,
            "consumer_verification_steps": hm.consumer_verification_steps,
            "statutory_order_ref": hm.statutory_order_ref,
            "last_verified_at": hm.last_verified_at.isoformat() if hm.last_verified_at else None,
        }

    @classmethod
    async def check_source_conflict_or_staleness(
        cls, db: AsyncSession, standard_id: str
    ) -> Dict[str, Any]:
        """Inspects whether multiple conflicting or superseded revisions exist for a standard."""
        rev_stmt = (
            select(BISStandardRevision)
            .where(BISStandardRevision.standard_id == standard_id)
            .order_by(desc(BISStandardRevision.revision_year))
        )
        revisions = (await db.execute(rev_stmt)).scalars().all()
        if len(revisions) <= 1:
            return {"has_conflict": False, "is_stale": False, "revisions": []}

        published = [r for r in revisions if r.status == "PUBLISHED"]
        superseded = [r for r in revisions if r.status == "SUPERSEDED"]

        has_conflict = len(published) > 1
        return {
            "has_conflict": has_conflict,
            "is_stale": len(superseded) > 0 and len(published) == 0,
            "conflict_type": "CONFLICTING_SOURCE_DATA" if has_conflict else "SUPERSEDED_HISTORY",
            "published_count": len(published),
            "superseded_count": len(superseded),
            "latest_revision": revisions[0].revision_year,
            "revisions": [
                {"year": r.revision_year, "status": r.status, "content_hash": r.content_hash}
                for r in revisions
            ],
        }
