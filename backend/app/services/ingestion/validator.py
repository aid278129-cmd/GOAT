"""Multi-Tier Document & Input Pre-Flight Validator.

Enforces production-grade security, structural integrity, and content validation
before multi-modal inputs can enter Layer 2 Product DNA.
"""

import hashlib
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from backend.app.schemas.unified_input import (
    InputMode,
    DocumentValidationResult,
    ValidationIssue,
    ValidationIssueSeverity,
)
from backend.app.core.logging import logger

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

# In-memory registry of uploaded document hashes to detect duplicates
SEEN_DOCUMENT_HASHES: Set[str] = set()

# Known magic bytes signatures
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "wav": b"RIFF",
    "ogg": b"OggS",
    "webm": b"\x1a\x45\xdf\xa3",
}

PLACEHOLDER_PATTERNS = [
    re.compile(r"\[(?:FILL[_\s]HERE|REQUIRED[_\s]VALUE|ENTER[_\s]VALUE|TODO|INSERT[_\s].+?)\]", re.IGNORECASE),
    re.compile(r"<(?:FILL[_\s]HERE|REQUIRED[_\s]VALUE|SPECIFY[_\s].+?)>", re.IGNORECASE),
    re.compile(r"\bTODO:\s*.+", re.IGNORECASE),
]


class DocumentValidator:
    """Rigorous pre-flight validator for Layer 1 inputs."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Strip dangerous path traversal characters and non-printable bytes."""
        if not filename:
            return "unnamed_input"
        clean = os.path.basename(filename).strip()
        # Remove null bytes and directory traversal sequences
        clean = clean.replace("\x00", "").replace("..", "")
        clean = re.sub(r"[^\w\.\-\s]", "_", clean)
        return clean or "unnamed_input"

    @classmethod
    def calculate_sha256(cls, data: bytes) -> str:
        """Compute SHA-256 hash of byte content."""
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def validate_file(
        cls,
        file_bytes: bytes,
        filename: str,
        input_mode: InputMode,
        check_duplicate: bool = True,
    ) -> DocumentValidationResult:
        """Execute full pre-flight validation on raw file bytes."""
        safe_name = cls.sanitize_filename(filename)
        size = len(file_bytes)
        sha256 = cls.calculate_sha256(file_bytes) if size > 0 else ""
        issues: List[ValidationIssue] = []

        # 1. Size Validation
        if size == 0:
            issues.append(
                ValidationIssue(
                    code="EMPTY_FILE",
                    field="file_bytes",
                    severity=ValidationIssueSeverity.ERROR,
                    message=f"Uploaded file '{safe_name}' is empty (0 bytes).",
                    actionable_remediation="Ensure the file is saved properly on your local drive and contains valid data.",
                )
            )
            return DocumentValidationResult(
                is_valid=False,
                input_mode=input_mode,
                filename=safe_name,
                file_size_bytes=0,
                sha256_hash="",
                issues=issues,
                is_empty=True,
            )

        if size > MAX_FILE_SIZE_BYTES:
            issues.append(
                ValidationIssue(
                    code="FILE_TOO_LARGE",
                    field="file_size",
                    severity=ValidationIssueSeverity.ERROR,
                    message=f"File '{safe_name}' ({size / (1024*1024):.2f}MB) exceeds the 25MB regulatory upload limit.",
                    actionable_remediation="Compress the document or split multi-page attachments before uploading.",
                )
            )

        # 2. Magic Bytes Format Validation
        ext = safe_name.lower().split(".")[-1] if "." in safe_name else ""
        detected_format = ext

        if ext == "pdf":
            if not file_bytes.startswith(MAGIC_BYTES["pdf"]):
                issues.append(
                    ValidationIssue(
                        code="INVALID_PDF_HEADER",
                        field="magic_bytes",
                        severity=ValidationIssueSeverity.ERROR,
                        message=f"File '{safe_name}' has .pdf extension but does not contain a valid %PDF header.",
                        actionable_remediation="Check if the file is corrupted or was incorrectly renamed. Export standard PDF directly from viewer.",
                    )
                )
        elif ext in ("png", "jpg", "jpeg"):
            if ext == "png" and not file_bytes.startswith(MAGIC_BYTES["png"]):
                issues.append(
                    ValidationIssue(
                        code="INVALID_PNG_HEADER",
                        field="magic_bytes",
                        severity=ValidationIssueSeverity.ERROR,
                        message=f"File '{safe_name}' is not a valid PNG image binary.",
                        actionable_remediation="Re-save image in standard PNG format.",
                    )
                )
            elif ext in ("jpg", "jpeg") and not file_bytes.startswith(MAGIC_BYTES["jpg"]):
                issues.append(
                    ValidationIssue(
                        code="INVALID_JPEG_HEADER",
                        field="magic_bytes",
                        severity=ValidationIssueSeverity.ERROR,
                        message=f"File '{safe_name}' is not a valid JPEG image binary.",
                        actionable_remediation="Re-save image in standard JPEG format.",
                    )
                )

        # 3. Duplicate Document Detection
        is_dup = False
        if check_duplicate and sha256:
            if sha256 in SEEN_DOCUMENT_HASHES:
                is_dup = True
                issues.append(
                    ValidationIssue(
                        code="DUPLICATE_DOCUMENT",
                        field="sha256_hash",
                        severity=ValidationIssueSeverity.WARNING,
                        message=f"Document '{safe_name}' has an identical SHA-256 hash to a previously uploaded file.",
                        actionable_remediation="This document has already been registered in the current session. Existing extracted records will be refreshed.",
                    )
                )
            else:
                SEEN_DOCUMENT_HASHES.add(sha256)

        # 4. Text Content & Incomplete Template Inspection (for text-based files)
        contains_placeholders = False
        if ext in ("txt", "csv", "json", "tsv"):
            try:
                text_content = file_bytes.decode("utf-8", errors="ignore").strip()
                if len(text_content) < 10:
                    issues.append(
                        ValidationIssue(
                            code="INSUFFICIENT_CONTENT",
                            field="content_length",
                            severity=ValidationIssueSeverity.ERROR,
                            message=f"Document '{safe_name}' contains virtually no text (<10 characters).",
                            actionable_remediation="Verify that the file contains actual product specifications, ratings, or BOM rows.",
                        )
                    )

                # Check for unfinished template tokens
                for pat in PLACEHOLDER_PATTERNS:
                    if pat.search(text_content):
                        contains_placeholders = True
                        issues.append(
                            ValidationIssue(
                                code="INCOMPLETE_TEMPLATE_PLACEHOLDERS",
                                field="text_content",
                                severity=ValidationIssueSeverity.WARNING,
                                message="File appears to contain unfilled template placeholders (e.g. [FILL_HERE] or TODO).",
                                actionable_remediation="Replace all template placeholders with genuine product technical data before final compliance assessment.",
                            )
                        )
                        break
            except Exception as e:
                logger.warning(f"Text decode warning for {safe_name}: {e}")

        # Determine overall validity (ERROR issues invalidate, WARNINGs are flagged)
        has_errors = any(i.severity == ValidationIssueSeverity.ERROR for i in issues)

        return DocumentValidationResult(
            is_valid=not has_errors,
            input_mode=input_mode,
            filename=safe_name,
            file_size_bytes=size,
            sha256_hash=sha256,
            issues=issues,
            detected_format=detected_format,
            contains_placeholder_tokens=contains_placeholders,
            is_empty=False,
            is_duplicate=is_dup,
        )

    @classmethod
    def validate_manual_spec(cls, product_name: str, category: str, description: str) -> DocumentValidationResult:
        """Validate manual technical specification form input."""
        issues: List[ValidationIssue] = []

        if not product_name or not product_name.strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_PRODUCT_NAME",
                    field="product_name",
                    severity=ValidationIssueSeverity.ERROR,
                    message="Product Trade Name or Model Number is required.",
                    actionable_remediation="Provide the commercial name or model number (e.g. 'Electric Immersion Water Heater EWH-1500').",
                )
            )

        if not category or not category.strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_CATEGORY",
                    field="category",
                    severity=ValidationIssueSeverity.ERROR,
                    message="Product Category / Industry Sector is required.",
                    actionable_remediation="Select or specify the category (e.g. 'Kitchen & Domestic Appliances').",
                )
            )

        clean_desc = (description or "").strip()
        if not clean_desc or len(clean_desc) < 20:
            issues.append(
                ValidationIssue(
                    code="INSUFFICIENT_DESCRIPTION",
                    field="description",
                    severity=ValidationIssueSeverity.ERROR,
                    message="Product technical description is too short (< 20 characters) for deterministic standard matching.",
                    actionable_remediation="Include electrical ratings (voltage, wattage), materials, and intended domestic or industrial application.",
                )
            )

        # Check for placeholder tokens
        contains_placeholders = False
        for pat in PLACEHOLDER_PATTERNS:
            if pat.search(clean_desc):
                contains_placeholders = True
                issues.append(
                    ValidationIssue(
                        code="INCOMPLETE_SPEC_PLACEHOLDERS",
                        field="description",
                        severity=ValidationIssueSeverity.WARNING,
                        message="Description contains unfilled template placeholder tokens.",
                        actionable_remediation="Replace all placeholders with actual product parameters.",
                    )
                )
                break

        has_errors = any(i.severity == ValidationIssueSeverity.ERROR for i in issues)

        return DocumentValidationResult(
            is_valid=not has_errors,
            input_mode=InputMode.MANUAL,
            filename=None,
            file_size_bytes=len(clean_desc.encode("utf-8")),
            sha256_hash=cls.calculate_sha256(clean_desc.encode("utf-8")),
            issues=issues,
            detected_format="text/plain",
            contains_placeholder_tokens=contains_placeholders,
            is_empty=len(clean_desc) == 0,
            is_duplicate=False,
        )


document_validator = DocumentValidator()
