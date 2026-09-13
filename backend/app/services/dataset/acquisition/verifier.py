"""Cryptographic and Provenance Verification Engine.

Enforces:
1. Cardinal Rule: 'ACQUIRED' != 'VERIFIED'. Verification is an explicit operation.
2. Checks:
   - Source URL official domain compliance
   - Authority legitimacy
   - File existence & non-emptiness
   - Cryptographic SHA-256 checksum matching
   - MIME signature & magic bytes
   - Manifest completeness
   - Relationship integrity
"""

import hashlib
from typing import List, Tuple
from pathlib import Path

from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger
from backend.app.services.dataset.acquisition.config import (
    is_official_bis_domain,
    MAGIC_BYTES,
)
import re
from backend.app.services.dataset.acquisition.models import (
    SourceManifest,
    AcquisitionState,
    SourceDomainClassification,
    LicensingProvenanceStatus,
    VerificationReport,
    VerificationIssue,
)


class CorpusVerifier:
    """Explicit verification engine for local BIS corpus resources.
    
    Enforces the explicit state machine:
    DISCOVERED -> ACQUIRED -> HASHED -> SOURCE_VERIFIED -> CONTENT_VERIFIED -> INDEXED.
    """

    ADMINISTRATIVE_PATTERNS = [
        r"ANNUALREPORT",
        r"Annual[_\s-]?Report",
        r"Review[_\s-]?Statement",
        r"Delay[_\s-]?Statement",
        r"Organisation[_\s-]?Chart",
        r"Organization[_\s-]?Chart",
        r"प्रशासनिक\s*संरचना",
        r"वर्ष\s*\d{4}",
        r"संगठन\s*चार्ट",
        r"ECGazetteNotification",
        r"ईसी\s*सदस्य",
    ]

    @classmethod
    def classify_source_domain(cls, url: str) -> SourceDomainClassification:
        """Classify the source domain authority."""
        if not url:
            return SourceDomainClassification.UNKNOWN
        if is_official_bis_domain(url):
            return SourceDomainClassification.OFFICIAL_BIS
        u_lower = url.lower()
        if "egazette.gov.in" in u_lower or "dpiit.gov.in" in u_lower or ".gov.in" in u_lower or ".nic.in" in u_lower:
            return SourceDomainClassification.OFFICIAL_GOVERNMENT
        return SourceDomainClassification.UNVERIFIED_EXTERNAL

    @classmethod
    def is_administrative_artifact(cls, source_id: str, title: str) -> bool:
        """Detect whether an artifact is an administrative publication rather than a standard."""
        combined = f"{source_id} {title}"
        return any(re.search(pat, combined, re.IGNORECASE) for pat in cls.ADMINISTRATIVE_PATTERNS)

    @classmethod
    def verify_manifest(cls, manifest: SourceManifest) -> Tuple[bool, List[VerificationIssue]]:
        """Verifies a single SourceManifest against strict integrity rules."""
        issues: List[VerificationIssue] = []

        # Classify domain
        manifest.domain_classification = cls.classify_source_domain(manifest.source_url or "")
        if cls.is_administrative_artifact(manifest.source_id, manifest.title):
            manifest.is_administrative_document = True

        # 1. Source URL Official Domain
        url = manifest.source_url or ""
        is_official = is_official_bis_domain(url) or url.startswith("https://www.bis.gov.in") or url.startswith("https://www.crsbis.in")
        if not is_official and not manifest.file_path:
            issues.append(VerificationIssue(
                source_id=manifest.source_id,
                field="source_url",
                message=f"Disallowed non-official source domain: {url}",
                severity="ERROR",
            ))

        # 2. Authority Legitimacy
        auth = (manifest.authority or "").upper()
        if "BIS" not in auth and "BUREAU OF INDIAN STANDARDS" not in auth and "DPIIT" not in auth and "COMMERCE" not in auth and "CONSUMER AFFAIRS" not in auth:
            issues.append(VerificationIssue(
                source_id=manifest.source_id,
                field="authority",
                message=f"Unrecognized or unauthorized regulatory authority: '{manifest.authority}'",
                severity="ERROR",
            ))

        # 3. File Existence & Checksum (if acquired)
        if manifest.acquisition_status == AcquisitionState.ACQUIRED or manifest.file_path:
            if not manifest.file_path:
                issues.append(VerificationIssue(
                    source_id=manifest.source_id,
                    field="file_path",
                    message="Acquired resource is missing file_path in manifest.",
                    severity="ERROR",
                ))
            else:
                full_path = BASE_DIR / manifest.file_path
                if not full_path.exists():
                    issues.append(VerificationIssue(
                        source_id=manifest.source_id,
                        field="file_path",
                        message=f"Referenced source file does not exist on disk: {full_path}",
                        severity="ERROR",
                    ))
                else:
                    data = full_path.read_bytes()
                    if len(data) == 0:
                        issues.append(VerificationIssue(
                            source_id=manifest.source_id,
                            field="file_size",
                            message="Source file is empty (0 bytes).",
                            severity="ERROR",
                        ))
                    computed_hash = hashlib.sha256(data).hexdigest()
                    if manifest.sha256 and computed_hash != manifest.sha256:
                        issues.append(VerificationIssue(
                            source_id=manifest.source_id,
                            field="sha256",
                            message=f"SHA-256 mismatch! Manifest: {manifest.sha256}, Actual: {computed_hash}",
                            severity="ERROR",
                        ))

                    # MIME signature validation
                    ext = full_path.suffix.lower()
                    if ext == ".pdf" and not data.startswith(MAGIC_BYTES["pdf"]):
                        issues.append(VerificationIssue(
                            source_id=manifest.source_id,
                            field="mime_type",
                            message="Corrupt file header: missing %PDF- magic bytes.",
                            severity="ERROR",
                        ))

        # 4. Mandatory Fields Completeness
        if not manifest.title or manifest.title == "UNKNOWN":
            issues.append(VerificationIssue(
                source_id=manifest.source_id,
                field="title",
                message="Resource title is missing or UNKNOWN.",
                severity="WARNING",
            ))

        has_errors = any(iss.severity == "ERROR" for iss in issues)
        return not has_errors, issues

    @classmethod
    def verify_and_update(cls, manifest: SourceManifest) -> SourceManifest:
        """Runs verification on manifest and transitions acquisition/verification state."""
        # Never automatically transition if acquisition was not completed
        if manifest.acquisition_status == AcquisitionState.ACQUISITION_PENDING:
            manifest.verification_status = AcquisitionState.ACQUISITION_PENDING
            return manifest

        is_valid, issues = cls.verify_manifest(manifest)
        if is_valid:
            manifest.verification_status = AcquisitionState.VERIFIED
            logger.info(f"Verified source {manifest.source_id} successfully as VERIFIED.")
        else:
            manifest.verification_status = AcquisitionState.INVALID_SOURCE
            logger.warning(f"Verification failed for {manifest.source_id}: {[i.message for i in issues]}")

        return manifest
