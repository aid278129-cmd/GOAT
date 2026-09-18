"""Cryptographic integrity and canonical manifest services for Phase 5 Regulatory Dossier."""

import json
import hashlib
from typing import Dict, Any, List, Optional


def canonicalize_json(data: Any) -> str:
    """
    Produce canonical deterministic JSON string representation:
    - Sorted dictionary keys
    - Compact separators (',', ':')
    - UTF-8 safe
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_sha256(content: str | bytes) -> str:
    """Compute SHA-256 hex digest for string or byte content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def compute_evidence_manifest_digest(evidence_items: List[Dict[str, Any]]) -> str:
    """
    Compute deterministic SHA-256 digest of accepted and supporting evidence manifest.
    Each item is projected to stable canonical fields: id, sha256_hash, file_name, acceptance_status.
    """
    projected = []
    for ev in sorted(evidence_items, key=lambda x: str(x.get("id", ""))):
        projected.append({
            "id": str(ev.get("id", "")),
            "file_name": str(ev.get("file_name", "")),
            "sha256_hash": str(ev.get("sha256_hash", "")),
            "acceptance_status": str(ev.get("acceptance_status", "")),
            "evidence_type": str(ev.get("file_type", ev.get("evidence_type", ""))),
        })
    canonical_str = canonicalize_json(projected)
    return compute_sha256(canonical_str)


def compute_product_dna_digest(dna_parameters: List[Dict[str, Any]]) -> str:
    """
    Compute deterministic SHA-256 digest of Product DNA snapshot.
    Each parameter is projected to stable canonical fields: category, parameter, value, unit, status.
    """
    projected = []
    for dna in sorted(dna_parameters, key=lambda x: (str(x.get("category", "")), str(x.get("parameter", "")))):
        projected.append({
            "category": str(dna.get("category", "")),
            "parameter": str(dna.get("parameter", "")),
            "value": str(dna.get("value", "")),
            "unit": str(dna.get("unit", "") or ""),
            "status": str(dna.get("status", "")),
            "extraction_method": str(dna.get("extraction_method", "") or ""),
        })
    canonical_str = canonicalize_json(projected)
    return compute_sha256(canonical_str)


def compute_finding_digest(findings: List[Dict[str, Any]]) -> str:
    """
    Compute deterministic SHA-256 digest of compliance findings register.
    Each finding projected to: id, severity, status, requirement_id.
    """
    projected = []
    for f in sorted(findings, key=lambda x: str(x.get("id", ""))):
        projected.append({
            "id": str(f.get("id", "")),
            "severity": str(f.get("severity", "")),
            "status": str(f.get("status", "")),
            "requirement_id": str(f.get("requirement_id", "") or ""),
            "description": str(f.get("description", "")),
        })
    canonical_str = canonicalize_json(projected)
    return compute_sha256(canonical_str)


def create_canonical_manifest(
    dossier_id: str,
    version: int,
    job_id: str,
    assessment_run_id: Optional[str],
    standard_revisions: List[str],
    evidence_manifest_digest: str,
    product_dna_digest: str,
    finding_digest: str,
    attestation_ids: List[str],
    generated_at_iso: str,
    application_version: str = "v5.0-production",
) -> Dict[str, Any]:
    """Create the canonical master manifest dictionary."""
    return {
        "dossier_id": dossier_id,
        "version": version,
        "job_id": job_id,
        "assessment_run_id": assessment_run_id or "NONE",
        "standard_revisions": sorted(standard_revisions),
        "evidence_manifest_digest": evidence_manifest_digest,
        "product_dna_digest": product_dna_digest,
        "finding_digest": finding_digest,
        "attestation_ids": sorted(attestation_ids),
        "generated_at": generated_at_iso,
        "application_version": application_version,
    }


def compute_dossier_digest(manifest: Dict[str, Any]) -> str:
    """Compute canonical SHA-256 digest of the master dossier manifest."""
    canonical_str = canonicalize_json(manifest)
    return compute_sha256(canonical_str)
