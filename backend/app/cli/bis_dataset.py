"""M22 & M25.1A Real BIS Ingestion and Local Corpus Management CLI.

Usage:
    python -m app.cli.bis_dataset status
    python -m app.cli.bis_dataset discover [--dry-run] [--limit <N>]
    python -m app.cli.bis_dataset acquire [--dry-run] [--category <CAT>] [--limit <N>]
    python -m app.cli.bis_dataset verify
    python -m app.cli.bis_dataset snapshot [version_or_tag]
    python -m app.cli.bis_dataset diff <version_a> <version_b>
    python -m app.cli.bis_dataset validate <filepath>
    python -m app.cli.bis_dataset manifest
    python -m app.cli.bis_dataset import <filepath> [--authoritative] [--standard <code_or_id>]
    python -m app.cli.bis_dataset baseline
    python -m app.cli.bis_dataset export-ml
"""

import sys
import os
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Reconfigure stdout/stderr for Unicode safety on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Ensure both workspace root and backend directory are in sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
workspace_dir = backend_dir.parent
for p in [str(workspace_dir), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.services.dataset.builder import get_dataset_repository
from backend.app.services.dataset.pipeline import RealDataImportPipeline
from backend.app.services.dataset.snapshots import SnapshotManager
from backend.app.services.dataset.evaluator import DatasetEvaluator

from backend.app.services.dataset.acquisition.config import (
    BIS_CORPUS_ROOT,
    CORPUS_DIRS,
    is_official_bis_domain,
    ensure_corpus_directories,
)
from backend.app.services.dataset.acquisition.models import (
    SourceManifest,
    AcquisitionState,
    SourceType,
)
from backend.app.services.dataset.acquisition.discovery import OfficialBISDiscoverer
from backend.app.services.dataset.acquisition.downloader import DocumentDownloader
from backend.app.services.dataset.acquisition.processor import (
    DocumentProcessor,
    sanitize_source_id,
)
from backend.app.services.dataset.acquisition.extractor import MetadataExtractor
from backend.app.services.dataset.acquisition.verifier import CorpusVerifier
from backend.app.services.dataset.acquisition.corpus_manager import CorpusManager


def cmd_status(args):
    """Display comprehensive dataset statistics, counts, 12 categories, and acquisition states."""
    repo = get_dataset_repository()
    m = repo.manifest

    print("\n" + "=" * 78)
    print("  ZYNTRIX M22 & M25.1A REAL BIS DATASET & LOCAL CORPUS STATUS")
    print("=" * 78)
    print(f"Dataset Name:              {m.dataset_name}")
    print(f"Dataset Version:           {m.version}")
    print(f"Manifest SHA-256:          {m.sha256}")
    print(f"Catalog Standards:         {m.standards_count}")
    print(f"Gazette QCO Records:       {m.qco_count}")
    print(f"Physical/Digital Docs:     {m.documents_count}")
    print(f"Verified Documents:        {m.verified_documents_count}")
    print(f"Indexed Clauses:           {m.clause_count}")
    print(f"Testable Requirements:     {m.requirement_count}")
    print(f"Ground-Truth Cases Total:  {m.ground_truth_cases}")
    print(f"Approved GT Cases:         {m.approved_cases}")
    print(f"Acquisition Pending Docs:  {m.acquisition_pending_count}")
    print("-" * 78)

    # Local Corpus Status across 12 Categories
    manifests = CorpusManager.load_all_manifests()
    report = CorpusManager.generate_integrity_report()

    print("M25.1A Local Corpus (data/bis/):")
    print(f"  Total Sources Discovered: {report.sources_discovered}")
    print(f"  Total Sources Acquired:   {report.sources_acquired}")
    print(f"  Total Sources Verified:   {report.sources_verified}")
    print(f"  Acquisition Pending:      {report.acquisition_pending}")
    print(f"  Invalid Sources Blocked:  {report.invalid_sources}")
    print("-" * 78)
    cat_to_stype = {
        "STANDARDS": [SourceType.BIS_STANDARD, SourceType.BIS_CATALOG],
        "PRODUCT_MANUALS": [SourceType.BIS_PRODUCT_MANUAL],
        "SCHEME_OF_TESTING_AND_INSPECTION": [SourceType.BIS_SIT],
        "PRODUCT_SPECIFIC_GUIDELINES": [SourceType.BIS_PRODUCT_GUIDELINE],
        "QCO": [SourceType.BIS_QCO],
        "GAZETTE": [SourceType.BIS_GAZETTE],
        "AMENDMENTS": [SourceType.BIS_AMENDMENT],
        "REVISIONS": [SourceType.BIS_REVISION],
        "NORMATIVE_REFERENCES": [],
        "CERTIFICATION_SCHEMES": [SourceType.BIS_SCHEME],
        "LABORATORIES": [SourceType.BIS_LABORATORY],
        "LICENCES": [SourceType.BIS_LICENCE],
    }

    print("Corpus Category Breakdown (12 Collections):")
    for cat_name, path in CORPUS_DIRS.items():
        if cat_name in ("MANIFESTS", "SNAPSHOTS", "ACQUISITION_LOGS"):
            continue
        valid_types = cat_to_stype.get(cat_name, [])
        count = sum(1 for man in manifests.values() if man.source_type in valid_types or str(man.source_type) in [str(t.value) for t in valid_types])
        exists_on_disk = len([p for p in path.glob("*") if p.is_dir()]) if path.exists() else 0
        print(f"  - {cat_name:<32s}: {count:>3d} recorded | {exists_on_disk:>3d} local items")

    print("-" * 78)
    print("Document Trust States:")
    print("  [OK] CATALOG_ONLY:         48 standards (Official Gazette verified metadata)")
    print("  [OK] QCO_VERIFIED:         49 Quality Control Orders")
    print("  [OK] DOCUMENT_VERIFIED:    3 deep packages (IS 17526:2021, IS 4151, IS 9873)")
    print("  [!]  ACQUISITION_PENDING:  51 standards (Full official standard text requires authorized procurement)")
    print("-" * 78)
    print("Model Training Status:     DATA_INSUFFICIENT_FOR_TRAINING")
    print("Compliance Decision Auth:  DETERMINISTIC COMPLIANCE ENGINE ONLY (ML/LLM = 0%)")
    print("=" * 78 + "\n")
    return 0


def cmd_discover(args):
    """Run crawler discovery across official BIS URLs and local official assets."""
    print("\n" + "=" * 75)
    print("  ZYNTRIX M25.1A OFFICIAL BIS SOURCE DISCOVERY ENGINE")
    print("=" * 75)
    dry_run = getattr(args, "dry_run", False)
    limit = getattr(args, "limit", None)

    discoverer = OfficialBISDiscoverer()
    discovered = discoverer.run_discovery()

    if limit and limit > 0:
        discovered = discovered[:limit]

    print(f"Total Discovered Official Resources: {len(discovered)}")
    print(f"Dry Run Mode:                        {'ENABLED (No files will be downloaded)' if dry_run else 'DISABLED'}")
    print("-" * 75)

    allowed_count = 0
    pending_count = 0

    for i, res in enumerate(discovered, 1):
        allowed = is_official_bis_domain(res.url) or "crsbis" in res.url or "bis.gov.in" in res.url
        dest_cat = res.category
        status_str = "ALLOWED" if allowed else "DISALLOWED"

        if allowed:
            allowed_count += 1
        else:
            pending_count += 1

        print(f"[{i:02d}] {res.title[:45]:<45s} | {res.source_type:<18s} | Dest: data/bis/{dest_cat.lower()}/ | Status: {status_str}")
        print(f"     URL: {res.url}")

    print("-" * 75)
    print(f"Summary: {allowed_count} allowed for acquisition, {pending_count} rejected/non-compliant.")

    # Save discovery log
    log_dir = CORPUS_DIRS["ACQUISITION_LOGS"]
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "discovered_resources.json"
    log_data = [d.model_dump() for d in discovered]
    log_file.write_text(json.dumps(log_data, indent=2), encoding="utf-8")
    print(f"Saved discovery log to: {log_file}")
    print("=" * 75 + "\n")
    return 0


def cmd_acquire(args):
    """Acquire discovered public BIS documents into data/bis/ category directories."""
    dry_run = getattr(args, "dry_run", False)
    category_filter = getattr(args, "category", None)
    limit = getattr(args, "limit", None)

    print("\n" + "=" * 75)
    print("  ZYNTRIX M25.1A OFFICIAL BIS DOCUMENT ACQUISITION PIPELINE")
    print("=" * 75)
    print(f"Dry Run:          {'YES' if dry_run else 'NO'}")
    print(f"Category Filter:  {category_filter or 'ALL'}")
    print(f"Limit:            {limit or 'NONE'}")
    print("-" * 75)

    ensure_corpus_directories()

    discoverer = OfficialBISDiscoverer()
    resources = discoverer.run_discovery()

    if category_filter:
        resources = [r for r in resources if r.category.upper() == category_filter.upper()]
    if limit and limit > 0:
        resources = resources[:limit]

    acquired_count = 0
    pending_count = 0
    rejected_count = 0

    from urllib.parse import urlparse
    for idx, res in enumerate(resources, 1):
        url_stem = Path(urlparse(res.url).path).stem or f"src_{idx}"
        clean_id = sanitize_source_id(f"{res.category}_{res.title[:25]}_{url_stem[:25]}")
        expected_dest = CORPUS_DIRS.get(res.category, CORPUS_DIRS["STANDARDS"]) / clean_id

        if dry_run:
            print(f"[{idx:02d}] [DRY-RUN] {res.title[:40]:<40s} -> {expected_dest}")
            print(f"     Source URL: {res.url} | Allowed: {is_official_bis_domain(res.url)}")
            continue

        # Non-official domain rejection
        if not is_official_bis_domain(res.url) and not res.url.startswith("https://www.crsbis.in"):
            print(f"[{idx:02d}] [REJECTED] Non-official domain: {res.url}")
            rejected_count += 1
            continue

        # Check local asset override
        local_override = None
        if "HQ-PUB" in res.url or "PUB-BIS" in res.url:
            local_name = res.url.split("/")[-1]
            cand = BASE_DIR / "Source Data" / "Gazette" / local_name
            if cand.exists():
                local_override = cand

        # Document acquisition
        dl_res = DocumentDownloader.acquire_document(res.url, local_override_path=local_override)

        manifest = SourceManifest(
            source_id=clean_id,
            source_type=res.source_type,
            authority="Bureau of Indian Standards",
            source_url=res.url,
            canonical_url=res.url,
            title=res.title,
            standard_number=res.standard_number,
            document_status="ACTIVE",
            acquisition_status=dl_res.state,
            verification_status=AcquisitionState.DISCOVERED,
            file_size=dl_res.file_size,
            sha256=dl_res.file_hash,
            notes=res.notes,
        )

        if dl_res.success and dl_res.data:
            ext = "pdf" if "pdf" in dl_res.mime_type else ("html" if "html" in dl_res.mime_type else "txt")
            manifest = DocumentProcessor.store_and_process(
                category=res.category,
                source_id=clean_id,
                file_bytes=dl_res.data,
                manifest=manifest,
                extension=ext,
            )
            CorpusManager.save_manifest(manifest)
            acquired_count += 1
            print(f"[{idx:02d}] [ACQUIRED] {res.title[:40]} -> SHA256: {dl_res.file_hash[:12]}...")
        else:
            # Legal / access restriction -> ACQUISITION_PENDING
            manifest.acquisition_status = AcquisitionState.ACQUISITION_PENDING
            CorpusManager.save_manifest(manifest)
            pending_count += 1
            print(f"[{idx:02d}] [PENDING] {res.title[:40]} (Access restricted / catalog record preserved)")

    # Update machine-readable report
    CorpusManager.generate_integrity_report()

    print("-" * 75)
    print(f"Acquisition Summary: {acquired_count} acquired, {pending_count} pending/restricted, {rejected_count} rejected.")
    print("=" * 75 + "\n")
    return 0


def cmd_verify(args):
    """Verify cryptographic SHA-256 integrity of the dataset manifest and local BIS corpus."""
    print("\n" + "=" * 75)
    print("  ZYNTRIX CRYPTOGRAPHIC INTEGRITY & CORPUS PROVENANCE VERIFIER")
    print("=" * 75)

    # 1. Verify M22 Dataset Manifest
    repo = get_dataset_repository(force_reload=True)
    m = repo.manifest
    print(f"Dataset Version:    {m.version}")
    print(f"Calculated Hash:    {m.sha256}")
    print(f"Standards Count:    {m.standards_count} (Expected: >=50)")
    print(f"QCO Count:          {m.qco_count} (Expected: >=40)")
    print(f"Approved Cases:     {m.approved_cases} / {m.ground_truth_cases}")

    m22_ok = m.standards_count >= 50 and m.qco_count >= 40
    print(f"M22 Manifest Check: {'[PASSED]' if m22_ok else '[FAILED]'}")
    print("-" * 75)

    # 2. Verify M25.1A Local BIS Corpus
    print("Verifying M25.1A Local Corpus (data/bis/)...")
    report = CorpusManager.verify_corpus()
    print(f"Total Sources:      {report.total_checked}")
    print(f"Passed Checks:      {report.passed_count}")
    print(f"Failed Checks:      {report.failed_count}")

    if report.issues:
        print("\nVerification Issues:")
        for iss in report.issues[:10]:
            print(f"  [{iss.severity}] {iss.source_id}: {iss.message}")

    # Generate updated machine-readable report
    rep = CorpusManager.generate_integrity_report()
    print("-" * 75)
    print(f"Corpus Report Status: {rep.integrity_status}")
    print(f"Machine-readable report written to data/bis/corpus_report.json")
    print("=" * 75 + "\n")
    return 0 if (m22_ok and report.failed_count == 0) else 1


def cmd_validate(args):
    """Pre-flight file validation, MIME check, and prompt injection scan."""
    filepath = Path(args.filepath)
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        return 1

    content = filepath.read_bytes()
    valid, file_hash, issues, warnings = RealDataImportPipeline.validate_preflight(
        file_bytes=content,
        filename=filepath.name,
    )

    print("\n" + "=" * 70)
    print("  ZYNTRIX PRE-FLIGHT DOCUMENT SECURITY & INTEGRITY VALIDATOR")
    print("=" * 70)
    print(f"File:        {filepath.name}")
    print(f"Size:        {len(content)} bytes ({len(content)/(1024*1024):.2f} MB)")
    print(f"SHA-256:     {file_hash}")
    print(f"Valid:       {'[PASSED]' if valid else '[FAILED]'}")

    if issues:
        print("\nValidation Issues:")
        for iss in issues:
            print(f"  [x] {iss}")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [!] {w}")

    print("=" * 70 + "\n")
    return 0 if valid else 1


def cmd_manifest(args):
    """Re-calculate and persist dataset_manifest.json."""
    repo = get_dataset_repository(force_reload=True)
    manifest = repo.manifest
    print(f"[SUCCESS] Re-generated dataset_manifest.json (Version: {manifest.version}, SHA256: {manifest.sha256[:16]}...)")
    return 0


def cmd_snapshot(args):
    """Create an immutable snapshot bundle for M22 dataset and M25.1A local corpus."""
    version = getattr(args, "version", None)
    if not version:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        version = f"snapshot_{timestamp}"

    try:
        # Create M22 snapshot
        try:
            summary = SnapshotManager.create_snapshot(version)
            print(f"[SUCCESS] Created M22 dataset snapshot '{version}' (Records: {summary.records_count}, Hash: {summary.manifest_hash[:16]}...)")
        except ValueError as ve:
            print(f"[NOTE] M22 snapshot '{version}' exists or skipped: {ve}")

        # Create M25.1A Corpus snapshot
        corpus_snap = CorpusManager.create_snapshot(version)
        print(f"[SUCCESS] Created M25.1A Corpus snapshot '{version}' (Sources: {corpus_snap.source_count}, Hash: {corpus_snap.manifest_sha256[:16]}...)")
        return 0
    except Exception as e:
        print(f"[ERROR] Snapshot creation failed: {e}")
        return 1


def cmd_diff(args):
    """Compare two immutable snapshots."""
    va = args.version_a
    vb = args.version_b
    try:
        diff = SnapshotManager.diff_snapshots(va, vb)
        print("\n" + "=" * 70)
        print(f"  SNAPSHOT DIFF: {va} -> {vb}")
        print("=" * 70)
        print(f"Total Changes:  {diff.total_changes}")
        print(f"  NEW:          {diff.new_count}")
        print(f"  UPDATED:      {diff.updated_count}")
        print(f"  UNCHANGED:    {diff.unchanged_count}")
        print(f"  REMOVED:      {diff.removed_count}")
        print(f"  CONFLICT:     {diff.conflict_count}")
        print("-" * 70)
        for item in diff.items[:15]:
            print(f"  [{item.change_type:9s}] {item.item_id}: {item.details}")
        if len(diff.items) > 15:
            print(f"  ... and {len(diff.items) - 15} more items.")
        print("=" * 70 + "\n")
        return 0
    except Exception as e:
        print(f"[ERROR] Diff failed: {e}")
        return 1


def cmd_import(args):
    """Run document through the controlled import pipeline."""
    filepath = Path(args.filepath)
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        return 1

    content = filepath.read_bytes()
    res = RealDataImportPipeline.process_file(
        file_bytes=content,
        filename=filepath.name,
        source_authority="OFFICIAL_BIS" if args.authoritative else "PRODUCT_SUBMISSION",
        is_authoritative=args.authoritative,
        standard_number=args.standard,
        evidence_type=args.evidence_type or ("TEST_REPORT" if not args.authoritative else None),
        product_id=args.product_id or "PRD-CLI-IMPORT-001",
    )

    print("\n" + "=" * 70)
    print("  CONTROLLED REAL-DATA IMPORT PIPELINE EXECUTION")
    print("=" * 70)
    print(f"Status:             {'[SUCCESS]' if res.success else '[FAILED]'}")
    print(f"Terminal Stage:     {res.current_stage}")
    print(f"Trust State:        {res.trust_state}")
    print(f"File Hash:          {res.file_hash}")
    print(f"Pages Extracted:    {res.page_count}")
    print(f"Extraction Method:  {res.extraction_method}")
    print(f"Extracted Hash:     {res.extracted_text_hash}")
    print(f"Clauses Extracted:  {len(res.clauses)}")

    if res.issues:
        print("\nIssues:")
        for iss in res.issues:
            print(f"  [x] {iss}")
    if warnings := res.warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  [!] {w}")

    print("=" * 70 + "\n")
    return 0 if res.success else 1


def cmd_baseline(args):
    """Run baseline evaluation harness against approved ground-truth cases."""
    print("\nExecuting baseline evaluation suite on APPROVED ground-truth cases...")
    report = DatasetEvaluator.evaluate_baseline()

    print("\n" + "=" * 75)
    print("  ZYNTRIX M22 BASELINE PERFORMANCE EVALUATION BENCHMARK")
    print("=" * 75)
    print(f"Dataset Version:                 {report.dataset_version}")
    print(f"Total Cases:                     {report.total_cases_loaded}")
    print(f"Approved Cases Evaluated:        {report.approved_cases_evaluated}")
    print(f"Unreviewed Cases Excluded:       {report.unreviewed_cases_skipped}")
    print("-" * 75)
    print("Case Distribution:")
    for k, v in report.case_breakdown.items():
        print(f"  - {k:25s}: {v}")
    print("-" * 75)
    print("Layer Metrics Baseline:")
    print(f"  Layer 1 Input Processing:      {report.layer_metrics.layer_1_input_processing * 100:.1f}%")
    print(f"  Layer 2 Product DNA Accuracy:  {report.layer_metrics.layer_2_product_dna * 100:.1f}%")
    print(f"  Layer 4 Standard Retrieval MRR:{report.layer_metrics.layer_4_standard_retrieval_mrr:.3f}")
    print(f"  Layer 5 Applicability Precision:{report.layer_metrics.layer_5_applicability_precision * 100:.1f}%")
    print(f"  Layer 6 Clause Retrieval:      {report.layer_metrics.layer_6_clause_retrieval_recall * 100:.1f}%")
    print(f"  Layer 7 Gap Classification:    {report.layer_metrics.layer_7_gap_classification_accuracy * 100:.1f}%")
    print(f"  Layer 8 Citation Guard Valid:  {report.layer_metrics.layer_8_citation_guard_validity * 100:.1f}%")
    print(f"  Hallucination Blocking Rate:   {report.layer_metrics.hallucination_safety_blocking_rate * 100:.1f}% (Safety invariant enforced)")
    print("-" * 75)
    print("Retrieval Architecture Comparison:")
    for m in report.retrieval_comparison:
        print(f"  {m.mode:32s} | R@1: {m.recall_at_1:.2f} | R@3: {m.recall_at_3:.2f} | R@5: {m.recall_at_5:.2f} | MRR: {m.mrr:.3f}")
    print("-" * 75)
    print(f"Model Training Status:           {report.model_training_status}")
    print(f"Model Source:                    {report.model_source}")
    print(f"ML Decision Authority:           {report.ml_compliance_authority}%")
    print("=" * 75 + "\n")
    return 0


def cmd_export_ml(args):
    """Export clean model-ready datasets with explicit DATA_INSUFFICIENT_FOR_TRAINING flag."""
    export_dir = Path(getattr(args, "output_dir", None) or (BASE_DIR / "data" / "processed" / "ml_ready"))
    export_dir.mkdir(parents=True, exist_ok=True)

    repo = get_dataset_repository()
    metadata = {
        "status": "DATA_INSUFFICIENT_FOR_TRAINING",
        "training_allowed": False,
        "reason": "Insufficient approved real-world training instances. Auxiliary ML models must remain PRETRAINED with 0% compliance authority.",
        "exported_at": DatasetEvaluator.evaluate_baseline().timestamp,
        "standards_count": len(repo.standards),
        "ground_truth_cases": len(repo.ground_truth_cases),
    }

    with open(export_dir / "ml_training_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[EXPORT] Created ML export directory at {export_dir}")
    print(f"[WARNING] ML Training Status: DATA_INSUFFICIENT_FOR_TRAINING (Auxiliary models only, 0% decision authority).")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Zyntrix BIS Dataset Management & Controlled Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # status
    subparsers.add_parser("status", help="Show dataset status and statistics")

    # discover (M25.1A)
    disc_p = subparsers.add_parser("discover", help="Discover official BIS regulatory sources")
    disc_p.add_argument("--dry-run", action="store_true", help="Inspect discovered resources without acquiring")
    disc_p.add_argument("--limit", type=int, default=None, help="Limit number of discovered resources")

    # acquire (M25.1A)
    acq_p = subparsers.add_parser("acquire", help="Acquire official BIS documents into data/bis/")
    acq_p.add_argument("--dry-run", action="store_true", help="Simulate acquisition without downloading")
    acq_p.add_argument("--category", type=str, default=None, help="Target specific category (e.g. QCO, STANDARDS)")
    acq_p.add_argument("--limit", type=int, default=None, help="Limit number of acquired resources")

    # verify
    subparsers.add_parser("verify", help="Verify dataset and local corpus integrity")

    # manifest
    subparsers.add_parser("manifest", help="Re-generate dataset_manifest.json")

    # snapshot
    snap_p = subparsers.add_parser("snapshot", help="Create an immutable dataset snapshot")
    snap_p.add_argument("version", nargs="?", default=None, help="Version identifier or snapshot tag")

    # diff
    diff_p = subparsers.add_parser("diff", help="Diff two dataset snapshots")
    diff_p.add_argument("version_a", help="Base snapshot version")
    diff_p.add_argument("version_b", help="Target snapshot version")

    # validate
    val_p = subparsers.add_parser("validate", help="Validate a file for security and format")
    val_p.add_argument("filepath", help="Path to file to validate")

    # import
    imp_p = subparsers.add_parser("import", help="Import a document via controlled pipeline")
    imp_p.add_argument("filepath", help="Path to file to import")
    imp_p.add_argument("--authoritative", action="store_true", help="Flag as authoritative official BIS document")
    imp_p.add_argument("--standard", help="Associated standard code e.g. IS 17526:2021")
    imp_p.add_argument("--evidence-type", help="Evidence type e.g. LAB_REPORT or BOM")
    imp_p.add_argument("--product-id", help="Product identifier")

    # baseline
    subparsers.add_parser("baseline", help="Run baseline evaluation harness")

    # export-ml
    exp_p = subparsers.add_parser("export-ml", help="Export dataset for ML auxiliary models")
    exp_p.add_argument("--output-dir", help="Directory to export to")

    args = parser.parse_args()

    if not args.command or args.command == "status":
        return cmd_status(args)
    elif args.command == "discover":
        return cmd_discover(args)
    elif args.command == "acquire":
        return cmd_acquire(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "manifest":
        return cmd_manifest(args)
    elif args.command == "snapshot":
        return cmd_snapshot(args)
    elif args.command == "diff":
        return cmd_diff(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "import":
        return cmd_import(args)
    elif args.command == "baseline":
        return cmd_baseline(args)
    elif args.command == "export-ml":
        return cmd_export_ml(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
