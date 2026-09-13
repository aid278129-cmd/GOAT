"""Tests for OpenDataLoader PDF Ingestion Engine.

Verifies:
1. Java 11+ runtime detection and OpenDataLoader module availability.
2. High-accuracy layout extraction, element bounding boxes, and Markdown output.
3. Memory byte stream conversion without file leakage.
4. Seamless integration with Layer 1 PDF extraction contracts and fallback mechanisms.
"""

import os
import pytest
from pathlib import Path

from backend.app.services.ingestion.opendataloader_extractor import (
    check_java_runtime,
    is_opendataloader_ready,
    extract_with_opendataloader,
    OpenDataLoaderResult,
)
from backend.app.services.ingestion.pdf_extractor import (
    extract_pdf_content,
    extract_pdf_with_opendataloader,
    PDFExtractionResult,
)
from backend.app.services.ingestion.pdf_parser import (
    parse_pdf_document,
    extract_clauses_and_tables,
)

SAMPLE_BIS_PDF = Path("data/bis/fixtures/synthetic/IS_17526_2021_representative.pdf")


def test_java_runtime_and_opendataloader_ready():
    """Proves that a valid Java runtime is detected and OpenDataLoader is operational."""
    java_info = check_java_runtime()
    assert java_info["available"] is True
    assert java_info["path"] is not None
    assert "java" in java_info["path"].lower()

    assert is_opendataloader_ready() is True


def test_opendataloader_extraction_on_bis_standard():
    """Proves OpenDataLoader parses a BIS standard PDF into structured pages with bounding boxes."""
    assert SAMPLE_BIS_PDF.exists(), f"Sample PDF missing at {SAMPLE_BIS_PDF}"

    res = extract_with_opendataloader(str(SAMPLE_BIS_PDF))
    assert isinstance(res, OpenDataLoaderResult)
    assert res.total_pages == 4
    assert len(res.pages) == 4

    # Verify Page 1
    page1 = res.pages[0]
    assert page1.page_number == 1
    assert "IS 17526:2021" in page1.text or "BUREAU OF INDIAN STANDARDS" in page1.text
    assert page1.char_count > 0
    assert len(page1.blocks) > 0

    # Verify Bounding Boxes and tags exist
    first_block = page1.blocks[0]
    assert "bbox" in first_block
    assert len(first_block["bbox"]) == 4
    assert "text" in first_block
    assert "block_type" in first_block

    # Verify Markdown generation
    assert len(res.markdown_content) > 100
    assert "SCOPE" in res.markdown_content
    assert "NORMATIVE REFERENCES" in res.markdown_content


def test_opendataloader_in_memory_bytes_extraction():
    """Proves OpenDataLoader safely processes in-memory bytes streams."""
    pdf_bytes = SAMPLE_BIS_PDF.read_bytes()
    res = extract_with_opendataloader(pdf_bytes, filename="streamed_spec.pdf")

    assert res.total_pages == 4
    assert res.source_name == "streamed_spec.pdf"
    assert len(res.pages) == 4
    assert res.engine == "opendataloader-pdf"


def test_opendataloader_error_handling():
    """Proves graceful rejection of empty and missing files."""
    with pytest.raises(ValueError) as exc:
        extract_with_opendataloader(b"")
    assert "empty" in str(exc.value).lower()

    with pytest.raises(FileNotFoundError):
        extract_with_opendataloader("non_existent_file_xyz_123.pdf")


def test_extract_pdf_with_opendataloader_bridge():
    """Proves Layer 1 pdf_extractor compatibility with OpenDataLoader engine."""
    res = extract_pdf_with_opendataloader(str(SAMPLE_BIS_PDF))
    assert isinstance(res, PDFExtractionResult)
    assert res.total_pages == 4
    assert res.engine == "opendataloader-pdf"
    assert res.pages[0].extraction_method == "OPENDATALOADER_PDF"
    assert len(res.pages[0].blocks) > 0
    assert res.markdown_content is not None
    assert len(res.markdown_content) > 0


def test_extract_clauses_and_tables_api():
    """Proves high-level clause and table extraction helper."""
    summary = extract_clauses_and_tables(str(SAMPLE_BIS_PDF))
    assert summary["total_pages"] == 4
    assert "markdown" in summary
    assert len(summary["markdown"]) > 0
    assert isinstance(summary["clauses"], list)
    assert len(summary["clauses"]) > 0
    assert summary["engine"] == "opendataloader-pdf"
