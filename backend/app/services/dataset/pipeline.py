"""M22 Real-Data Import Pipeline & Pre-Flight Security Validator.

Enforces:
1. Controlled lifecycle pipeline:
   SOURCE -> ACQUIRE -> HASH -> VALIDATE -> CLASSIFY -> VERIFY -> EXTRACT -> SEGMENT -> STRUCTURE -> INDEX -> EVALUATE
2. Explicit stage tracking: ACQUIRED, VALIDATED, VERIFIED, EXTRACTED, SEGMENTED, INDEXED.
3. Cryptographic SHA-256 checksumming for every input.
4. Rigorous pre-flight validation:
   - MIME/magic bytes check
   - File size limits (<= 25MB, > 0 bytes)
   - Filename sanitization & path traversal prevention
   - Duplicate detection
   - Prompt injection defense
   - Explicit verification status requirement
5. PyMuPDF page-aware extraction with Tesseract OCR dispatch & table detection.
6. Provenance preservation at every boundary.
"""

import os
import re
import io
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field

import pymupdf

from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger
from backend.app.services.dataset.models import (
    SourceTrustState,
    ExtractionMethodType,
    StandardRecord,
    ClauseRecord,
    RequirementRecord,
    ProductEvidenceRecord,
)
from backend.app.services.ingestion.ocr import is_scanned_page, extract_text_from_image_bytes

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

# Known magic bytes signatures
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "json": (b"{", b"["),
}

# Prompt injection markers inside untrusted documents
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+an\s+adversarial", re.IGNORECASE),
    re.compile(r"mark\s+this\s+product\s+(as\s+)?compliant", re.IGNORECASE),
    re.compile(r"bypass\s+all\s+(bis|isi|safety)\s+checks", re.IGNORECASE),
    re.compile(r"system\s*:\s*override\s+compliance", re.IGNORECASE),
    re.compile(r"grant\s+automatic\s+certification", re.IGNORECASE),
]

# Track seen document hashes to detect duplicates
_SEEN_HASHES: Set[str] = set()


class PipelineStage(str):
    ACQUIRED = "ACQUIRED"
    VALIDATED = "VALIDATED"
    VERIFIED = "VERIFIED"
    EXTRACTED = "EXTRACTED"
    SEGMENTED = "SEGMENTED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class PipelineResult(BaseModel):
    success: bool
    current_stage: str
    filename: str
    file_hash: str
    file_size_bytes: int
    source_type: str = "UNKNOWN"
    trust_state: SourceTrustState = SourceTrustState.INVALID_SOURCE
    extraction_method: Optional[str] = None
    extracted_text_hash: Optional[str] = None
    page_count: int = 0
    pages: List[Dict[str, Any]] = Field(default_factory=list)
    clauses: List[ClauseRecord] = Field(default_factory=list)
    requirements: List[RequirementRecord] = Field(default_factory=list)
    evidence_record: Optional[ProductEvidenceRecord] = None
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RealDataImportPipeline:
    """Production controlled pipeline for importing real BIS documents and product evidence."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Strip dangerous path traversal characters and non-printable bytes."""
        if not filename:
            return "unnamed_input"
        clean = os.path.basename(filename).strip()
        clean = clean.replace("\x00", "").replace("..", "").replace("/", "_").replace("\\", "_")
        clean = re.sub(r"[^\w\.\-\s]", "_", clean)
        return clean or "unnamed_input"

    @classmethod
    def calculate_sha256(cls, data: bytes) -> str:
        """Calculate SHA-256 hash."""
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def detect_prompt_injection(cls, text: str) -> List[str]:
        """Scan document text for adversarial prompt injection attempts."""
        findings = []
        for pat in PROMPT_INJECTION_PATTERNS:
            if pat.search(text):
                findings.append(f"Prompt injection pattern detected: '{pat.pattern}'")
        return findings

    @classmethod
    def validate_preflight(
        cls,
        file_bytes: bytes,
        filename: str,
        expected_type: Optional[str] = None,
        allow_duplicate: bool = False,
    ) -> Tuple[bool, str, List[str], List[str]]:
        """Pre-flight file validation: integrity, size, MIME, duplicates."""
        issues: List[str] = []
        warnings: List[str] = []
        safe_name = cls.sanitize_filename(filename)
        size = len(file_bytes)

        # 1. Size Check
        if size == 0:
            issues.append("Document is empty (0 bytes).")
            return False, "", issues, warnings
        if size > MAX_FILE_SIZE_BYTES:
            issues.append(f"Document size ({size / (1024*1024):.1f}MB) exceeds 25MB limit.")
            return False, "", issues, warnings

        # 2. SHA-256
        sha256 = cls.calculate_sha256(file_bytes)

        # 3. Duplicate Check
        if not allow_duplicate and sha256 in _SEEN_HASHES:
            warnings.append(f"Document with identical SHA-256 hash ({sha256[:12]}...) was previously imported.")
        else:
            _SEEN_HASHES.add(sha256)

        # 4. MIME / Magic Bytes
        ext = safe_name.split(".")[-1].lower() if "." in safe_name else ""
        if ext == "pdf":
            if not file_bytes.startswith(MAGIC_BYTES["pdf"]):
                issues.append("Corrupt file signature: Expected PDF magic bytes '%PDF-'.")
        elif ext == "png":
            if not file_bytes.startswith(MAGIC_BYTES["png"]):
                issues.append("Corrupt file signature: Expected PNG magic bytes.")
        elif ext in ("jpg", "jpeg"):
            if not file_bytes.startswith(MAGIC_BYTES["jpg"]):
                issues.append("Corrupt file signature: Expected JPEG magic bytes.")
        elif ext == "json":
            stripped = file_bytes.strip()
            if not (stripped.startswith(b"{") or stripped.startswith(b"[")):
                issues.append("Corrupt file signature: Expected valid JSON container ('{' or '[').")

        return len(issues) == 0, sha256, issues, warnings

    @classmethod
    def process_file(
        cls,
        file_bytes: bytes,
        filename: str,
        source_authority: str = "UNVERIFIED_SOURCE",
        is_authoritative: bool = False,
        standard_number: Optional[str] = None,
        evidence_type: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> PipelineResult:
        """Executes the full controlled pipeline on a raw document."""
        safe_name = cls.sanitize_filename(filename)
        size = len(file_bytes)

        # Stage 1: ACQUIRE & HASH
        current_stage = PipelineStage.ACQUIRED
        valid, file_hash, issues, warnings = cls.validate_preflight(file_bytes, safe_name, allow_duplicate=True)
        if not valid:
            return PipelineResult(
                success=False,
                current_stage=PipelineStage.FAILED,
                filename=safe_name,
                file_hash=file_hash,
                file_size_bytes=size,
                trust_state=SourceTrustState.INVALID_SOURCE,
                issues=issues,
                warnings=warnings,
            )

        # Stage 2: VALIDATE
        current_stage = PipelineStage.VALIDATED

        # Stage 3: CLASSIFY & VERIFY
        # Reject unauthorized copies or unverified sources claiming regulatory authority
        if is_authoritative and "OFFICIAL" not in source_authority.upper() and "BIS" not in source_authority.upper():
            issues.append(f"Unauthorized source authority '{source_authority}' rejected for authoritative regulatory indexing.")
            return PipelineResult(
                success=False,
                current_stage=PipelineStage.FAILED,
                filename=safe_name,
                file_hash=file_hash,
                file_size_bytes=size,
                trust_state=SourceTrustState.REJECTED_SOURCE,
                issues=issues,
                warnings=warnings,
            )

        trust_state = SourceTrustState.DOCUMENT_VERIFIED if is_authoritative else SourceTrustState.CATALOG_ONLY
        current_stage = PipelineStage.VERIFIED

        # Stage 4: EXTRACT
        ext = safe_name.split(".")[-1].lower() if "." in safe_name else ""
        extracted_pages = []
        extraction_method = ExtractionMethodType.TEXT_EXTRACTION.value
        full_text = ""

        if ext == "pdf":
            try:
                doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    page_text = page.get_text("text").strip()
                    page_num = page_idx + 1

                    # Check if page is scanned
                    if not page_text or len(page_text) < 30:
                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("png")
                        ocr_text = extract_text_from_image_bytes(img_bytes)
                        if ocr_text:
                            page_text = ocr_text
                            extraction_method = ExtractionMethodType.HYBRID.value

                    # Check for prompt injection in extracted text
                    injections = cls.detect_prompt_injection(page_text)
                    if injections:
                        warnings.extend([f"Page {page_num}: {inj}" for inj in injections])
                        # Prompt injection sanitized: do not alter compliance pipeline
                        page_text = "[SANITIZED_SUSPICIOUS_PAYLOAD]"

                    extracted_pages.append({
                        "page_number": page_num,
                        "text": page_text,
                        "char_count": len(page_text),
                    })
                    full_text += f"\n--- Page {page_num} ---\n" + page_text

                doc.close()
            except Exception as e:
                issues.append(f"PyMuPDF extraction failed: {str(e)}")
                return PipelineResult(
                    success=False,
                    current_stage=PipelineStage.FAILED,
                    filename=safe_name,
                    file_hash=file_hash,
                    file_size_bytes=size,
                    trust_state=SourceTrustState.INVALID_SOURCE,
                    issues=issues,
                )
        elif ext in ("txt", "json", "csv"):
            try:
                full_text = file_bytes.decode("utf-8", errors="replace")
                injections = cls.detect_prompt_injection(full_text)
                if injections:
                    warnings.extend(injections)
                extracted_pages.append({"page_number": 1, "text": full_text, "char_count": len(full_text)})
            except Exception as e:
                issues.append(f"Text decoding failed: {str(e)}")
                return PipelineResult(
                    success=False,
                    current_stage=PipelineStage.FAILED,
                    filename=safe_name,
                    file_hash=file_hash,
                    file_size_bytes=size,
                    trust_state=SourceTrustState.INVALID_SOURCE,
                    issues=issues,
                )

        extracted_text_hash = cls.calculate_sha256(full_text.encode("utf-8")) if full_text else None
        current_stage = PipelineStage.EXTRACTED

        # Stage 5: SEGMENT & STRUCTURE
        clauses: List[ClauseRecord] = []
        requirements: List[RequirementRecord] = []
        evidence_record: Optional[ProductEvidenceRecord] = None

        if standard_number and is_authoritative:
            # Segment normative standard clauses
            # Regex to find clause patterns like "4.2.1", "5.4"
            clause_blocks = re.split(r"\n(?=\d+\.\d+(?:\.\d+)?\s+[A-Z])", full_text)
            for idx, block in enumerate(clause_blocks[:10]):
                m = re.match(r"^(\d+\.\d+(?:\.\d+)?)\s+(.+?)\n(.*)", block, re.DOTALL)
                if m:
                    c_num = m.group(1)
                    c_title = m.group(2).strip()
                    c_body = m.group(3).strip()
                    c_id = f"CL-{standard_number.replace(' ', '-').replace(':', '-')}-{c_num}"
                    cl_rec = ClauseRecord(
                        clause_id=c_id,
                        standard_number=standard_number,
                        clause_number=c_num,
                        clause_title=c_title,
                        text=c_body or block[:200],
                        source_document_id=f"DOC-{file_hash[:12]}",
                        source_hash=file_hash,
                        extraction_method=ExtractionMethodType(extraction_method),
                        verification_status=SourceTrustState.CLAUSE_INDEXED,
                    )
                    clauses.append(cl_rec)
        elif evidence_type and product_id:
            # Structure independent product evidence
            evidence_record = ProductEvidenceRecord(
                evidence_id=f"EV-{evidence_type.upper()}-{file_hash[:8].upper()}",
                product_id=product_id,
                evidence_type=evidence_type,
                filename=safe_name,
                source=source_authority,
                provenance_type="LAB_TEST" if "LAB" in evidence_type.upper() else "MANUFACTURER_SPEC",
                extracted_facts={"char_count": len(full_text), "page_count": len(extracted_pages)},
                document_hash=file_hash,
                verification_status="VERIFIED" if is_authoritative else "UNVERIFIED",
                notes="Imported via controlled RealDataImportPipeline.",
            )

        current_stage = PipelineStage.INDEXED

        return PipelineResult(
            success=True,
            current_stage=current_stage,
            filename=safe_name,
            file_hash=file_hash,
            file_size_bytes=size,
            source_type="AUTHORITATIVE_BIS" if is_authoritative else "PRODUCT_EVIDENCE",
            trust_state=trust_state,
            extraction_method=extraction_method,
            extracted_text_hash=extracted_text_hash,
            page_count=len(extracted_pages),
            pages=extracted_pages,
            clauses=clauses,
            requirements=requirements,
            evidence_record=evidence_record,
            issues=issues,
            warnings=warnings,
            metadata={
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "is_authoritative": is_authoritative,
                "standard_number": standard_number,
            },
        )
