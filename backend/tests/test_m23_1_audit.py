"""M23.1 Benchmark & Model Provenance Audit Test Suite.

Verifies:
1. Model provenance schema, checksums, CPU device assignment, and 0.0% regulatory authority.
2. Dynamic retrieval benchmark evaluation across all 5 modes on authentic N=21 scorable queries.
3. Realistic latencies (P50, P95) measured dynamically on CPU.
4. Statistical sufficiency classification (STATISTICALLY_INSUFFICIENT for N < 10 cases/records).
5. 100% Out-of-domain refusal, 100% cross-standard isolation, 100% unverified claim blocking.
6. GOLDEN-SIH-2026-DEMO locked integrity (golden_locked=True) and 5 clause / 3 evidence verification.
7. Machine-readable audit artifact generation (all 10 JSON artifacts + root reproducibility manifest).
"""

import os
import json
from pathlib import Path
import pytest

from backend.app.core.config import BASE_DIR
from backend.app.services.ml.registry import ml_model_registry
from backend.app.services.ml.evaluation.benchmark import ml_benchmark_runner, AuditedMetric, RetrievalBenchmarkRow
from backend.app.services.dataset.builder import get_dataset_repository
from backend.app.services.dataset.models import ReviewState, CaseType
from backend.app.services.retrieval.knowledge_registry import is_out_of_scope_query


# 1. Model Registry Provenance Schema
def test_m23_1_01_model_registry_provenance_schema():
    models = ml_model_registry.list_models()
    assert len(models) >= 6
    required_fields = [
        "model_id", "display_name", "upstream_model", "model_type",
        "task", "layer", "source", "revision", "library", "library_version",
        "license_metadata", "checksum", "device", "available",
        "fallback_available", "regulatory_authority", "training_status"
    ]
    for m in models:
        for field in required_fields:
            assert hasattr(m, field), f"Model {m.model_name} missing {field}"
            val = getattr(m, field)
            assert val is not None, f"Model {m.model_name} field {field} is None"
        assert m.checksum.startswith("sha256:"), f"Checksum not SHA-256 for {m.model_name}"


# 2. All Models Zero Regulatory Authority
def test_m23_1_02_all_models_zero_regulatory_authority():
    models = ml_model_registry.list_models()
    for m in models:
        assert m.regulatory_authority == 0.0, f"Violation: {m.model_name} has non-zero authority"


# 3. Training Status Invariant
def test_m23_1_03_training_status_data_insufficient():
    models = ml_model_registry.list_models()
    for m in models:
        assert m.training_status == "DATA_INSUFFICIENT_FOR_TRAINING"


# 4. CPU Device Assignment
def test_m23_1_04_cpu_device_assignment():
    models = ml_model_registry.list_models()
    for m in models:
        assert m.device == "cpu"


# 5. Dynamic Retrieval Benchmark Runs
def test_m23_1_05_dynamic_retrieval_benchmark_runs():
    stds, scorable, _ = ml_benchmark_runner._load_standards_and_queries()
    assert len(stds) == 51
    assert len(scorable) == 21
    rows, details = ml_benchmark_runner.run_retrieval_benchmark(stds, scorable)
    assert len(rows) == 5
    assert len(details) == 5


# 6. Retrieval 5 Modes Evaluated
def test_m23_1_06_retrieval_five_modes_evaluated():
    stds, scorable, _ = ml_benchmark_runner._load_standards_and_queries()
    rows, _ = ml_benchmark_runner.run_retrieval_benchmark(stds, scorable)
    modes = [r.mode for r in rows]
    assert any("BM25" in m for m in modes)
    assert any("Dense" in m for m in modes)
    assert any("Hybrid" in m for m in modes)
    assert any("Deterministic" in m or "Existing" in m for m in modes)
    assert any("Neural" in m for m in modes)


# 7. Retrieval Scorable Dataset Count
def test_m23_1_07_retrieval_scorable_dataset_count():
    stds, scorable, _ = ml_benchmark_runner._load_standards_and_queries()
    rows, _ = ml_benchmark_runner.run_retrieval_benchmark(stds, scorable)
    for r in rows:
        assert r.dataset_n == 21


# 8. Retrieval MRR and Recall Bounds
def test_m23_1_08_retrieval_mrr_and_recall_bounds():
    stds, scorable, _ = ml_benchmark_runner._load_standards_and_queries()
    rows, _ = ml_benchmark_runner.run_retrieval_benchmark(stds, scorable)
    for r in rows:
        assert 0.70 <= r.recall_at_1 <= 1.0
        assert 0.75 <= r.mrr <= 1.0


# 9. Retrieval Latencies Measured
def test_m23_1_09_retrieval_latencies_measured():
    stds, scorable, _ = ml_benchmark_runner._load_standards_and_queries()
    rows, _ = ml_benchmark_runner.run_retrieval_benchmark(stds, scorable)
    for r in rows:
        assert r.latency_p50_ms > 0.0
        assert r.latency_p95_ms >= r.latency_p50_ms


# 10. Extraction Metric Provenance Audit
def test_m23_1_10_extraction_metric_provenance_audit():
    repo = get_dataset_repository()
    metrics, _ = ml_benchmark_runner.run_extraction_benchmark(repo, "2026-09-10")
    for m in metrics:
        assert m.audit_status == "STATISTICALLY_INSUFFICIENT"
        assert m.sample_count < 10
        assert m.reported_m23_value > 0.90
        assert m.reproduced_value is not None


# 11. Evidence Matching Audit Sample Size
def test_m23_1_11_evidence_matching_audit_sample_size():
    repo = get_dataset_repository()
    metrics, _ = ml_benchmark_runner.run_evidence_matching_benchmark(repo, "2026-09-10")
    for m in metrics:
        assert m.audit_status == "STATISTICALLY_INSUFFICIENT"
        assert m.sample_count == 5


# 12. Anomaly Conflict Detection Audit
def test_m23_1_12_anomaly_conflict_detection_audit():
    repo = get_dataset_repository()
    metrics, details = ml_benchmark_runner.run_anomaly_benchmark(repo, "2026-09-10")
    conflict_m = next(m for m in metrics if "Conflict" in m.metric_name)
    assert conflict_m.audit_status == "STATISTICALLY_INSUFFICIENT"
    assert conflict_m.sample_count == 1
    assert conflict_m.reproduced_value == 1.00


# 13. False Positive Rate on Clean Matches
def test_m23_1_13_false_positive_rate_clean_matches():
    repo = get_dataset_repository()
    metrics, details = ml_benchmark_runner.run_anomaly_benchmark(repo, "2026-09-10")
    fpr_m = next(m for m in metrics if "False Positive" in m.metric_name)
    assert fpr_m.reproduced_value == 0.00


# 14. Adversarial Out-of-Domain Refusal 100%
def test_m23_1_14_adversarial_out_of_domain_refusal_100():
    _, _, ood = ml_benchmark_runner._load_standards_and_queries()
    assert len(ood) == 4
    for q in ood:
        assert is_out_of_scope_query(q["query"]) is True


# 15. Cross-Standard Leakage Prevention 100%
def test_m23_1_15_cross_standard_leakage_firewall_100():
    _, _, ood = ml_benchmark_runner._load_standards_and_queries()
    metrics, details = ml_benchmark_runner.run_safety_benchmark(ood)
    leakage_m = next(m for m in metrics if "Cross-Standard" in m.metric_name)
    assert leakage_m.reproduced_value == 1.00
    assert details["leakage_prevention_rate"] == 1.00


# 16. Unsupported Claim Blocking 100%
def test_m23_1_16_unsupported_claim_blocking_100():
    _, _, ood = ml_benchmark_runner._load_standards_and_queries()
    metrics, details = ml_benchmark_runner.run_safety_benchmark(ood)
    blocking_m = next(m for m in metrics if "Unsupported Claim" in m.metric_name)
    assert blocking_m.reproduced_value == 1.00
    assert details["unsupported_blocking_rate"] == 1.00


# 17. Golden Case Locked Integrity
def test_m23_1_17_golden_case_locked_integrity():
    repo = get_dataset_repository()
    golden = repo.ground_truth_cases.get("GOLDEN-SIH-2026-DEMO")
    assert golden is not None
    assert getattr(golden, "golden_locked", False) is True
    assert golden.golden_sih_demo is True
    assert golden.review_status == ReviewState.APPROVED.value


# 18. Golden Case Clauses and Evidence
def test_m23_1_18_golden_case_clauses_and_evidence():
    repo = get_dataset_repository()
    golden = repo.ground_truth_cases.get("GOLDEN-SIH-2026-DEMO")
    expected_clauses = ["4.2.1", "4.2.2", "5.2", "5.4", "7.1"]
    for c in expected_clauses:
        assert c in golden.expected_clauses
    expected_evs = [
        "EV-LAB-IS17526-750ML-001",
        "EV-BOM-IS17526-750ML-002",
        "EV-PHOTO-IS17526-750ML-003",
    ]
    actual_ev_ids = [e["evidence_id"] for e in golden.evidence_records]
    for ev_id in expected_evs:
        assert ev_id in actual_ev_ids
    assert golden.expected_gap_classification == "SATISFIED"


# 19. Audit Artifacts Generated
def test_m23_1_19_audit_artifacts_generated():
    report = ml_benchmark_runner.run_full_benchmark(export_artifacts=True)
    out_dir = BASE_DIR / "data" / "evaluation" / "results" / "m23_1"
    required_files = [
        "manifest.json",
        "retrieval_results.json",
        "extraction_results.json",
        "evidence_matching_results.json",
        "anomaly_results.json",
        "nli_results.json",
        "applicability_results.json",
        "adversarial_results.json",
        "latency_results.json",
        "summary.json",
    ]
    for rf in required_files:
        p = out_dir / rf
        assert p.exists(), f"Missing artifact: {p}"
        assert p.stat().st_size > 0, f"Empty artifact: {p}"
        with open(p, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            assert data is not None


# 20. Root Reproducibility File Validity
def test_m23_1_20_root_reproducibility_file_validity():
    root_file = BASE_DIR / "m23_1_reproducibility.json"
    assert root_file.exists(), "Root m23_1_reproducibility.json does not exist"
    assert root_file.stat().st_size > 0
    with open(root_file, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    assert data["milestone"] == "M23.1"
    assert "manifest" in data
    assert "summary" in data
