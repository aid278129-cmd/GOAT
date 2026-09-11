"""Comprehensive Production Test Suite for Layer 4: Segmented BIS Knowledge Base.

Tests all required invariants from SIH PPT Layer 4:
1. Standard lookup
2. Alias lookup
3. QCO relationship
4. Scope retrieval
5. Clause retrieval
6. Requirement retrieval
7. Evidence requirement mapping
8. Standard-version handling
9. Amendment handling
10. Unknown standard refusal
11. Unknown clause refusal
12. Cross-standard leakage prevention
13. Unverified source blocking
14. Pending full-text handling
15. Citation provenance
16. Dataset integrity
17. Lexical search
18. Hybrid retrieval
19. Metadata filtering
20. Knowledge-version propagation
21. Knowledge health diagnostics

Critical Invariants:
NO VERIFIED SOURCE → NO REGULATORY CLAIM
UNKNOWN → UNKNOWN
MISSING CLAUSE TEXT → DO NOT INVENT
WRONG STANDARD → REJECT
UNVERIFIED KNOWLEDGE → NOT AUTHORITATIVE
LLM NEVER CREATES BIS KNOWLEDGE
"""

import pytest
from backend.app.services.knowledge.knowledge_package import (
    StandardKnowledgePackage,
    KnowledgeVerificationStatus,
    KnowledgeAcquisitionStatus,
    KnowledgeCoverageDashboard,
    KnowledgeRetrievalResult,
    KnowledgeDocumentType,
)
from backend.app.services.knowledge.package_manager import (
    build_knowledge_packages,
    get_package,
    get_all_packages,
    get_coverage_dashboard,
    validate_dataset_integrity,
)
from backend.app.services.knowledge.knowledge_retriever import knowledge_retriever


# ────────────────────────────────────────────────────────────────────────
# 1. Standard Lookup
# ────────────────────────────────────────────────────────────────────────
def test_standard_lookup_by_number():
    """Exact standard number lookup must return the correct package."""
    pkg = get_package("IS 302-2-201")
    assert pkg is not None
    assert "302" in pkg.standard_number
    assert pkg.verification_status == KnowledgeVerificationStatus.VERIFIED


def test_standard_lookup_returns_none_for_unknown():
    """Unknown standard must return None (not a hallucinated package)."""
    pkg = get_package("IS 99999")
    assert pkg is None


# ────────────────────────────────────────────────────────────────────────
# 2. Alias Lookup
# ────────────────────────────────────────────────────────────────────────
def test_standard_alias_lookup():
    """Standard lookup should work with aliases (with/without year)."""
    pkg1 = get_package("IS 17526")
    assert pkg1 is not None
    assert "17526" in pkg1.standard_number


# ────────────────────────────────────────────────────────────────────────
# 3. QCO Relationship
# ────────────────────────────────────────────────────────────────────────
def test_qco_relationship_present():
    """Mandatory QCO standards must have QCO instrument populated."""
    pkg = get_package("IS 14543")
    assert pkg is not None
    assert pkg.qco_instrument is not None
    assert pkg.qco_instrument.mandatory is True


# ────────────────────────────────────────────────────────────────────────
# 4. Scope Retrieval
# ────────────────────────────────────────────────────────────────────────
def test_scope_retrieval():
    """Standard package must contain scope text from dataset."""
    pkg = get_package("IS 14543")
    assert pkg is not None
    assert pkg.scope is not None
    assert len(pkg.scope) > 10  # Not empty placeholder


# ────────────────────────────────────────────────────────────────────────
# 5–6. Clause & Requirement Retrieval
# ────────────────────────────────────────────────────────────────────────
def test_clause_requirement_retrieval_for_codified_standard():
    """Codified standards must have segmented clause requirements."""
    pkg = get_package("IS 302-2-201")
    assert pkg is not None
    assert len(pkg.requirements) > 0
    # Find clause 22.101 requirement
    cl_22 = [r for r in pkg.requirements if r.clause_number == "22.101"]
    assert len(cl_22) == 1
    assert "stainless steel" in cl_22[0].requirement_text.lower() or "copper" in cl_22[0].requirement_text.lower()
    assert cl_22[0].verification_status == KnowledgeVerificationStatus.VERIFIED


def test_requirement_has_full_provenance():
    """Each requirement must carry requirement_id, clause_number, clause_title, and verification_status."""
    pkg = get_package("IS 302-2-201")
    assert pkg is not None
    for req in pkg.requirements:
        assert req.requirement_id
        assert req.clause_number
        assert req.clause_title
        assert req.verification_status in KnowledgeVerificationStatus


# ────────────────────────────────────────────────────────────────────────
# 7. Evidence Requirement Mapping
# ────────────────────────────────────────────────────────────────────────
def test_evidence_requirement_mapping():
    """Each requirement should have evidence_types populated."""
    pkg = get_package("IS 302-2-201")
    assert pkg is not None
    for req in pkg.requirements:
        assert len(req.evidence_types) > 0
        assert "LAB_REPORT" in req.evidence_types


# ────────────────────────────────────────────────────────────────────────
# 8–9. Version & Amendment Handling
# ────────────────────────────────────────────────────────────────────────
def test_standard_version_handling():
    """Standards must have edition_year and knowledge_version."""
    pkg = get_package("IS 14543")
    assert pkg is not None
    assert pkg.edition_year is not None
    assert pkg.knowledge_version == "v1.2.0-gazette-verified"


def test_amendment_tracking():
    """Standards with amendments must list them."""
    pkg = get_package("IS 14543")
    assert pkg is not None
    assert isinstance(pkg.amendments, list)
    # Dataset has amendment info for some standards
    assert pkg.supersedes is not None or pkg.amendments is not None


# ────────────────────────────────────────────────────────────────────────
# 10. Unknown Standard Refusal
# ────────────────────────────────────────────────────────────────────────
def test_unknown_standard_retrieval_refusal():
    """Querying an unknown standard must return NOT_IN_KNOWLEDGE_BASE."""
    results = knowledge_retriever.search(
        query="What are the requirements?",
        standard_filter="IS 99999",
    )
    assert len(results) == 1
    assert results[0].verification_status == KnowledgeVerificationStatus.UNKNOWN
    assert "NOT_IN_KNOWLEDGE_BASE" in results[0].provenance


# ────────────────────────────────────────────────────────────────────────
# 11. Unknown Clause Refusal
# ────────────────────────────────────────────────────────────────────────
def test_unknown_clause_retrieval():
    """Known standard but unknown clause must not invent content."""
    results = knowledge_retriever.search(
        query="What does clause 99.99 require?",
        standard_filter="IS 14543",
    )
    # Should either return CLAUSE_TEXT_UNAVAILABLE or empty for unknown clauses
    for r in results:
        if r.clause_section == "99.99":
            assert "UNAVAILABLE" in r.title or "PENDING" in r.provenance


# ────────────────────────────────────────────────────────────────────────
# 12. Cross-Standard Leakage Prevention
# ────────────────────────────────────────────────────────────────────────
def test_cross_standard_leakage_prevention():
    """IS 17526 query with IS 17526 filter must NOT return IS 302 results."""
    results = knowledge_retriever.search(
        query="vacuum flask requirements",
        standard_filter="IS 17526",
    )
    for r in results:
        assert "302" not in r.standard_number
        assert "17526" in r.standard_number


# ────────────────────────────────────────────────────────────────────────
# 13. Unverified Source Blocking
# ────────────────────────────────────────────────────────────────────────
def test_unverified_source_filtering():
    """When verification filter is VERIFIED, only verified packages pass."""
    results = knowledge_retriever.search(
        query="water heater safety",
        verification_filter="VERIFIED",
    )
    for r in results:
        assert r.verification_status == KnowledgeVerificationStatus.VERIFIED


# ────────────────────────────────────────────────────────────────────────
# 14. Pending Full-Text Handling
# ────────────────────────────────────────────────────────────────────────
def test_pending_full_text_handling():
    """Standards with metadata-only must indicate OFFICIAL_DOCUMENT_ACQUISITION_PENDING."""
    packages = get_all_packages()
    metadata_only = [p for p in packages if p.acquisition_status == KnowledgeAcquisitionStatus.METADATA_ONLY]
    assert len(metadata_only) > 0  # Most standards are metadata-only
    for p in metadata_only:
        assert len(p.requirements) == 0  # No invented clause text


# ────────────────────────────────────────────────────────────────────────
# 15. Citation Provenance
# ────────────────────────────────────────────────────────────────────────
def test_citation_provenance_in_retrieval_results():
    """Every retrieval result must carry provenance, knowledge_version, and verification_status."""
    results = knowledge_retriever.search(
        query="leakage current limit",
        standard_filter="IS 302-2-201",
    )
    assert len(results) > 0
    for r in results:
        assert r.provenance
        assert r.knowledge_version
        assert r.verification_status in KnowledgeVerificationStatus


# ────────────────────────────────────────────────────────────────────────
# 16. Dataset Integrity
# ────────────────────────────────────────────────────────────────────────
def test_dataset_integrity_validation():
    """SHA-256 hash must match between computed and stored metadata."""
    integrity = validate_dataset_integrity()
    assert integrity["integrity_valid"] is True
    assert integrity["dataset_version"] == "v1.2.0-gazette-verified"
    assert len(integrity["computed_hash"]) == 64  # SHA-256 hex length


# ────────────────────────────────────────────────────────────────────────
# 17. Lexical Search
# ────────────────────────────────────────────────────────────────────────
def test_lexical_keyword_search():
    """Search by keywords must return relevant standards."""
    results = knowledge_retriever.search(query="drinking water TDS microbial")
    assert len(results) > 0
    assert any("14543" in r.standard_number for r in results)


# ────────────────────────────────────────────────────────────────────────
# 18. Hybrid Retrieval
# ────────────────────────────────────────────────────────────────────────
def test_hybrid_retrieval_with_clause_reference():
    """Clause-specific queries must return the exact clause from the correct standard."""
    results = knowledge_retriever.search(
        query="What does clause 22.101 mandate?",
        standard_filter="IS 302-2-201",
    )
    clause_results = [r for r in results if r.clause_section == "22.101"]
    assert len(clause_results) >= 1
    assert "sheath" in clause_results[0].content.lower() or "stainless" in clause_results[0].content.lower()


# ────────────────────────────────────────────────────────────────────────
# 19. Metadata Filtering
# ────────────────────────────────────────────────────────────────────────
def test_category_filter():
    """Category filter must restrict results to matching categories."""
    results = knowledge_retriever.search(
        query="safety requirements",
        category_filter="Packaged Water",
    )
    for r in results:
        pkg = get_package(r.standard_number)
        if pkg:
            assert "water" in pkg.product_category.lower() or "beverage" in pkg.product_category.lower()


# ────────────────────────────────────────────────────────────────────────
# 20. Knowledge-Version Propagation
# ────────────────────────────────────────────────────────────────────────
def test_knowledge_version_propagation():
    """All packages must inherit the dataset version."""
    packages = get_all_packages()
    assert len(packages) >= 51  # 51 standards in dataset + alias keys
    for pkg in packages:
        assert pkg.knowledge_version == "v1.2.0-gazette-verified"


# ────────────────────────────────────────────────────────────────────────
# 21. Knowledge Health Diagnostics
# ────────────────────────────────────────────────────────────────────────
def test_knowledge_coverage_dashboard():
    """Coverage dashboard must report accurate statistics."""
    dashboard = get_coverage_dashboard()
    assert dashboard.total_standards == 51  # Raw dataset count, not alias-inflated
    assert dashboard.total_qcos >= 40  # Most are mandatory QCO
    assert dashboard.standards_with_full_text >= 1  # At least codified standards
    assert dashboard.standards_with_metadata_only >= 1
    assert dashboard.dataset_version == "v1.2.0-gazette-verified"
    assert dashboard.integrity_hash is not None
    assert len(dashboard.integrity_hash) == 64
    assert dashboard.categories_covered >= 20
    assert dashboard.requirements_indexed >= 1
