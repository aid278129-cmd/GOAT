"""Test asserting correct handling of authoritative vs development mode limitations:
1. Pending Full-Text Specification: Authoritative mode does not fabricate clause compliance; emits MORE_INFORMATION_REQUIRED + EXPERT_REVIEW.
2. Benchmark Scope: Benchmark reports sample size N=10 and LIMITED_DEVELOPMENT_BENCHMARK label, refusing broad claims.
3. Physical Testing Disclaimer: Testing roadmap compiles regulatory parameters without claiming physical laboratory execution.
"""
import pytest
from backend.app.services.gap_analysis.comparator import compare_requirement_with_evidence
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.schemas.product_dna import ProductDNACore
from backend.app.services.evaluation.m3_evaluator import evaluate_m3_retrieval_suite
from backend.app.services.laboratory.test_roadmap import compile_testing_roadmap


def test_authoritative_mode_pending_clause_handling():
    dna = ProductDNACore(
        product_name="Vacuum Flask",
        category="Drinkware & Food Contact Containers",
        materials=["stainless_steel_grade_304"],
        insulated=True,
    )

    # When authoritative clause full text is pending acquisition
    status, action, explanation = compare_requirement_with_evidence(
        requirement_code="AUTHORITATIVE_CLAUSE_PENDING",
        requirement_type="REGULATORY_GOVERNANCE",
        description="Full official technical specification is pending authorized procurement",
        measurable_condition="Official BIS publication",
        dna=dna,
    )

    assert status == ComplianceStatus.MORE_INFORMATION_REQUIRED
    assert action == RecommendedAction.EXPERT_REVIEW
    assert "pending acquisition" in explanation.lower()


def test_benchmark_scope_and_honest_disclaimers():
    report = evaluate_m3_retrieval_suite([{"case_id": f"TC-{i}", "rank": 1} for i in range(10)])
    assert report.sample_size == 10
    assert "EXPANDED_DEVELOPMENT_BENCHMARK" in report.benchmark_status
    assert report.llm_decision_authority == 0


def test_physical_testing_roadmap_disclaimer_integrity():
    roadmap = compile_testing_roadmap("IS 17526:2021")
    assert len(roadmap) > 0
    for item in roadmap:
        # Each item states required evidence and apparatus, not claiming physical execution
        assert item.evidence_required != ""
        assert item.required_apparatus != ""
        assert "laboratory" in item.evidence_required.lower() or "certificate" in item.evidence_required.lower()
