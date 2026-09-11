"""Tests for Voice STT, BOM Parser, and Citation Guard services."""

import pytest
from backend.app.services.ingestion.voice_stt import voice_transcription_service
from backend.app.services.ingestion.bom_parser import bom_parser_service
from backend.app.services.citation_guard.guard import citation_guard
from backend.app.schemas.evidence import CitationGuardCheckRequest, ValidationStatus


@pytest.mark.asyncio
async def test_voice_transcription_fallback():
    dummy_audio = b"RIFF....WAVEfmt ...."
    result = await voice_transcription_service.transcribe_audio(dummy_audio, "test.wav")
    assert result["success"] is True
    assert "immersion water heater" in result["text"].lower() or len(result["text"]) > 0


def test_bom_csv_parser():
    sample_csv = """Part Number,Component,Material,Rating,Quantity
P001,Heating Element,Stainless Steel 304,1500 W,1
P002,Insulated Handle,Heat Resistant Polymer,120 C,1
P003,Power Cord,PVC Insulated,230 V 6 A,1
P004,Indicator Lamp,LED Neon,230 V,1
"""
    parsed = bom_parser_service.parse_bom_content(sample_csv)
    assert parsed["total_parts"] == 4
    assert len(parsed["components"]) == 4
    assert "Stainless Steel 304" in parsed["materials"]
    assert "voltage" in parsed["electrical_ratings"] or "power" in parsed["electrical_ratings"]


def test_citation_guard_valid():
    req = CitationGuardCheckRequest(
        claim="Rated power input is 1492W within +/- 5% tolerance",
        target_standard="IS 302-2-201:2008",
        target_clause="10.1",
        extracted_evidence_text="Clause 10.1 Rated power input measured at 1492 W under 230 V AC. Within permitted tolerance.",
    )
    res = citation_guard.verify_claim(req)
    assert res.is_valid is True
    assert res.status == ValidationStatus.SUPPORTED
    assert res.confidence >= 0.70


def test_citation_guard_missing_source():
    req = CitationGuardCheckRequest(
        claim="Product is completely safe",
        target_standard="",
        target_clause="",
        extracted_evidence_text="",
    )
    res = citation_guard.verify_claim(req)
    assert res.is_valid is False
    assert res.status == ValidationStatus.UNVERIFIED


def test_citation_guard_conflict_routing():
    req = CitationGuardCheckRequest(
        claim="Dielectric strength is compliant",
        target_standard="IS 302-1:2008",
        target_clause="13.3",
        extracted_evidence_text="Dielectric spark breakdown occurred at 1250V during electric strength test.",
    )
    res = citation_guard.verify_claim(req)
    assert res.is_valid is False
    assert res.status == ValidationStatus.CONTRADICTED
