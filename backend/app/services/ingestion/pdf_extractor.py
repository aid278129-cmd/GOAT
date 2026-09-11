"""PDF Text, Layout & Scanned Document Extractor.

Layer 1: Input Processing (PyMuPDF Vector Layout & Scanned OCR Engine).
Enforces zero-hallucination and evidence provenance:
- Native PDF layout extraction with page/block bounding boxes.
- Scanned PDF detection and Tesseract OCR dispatch.
- Corrupted and malformed PDF detection with actionable diagnostics.
- Supports both filesystem paths and in-memory byte streams.
"""

import os
import io
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import pymupdf  # PyMuPDF

from backend.app.core.logging import logger
from backend.app.services.ingestion.ocr import (
    is_scanned_page,
    extract_text_from_image_bytes,
    configure_tesseract,
)


class ExtractedPage(BaseModel):
    page_number: int  # 1-indexed
    text: str
    extraction_method: str = "TEXT"  # TEXT | NATIVE_TESSERACT_OCR | FALLBACK_PARSER
    char_count: int = 0
    blocks: List[Dict[str, Any]] = Field(default_factory=list)
    images_count: int = 0


class PDFExtractionResult(BaseModel):
    total_pages: int
    pages: List[ExtractedPage]
    title_metadata: Optional[str] = None
    author_metadata: Optional[str] = None
    is_mostly_scanned: bool = False
    source_name: str = "document.pdf"


def extract_pdf_content(
    file_input: Union[str, bytes],
    filename: Optional[str] = None,
    enable_ocr: bool = True,
) -> PDFExtractionResult:
    """Extract structured text and page provenance from a PDF document.
    
    Accepts either an absolute file path or raw in-memory PDF bytes.
    Enforces robust error handling for corrupted, empty, or scanned documents.
    """
    doc_name = filename or "uploaded_document.pdf"

    # 1. Open document via PyMuPDF
    try:
        if isinstance(file_input, bytes):
            if len(file_input) == 0:
                raise ValueError("PDF content is empty (0 bytes).")
            doc = pymupdf.open(stream=file_input, filetype="pdf")
        elif isinstance(file_input, str):
            doc_name = filename or os.path.basename(file_input)
            if not os.path.exists(file_input):
                raise FileNotFoundError(f"PDF file does not exist at {file_input}")
            if os.path.getsize(file_input) == 0:
                raise ValueError(f"PDF file '{doc_name}' is empty (0 bytes).")
            doc = pymupdf.open(file_input)
        else:
            raise TypeError(f"Unsupported file_input type: {type(file_input)}")
    except Exception as exc:
        logger.error(f"PyMuPDF failed to open PDF '{doc_name}': {exc}")
        raise ValueError(f"Corrupted or invalid PDF format in '{doc_name}': {str(exc)}")

    total_pages = len(doc)
    pages: List[ExtractedPage] = []
    scanned_pages_count = 0

    meta = doc.metadata or {}
    title_meta = meta.get("title") or None
    author_meta = meta.get("author") or None

    try:
        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1

            # Extract native vector text blocks
            text = page.get_text("text") or ""
            blocks_data = page.get_text("blocks") or []
            image_list = page.get_images(full=True) or []
            image_count = len(image_list)

            extraction_method = "TEXT"

            # Check if page is scanned/image-only
            if is_scanned_page(text, image_count) and enable_ocr and image_count > 0:
                scanned_pages_count += 1
                ocr_text_accum = []
                method_used = "FALLBACK_PARSER"

                for img_info in image_list:
                    xref = img_info[0]
                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image.get("image")
                        if image_bytes:
                            ocr_res = extract_text_from_image_bytes(image_bytes, is_scanned_pdf_page=True)
                            if ocr_res.success and ocr_res.text:
                                ocr_text_accum.append(ocr_res.text)
                                method_used = ocr_res.extraction_method
                    except Exception as img_err:
                        logger.warning(f"Failed to extract image xref {xref} on page {page_num}: {img_err}")

                if ocr_text_accum:
                    text = "\n".join(ocr_text_accum)
                    extraction_method = method_used
                else:
                    extraction_method = "FALLBACK_PARSER"

            # Structured block analysis for provenance tracking
            structured_blocks = []
            for b in blocks_data:
                if len(b) >= 5 and isinstance(b[4], str) and b[4].strip():
                    structured_blocks.append({
                        "bbox": [round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1)],
                        "text": b[4].strip(),
                        "block_type": b[5] if len(b) > 5 else 0,
                    })

            pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=text.strip(),
                    extraction_method=extraction_method,
                    char_count=len(text.strip()),
                    blocks=structured_blocks,
                    images_count=image_count,
                )
            )

    finally:
        doc.close()

    is_mostly_scanned = total_pages > 0 and (scanned_pages_count / total_pages) > 0.5

    logger.info(
        f"Extracted {total_pages} pages from '{doc_name}' "
        f"(Scanned pages: {scanned_pages_count}, Mostly scanned: {is_mostly_scanned})"
    )

    return PDFExtractionResult(
        total_pages=total_pages,
        pages=pages,
        title_metadata=title_meta,
        author_metadata=author_meta,
        is_mostly_scanned=is_mostly_scanned,
        source_name=doc_name,
    )
