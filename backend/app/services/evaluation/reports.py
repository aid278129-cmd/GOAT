"""M24.6 Evaluation & Benchmark Reporting Engine.

Formats and exports comprehensive evaluation reports:
- CLI formatted tabular displays
- Machine-readable JSON summary and manifest artifacts
- Honest statistical confidence reporting and sample size classification
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from backend.app.core.config import BASE_DIR
from backend.app.services.evaluation.metrics import (
    DimensionEvaluationResult,
    M246EvaluationReport,
)

OUTPUT_DIR = BASE_DIR / "data" / "evaluation" / "results" / "m24_6"


def format_row(cols: List[Any], widths: List[int], align: str = "left") -> str:
    res = []
    for c, w in zip(cols, widths):
        s = str(c)
        if align == "right":
            res.append(s.rjust(w))
        else:
            res.append(s.ljust(w))
    return " | ".join(res)


def print_evaluation_report(report: M246EvaluationReport) -> None:
    """Prints a clear, publication-grade benchmark table to stdout."""
    print("\n" + "=" * 110)
    print("  ZYNTRIX BIS COMPLIANCE COMPILER — MILESTONE M24.6")
    print("  LANGGRAPH REASONING PIPELINE EVALUATION & BENCHMARK REPORT")
    print("=" * 110)
    print(f"Timestamp:                 {report.timestamp}")
    print(f"Milestone:                 {report.milestone}")
    print(f"Dataset Version:           {report.dataset_summary.dataset_version}")
    print(f"Catalog Standards:         {report.dataset_summary.total_standards_in_catalog} Authentic BIS Standards")
    print(f"Ground Truth Cases:        {report.dataset_summary.total_ground_truth_cases} Total ({report.dataset_summary.positive_cases} Pos, {report.dataset_summary.conflict_cases} Conflict, {report.dataset_summary.insufficient_cases} Insufficient, {report.dataset_summary.negative_or_ood_cases} Neg/OOD)")
    print(f"Golden Demo Case:          {report.dataset_summary.golden_case_id} (Locked: {report.golden_case_locked})")
    print(f"Compliance Authority:      {report.compliance_authority_check}")
    print(f"Dimensions Evaluated:      {report.total_dimensions_evaluated} / 15 ({report.passed_dimensions} Passed)")
    print(f"Total Scorable Queries:    {report.scorable_cases_total}")
    print(f"Unsupported / OOD Cases:   {report.unsupported_or_insufficient_cases_total}")
    print("=" * 110)

    print("\n" + "-" * 110)
    print("  15-DIMENSION REASONING EVALUATION MATRIX")
    print("-" * 110)
    headers = ["#", "Dimension Name", "N", "Success", "Rate", "95% Wilson CI", "Statistical Status"]
    widths = [2, 36, 3, 7, 6, 16, 26]
    print(format_row(headers, widths))
    print("-" * 110)

    for d in report.dimensions:
        ci_str = f"[{d.confidence_interval_95[0]:.2f}, {d.confidence_interval_95[1]:.2f}]"
        rate_str = f"{d.accuracy_rate * 100:.1f}%"
        stat_short = "INSUFFICIENT (N<30)" if "INSUFFICIENT" in d.statistical_status else "VALID"
        row = [
            str(d.dimension_id),
            d.dimension_name[:36],
            str(d.total_cases),
            str(d.successful_cases),
            rate_str,
            ci_str,
            stat_short,
        ]
        print(format_row(row, widths))

    print("-" * 110)

    print("\n" + "-" * 110)
    print("  REASONING PIPELINE LATENCY PROFILE (ms)")
    print("-" * 110)
    lat = report.latency_summary
    lat_headers = ["Samples", "Mean", "Median (P50)", "P90", "P95", "Min", "Max"]
    lat_widths = [8, 10, 14, 10, 10, 10, 10]
    print(format_row(lat_headers, lat_widths))
    print("-" * 110)
    lat_row = [
        str(lat.sample_count),
        f"{lat.mean_ms:.1f}",
        f"{lat.median_ms:.1f}",
        f"{lat.p90_ms:.1f}",
        f"{lat.p95_ms:.1f}",
        f"{lat.min_ms:.1f}",
        f"{lat.max_ms:.1f}",
    ]
    print(format_row(lat_row, lat_widths))
    print("-" * 110)
    print("NOTE: Any metric with sample size N < 30 is cardinally marked STATISTICALLY INSUFFICIENT.")
    print("      No metrics are fabricated or extrapolated to production claims.")
    print("=" * 110 + "\n")


def export_evaluation_artifacts(report: M246EvaluationReport, export_dir: Path = OUTPUT_DIR) -> Dict[str, Path]:
    """Serializes summary.json and manifest.json to the output directory."""
    export_dir.mkdir(parents=True, exist_ok=True)

    summary_file = export_dir / "summary.json"
    manifest_file = export_dir / "manifest.json"

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)

    manifest_data = {
        "milestone": "M24.6",
        "title": "LangGraph Reasoning Pipeline Evaluation & Benchmark",
        "timestamp": report.timestamp,
        "dataset_version": report.dataset_summary.dataset_version,
        "golden_case_id": report.dataset_summary.golden_case_id,
        "golden_locked": report.golden_case_locked,
        "dimensions_evaluated": report.total_dimensions_evaluated,
        "dimensions_passed": report.passed_dimensions,
        "scorable_cases_total": report.scorable_cases_total,
        "unsupported_or_insufficient_cases_total": report.unsupported_or_insufficient_cases_total,
        "artifacts_generated": ["summary.json", "manifest.json"],
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return {"summary": summary_file, "manifest": manifest_file}
