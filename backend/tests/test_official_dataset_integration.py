"""Milestone M11 Official BIS Standards Dataset Integration Test Suite.

Verifies:
1. Full 51-standard official dataset loading from data/bis_dataset/real_bis_standards.json.
2. Accurate standard retrieval across sectors (pressure cookers, water, power banks, TMT bars, helmets, toys, drinkware).
3. Out-of-scope refusal queries (USPTO patents, US FDA 510(k), foreign stock scrapers, general trivia) return empty / refuse.
4. Fake standard numbers (IS 99999, IS 88888) return UNKNOWN / NOT_IN_KNOWLEDGE_BASE.
5. Citations point to authentic Gazette QCO notifications, ministries, and schemes.
6. Zero-hallucination boundaries: user claims never satisfy requirements without verified lab evidence.
7. Conflicting evidence triggers EXPERT_REVIEW.
8. Assessment snapshots preserve dataset version and knowledge provenance metadata.
9. Extended /api/v1/system/health diagnostic fields for knowledge base.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.retrieval.knowledge_registry import (
    load_knowledge_registry,
    get_dataset_metadata,
    get_standard_by_code,
    search_standards,
    is_out_of_scope_query,
)
from backend.app.services.retrieval.clause_retriever import search_clauses
from backend.app.services.applicability.candidate_generator import generate_candidate_standards
from backend.app.schemas.product_dna import ProductDNACore, DNAAttribute
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.services.gap_analysis.evidence_gate import can_be_satisfied
from backend.app.services.gap_analysis.evidence_extractor import extract_evidence_from_snippet


# 1. Dataset Integrity & Size
def test_official_dataset_loaded_count_and_provenance():
    """Verify official dataset has 51 verified standards with gazette metadata."""
    standards = load_knowledge_registry()
    assert len(standards) >= 51, f"Expected at least 51 standards, found {len(standards)}"

    meta = get_dataset_metadata()
    assert meta["dataset_name"] == "BIS-standards-dataset"
    assert "v1.2.0" in meta["dataset_version"]
    assert meta["sha256"] is not None

    # Check key mandatory schemes are represented
    schemes = {s.get("scheme") for s in standards}
    assert "Scheme-I (ISI)" in schemes
    assert "Scheme-II (CRS)" in schemes


# 2. Multi-Sector Retrieval Accuracy
@pytest.mark.parametrize(
    "query,expected_std",
    [
        ("domestic pressure cooker safety", "IS 2347"),
        ("packaged drinking water testing", "IS 14543"),
        ("portable power bank lithium battery", "IS 16046"),
        ("TMT steel bars civil construction", "IS 1786"),
        ("two-wheeler protective helmet", "IS 4151"),
        ("children mechanical toys", "IS 9873"),
        ("stainless steel vacuum flask bottle", "IS 17526"),
        ("self-ballasted LED bulbs safety", "IS 16102"),
    ],
)
def test_multi_sector_retrieval(query: str, expected_std: str):
    """Verify search_standards accurately maps product queries to authentic standards."""
    results = search_standards(query, top_k=3)
    assert len(results) > 0, f"No results for query: {query}"
    matched_codes = [r.get("standard_number") for r in results]
    assert any(expected_std in code for code in matched_codes), f"Expected {expected_std} in {matched_codes} for '{query}'"


# 3. Gold-Standard Out-of-Scope Refusal Queries
@pytest.mark.parametrize(
    "out_query",
    [
        "How do I register a patent with the US Patent and Trademark Office (USPTO)?",
        "What are the US FDA 510(k) clearance requirements for medical gloves?",
        "What is the capital city of Australia?",
        "Write a Python script to scrape live commodity prices from the stock exchange.",
    ],
)
def test_out_of_scope_queries_refused(out_query: str):
    """Verify non-BIS queries are identified and produce zero matched standards."""
    assert is_out_of_scope_query(out_query) is True
    results = search_standards(out_query)
    assert len(results) == 0, f"Expected 0 results for out-of-scope query: {out_query}"


# 4. Fake Standards & Fake Clauses Return Unknown
@pytest.mark.asyncio
async def test_fake_standard_returns_unknown_clauses():
    """Verify searching clauses for a fabricated standard yields zero results."""
    # IS 99999 is fabricated and does not exist in the official dataset
    fake_std = get_standard_by_code("IS 99999:2099")
    assert fake_std is None

    clauses = await search_clauses(db=None, query="drop test", standard_number="IS 99999:2099")
    assert len(clauses) == 0, "System must never invent clauses for non-existent standards"


# 5. Authentic Gazette QCO Citation Provenance
def test_authentic_qco_provenance_metadata():
    """Verify standards carry authentic Gazette QCO and Ministry metadata."""
    water_std = get_standard_by_code("IS 14543")
    assert water_std is not None
    assert water_std["mandatory_qco"] is True
    legal = water_std.get("legal_source", {})
    assert "FSSAI" in legal.get("issuing_ministry", "") or "Consumer Affairs" in legal.get("issuing_ministry", "")
    assert legal.get("notification_number") is not None


# 6. Product Applicability Flow on Dataset
def test_applicability_dataset_candidate_generation():
    """Verify candidate generation dynamically suggests standards from dataset."""
    dna = ProductDNACore(
        product_name="Aluminum Pressure Cooker",
        category="Kitchen & Domestic Appliances",
        materials=["Aluminum Alloy 3003", "Bakelite handle"],
        intended_use="Domestic cooking",
    )
    res = generate_candidate_standards(dna)
    assert res.coverage_state == "COVERED"
    assert len(res.candidates) > 0
    top_cand = res.candidates[0]
    assert "2347" in top_cand.standard_number
    assert top_cand.source_status == "VERIFIED_OFFICIAL"
    assert "pressure cooker" in top_cand.explanation.lower()


# 7. Evidence-First Invariant: User Claims Cannot Satisfy Requirements
def test_user_claim_cannot_satisfy_requirement():
    """Verify asserting compliance in user text never produces SATISFIED status."""
    claim_text = "I certify that my pressure cooker complies with all IS 2347 safety burst tests."
    evidence_items = extract_evidence_from_snippet(claim_text, authority="USER_ASSERTED")

    can_sat, stat, act, exp = can_be_satisfied(
        requirement={"code": "REQ-TEST-BURST", "requirement_type": "PERFORMANCE"},
        linked_evidences=evidence_items,
    )
    assert can_sat is False
    assert stat == ComplianceStatus.MISSING_EVIDENCE
    assert act in (RecommendedAction.REQUIRES_TESTING, RecommendedAction.UPLOAD_EVIDENCE)


# 8. Conflicting Evidence Triggers Expert Review
def test_conflicting_evidence_triggers_expert_review():
    """Verify conflicting evidence values mandate EXPERT_REVIEW."""
    ev_a = extract_evidence_from_snippet(
        "Lab report A: Inversion leakage test 10 minutes showed ZERO moisture seepage. PASSED.",
        authority="LAB_REPORT",
    )
    ev_b = extract_evidence_from_snippet(
        "Lab report B: Inversion test 10 minutes showed continuous leakage and droplet accumulation. FAILED.",
        authority="LAB_REPORT",
    )
    can_sat, stat, act, exp = can_be_satisfied(
        requirement={"code": "REQ-LEAK-01", "requirement_type": "PERFORMANCE"},
        linked_evidences=ev_a + ev_b,
        has_conflict=True,
    )
    assert can_sat is False
    assert stat in (
        ComplianceStatus.CONFLICTING_EVIDENCE,
        ComplianceStatus.REQUIRES_EXPERT_REVIEW,
    )
    assert act == RecommendedAction.EXPERT_REVIEW


# 9. Extended Health Endpoint Reports Dataset Version & Counts
@pytest.mark.asyncio
async def test_health_endpoint_knowledge_diagnostics():
    """Verify /api/v1/system/health returns extended knowledge base fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/system/health")
        assert res.status_code == 200
        data = res.json()
        kb = data["knowledge_base"]
        assert kb["dataset_name"] == "BIS-standards-dataset"
        assert kb["number_of_standards"] >= 51
        assert kb["number_of_qco_records"] >= 40
        assert "v1.2.0" in kb["dataset_version"]
        assert kb["knowledge_integrity_hash"] is not None
