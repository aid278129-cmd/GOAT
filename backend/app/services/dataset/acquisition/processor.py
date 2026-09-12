"""Document Storage and Derived Processing Engine.

Enforces:
1. Complete separation of original acquired files from derived/extracted text.
2. Preserves exact bytes in data/bis/<category>/<source_id>/original.pdf (or .html/.txt).
3. Produces derived.txt with page-aware extraction, recording engine, version, and text hash.
4. Generates and persists manifest.json for each acquired source.
"""

import re
import json
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import pymupdf

from backend.app.core.logging import logger
from backend.app.services.dataset.acquisition.config import (
    CORPUS_DIRS,
    ensure_corpus_directories,
)
from backend.app.services.dataset.acquisition.models import (
    SourceManifest,
    AcquisitionState,
    SourceType,
)


def sanitize_source_id(raw_id: str) -> str:
    """Sanitizes raw strings into a clean directory/source ID."""
    clean = re.sub(r"[^\w\-\.]", "_", raw_id.strip())
    clean = re.sub(r"_+", "_", clean)
    return clean.strip("_")


class DocumentProcessor:
    """Stores acquired documents and creates derived text artifacts."""

    @classmethod
    def store_and_process(
        cls,
        category: str,
        source_id: str,
        file_bytes: bytes,
        manifest: SourceManifest,
        extension: str = "pdf",
        base_dir: Optional[Path] = None,
    ) -> SourceManifest:
        """Stores the original file and generates derived text & manifest."""
        ensure_corpus_directories()

        cat_key = category.upper()
        if base_dir:
            target_dir = Path(base_dir) / sanitize_source_id(source_id)
        else:
            target_dir = CORPUS_DIRS.get(cat_key, CORPUS_DIRS["STANDARDS"]) / sanitize_source_id(source_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        orig_filename = f"original.{extension}"
        orig_file_path = target_dir / orig_filename

        # 1. Preserve original file
        if not orig_file_path.exists() or orig_file_path.read_bytes() != file_bytes:
            orig_file_path.write_bytes(file_bytes)
            logger.info(f"Preserved original source at {orig_file_path}")

        # Update manifest file path and size
        try:
            manifest.file_path = str(orig_file_path.relative_to(CORPUS_DIRS["STANDARDS"].parent.parent.parent))
        except ValueError:
            manifest.file_path = str(orig_file_path)
        manifest.file_size = len(file_bytes)
        manifest.sha256 = hashlib.sha256(file_bytes).hexdigest()
        manifest.acquisition_status = AcquisitionState.ACQUIRED

        # 2. Derived text extraction (for PDFs or HTML)
        derived_filename = "derived.txt"
        derived_path = target_dir / derived_filename

        if extension.lower() == "pdf":
            try:
                doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                pages_text = []
                for page_idx in range(len(doc)):
                    p_text = doc[page_idx].get_text("text").strip()
                    pages_text.append(f"--- Page {page_idx + 1} ---\n" + p_text)
                doc.close()

                full_derived = "\n\n".join(pages_text)
                derived_path.write_text(full_derived, encoding="utf-8")

                text_hash = hashlib.sha256(full_derived.encode("utf-8")).hexdigest()
                manifest.derived_text_path = str(derived_path.relative_to(CORPUS_DIRS["STANDARDS"].parent.parent.parent))
                manifest.extraction_metadata = {
                    "extraction_engine": "pymupdf",
                    "extraction_version": pymupdf.__version__,
                    "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                    "page_count": len(pages_text),
                    "text_hash": text_hash,
                }
            except Exception as e:
                logger.warning(f"Derived PDF extraction failed for {source_id}: {e}")
        elif extension.lower() in ("html", "htm", "txt"):
            try:
                text_content = file_bytes.decode("utf-8", errors="replace")
                derived_path.write_text(text_content, encoding="utf-8")
                manifest.derived_text_path = str(derived_path.relative_to(CORPUS_DIRS["STANDARDS"].parent.parent.parent))
                manifest.extraction_metadata = {
                    "extraction_engine": "text_decoder",
                    "extraction_version": "1.0",
                    "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                    "page_count": 1,
                    "text_hash": hashlib.sha256(file_bytes).hexdigest(),
                }
            except Exception as e:
                logger.warning(f"Derived text extraction failed: {e}")

        # 3. Save manifest.json in source directory
        manifest_path = target_dir / "manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        return manifest
