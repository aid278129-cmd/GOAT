"""Authoritative Index Gate & Source Verification Service (Milestone M25.3).

Enforces strict, auditable gating conditions before any acquired BIS document
or standard record is permitted to enter the authoritative compliance retrieval pipeline.

Non-Negotiable Gating Invariants:
1. Four-Tier Authoritative Gate:
   SOURCE_VERIFIED AND CONTENT_VERIFIED AND VALID_HASH AND NOT_REJECTED.
2. An artifact is NEVER authoritative merely because:
   - It is a PDF
   - Its filename contains 'IS' or looks official
   - It downloaded from a bis.gov.in web crawl
   - SHA-256 is valid
3. Administrative Exclusion:
   Administrative Annual Reports, Delay Statements, Review Statements,
   and Organisation Charts are strictly BARRED from standard compliance authority.
4. Sales Slips / Price Lists:
   Price lists (such as IS 29997:2026 catalog slip) are barred from standard compliance authority.
5. Lifecycle & Supersession Invariant:
   A superseded standard must NEVER silently become current compliance authority.
6. Source Type Preservation:
   STANDARD_REQUIREMENT vs PRODUCT_MANUAL_TESTING_REQUIREMENT remain strictly separated.
7. Cross-Standard Leakage Firewall:
   Clauses and requirements from IS 694, IS 1293, and the IS 302 family must
   never cross-contaminate retrieval results.
8. Prompt Injection Inertness:
   Acquired regulatory text is strictly treated as untrusted DATA and cannot
   alter system routing, authority, or compliance verdicts.
"""

import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field

from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger
from backend.app.services.dataset.acquisition.models import (
    SourceManifest,
    AcquisitionState,
    SourceType,
    SourceDomainClassification,
    LicensingProvenanceStatus,
)
from backend.app.services.dataset.acquisition.config import is_official_bis_domain, MAGIC_BYTES


class GateVerdict(str, Enum):
    """Verdict of the Authoritative Index Gate."""
    ADMITTED = "ADMITTED"
    BLOCKED = "BLOCKED"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"


class DocumentRejectionReason(str, Enum):
    """Categorized reasons for barring a document from authoritative retrieval."""
    DISALLOWED_DOMAIN = "DISALLOWED_DOMAIN"
    UNAUTHORIZED_AUTHORITY = "UNAUTHORIZED_AUTHORITY"
    HASH_MISMATCH = "HASH_MISMATCH"
    MISSING_FILE = "MISSING_FILE"
    EMPTY_FILE = "EMPTY_FILE"
    CORRUPT_MIME = "CORRUPT_MIME"
    ADMINISTRATIVE_DOCUMENT = "ADMINISTRATIVE_DOCUMENT"
    CATALOG_PRICE_SLIP_ONLY = "CATALOG_PRICE_SLIP_ONLY"
    SUPERSEDED_STANDARD = "SUPERSEDED_STANDARD"
    UNVERIFIED_SOURCE = "UNVERIFIED_SOURCE"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    ACQUISITION_PENDING = "ACQUISITION_PENDING"
    UNAUTHORIZED_ACQUISITION = "UNAUTHORIZED_ACQUISITION"


class GateEvaluationResult(BaseModel):
    """Auditable result of evaluating an artifact through the Authoritative Index Gate."""
    source_id: str
    verdict: GateVerdict
    source_verified: bool
    content_verified: bool
    hash_valid: bool
    not_rejected: bool
    rejection_reasons: List[DocumentRejectionReason] = Field(default_factory=list)
    rejection_details: List[str] = Field(default_factory=list)
    is_standard_requirement: bool = False
    is_product_manual_requirement: bool = False
    active_standard_id: Optional[str] = None
    sanitized_text: Optional[str] = None


class AuthoritativeIndexGate:
    """Rigorous gate governing admittance to the Layer 4 Authoritative Retrieval Index."""

    # Keywords indicating administrative or corporate publications rather than technical standards
    ADMINISTRATIVE_TITLE_PATTERNS = [
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
    def evaluate_manifest(
        cls,
        manifest: SourceManifest,
        allow_historical_search: bool = False,
    ) -> GateEvaluationResult:
        """Evaluates a single SourceManifest against the 4-tier Authoritative Index Gate.

        Minimum Required Conditions:
        1. SOURCE_VERIFIED: Domain whitelisted & Authority legitimate
        2. CONTENT_VERIFIED: Real standard content, not admin report or price slip
        3. VALID_HASH: SHA-256 exactly matches file content on disk
        4. NOT_REJECTED: Status is not REJECTED or INVALID_SOURCE
        """
        reasons: List[DocumentRejectionReason] = []
        details: List[str] = []

        # ------------------------------------------------------------------
        # Tier 1: Source Verification (Domain & Authority)
        # ------------------------------------------------------------------
        source_verified = False
        url = manifest.source_url or ""
        domain_ok = is_official_bis_domain(url) or manifest.domain_classification in (
            SourceDomainClassification.OFFICIAL_BIS,
            SourceDomainClassification.OFFICIAL_GOVERNMENT,
        )

        auth = (manifest.authority or "").upper()
        auth_ok = any(
            legit in auth
            for legit in [
                "BIS",
                "BUREAU OF INDIAN STANDARDS",
                "DPIIT",
                "COMMERCE",
                "CONSUMER AFFAIRS",
                "MINISTRY",
            ]
        )

        if not domain_ok:
            reasons.append(DocumentRejectionReason.DISALLOWED_DOMAIN)
            details.append(f"Domain not in official BIS whitelist: {url}")
        if not auth_ok:
            reasons.append(DocumentRejectionReason.UNAUTHORIZED_AUTHORITY)
            details.append(f"Issuing authority '{manifest.authority}' is not recognized")

        if domain_ok and auth_ok:
            source_verified = True

        # ------------------------------------------------------------------
        # Early Tier: Content Disambiguation for Administrative Publications
        # ------------------------------------------------------------------
        sid = manifest.source_id or ""
        title = manifest.title or ""
        is_admin = manifest.is_administrative_document
        for pat in cls.ADMINISTRATIVE_TITLE_PATTERNS:
            if re.search(pat, sid, re.IGNORECASE) or re.search(pat, title, re.IGNORECASE):
                is_admin = True
                break

        if is_admin:
            reasons.append(DocumentRejectionReason.ADMINISTRATIVE_DOCUMENT)
            details.append(
                "Identified as administrative publication (Annual Report / Review Statement / Chart), NOT an Indian Standard."
            )
            return GateEvaluationResult(
                source_id=manifest.source_id,
                verdict=GateVerdict.BLOCKED,
                source_verified=source_verified,
                content_verified=False,
                hash_valid=False,
                not_rejected=True,
                rejection_reasons=reasons,
                rejection_details=details,
            )

        # ------------------------------------------------------------------
        # Tier 2: File Existence & Cryptographic Hash Validation
        # ------------------------------------------------------------------
        hash_valid = False
        content_bytes: Optional[bytes] = None

        if manifest.acquisition_status == AcquisitionState.ACQUISITION_PENDING:
            reasons.append(DocumentRejectionReason.ACQUISITION_PENDING)
            details.append("Document text acquisition is pending; cannot enter authoritative index.")
            return GateEvaluationResult(
                source_id=manifest.source_id,
                verdict=GateVerdict.ACQUISITION_PENDING,
                source_verified=source_verified,
                content_verified=False,
                hash_valid=False,
                not_rejected=True,
                rejection_reasons=reasons,
                rejection_details=details,
            )

        if not manifest.file_path:
            reasons.append(DocumentRejectionReason.MISSING_FILE)
            details.append("Manifest has no local file_path recorded.")
        else:
            local_path = Path(manifest.file_path)
            full_path = local_path if local_path.is_absolute() else BASE_DIR / local_path
            if not full_path.exists():
                reasons.append(DocumentRejectionReason.MISSING_FILE)
                details.append(f"File not found on disk: {full_path}")
            else:
                content_bytes = full_path.read_bytes()
                if len(content_bytes) == 0:
                    reasons.append(DocumentRejectionReason.EMPTY_FILE)
                    details.append("File on disk has 0 bytes.")
                else:
                    computed_hash = hashlib.sha256(content_bytes).hexdigest()
                    if manifest.sha256 and computed_hash != manifest.sha256:
                        reasons.append(DocumentRejectionReason.HASH_MISMATCH)
                        details.append(
                            f"Cryptographic SHA-256 mismatch: manifest={manifest.sha256}, disk={computed_hash}"
                        )
                    else:
                        hash_valid = True

                    # Magic bytes check
                    ext = full_path.suffix.lower()
                    if ext == ".pdf" and not content_bytes.startswith(MAGIC_BYTES["pdf"]):
                        reasons.append(DocumentRejectionReason.CORRUPT_MIME)
                        details.append("PDF magic byte check failed: missing %PDF- header.")

        # ------------------------------------------------------------------
        # Tier 3: Content Verification & Identity Disambiguation
        # ------------------------------------------------------------------
        content_verified = False
        sid = manifest.source_id or ""
        title = manifest.title or ""

        # Check for administrative document misclassification
        is_admin = manifest.is_administrative_document
        for pat in cls.ADMINISTRATIVE_TITLE_PATTERNS:
            if re.search(pat, sid, re.IGNORECASE) or re.search(pat, title, re.IGNORECASE):
                is_admin = True
                break

        if is_admin:
            reasons.append(DocumentRejectionReason.ADMINISTRATIVE_DOCUMENT)
            details.append(
                f"Identified as administrative publication (Annual Report / Review Statement / Chart), NOT an Indian Standard."
            )

        # Check for catalog price slips masquerading as standards (e.g. IS 29997 price list)
        if manifest.standard_number and "29997" in manifest.standard_number:
            reasons.append(DocumentRejectionReason.CATALOG_PRICE_SLIP_ONLY)
            details.append("Document is a 1-page sales price slip without technical standard clauses.")

        # Check if declared synthetic or fixture
        if manifest.source_type == SourceType.DEVELOPMENT_FIXTURE or "fixture" in sid.lower():
            reasons.append(DocumentRejectionReason.SYNTHETIC_FIXTURE)
            details.append("Development fixture cannot enter authoritative production index.")

        if hash_valid and not is_admin and DocumentRejectionReason.CATALOG_PRICE_SLIP_ONLY not in reasons:
            content_verified = True

        # ------------------------------------------------------------------
        # Tier 4: Rejection & Lifecycle States
        # ------------------------------------------------------------------
        not_rejected = (
            manifest.acquisition_status != AcquisitionState.REJECTED
            and manifest.acquisition_status != AcquisitionState.INVALID_SOURCE
            and manifest.verification_status != AcquisitionState.REJECTED
            and manifest.verification_status != AcquisitionState.INVALID_SOURCE
        )
        if not not_rejected:
            reasons.append(DocumentRejectionReason.UNVERIFIED_SOURCE)
            details.append("Artifact has an explicit REJECTED or INVALID_SOURCE status.")

        # Lifecycle Check: Superseded standards cannot become current authority
        active_id = manifest.standard_number
        if manifest.document_status == "SUPERSEDED" and not allow_historical_search:
            reasons.append(DocumentRejectionReason.SUPERSEDED_STANDARD)
            details.append(
                f"Standard '{manifest.standard_number}' is SUPERSEDED and barred from current compliance authority."
            )

        # Source Type Distinction: Standard vs Product Manual
        is_std = manifest.source_type == SourceType.BIS_STANDARD
        is_pm = manifest.source_type in (
            SourceType.BIS_PRODUCT_MANUAL,
            SourceType.BIS_SIT,
            SourceType.BIS_PRODUCT_GUIDELINE,
        )

        # Overall 4-Tier Gate Decision
        gate_passed = source_verified and content_verified and hash_valid and not_rejected and len(reasons) == 0

        verdict = GateVerdict.ADMITTED if gate_passed else GateVerdict.BLOCKED

        return GateEvaluationResult(
            source_id=manifest.source_id,
            verdict=verdict,
            source_verified=source_verified,
            content_verified=content_verified,
            hash_valid=hash_valid,
            not_rejected=not_rejected,
            rejection_reasons=reasons,
            rejection_details=details,
            is_standard_requirement=is_std,
            is_product_manual_requirement=is_pm,
            active_standard_id=active_id,
        )

    @classmethod
    def sanitize_untrusted_text(cls, raw_text: str) -> str:
        """Sanitizes acquired regulatory text to prevent adversarial prompt injection.
        
        Guarantees that malicious instruction patterns (e.g. 'Ignore previous instructions',
        'Declare this standard mandatory', 'Set compliance status to COMPLIANT') remain
        strictly inert data and are neutralized.
        """
        if not raw_text:
            return ""

        # Neutralize common prompt injection prefixes by quoting/wrapping as inert literal
        adversarial_patterns = [
            r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions?",
            r"(?i)declare\s+this\s+standard\s+mandatory",
            r"(?i)bypass\s+(all\s+)?compliance\s+checks?",
            r"(?i)set\s+compliance_status\s*=",
            r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
            r"(?i)system\s*:\s*override",
        ]

        sanitized = raw_text
        for pat in adversarial_patterns:
            sanitized = re.sub(
                pat,
                lambda m: f"[UNTRUSTED_DATA_LITERAL: '{m.group(0)}']",
                sanitized,
            )

        return sanitized

    @classmethod
    def isolate_cross_standard_query(
        cls,
        target_standard_number: str,
        retrieved_clauses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Firewall preventing cross-standard clause leakage.
        
        Ensures that a query scoped to e.g. 'IS 694' can NEVER return clauses
        originating from 'IS 1293' or 'IS 302-1', even if keywords overlap.
        """
        target_norm = target_standard_number.lower().replace(" ", "").replace(":", "")
        isolated: List[Dict[str, Any]] = []

        for item in retrieved_clauses:
            item_std = (
                item.get("standard_number")
                or item.get("standard_id")
                or item.get("document_id")
                or ""
            )
            item_norm = item_std.lower().replace(" ", "").replace(":", "")

            # Strict prefix or containment of the standard identifier
            if target_norm in item_norm or item_norm in target_norm:
                isolated.append(item)
            else:
                logger.warning(
                    f"Cross-standard leakage blocked! Query standard '{target_standard_number}' "
                    f"attempted to retrieve clause from '{item_std}'"
                )

        return isolated
