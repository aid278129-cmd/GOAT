import os
import tempfile
import pytest
from pathlib import Path

from backend.app.services.ingestion.document_loader import calculate_file_sha256
from backend.app.services.ingestion.pdf_extractor import extract_pdf_content
from backend.app.services.ingestion.clause_segmenter import segment_clauses_from_pages, get_parent_clause_number
from backend.app.services.ingestion.metadata_extractor import extract_standard_metadata_from_text
from backend.app.services.ingestion.requirement_extractor import extract_requirements_from_clause
from backend.app.services.ingestion.embedder import default_embedding_provider, cosine_similarity

FIXTURE_PDF = "data/bis/standards/IS_17526_2021.pdf"


def test_sha256_calculation():
    assert os.path.exists(FIXTURE_PDF)
    sha256_hash = calculate_file_sha256(FIXTURE_PDF)
    assert len(sha256_hash) == 64
    assert isinstance(sha256_hash, str)


def test_file_hash_determinism_and_uniqueness():
    """Hash must be deterministic: same content -> same hash, different content -> different hash."""
    with tempfile.NamedTemporaryFile("w", delete=False) as f1:
        f1.write("BIS Standard IS 17526:2021 Content Sample A")
        path1 = f1.name

    with tempfile.NamedTemporaryFile("w", delete=False) as f2:
        f2.write("BIS Standard IS 17526:2021 Content Sample A")
        path2 = f2.name

    with tempfile.NamedTemporaryFile("w", delete=False) as f3:
        f3.write("Different content for IS 302-1 Electrical Safety")
        path3 = f3.name

    try:
        hash1 = calculate_file_sha256(path1)
        hash2 = calculate_file_sha256(path2)
        hash3 = calculate_file_sha256(path3)

        assert hash1 == hash2, "Same file content must produce identical SHA-256 hash"
        assert hash1 != hash3, "Different file content must produce different SHA-256 hash"
    finally:
        os.unlink(path1)
        os.unlink(path2)
        os.unlink(path3)


def test_pdf_extraction_page_preservation():
    extraction = extract_pdf_content(FIXTURE_PDF)
    assert extraction.total_pages == 4
    assert len(extraction.pages) == 4
    assert extraction.pages[0].page_number == 1
    assert "IS 17526:2021" in extraction.pages[0].text
    assert extraction.pages[1].page_number == 2
    assert "4.2 Material Requirements" in extraction.pages[1].text


def test_metadata_extraction():
    extraction = extract_pdf_content(FIXTURE_PDF)
    full_text = "\n".join(p.text for p in extraction.pages)
    meta = extract_standard_metadata_from_text(full_text)
    assert meta.standard_number == "IS 17526:2021"
    assert "Drinkware" in meta.category


def test_clause_segmentation_hierarchy():
    extraction = extract_pdf_content(FIXTURE_PDF)
    clauses = segment_clauses_from_pages(extraction.pages)
    assert len(clauses) >= 8

    clause_nums = [c.clause_number for c in clauses]
    assert "1.1" in clause_nums
    assert "4.2.1" in clause_nums
    assert "5.4" in clause_nums
    assert "7.1" in clause_nums

    # Test parent clause linking
    assert get_parent_clause_number("4.2.1") == "4.2"
    assert get_parent_clause_number("5.4") == "5"

    c_421 = next((c for c in clauses if c.clause_number == "4.2.1"), None)
    assert c_421 is not None
    assert "Grade 304" in c_421.text_content
    assert c_421.page_start == 2


def test_requirement_extraction_typing():
    extraction = extract_pdf_content(FIXTURE_PDF)
    clauses = segment_clauses_from_pages(extraction.pages)

    c_421 = next(c for c in clauses if c.clause_number == "4.2.1")
    reqs_material = extract_requirements_from_clause(c_421, "IS 17526:2021")
    assert len(reqs_material) == 1
    assert reqs_material[0].requirement_type == "MATERIAL"

    c_54 = next(c for c in clauses if c.clause_number == "5.4")
    reqs_thermal = extract_requirements_from_clause(c_54, "IS 17526:2021")
    assert len(reqs_thermal) == 1
    assert reqs_thermal[0].requirement_type == "PERFORMANCE"
    assert "not be less than 60 deg C" in (reqs_thermal[0].measurable_condition or "")


def test_embedding_cosine_similarity():
    vec_a = default_embedding_provider.embed_text("stainless steel grade 304 material food contact")
    vec_b = default_embedding_provider.embed_text("stainless steel grade 304 material specification")
    vec_c = default_embedding_provider.embed_text("rubber tire tread depth measurement")

    sim_ab = cosine_similarity(vec_a, vec_b)
    sim_ac = cosine_similarity(vec_a, vec_c)

    assert sim_ab > sim_ac
    assert sim_ab > 0.4
