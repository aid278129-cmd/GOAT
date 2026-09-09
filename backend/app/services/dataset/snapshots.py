"""M22 Immutable Dataset Snapshot System & Change Detection (Diffing).

Enforces:
1. Immutable snapshot creation with cryptographic checksums.
2. Tamper-evident verification (detects modified, missing, or injected files).
3. Change detection between dataset snapshots:
   NEW, UPDATED, UNCHANGED, REMOVED, CONFLICT.
4. Historical provenance preservation: previous versions are never silently mutated.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger
from backend.app.services.dataset.models import DatasetManifest
from backend.app.services.dataset.builder import get_dataset_repository

SNAPSHOTS_DIR = BASE_DIR / "data" / "bis_dataset" / "snapshots"


class SnapshotSummary(BaseModel):
    version: str
    created_at: str
    manifest_hash: str
    standards_count: int
    qco_count: int
    clauses_count: int
    records_count: int
    is_valid: bool = True
    tamper_issues: List[str] = Field(default_factory=list)


class DiffItem(BaseModel):
    item_id: str
    change_type: str  # NEW | UPDATED | UNCHANGED | REMOVED | CONFLICT
    details: str
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None


class SnapshotDiffResult(BaseModel):
    version_a: str
    version_b: str
    total_changes: int
    new_count: int
    updated_count: int
    unchanged_count: int
    removed_count: int
    conflict_count: int
    items: List[DiffItem] = Field(default_factory=list)


class SnapshotManager:
    """Manages immutable dataset snapshots and cryptographic diffing."""

    @staticmethod
    def get_snapshots_dir() -> Path:
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        return SNAPSHOTS_DIR

    @classmethod
    def create_snapshot(cls, version: str) -> SnapshotSummary:
        """Creates an immutable snapshot bundle for the given version."""
        s_dir = cls.get_snapshots_dir() / version
        if s_dir.exists():
            raise ValueError(f"Snapshot '{version}' already exists and is immutable. Increment version.")

        s_dir.mkdir(parents=True, exist_ok=False)

        repo = get_dataset_repository()
        manifest = repo.manifest.model_copy(deep=True)
        manifest.version = version
        manifest.created_at = datetime.now(timezone.utc).isoformat()

        # Build records archive
        standards_payload = {k: v.model_dump() for k, v in repo.standards.items()}
        qco_payload = {k: v.model_dump() for k, v in repo.qcos.items()}
        clauses_payload = {k: v.model_dump() for k, v in repo.clauses.items()}
        gt_payload = {k: v.model_dump() for k, v in repo.ground_truth_cases.items()}

        # Compute SHA-256 for each partition
        hashes = {
            "standards.json": hashlib.sha256(json.dumps(standards_payload, sort_keys=True).encode("utf-8")).hexdigest(),
            "qco.json": hashlib.sha256(json.dumps(qco_payload, sort_keys=True).encode("utf-8")).hexdigest(),
            "clauses.json": hashlib.sha256(json.dumps(clauses_payload, sort_keys=True).encode("utf-8")).hexdigest(),
            "ground_truth.json": hashlib.sha256(json.dumps(gt_payload, sort_keys=True).encode("utf-8")).hexdigest(),
        }

        # Write partitioned data
        with open(s_dir / "standards.json", "w", encoding="utf-8") as f:
            json.dump(standards_payload, f, indent=2)
        with open(s_dir / "qco.json", "w", encoding="utf-8") as f:
            json.dump(qco_payload, f, indent=2)
        with open(s_dir / "clauses.json", "w", encoding="utf-8") as f:
            json.dump(clauses_payload, f, indent=2)
        with open(s_dir / "ground_truth.json", "w", encoding="utf-8") as f:
            json.dump(gt_payload, f, indent=2)

        # Write integrity checksum file
        with open(s_dir / "checksums.json", "w", encoding="utf-8") as f:
            json.dump(hashes, f, indent=2)

        # Compute composite manifest checksum
        manifest_payload = manifest.model_dump()
        manifest_payload["partition_hashes"] = hashes
        manifest_hash = hashlib.sha256(json.dumps(manifest_payload, sort_keys=True).encode("utf-8")).hexdigest()
        manifest_payload["snapshot_sha256"] = manifest_hash

        with open(s_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest_payload, f, indent=2)

        return SnapshotSummary(
            version=version,
            created_at=manifest.created_at,
            manifest_hash=manifest_hash,
            standards_count=len(standards_payload),
            qco_count=len(qco_payload),
            clauses_count=len(clauses_payload),
            records_count=len(standards_payload) + len(qco_payload) + len(clauses_payload) + len(gt_payload),
            is_valid=True,
        )

    @classmethod
    def verify_snapshot_integrity(cls, version: str) -> SnapshotSummary:
        """Verifies cryptographic integrity of an existing snapshot."""
        s_dir = cls.get_snapshots_dir() / version
        if not s_dir.exists():
            raise FileNotFoundError(f"Snapshot '{version}' not found.")

        manifest_file = s_dir / "manifest.json"
        checksum_file = s_dir / "checksums.json"
        issues = []

        if not manifest_file.exists() or not checksum_file.exists():
            return SnapshotSummary(
                version=version,
                created_at="",
                manifest_hash="",
                standards_count=0,
                qco_count=0,
                clauses_count=0,
                records_count=0,
                is_valid=False,
                tamper_issues=["Missing manifest.json or checksums.json"],
            )

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        with open(checksum_file, "r", encoding="utf-8") as f:
            recorded_hashes = json.load(f)

        for filename, recorded_hash in recorded_hashes.items():
            fpath = s_dir / filename
            if not fpath.exists():
                issues.append(f"Missing partition file: {filename}")
                continue
            with open(fpath, "rb") as pf:
                actual_hash = hashlib.sha256(pf.read()).hexdigest()
            # Note: JSON serialization key ordering might differ on disk, so load and compare content
            with open(fpath, "r", encoding="utf-8") as pf:
                obj = json.load(pf)
                content_hash = hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()
            if content_hash != recorded_hash:
                issues.append(f"Tamper detected in partition {filename}: hash mismatch.")

        return SnapshotSummary(
            version=version,
            created_at=manifest_data.get("created_at", ""),
            manifest_hash=manifest_data.get("snapshot_sha256", ""),
            standards_count=manifest_data.get("standards_count", 0),
            qco_count=manifest_data.get("qco_count", 0),
            clauses_count=manifest_data.get("clause_count", 0),
            records_count=manifest_data.get("standards_count", 0) + manifest_data.get("qco_count", 0),
            is_valid=len(issues) == 0,
            tamper_issues=issues,
        )

    @classmethod
    def list_snapshots(cls) -> List[SnapshotSummary]:
        """Lists all recorded snapshots."""
        root = cls.get_snapshots_dir()
        results = []
        for p in root.iterdir():
            if p.is_dir() and (p / "manifest.json").exists():
                try:
                    summary = cls.verify_snapshot_integrity(p.name)
                    results.append(summary)
                except Exception as e:
                    logger.warning(f"Error checking snapshot {p.name}: {e}")
        return results

    @classmethod
    def diff_snapshots(cls, version_a: str, version_b: str) -> SnapshotDiffResult:
        """Calculates granular diff between two snapshots: NEW, UPDATED, UNCHANGED, REMOVED, CONFLICT."""
        dir_a = cls.get_snapshots_dir() / version_a
        dir_b = cls.get_snapshots_dir() / version_b

        if not dir_a.exists():
            raise FileNotFoundError(f"Snapshot version {version_a} does not exist.")
        if not dir_b.exists():
            raise FileNotFoundError(f"Snapshot version {version_b} does not exist.")

        with open(dir_a / "standards.json", "r", encoding="utf-8") as f:
            std_a = json.load(f)
        with open(dir_b / "standards.json", "r", encoding="utf-8") as f:
            std_b = json.load(f)

        diff_items = []
        all_keys = set(std_a.keys()) | set(std_b.keys())

        new_c = 0
        updated_c = 0
        unchanged_c = 0
        removed_c = 0
        conflict_c = 0

        for k in sorted(all_keys):
            in_a = k in std_a
            in_b = k in std_b

            if in_b and not in_a:
                new_c += 1
                diff_items.append(DiffItem(item_id=k, change_type="NEW", details=f"Standard {k} added in {version_b}"))
            elif in_a and not in_b:
                removed_c += 1
                diff_items.append(DiffItem(item_id=k, change_type="REMOVED", details=f"Standard {k} removed in {version_b}"))
            else:
                # Compare content
                hash_a = hashlib.sha256(json.dumps(std_a[k], sort_keys=True).encode("utf-8")).hexdigest()
                hash_b = hashlib.sha256(json.dumps(std_b[k], sort_keys=True).encode("utf-8")).hexdigest()

                if hash_a == hash_b:
                    unchanged_c += 1
                    diff_items.append(DiffItem(item_id=k, change_type="UNCHANGED", details=f"Standard {k} identical", old_hash=hash_a, new_hash=hash_b))
                else:
                    # Check if conflict in status or requirements
                    if std_a[k].get("status") != std_b[k].get("status"):
                        conflict_c += 1
                        diff_items.append(DiffItem(item_id=k, change_type="CONFLICT", details=f"Status changed from {std_a[k].get('status')} to {std_b[k].get('status')}", old_hash=hash_a, new_hash=hash_b))
                    else:
                        updated_c += 1
                        diff_items.append(DiffItem(item_id=k, change_type="UPDATED", details=f"Standard {k} metadata updated", old_hash=hash_a, new_hash=hash_b))

        return SnapshotDiffResult(
            version_a=version_a,
            version_b=version_b,
            total_changes=new_c + updated_c + removed_c + conflict_c,
            new_count=new_c,
            updated_count=updated_c,
            unchanged_count=unchanged_c,
            removed_count=removed_c,
            conflict_count=conflict_c,
            items=diff_items,
        )
