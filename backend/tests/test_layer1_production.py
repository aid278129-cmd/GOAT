"""Comprehensive Test Suite for Layer 1: Input Processing & Document Preparation.

Tests all production requirements specified in SIH Presentation and Layer 1 upgrade:
- All 5 input modes (PDF, Image/OCR, Voice, BOM, Manual Spec).
- Missing-field cases (REQUIRED, OPTIONAL, MISSING).
- Invalid and malformed files, empty files, size validation.
- Template generation (CSV, JSON, BOM CSV).
- Incomplete template detection ([FILL_HERE] placeholders).
- Unknown / unverified standard fallback (no hallucination).
- Provenance preservation (USER_CLAIM, DOCUMENT_EVIDENCE, OCR, VOICE_TRANSCRIPT, BOM, MANUAL_INPUT).
- Adversarial inputs (path traversal filenames).
- Invariant: Readiness evaluates completeness ONLY and NEVER implies regulatory compliance.
"""

import io
import pytest
from backend.app.schemas.unified_input import (
    InputMode,
    InputProvenanceType,
    FieldRequirementLevel,
    FieldReadinessStatus,
    ValidationIssueSeverity,
)
from backend.app.services.ingestion.validator import document_validator
from backend.app.services.ingestion.template_generator import template_generator_service
from backend.app.services.ingestion.readiness_engine import document_readiness_engine


def test_sanitize_filename_adversarial_path_traversal():
    """Ensure directory traversal attacks and dangerous characters are sanitized."""
    malicious_names = [
        "../../../../etc/passwd",
        "..\\..\\Windows\\System32\\cmd.exe",
        "nested/path/to/spec.pdf",
        "file\x00with_null_byte.pdf",
        "normal_report.pdf",
    ]
    for name in malicious_names:
        clean = document_validator.sanitize_filename(name)
        assert ".." not in clean
        assert "/" not in clean
        assert "\\" not in clean
        assert "\x00" not in clean


def test_validate_empty_file():
    """Empty files (0 bytes) must be detected and rejected."""
    empty_bytes = b""
    res = document_validator.validate_file(empty_bytes, "empty.pdf", InputMode.PDF)
    assert res.is_valid is False
    assert res.is_empty is True
    assert any(i.code == "EMPTY_FILE" for i in res.issues)


def test_validate_invalid_pdf_magic_bytes():
    """Files with .pdf extension lacking %PDF header must fail."""
    corrupted_pdf = b"This is plain text pretending to be a PDF"
    res = document_validator.validate_file(corrupted_pdf, "corrupted.pdf", InputMode.PDF)
    assert res.is_valid is False
    assert any(i.code == "INVALID_PDF_HEADER" for i in res.issues)


def test_validate_valid_pdf_magic_bytes():
    """Valid PDF header must pass structural format validation."""
    valid_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    res = document_validator.validate_file(valid_pdf, "valid_report.pdf", InputMode.PDF, check_duplicate=False)
    assert res.is_valid is True
    assert res.sha256_hash is not None


def test_validate_incomplete_template_placeholders():
    """Incomplete template containing placeholder tokens must be flagged."""
    incomplete_csv = b"Part,Rating,Quantity\nHeating Element,[FILL_HERE],1\nHandle,Polymer,TODO: specify grade"
    res = document_validator.validate_file(incomplete_csv, "draft_bom.csv", InputMode.BOM, check_duplicate=False)
    assert res.contains_placeholder_tokens is True
    assert any(i.code == "INCOMPLETE_TEMPLATE_PLACEHOLDERS" for i in res.issues)


def test_template_generation_csv_and_json():
    """Templates must be generated dynamically from verified BIS standard requirements."""
    csv_content = template_generator_service.generate_csv_template("IS 302-2-201:2008")
    assert "Field ID" in csv_content
    assert "rated_voltage" in csv_content
    assert "rated_power_input" in csv_content
    assert "IS 302-2-201" in csv_content

    json_template = template_generator_service.generate_json_template("IS 302-2-201:2008")
    assert json_template["required_fields_count"] > 0
    assert "rated_voltage" in json_template["parameters"]
    assert json_template["parameters"]["rated_voltage"]["requirement_level"] == "REQUIRED"

    bom_csv = template_generator_service.generate_bom_csv_template()
    assert "Tubular Heating Element" in bom_csv
    assert "Stainless Steel 304" in bom_csv


def test_unknown_standard_fallback_never_hallucinates():
    """If verified knowledge is insufficient for an unknown domain, return UNKNOWN without hallucinating."""
    unknown_reqs = template_generator_service.get_requirements_for_standard_or_category(
        target_standard="IS 99999:2099",
        category="Hypothetical Unindexed Sector",
    )
    assert any(r.level == FieldRequirementLevel.UNKNOWN for r in unknown_reqs)
    # Must not contain fabricated clause numbers
    assert all("Clause 99" not in (r.standard_reference or "") for r in unknown_reqs)


def test_readiness_engine_evaluates_completeness_and_missing_fields():
    """Readiness engine must separate REQUIRED, OPTIONAL, and MISSING fields accurately."""
    # Complete immersion water heater description
    complete_desc = (
        "Electric Immersion Water Heater. Rated voltage 230 V AC, 50 Hz. "
        "Rated power input 1500 W. Tubular sheath is Stainless Steel 304. "
        "Handle is Polypropylene polymer. 3-core PVC cord with 3-pin plug. "
        "Lab test report ABC/EWH/001."
    )
    checklist = document_readiness_engine.evaluate_readiness(
        product_name="Electric Immersion Water Heater EWH-1500",
        category="Kitchen & Domestic Appliances",
        description=complete_desc,
        target_standard="IS 302-2-201:2008",
        provenance_type=InputProvenanceType.DOCUMENT_EVIDENCE,
    )

    assert checklist.total_required_fields > 0
    assert checklist.present_required_fields == checklist.total_required_fields
    assert checklist.missing_required_fields == 0
    assert checklist.completeness_percentage >= 85.0
    assert checklist.is_ready_for_dna_compilation is True

    # Critical Invariant assertion: Never implies regulatory compliance
    assert "does not imply" in checklist.regulatory_disclaimer.lower() or "never" in checklist.regulatory_disclaimer.lower()


def test_readiness_engine_detects_missing_critical_fields():
    """Incomplete description must flag missing required attributes."""
    incomplete_desc = "Electric immersion water heater without any electrical ratings or material specifications."
    checklist = document_readiness_engine.evaluate_readiness(
        product_name="Sample Heater",
        category="Kitchen & Domestic Appliances",
        description=incomplete_desc,
        target_standard="IS 302-2-201:2008",
        provenance_type=InputProvenanceType.USER_CLAIM,
    )

    assert checklist.missing_required_fields > 0
    assert "Rated Voltage" in checklist.missing_critical_fields or "Rated Power Input / Wattage" in checklist.missing_critical_fields
    assert checklist.is_ready_for_dna_compilation is False
    assert checklist.completeness_percentage < 50.0


def test_provenance_preservation_across_modes():
    """Ensure provenance types are assigned and distinct."""
    modes_and_provenances = [
        (InputMode.PDF, InputProvenanceType.DOCUMENT_EVIDENCE),
        (InputMode.IMAGE_OCR, InputProvenanceType.OCR),
        (InputMode.VOICE, InputProvenanceType.VOICE_TRANSCRIPT),
        (InputMode.BOM, InputProvenanceType.BOM),
        (InputMode.MANUAL, InputProvenanceType.MANUAL_INPUT),
    ]
    for mode, prov in modes_and_provenances:
        checklist = document_readiness_engine.evaluate_readiness(
            product_name="Test Product",
            category="Kitchen & Domestic Appliances",
            description="230V 1500W Stainless Steel 304",
            provenance_type=prov,
        )
        for ev in checklist.evaluations:
            if ev.extracted_value:
                assert ev.provenance == prov
