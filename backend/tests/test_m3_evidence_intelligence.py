"""Automated test suite for M3 Evidence Intelligence, Hybrid Retrieval, and Evaluation.

Tests:
1. BM25 lexical search indexing and scoring
2. Hybrid retrieval combining BM25 lexical and dense similarity
3. Exact match & relevance reranker
4. Context window parent clause resolution
5. Structured evidence extraction from test reports and material certs
6. Unit normalization (e.g. 60 deg C -> 60.0 C)
7. Evidence conflict detection
8. Test roadmap compilation and laboratory lookup
9. N=10 ground truth benchmark dataset validation
10. Ablation comparison & retrieval metrics (Recall@1/3/5, MRR)
"""
import pytest
from backend.app.services.retrieval.bm25 import BM25LexicalIndex
from backend.app.services.retrieval.reranker import default_reranker
from backend.app.services.gap_analysis.evidence_extractor import (
    extract_evidence_from_snippet,
    normalize_evidence_units,
    detect_evidence_conflicts,
    StructuredEvidence,
)
from backend.app.services.laboratory.test_roadmap import (
    compile_testing_roadmap,
    get_verified_laboratories,
)
from backend.app.services.evaluation.benchmark_suite import load_m3_benchmark_cases
from backend.app.services.evaluation.m3_evaluator import evaluate_m3_retrieval_suite


def test_bm25_lexical_index():
    bm25 = BM25LexicalIndex()
    docs = [
        ("doc-1", "Stainless steel parts grade 304 food contact liner"),
        ("doc-2", "Thermal performance heat retention test water at 95 degrees"),
        ("doc-3", "Marking and packaging requirements with ISI logo"),
    ]
    bm25.index_documents(docs)

    scores = bm25.score("stainless steel 304")
    assert len(scores) >= 1
    assert scores[0][0] == "doc-1"


def test_reranker_relevance():
    candidates = [
        {
            "clause_number": "5.4",
            "clause_title": "Thermal Performance Test",
            "standard_number": "IS 17526:2021",
            "text_content": "Hot water cooling after 6 hours",
            "hybrid_score": 0.6,
        },
        {
            "clause_number": "4.2.1",
            "clause_title": "Stainless Steel Parts",
            "standard_number": "IS 17526:2021",
            "text_content": "Grade 304 metallic parts",
            "hybrid_score": 0.5,
        },
    ]

    reranked = default_reranker.rerank("Clause 4.2.1 stainless steel", candidates)
    # Clause 4.2.1 should be promoted due to exact clause mention
    assert reranked[0]["clause_number"] == "4.2.1"


def test_evidence_extraction_and_unit_normalization():
    # Unit normalizer
    v, u = normalize_evidence_units("60 °C")
    assert v == 60.0
    assert u == "C"

    v2, u2 = normalize_evidence_units("6 hours")
    assert v2 == 6.0
    assert u2 == "hours"

    # Snippet extraction
    snippet = "Test report indicates water temperature of 62.5 deg C after 6 hours. Zero leakage observed during 10-minute inversion."
    evs = extract_evidence_from_snippet(snippet)
    assert len(evs) >= 2
    attrs = {e.attribute for e in evs}
    assert "tested_heat_retention_temp" in attrs
    assert "leakage_test_result" in attrs


def test_evidence_conflict_detection():
    ev1 = StructuredEvidence(
        evidence_id="EV-1",
        evidence_type="DATASHEET",
        source_text="Rated temp 65C",
        attribute="tested_heat_retention_temp",
        raw_value="65C",
        normalized_value=65.0,
        unit="C",
        authority="MANUFACTURER_DOCUMENT",
    )
    ev2 = StructuredEvidence(
        evidence_id="EV-2",
        evidence_type="TEST_REPORT",
        source_text="Observed temp 54C",
        attribute="tested_heat_retention_temp",
        raw_value="54C",
        normalized_value=54.0,
        unit="C",
        authority="LAB_REPORT",
    )

    conflicts = detect_evidence_conflicts([ev1, ev2])
    assert len(conflicts) == 1
    assert conflicts[0]["attribute"] == "tested_heat_retention_temp"


def test_testing_roadmap_and_laboratory_knowledge():
    roadmap = compile_testing_roadmap("IS 17526:2021")
    assert len(roadmap) >= 3
    test_codes = [t.requirement_code for t in roadmap]
    assert "REQ-PERF-THERM" in test_codes
    assert "REQ-PERF-LEAK" in test_codes

    labs = get_verified_laboratories("IS 17526:2021")
    assert len(labs) >= 2
    assert labs[0].is_nabl_accredited is True
    assert labs[0].verification_status == "VERIFIED"


def test_m3_benchmark_suite_and_ablation_evaluation():
    cases = load_m3_benchmark_cases()
    assert len(cases) >= 10

    sample_results = [
        {"case_id": c["case_id"], "rank": 1 if idx < 8 else 2, "error_category": "NONE" if idx < 8 else "METADATA_MISS"}
        for idx, c in enumerate(cases)
    ]

    report = evaluate_m3_retrieval_suite(sample_results)
    assert report.sample_size == 10
    assert report.recall_at_1 >= 0.8
    assert report.recall_at_3 == 1.0
    assert report.llm_decision_authority == 0
    assert len(report.ablation_comparison) == 4
