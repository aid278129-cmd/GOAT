"""Milestone M24.6 - Evaluation & Benchmarking Test Suite.

Verifies:
1. Mathematical precision of Wilson score intervals and sample size classification.
2. M23.1 golden-case locking preservation (GOLDEN-SIH-2026-DEMO).
3. All 15 canonical reasoning evaluation dimensions.
4. Evaluation artifact serialization and manifest compliance.
5. Invariant preservation: 0 ML models added, 0 LLMs added, 0.0% compliance authority.
"""

import os
import pytest
from pathlib import Path

from backend.app.services.evaluation.metrics import (
    compute_wilson_score_interval,
    classify_statistical_sufficiency,
    calculate_latency_summary,
    MIN_STATISTICAL_SAMPLE_SIZE,
)
from backend.app.services.evaluation.evaluator import LangGraphEvaluator, M246EvaluationReport
from backend.app.services.evaluation.reports import export_evaluation_artifacts


# ------------------------------------------------------------------------------
# 1. Statistical Engine & Mathematical Tests
# ------------------------------------------------------------------------------

def test_wilson_score_interval_bounds():
    """Verify Wilson score interval stays within [0.0, 1.0] and handles edge cases."""
    # Zero sample case
    assert compute_wilson_score_interval(0, 0) == (0.0, 0.0)

    # 100% success rate
    low, high = compute_wilson_score_interval(10, 10)
    assert 0.0 < low < 1.0
    assert high == 1.0

    # 0% success rate
    low, high = compute_wilson_score_interval(0, 10)
    assert low == 0.0
    assert 0.0 < high < 1.0

    # 50% rate
    low, high = compute_wilson_score_interval(50, 100)
    assert 0.39 < low < 0.42
    assert 0.58 < high < 0.61


def test_statistical_sufficiency_guard():
    """Verify that sample size < 30 is strictly marked STATISTICALLY_INSUFFICIENT."""
    assert classify_statistical_sufficiency(0) == "STATISTICALLY_INSUFFICIENT"
    assert classify_statistical_sufficiency(1) == "STATISTICALLY_INSUFFICIENT"
    assert classify_statistical_sufficiency(MIN_STATISTICAL_SAMPLE_SIZE - 1) == "STATISTICALLY_INSUFFICIENT"
    assert classify_statistical_sufficiency(MIN_STATISTICAL_SAMPLE_SIZE) == "STATISTICALLY_VALID"
    assert classify_statistical_sufficiency(100) == "STATISTICALLY_VALID"


def test_latency_summary_calculations():
    """Verify latency percentile and mean calculations."""
    durations = [10.0, 20.0, 30.0, 40.0, 50.0]
    summary = calculate_latency_summary(durations)

    assert summary.sample_count == 5
    assert summary.mean_ms == 30.0
    assert summary.median_ms == 30.0
    assert summary.min_ms == 10.0
    assert summary.max_ms == 50.0


# ------------------------------------------------------------------------------
# 2. Golden Case Locking & Ground Truth Repository Tests
# ------------------------------------------------------------------------------

def test_golden_case_locked_invariant():
    """Verify GOLDEN-SIH-2026-DEMO is present and locked per M23.1 specifications."""
    evaluator = LangGraphEvaluator()
    assert evaluator.verify_golden_case_locking() is True
    golden = evaluator.ground_truth_cases.get("GOLDEN-SIH-2026-DEMO")
    assert golden is not None
    assert golden.golden_locked is True
    assert "IS 17526:2021" in golden.expected_standard_candidates


# ------------------------------------------------------------------------------
# 3. Canonical 15 Dimensions Individual Verification
# ------------------------------------------------------------------------------

def test_dim1_request_routing():
    """Dimension 1: Request routing accuracy."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_request_routing()
    assert res.dimension_id == 1
    assert res.accuracy_rate == 1.0
    assert res.statistical_status == "STATISTICALLY_INSUFFICIENT"


def test_dim2_dna_clarification():
    """Dimension 2: Product DNA clarification behavior."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_dna_clarification()
    assert res.dimension_id == 2
    assert res.accuracy_rate == 1.0


def test_dim3_standard_retrieval():
    """Dimension 3: BIS standard retrieval accuracy."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_standard_retrieval()
    assert res.dimension_id == 3
    assert res.accuracy_rate == 1.0


def test_dim4_clause_retrieval():
    """Dimension 4: Clause retrieval accuracy."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_clause_retrieval()
    assert res.dimension_id == 4
    assert res.accuracy_rate == 1.0


def test_dim5_evidence_grounding():
    """Dimension 5: Evidence grounding and citation validity."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_evidence_grounding()
    assert res.dimension_id == 5
    assert res.accuracy_rate == 1.0


def test_dim6_out_of_domain_refusal():
    """Dimension 6: Out-of-domain refusal rate."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_out_of_domain_refusal()
    assert res.dimension_id == 6
    assert res.accuracy_rate == 1.0


def test_dim7_insufficient_information():
    """Dimension 7: Insufficient information handling."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_insufficient_information()
    assert res.dimension_id == 7
    assert res.accuracy_rate == 1.0


def test_dim8_conflict_handling():
    """Dimension 8: Conflict handling."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_conflict_handling()
    assert res.dimension_id == 8
    assert res.accuracy_rate == 1.0


def test_dim9_tool_failure_handling():
    """Dimension 9: Tool failure and boundary handling."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_tool_failure_handling()
    assert res.dimension_id == 9
    assert res.accuracy_rate == 1.0


def test_dim10_authority_firewall():
    """Dimension 10: Authority firewall protection."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_authority_firewall()
    assert res.dimension_id == 10
    assert res.accuracy_rate == 1.0


def test_dim11_unsupported_claim_blocking():
    """Dimension 11: Unsupported claim blocking."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_unsupported_claim_blocking()
    assert res.dimension_id == 11
    assert res.accuracy_rate == 1.0


def test_dim12_cross_standard_leakage():
    """Dimension 12: Cross-standard leakage prevention."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_cross_standard_leakage()
    assert res.dimension_id == 12
    assert res.accuracy_rate == 1.0


def test_dim13_deterministic_compliance_preservation():
    """Dimension 13: Deterministic compliance result preservation."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_deterministic_compliance_preservation()
    assert res.dimension_id == 13
    assert res.accuracy_rate == 1.0


def test_dim14_end_to_end_graph_paths():
    """Dimension 14: End-to-end graph path correctness."""
    evaluator = LangGraphEvaluator()
    res = evaluator.evaluate_end_to_end_graph_paths()
    assert res.dimension_id == 14
    assert res.accuracy_rate == 1.0


def test_dim15_latency_metrics():
    """Dimension 15: Latency and execution metrics."""
    evaluator = LangGraphEvaluator()
    evaluator.run_all_evaluations()
    res = evaluator.evaluate_request_routing()
    assert len(evaluator.latencies_ms) > 0


# ------------------------------------------------------------------------------
# 4. Full Evaluation Report & Artifact Export Tests
# ------------------------------------------------------------------------------

def test_full_evaluation_run_and_artifact_export(tmp_path):
    """Run full evaluation suite, verify all 15 dimensions pass, and check JSON artifacts."""
    evaluator = LangGraphEvaluator()
    report = evaluator.run_all_evaluations()

    assert report.total_dimensions_evaluated == 15
    assert report.passed_dimensions == 15
    assert report.golden_case_locked is True
    assert "0.0%" in report.compliance_authority_check

    # Export artifacts to temporary directory
    artifacts = export_evaluation_artifacts(report, export_dir=tmp_path)
    assert artifacts["summary"].exists()
    assert artifacts["manifest"].exists()

    import json
    with open(artifacts["summary"], "r", encoding="utf-8") as f:
        summary_data = json.load(f)
    assert summary_data["milestone"] == "M24.6"
    assert len(summary_data["dimensions"]) == 15

    with open(artifacts["manifest"], "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert manifest_data["golden_locked"] is True
    assert manifest_data["dimensions_passed"] == 15
