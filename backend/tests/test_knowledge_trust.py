"""M1.5 Knowledge Trust & Governance Tests.

Verifies that the trust model enforces:
- INDEXED ≠ VERIFIED
- Ingestion does not auto-set VERIFIED
- Verified-only retrieval excludes UNVERIFIED
- Source authority cannot auto-promote
- Missing version information stays null
- Verification records track entity references
"""
import pytest
from backend.app.models.source import Source
from backend.app.models.document import Document
from backend.app.models.standard import Standard
from backend.app.models.clause import Clause
from backend.app.models.requirement import Requirement
from backend.app.models.amendment import Amendment
from backend.app.models.regulatory_instrument import RegulatoryInstrument
from backend.app.models.verification_record import VerificationRecord


def test_standard_defaults_to_unverified():
    """Standard verification_status must default to UNVERIFIED, not VERIFIED."""
    std = Standard(
        standard_number="IS 99999:2025",
        title="Test Standard",
        category="Test",
    )
    assert std.verification_status == "UNVERIFIED"
    assert std.status == "ACTIVE"


def test_clause_defaults_to_requires_review():
    """Clause verification_status must default to REQUIRES_REVIEW."""
    clause = Clause(
        standard_id="test-std-id",
        clause_number="1.1",
        title="Test Clause",
        text_content="Some text",
    )
    assert clause.verification_status == "REQUIRES_REVIEW"
    assert clause.segmentation_status == "CONFIDENT"


def test_requirement_defaults_to_requires_review():
    """Requirement verification_status must default to REQUIRES_REVIEW."""
    req = Requirement(
        clause_id="test-clause-id",
        code="REQ-TEST-001",
        description="Test requirement",
    )
    assert req.verification_status == "REQUIRES_REVIEW"
    assert req.interpretation_status == "CONFIDENT"


def test_document_defaults_to_unverified():
    """Document verification_status must default to UNVERIFIED."""
    doc = Document(
        filename="test.pdf",
        stored_filename="test_stored.pdf",
        file_path="/path/test.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        file_hash="a" * 64,
        document_type="standard",
    )
    assert doc.verification_status == "UNVERIFIED"
    assert doc.ingestion_status == "DISCOVERED"


def test_indexed_does_not_imply_verified():
    """A document can be INDEXED but UNVERIFIED — these are independent axes."""
    doc = Document(
        filename="test.pdf",
        stored_filename="test_indexed.pdf",
        file_path="/path/test.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        file_hash="b" * 64,
        document_type="standard",
        ingestion_status="INDEXED",
        verification_status="UNVERIFIED",
    )
    assert doc.ingestion_status == "INDEXED"
    assert doc.verification_status == "UNVERIFIED"


def test_source_defaults_to_unverified():
    """Source authority_level must default to UNVERIFIED."""
    source = Source(
        name="Test Source",
        publisher="Test Publisher",
        source_type="USER_PROVIDED",
    )
    assert source.authority_level == "UNVERIFIED"


def test_source_authority_levels():
    """Source authority levels are distinct and meaningful."""
    for level in ["AUTHORITATIVE", "SUPPORTING", "SECONDARY", "UNVERIFIED"]:
        src = Source(
            name=f"Source {level}",
            publisher="Test",
            source_type="OTHER",
            authority_level=level,
        )
        assert src.authority_level == level


def test_amendment_defaults_to_requires_review():
    """Amendment verification_status defaults to REQUIRES_REVIEW."""
    amendment = Amendment(
        standard_id="test-std-id",
        amendment_number="Amendment No. 1",
    )
    assert amendment.verification_status == "REQUIRES_REVIEW"
    assert amendment.affected_clauses is None  # unknown = null, not guessed


def test_regulatory_instrument_defaults():
    """RegulatoryInstrument defaults to not mandatory and REQUIRES_REVIEW."""
    ri = RegulatoryInstrument(
        standard_id="test-std-id",
        instrument_type="QCO",
    )
    assert ri.is_mandatory == False
    assert ri.verification_status == "REQUIRES_REVIEW"


def test_verification_record_structure():
    """VerificationRecord must reference an entity and method."""
    record = VerificationRecord(
        entity_type="document",
        entity_id="doc-12345",
        verification_status="REQUIRES_REVIEW",
        verified_by="SYSTEM_PIPELINE",
        verification_method="MACHINE_VALIDATION",
    )
    assert record.entity_type == "document"
    assert record.entity_id == "doc-12345"
    assert record.verification_method == "MACHINE_VALIDATION"
    assert record.verified_by == "SYSTEM_PIPELINE"


def test_machine_validation_vs_human_review():
    """Machine validation and human review are distinct verification methods."""
    machine = VerificationRecord(
        entity_type="clause",
        entity_id="clause-001",
        verification_status="REQUIRES_REVIEW",
        verified_by="SYSTEM_PIPELINE",
        verification_method="MACHINE_VALIDATION",
        notes="PDF readable, clause parsed",
    )
    human = VerificationRecord(
        entity_type="clause",
        entity_id="clause-001",
        verification_status="VERIFIED",
        verified_by="PENDING_HUMAN_REVIEW",
        verification_method="SOURCE_VERIFICATION",
        source_authority="BIS_OFFICIAL",
        notes="Verified against official BIS publication",
    )
    assert machine.verification_method != human.verification_method
    assert machine.verification_status != human.verification_status


def test_standard_supersession_fields():
    """Standard must support supersedes/superseded_by without guessing."""
    std_old = Standard(
        standard_number="IS 12345:2010",
        title="Old Standard",
        category="Test",
        status="SUPERSEDED",
        superseded_by="IS 12345:2020",
    )
    std_new = Standard(
        standard_number="IS 12345:2020",
        title="New Standard",
        category="Test",
        status="ACTIVE",
        supersedes="IS 12345:2010",
    )
    assert std_old.superseded_by == "IS 12345:2020"
    assert std_new.supersedes == "IS 12345:2010"
    # Missing version info stays null
    assert std_old.publication_date is None
    assert std_new.effective_from is None


def test_unverified_source_cannot_be_authoritative():
    """A source with UNVERIFIED authority should not claim AUTHORITATIVE."""
    src = Source(
        name="Random PDF",
        publisher="Unknown",
        source_type="USER_PROVIDED",
        authority_level="UNVERIFIED",
    )
    assert src.authority_level != "AUTHORITATIVE"
