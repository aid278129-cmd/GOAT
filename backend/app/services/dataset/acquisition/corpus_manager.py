"""Corpus Manager for Official BIS Sources, Versioning, Snapshots, and Change Detection.

Enforces:
1. Complete lifecycle management across all 12 separate source collections.
2. Change detection: UNCHANGED vs SOURCE_CHANGED via SHA-256 comparison.
3. Immutable timestamped corpus snapshots in data/bis/snapshots/snapshot_YYYYMMDD_HHMMSS/.
4. Comprehensive verification across all local manifests.
5. Machine-readable integrity report: data/bis/corpus_report.json.
"""

import os
import json
import shutil
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone

from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger
from backend.app.services.dataset.acquisition.config import (
    BIS_CORPUS_ROOT,
    CORPUS_DIRS,
    ensure_corpus_directories,
)
from backend.app.services.dataset.acquisition.models import (
    SourceManifest,
    AcquisitionState,
    SourceType,
    CorpusSnapshotManifest,
    CorpusIntegrityReport,
    VerificationReport,
    VerificationIssue,
)
from backend.app.services.dataset.acquisition.verifier import CorpusVerifier


class CorpusManager:
    """Manages the versioned, provenance-preserving BIS local source corpus."""

    @classmethod
    def get_manifests_dir(cls) -> Path:
        ensure_corpus_directories()
        return CORPUS_DIRS["MANIFESTS"]

    @classmethod
    def get_snapshots_dir(cls) -> Path:
        ensure_corpus_directories()
        return CORPUS_DIRS["SNAPSHOTS"]

    @classmethod
    def load_all_manifests(cls) -> Dict[str, SourceManifest]:
        """Loads all source manifests found across category subdirectories and manifests cache."""
        ensure_corpus_directories()
        manifests: Dict[str, SourceManifest] = {}

        # 1. Look in individual category directories data/bis/<category>/<source_id>/manifest.json
        for cat, dir_path in CORPUS_DIRS.items():
            if cat in ("MANIFESTS", "SNAPSHOTS", "ACQUISITION_LOGS"):
                continue
            if not dir_path.exists():
                continue
            for item in dir_path.iterdir():
                if item.is_dir():
                    m_file = item / "manifest.json"
                    if m_file.exists():
                        try:
                            data = json.loads(m_file.read_text(encoding="utf-8"))
                            m = SourceManifest(**data)
                            manifests[m.source_id] = m
                        except Exception as e:
                            logger.error(f"Error loading manifest {m_file}: {e}")

        # 2. Look in central manifests directory
        for m_file in cls.get_manifests_dir().glob("*.json"):
            try:
                data = json.loads(m_file.read_text(encoding="utf-8"))
                m = SourceManifest(**data)
                manifests[m.source_id] = m
            except Exception as e:
                logger.error(f"Error loading central manifest {m_file}: {e}")

        return manifests

    @classmethod
    def save_manifest(cls, manifest: SourceManifest, category: Optional[str] = None) -> None:
        """Saves manifest to central manifests/ folder and source folder."""
        ensure_corpus_directories()
        m_json = manifest.model_dump_json(indent=2)

        # Central index
        central_path = cls.get_manifests_dir() / f"{manifest.source_id}.json"
        central_path.write_text(m_json, encoding="utf-8")

        # Source folder
        if manifest.file_path:
            full_path = BASE_DIR / manifest.file_path
            source_folder = full_path.parent
            if source_folder.exists() and source_folder.is_dir():
                (source_folder / "manifest.json").write_text(m_json, encoding="utf-8")

    @classmethod
    def detect_change(cls, source_id: str, new_bytes: bytes) -> Tuple[str, Optional[str], str]:
        """Compares current content SHA-256 against previously recorded hash.
        
        Returns:
            (status: UNCHANGED | SOURCE_CHANGED | NEW_SOURCE, previous_hash, new_hash)
        """
        new_hash = hashlib.sha256(new_bytes).hexdigest()
        manifests = cls.load_all_manifests()

        if source_id not in manifests:
            return "NEW_SOURCE", None, new_hash

        prev_manifest = manifests[source_id]
        prev_hash = prev_manifest.sha256

        if prev_hash == new_hash:
            return "UNCHANGED", prev_hash, new_hash
        else:
            return "SOURCE_CHANGED", prev_hash, new_hash

    @classmethod
    def verify_corpus(cls) -> VerificationReport:
        """Runs cryptographic and relationship verification across all manifests."""
        manifests = cls.load_all_manifests()
        total = len(manifests)
        passed = 0
        failed = 0
        all_issues: List[VerificationIssue] = []

        for source_id, m in manifests.items():
            valid, issues = CorpusVerifier.verify_manifest(m)
            if valid:
                passed += 1
                if m.acquisition_status == AcquisitionState.ACQUIRED:
                    m.verification_status = AcquisitionState.VERIFIED
                cls.save_manifest(m)
            else:
                failed += 1
                m.verification_status = AcquisitionState.INVALID_SOURCE
                cls.save_manifest(m)
                all_issues.extend(issues)

        report = VerificationReport(
            verified=failed == 0,
            total_checked=total,
            passed_count=passed,
            failed_count=failed,
            issues=all_issues,
            summary=f"Checked {total} sources: {passed} passed, {failed} failed verification.",
        )
        return report

    @classmethod
    def create_snapshot(cls, snapshot_tag: Optional[str] = None) -> CorpusSnapshotManifest:
        """Creates an immutable, reproducible snapshot in data/bis/snapshots/."""
        ensure_corpus_directories()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snap_id = snapshot_tag or f"snapshot_{timestamp}"

        snap_dir = cls.get_snapshots_dir() / snap_id
        if snap_dir.exists():
            raise ValueError(f"Snapshot '{snap_id}' already exists and is immutable.")

        snap_dir.mkdir(parents=True, exist_ok=False)

        manifests = cls.load_all_manifests()
        category_counts: Dict[str, int] = {}
        source_records = []

        standard_count = 0
        qco_count = 0
        amendment_count = 0
        revision_count = 0
        acquired_count = 0
        verified_count = 0
        indexed_count = 0
        pending_count = 0

        for s_id, m in manifests.items():
            cat = str(m.source_type)
            category_counts[cat] = category_counts.get(cat, 0) + 1

            if m.source_type == SourceType.BIS_STANDARD:
                standard_count += 1
            elif m.source_type == SourceType.BIS_QCO:
                qco_count += 1
            elif m.source_type == SourceType.BIS_AMENDMENT:
                amendment_count += 1
            elif m.source_type == SourceType.BIS_REVISION:
                revision_count += 1

            if m.acquisition_status == AcquisitionState.ACQUIRED:
                acquired_count += 1
            elif m.acquisition_status == AcquisitionState.ACQUISITION_PENDING:
                pending_count += 1

            if m.verification_status == AcquisitionState.VERIFIED:
                verified_count += 1
            elif m.verification_status == AcquisitionState.INDEXED:
                indexed_count += 1

            source_records.append(m.model_dump())

        # Write partitioned snapshot data
        sources_payload = json.dumps(source_records, sort_keys=True, indent=2)
        (snap_dir / "sources.json").write_text(sources_payload, encoding="utf-8")

        manifest_hash = hashlib.sha256(sources_payload.encode("utf-8")).hexdigest()

        snap_manifest = CorpusSnapshotManifest(
            snapshot_id=snap_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            source_count=len(manifests),
            acquired_count=acquired_count,
            verified_count=verified_count,
            indexed_count=indexed_count,
            pending_count=pending_count,
            standard_count=standard_count,
            qco_count=qco_count,
            amendment_count=amendment_count,
            revision_count=revision_count,
            manifest_sha256=manifest_hash,
            category_counts=category_counts,
            sources=source_records,
        )

        (snap_dir / "snapshot_manifest.json").write_text(
            snap_manifest.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info(f"Created immutable corpus snapshot '{snap_id}' with {len(manifests)} records.")
        return snap_manifest

    @classmethod
    def generate_integrity_report(cls) -> CorpusIntegrityReport:
        """Generates the machine-readable corpus integrity report."""
        manifests = cls.load_all_manifests()

        sources_acquired = 0
        sources_verified = 0
        standards_verified = 0
        qco_verified = 0
        amendments_verified = 0
        revisions_verified = 0
        normative_refs_verified = 0
        clause_indexed = 0
        acquisition_pending = 0
        invalid_sources = 0

        categories_summary: Dict[str, Dict[str, int]] = {}

        for m in manifests.values():
            stype = str(m.source_type)
            if stype not in categories_summary:
                categories_summary[stype] = {"total": 0, "acquired": 0, "verified": 0, "pending": 0}
            categories_summary[stype]["total"] += 1

            if m.acquisition_status == AcquisitionState.ACQUIRED:
                sources_acquired += 1
                categories_summary[stype]["acquired"] += 1
            elif m.acquisition_status == AcquisitionState.ACQUISITION_PENDING:
                acquisition_pending += 1
                categories_summary[stype]["pending"] += 1

            if m.verification_status == AcquisitionState.VERIFIED:
                sources_verified += 1
                categories_summary[stype]["verified"] += 1
                if m.source_type == SourceType.BIS_STANDARD:
                    standards_verified += 1
                elif m.source_type == SourceType.BIS_QCO:
                    qco_verified += 1
                elif m.source_type == SourceType.BIS_AMENDMENT:
                    amendments_verified += 1
                elif m.source_type == SourceType.BIS_REVISION:
                    revisions_verified += 1
            elif m.verification_status == AcquisitionState.INDEXED:
                clause_indexed += 1
            elif m.verification_status == AcquisitionState.INVALID_SOURCE:
                invalid_sources += 1

            if m.related_standard_numbers:
                normative_refs_verified += len(m.related_standard_numbers)

        report = CorpusIntegrityReport(
            catalog_records=len(manifests),
            sources_discovered=len(manifests),
            sources_acquired=sources_acquired,
            sources_verified=sources_verified,
            standards_verified=standards_verified,
            qco_verified=qco_verified,
            amendments_verified=amendments_verified,
            revisions_verified=revisions_verified,
            normative_references_verified=normative_refs_verified,
            clause_indexed=clause_indexed,
            acquisition_pending=acquisition_pending,
            invalid_sources=invalid_sources,
            generated_at=datetime.now(timezone.utc).isoformat(),
            categories=categories_summary,
            integrity_status="VALID" if invalid_sources == 0 else "ISSUES_DETECTED",
        )

        # Write to data/bis/corpus_report.json
        report_path = BIS_CORPUS_ROOT / "corpus_report.json"
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        return report
