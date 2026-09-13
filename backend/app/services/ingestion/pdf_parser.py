"""Unified PDF Document Parser & Structured Clause Extractor.

Layer 1: Input Processing (Powered by OpenDataLoader PDF).
Extracts AI-ready structured text, clauses, tables, and provenance metadata from BIS standards,
technical datasheets, test reports, and compliance certificates.
"""

from typing import List, Dict, Any, Optional, Union
from backend.app.core.logging import logger
from backend.app.services.ingestion.opendataloader_extractor import (
    is_opendataloader_ready,
    extract_with_opendataloader,
    OpenDataLoaderResult,
    OpenDataLoaderPage,
)


def parse_pdf_document(
    file_input: Union[str, bytes],
    filename: Optional[str] = None,
) -> OpenDataLoaderResult:
    """Parse a compliance PDF into structured Markdown and bounding-box JSON pages.
    
    Uses OpenDataLoader PDF for deterministic XY-Cut++ reading order and element extraction.
    """
    return extract_with_opendataloader(file_input, filename=filename)


def extract_clauses_and_tables(
    file_input: Union[str, bytes],
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract segmented clauses, requirements, and tables from a PDF document."""
    res = parse_pdf_document(file_input, filename=filename)
    
    extracted_clauses = []
    extracted_tables = []
    
    for page in res.pages:
        for blk in page.blocks:
            b_type = blk.get("block_type", "")
            text = blk.get("text", "")
            if b_type in ("heading", "list item") or (b_type == "paragraph" and text.split("\n")[0][:3].replace(".", "").isdigit()):
                extracted_clauses.append({
                    "page": page.page_number,
                    "type": b_type,
                    "text": text,
                    "bbox": blk.get("bbox", []),
                })
            elif b_type == "table":
                extracted_tables.append({
                    "page": page.page_number,
                    "content": text,
                    "bbox": blk.get("bbox", []),
                })
                
    return {
        "total_pages": res.total_pages,
        "title": res.title_metadata,
        "markdown": res.markdown_content,
        "clauses": extracted_clauses,
        "tables": extracted_tables,
        "engine": res.engine,
    }


__all__ = [
    "is_opendataloader_ready",
    "parse_pdf_document",
    "extract_clauses_and_tables",
    "extract_with_opendataloader",
    "OpenDataLoaderResult",
    "OpenDataLoaderPage",
]
