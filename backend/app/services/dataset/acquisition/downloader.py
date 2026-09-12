"""Polite Document Downloader and Legal Access Boundary Controller.

Enforces:
1. Strict official BIS domain boundary.
2. Conservative rate-limiting and gentle crawling intervals.
3. Strict legal boundary: If a resource requires payment, authentication, or CAPTCHA,
   it transitions strictly to ACQUISITION_PENDING.
4. Exact byte preservation and SHA-256 calculation.
"""

import time
import ssl
import urllib.request
import hashlib
from typing import Optional
from pathlib import Path
from pydantic import BaseModel

from backend.app.core.logging import logger
from backend.app.services.dataset.acquisition.config import (
    USER_AGENT,
    REQUEST_TIMEOUT_SECONDS,
    REQUEST_DELAY_SECONDS,
    MAX_DOCUMENT_SIZE_BYTES,
    MAGIC_BYTES,
    is_official_bis_domain,
)
from backend.app.services.dataset.acquisition.models import AcquisitionState

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


class AcquisitionDownloadResult(BaseModel):
    success: bool
    data: bytes = b""
    file_hash: str = ""
    mime_type: str = "application/octet-stream"
    file_size: int = 0
    state: AcquisitionState = AcquisitionState.DISCOVERED
    status_code: Optional[int] = None
    error: Optional[str] = None


class DocumentDownloader:
    """Acquires document bytes while enforcing legal and technical constraints."""

    @staticmethod
    def detect_mime_type(data: bytes, filename: str = "") -> str:
        """Determines MIME type using magic bytes and filename extension."""
        if data.startswith(MAGIC_BYTES["pdf"]):
            return "application/pdf"
        elif data.startswith(MAGIC_BYTES["png"]):
            return "image/png"
        elif data.startswith(MAGIC_BYTES["jpg"]):
            return "image/jpeg"
        elif any(data.startswith(sig) for sig in MAGIC_BYTES["html"]):
            return "text/html"
        elif data.startswith(b"{") or data.startswith(b"["):
            return "application/json"

        if filename.lower().endswith(".pdf"):
            return "application/pdf"
        elif filename.lower().endswith(".html") or filename.lower().endswith(".htm"):
            return "text/html"
        elif filename.lower().endswith(".txt"):
            return "text/plain"

        return "application/octet-stream"

    @classmethod
    def acquire_document(
        cls,
        url: str,
        local_override_path: Optional[Path] = None,
        delay_seconds: float = REQUEST_DELAY_SECONDS,
    ) -> AcquisitionDownloadResult:
        """Safely acquires a document from an official BIS URL or local authoritative asset."""
        # 1. Local authoritative asset handling
        if local_override_path and local_override_path.exists():
            try:
                raw_bytes = local_override_path.read_bytes()
                sha256 = hashlib.sha256(raw_bytes).hexdigest()
                mime = cls.detect_mime_type(raw_bytes, local_override_path.name)
                return AcquisitionDownloadResult(
                    success=True,
                    data=raw_bytes,
                    file_hash=sha256,
                    mime_type=mime,
                    file_size=len(raw_bytes),
                    state=AcquisitionState.ACQUIRED,
                    status_code=200,
                )
            except Exception as e:
                logger.error(f"Failed to read local asset {local_override_path}: {e}")
                return AcquisitionDownloadResult(
                    success=False,
                    state=AcquisitionState.ACQUISITION_PENDING,
                    error=f"Local asset read error: {e}",
                )

        # 2. Strict Domain Whitelist
        if not is_official_bis_domain(url):
            return AcquisitionDownloadResult(
                success=False,
                state=AcquisitionState.INVALID_SOURCE,
                error=f"Disallowed non-official BIS domain: {url}",
            )

        # 3. Rate limiting sleep
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        # 4. HTTP Fetch
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/pdf,text/html,application/xhtml+xml,*/*",
                },
            )
            with urllib.request.urlopen(req, context=_SSL_CTX, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                status = resp.status
                raw_bytes = resp.read()

                # Size constraint
                if len(raw_bytes) > MAX_DOCUMENT_SIZE_BYTES:
                    return AcquisitionDownloadResult(
                        success=False,
                        state=AcquisitionState.ACQUISITION_PENDING,
                        status_code=status,
                        error=f"File exceeds maximum allowed size ({len(raw_bytes)} bytes)",
                    )

                # Check if PDF URL actually returned an HTML soft-404 error page
                if url.lower().endswith(".pdf") and not raw_bytes.startswith(MAGIC_BYTES["pdf"]):
                    return AcquisitionDownloadResult(
                        success=False,
                        state=AcquisitionState.ACQUISITION_PENDING,
                        status_code=404,
                        error="Server returned HTML error page instead of requested PDF document.",
                    )

                sha256 = hashlib.sha256(raw_bytes).hexdigest()
                mime = cls.detect_mime_type(raw_bytes, url)

                return AcquisitionDownloadResult(
                    success=True,
                    data=raw_bytes,
                    file_hash=sha256,
                    mime_type=mime,
                    file_size=len(raw_bytes),
                    state=AcquisitionState.ACQUIRED,
                    status_code=status,
                )

        except urllib.error.HTTPError as e:
            # 401, 403, 404, 429
            logger.warning(f"HTTP {e.code} for {url} - setting ACQUISITION_PENDING")
            return AcquisitionDownloadResult(
                success=False,
                state=AcquisitionState.ACQUISITION_PENDING,
                status_code=e.code,
                error=f"HTTP {e.code}: {e.reason}",
            )
        except Exception as e:
            logger.warning(f"Fetch error for {url}: {e}")
            return AcquisitionDownloadResult(
                success=False,
                state=AcquisitionState.ACQUISITION_PENDING,
                error=str(e),
            )
