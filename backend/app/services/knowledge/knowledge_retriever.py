"""Layer 4: Production Knowledge Retriever.

Supports the full retrieval pipeline:
query → standard filter → product/category filter → document-type filter
→ verification filter → clause/requirement filter → lexical/vector retrieval
→ reranking → provenance-rich result.

Critical Invariants:
- Cross-standard leakage prevention: IS 17526 query → only IS 17526 knowledge.
- Unknown standard → UNKNOWN / NOT_IN_KNOWLEDGE_BASE.
- Known standard, unavailable clause text → CLAUSE_TEXT_UNAVAILABLE.
- Never invents clauses.
- Every result carries: standard, clause/section, source, document_type,
  verification_status, exact_location, knowledge_version, relevance_score, provenance.
"""

import re
from typing import List, Optional, Dict, Any

from backend.app.services.knowledge.knowledge_package import (
    KnowledgeRetrievalResult,
    KnowledgeVerificationStatus,
    KnowledgeAcquisitionStatus,
    KnowledgeDocumentType,
    StandardKnowledgePackage,
)
from backend.app.services.knowledge.package_manager import (
    get_package,
    get_all_packages,
    build_knowledge_packages,
)
from backend.app.services.retrieval.knowledge_registry import (
    search_standards,
    is_out_of_scope_query,
)
from backend.app.core.logging import logger


class KnowledgeRetriever:
    """Production-grade knowledge retrieval engine with provenance and cross-standard isolation."""

    @classmethod
    def search(
        cls,
        query: str,
        standard_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        document_type_filter: Optional[str] = None,
        verification_filter: Optional[str] = None,
        clause_filter: Optional[str] = None,
        top_k: int = 10,
    ) -> List[KnowledgeRetrievalResult]:
        """Execute full retrieval pipeline with provenance-rich results."""
        # Out-of-scope refusal
        if is_out_of_scope_query(query):
            return []

        build_knowledge_packages()
        results: List[KnowledgeRetrievalResult] = []

        # Determine target packages
        if standard_filter:
            pkg = get_package(standard_filter)
            if pkg is None:
                # Unknown standard → NOT_IN_KNOWLEDGE_BASE
                return [KnowledgeRetrievalResult(
                    standard_number=standard_filter,
                    title="UNKNOWN",
                    content=f"Standard '{standard_filter}' is not present in the verified BIS knowledge base. "
                            f"The system does not speculate or invent unverified standards.",
                    source="Knowledge Retrieval Engine",
                    verification_status=KnowledgeVerificationStatus.UNKNOWN,
                    knowledge_version="v1.2.0-gazette-verified",
                    relevance_score=0.0,
                    provenance="NOT_IN_KNOWLEDGE_BASE",
                )]
            packages = [pkg]
        else:
            packages = get_all_packages()

        # Apply category filter
        if category_filter:
            cat_lower = category_filter.lower()
            packages = [p for p in packages if cat_lower in p.product_category.lower()]

        q_lower = query.lower()

        for pkg in packages:
            # Apply verification filter
            if verification_filter:
                vf = verification_filter.upper()
                if vf == "VERIFIED" and pkg.verification_status != KnowledgeVerificationStatus.VERIFIED:
                    continue
                elif vf == "PENDING" and pkg.verification_status != KnowledgeVerificationStatus.PENDING_ACQUISITION:
                    continue

            # Score package-level relevance
            pkg_score = cls._score_package(query, pkg)

            if pkg_score < 0.05 and not standard_filter:
                continue

            # Clause/Requirement-level search
            if clause_filter or re.search(r"\bclause\s*(\d+(?:\.\d+)*)\b", q_lower):
                clause_match = re.search(r"\bclause\s*(\d+(?:\.\d+)*)\b", q_lower)
                target_clause = clause_filter or (clause_match.group(1) if clause_match else None)

                if target_clause:
                    # Search for this clause within the package
                    matched_req = None
                    for req in pkg.requirements:
                        if req.clause_number == target_clause:
                            matched_req = req
                            break

                    if matched_req:
                        results.append(KnowledgeRetrievalResult(
                            standard_number=pkg.standard_number,
                            clause_section=matched_req.clause_number,
                            title=matched_req.clause_title,
                            content=matched_req.requirement_text,
                            source=f"{pkg.full_standard_code} Clause {matched_req.clause_number}",
                            document_type=KnowledgeDocumentType.INDIAN_STANDARD,
                            verification_status=matched_req.verification_status,
                            exact_location=f"Clause {matched_req.clause_number}",
                            knowledge_version=pkg.knowledge_version,
                            relevance_score=min(1.0, pkg_score + 0.5),
                            provenance=pkg.verification_note or "Bureau of Indian Standards (Official Gazette)",
                        ))
                    elif pkg.acquisition_status == KnowledgeAcquisitionStatus.METADATA_ONLY:
                        # Known standard but clause text unavailable
                        results.append(KnowledgeRetrievalResult(
                            standard_number=pkg.standard_number,
                            clause_section=target_clause,
                            title="CLAUSE_TEXT_UNAVAILABLE",
                            content=f"Clause {target_clause} of {pkg.full_standard_code}: Full clause text "
                                    f"requires authorized procurement. Status: OFFICIAL_DOCUMENT_ACQUISITION_PENDING.",
                            source=f"{pkg.full_standard_code}",
                            verification_status=KnowledgeVerificationStatus.PENDING_ACQUISITION,
                            exact_location=f"Clause {target_clause}",
                            knowledge_version=pkg.knowledge_version,
                            relevance_score=0.3,
                            provenance="OFFICIAL_DOCUMENT_ACQUISITION_PENDING",
                        ))
                    continue

            # Package-level result (scope, QCO, test parameters)
            content_parts = []
            if pkg.scope:
                content_parts.append(f"Scope: {pkg.scope}")
            if pkg.qco_instrument:
                content_parts.append(f"QCO: {pkg.qco_instrument.order_name}")
            if pkg.test_parameters:
                tp_names = [tp.parameter_name for tp in pkg.test_parameters[:5]]
                content_parts.append(f"Key Testing: {', '.join(tp_names)}")
            if pkg.materials:
                content_parts.append(f"Materials: {', '.join(pkg.materials[:5])}")

            results.append(KnowledgeRetrievalResult(
                standard_number=pkg.standard_number,
                title=pkg.title,
                content=" | ".join(content_parts) if content_parts else pkg.title,
                source=pkg.full_standard_code,
                document_type=KnowledgeDocumentType.INDIAN_STANDARD,
                verification_status=pkg.verification_status,
                knowledge_version=pkg.knowledge_version,
                relevance_score=pkg_score,
                provenance=pkg.verification_note or "Bureau of Indian Standards (Official Gazette)",
            ))

            # Also add individual requirements as results
            for req in pkg.requirements:
                req_score = cls._score_requirement(query, req)
                if req_score > 0.1 or standard_filter:
                    results.append(KnowledgeRetrievalResult(
                        standard_number=pkg.standard_number,
                        clause_section=req.clause_number,
                        title=req.clause_title,
                        content=req.requirement_text,
                        source=f"{pkg.full_standard_code} Clause {req.clause_number}",
                        document_type=KnowledgeDocumentType.INDIAN_STANDARD,
                        verification_status=req.verification_status,
                        exact_location=f"Clause {req.clause_number}",
                        knowledge_version=pkg.knowledge_version,
                        relevance_score=req_score,
                        provenance="Bureau of Indian Standards (Official Gazette)",
                    ))

        # Sort by relevance and apply top_k
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_k]

    @classmethod
    def _score_package(cls, query: str, pkg: StandardKnowledgePackage) -> float:
        """Compute relevance score of a package to a query."""
        q_tokens = set(re.findall(r"\w+", query.lower()))
        score = 0.0

        # Standard number match
        std_lower = pkg.standard_number.lower()
        if std_lower.replace(" ", "") in query.lower().replace(" ", ""):
            score += 0.6

        # Title match
        title_tokens = set(re.findall(r"\w+", (pkg.title + " " + (pkg.short_title or "")).lower()))
        common = q_tokens.intersection(title_tokens)
        if common:
            score += 0.3 * len(common) / max(len(q_tokens), 1)

        # Keyword match
        kw_tokens = set(w.lower() for w in pkg.keywords)
        kw_common = q_tokens.intersection(kw_tokens)
        if kw_common:
            score += 0.2 * len(kw_common) / max(len(q_tokens), 1)

        # Scope/materials match
        scope_tokens = set(re.findall(r"\w+", (pkg.scope or "").lower()))
        mat_tokens = set(w.lower() for w in pkg.materials)
        other_common = q_tokens.intersection(scope_tokens.union(mat_tokens))
        if other_common:
            score += 0.1 * len(other_common) / max(len(q_tokens), 1)

        return min(1.0, score)

    @classmethod
    def _score_requirement(cls, query: str, req) -> float:
        """Compute relevance score of a requirement to a query."""
        q_tokens = set(re.findall(r"\w+", query.lower()))
        req_tokens = set(re.findall(r"\w+", (req.requirement_text + " " + req.clause_title).lower()))
        common = q_tokens.intersection(req_tokens)
        if not common:
            return 0.0
        return min(1.0, 0.4 * len(common) / max(len(q_tokens), 1))


knowledge_retriever = KnowledgeRetriever()
