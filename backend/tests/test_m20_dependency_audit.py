"""M20: Full Dependency, Multi-Modal Input & External API Integration Audit Test Suite.

Audits runtime execution across all dependencies:
- PyMuPDF real document parsing
- Image/OCR availability and deterministic fallback
- Whisper audio ingestion and acoustic fallback
- BOM CSV and JSON parsing
- Database connection and zero-secret exposure
- Vector embedding and Layer 6 hybrid RAG
- Diagnostics endpoint /api/v1/system/dependencies
"""

import io
import os
import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.diagnostics.dependency_checker import check_all_dependencies
from backend.app.services.ingestion.pdf_extractor import extract_pdf_content
from backend.app.services.ingestion.bom_parser import bom_parser_service
from backend.app.services.ingestion.ocr import extract_text_from_image_bytes, is_scanned_page
from backend.app.services.ingestion.voice_stt import voice_transcription_service
from backend.app.services.ingestion.embedder import default_embedding_provider
from backend.app.services.rag.engine import layer6_clause_rag
from backend.app.services.rag.models import ClauseRAGSearchRequest

client = TestClient(app)


# 1. Diagnostics API Endpoint Verification
def test_system_dependencies_endpoint():
    res = client.get("/api/v1/system/dependencies")
    assert res.status_code == 200
    data = res.json()

    assert data["overall_health"] in ("OPERATIONAL", "DEGRADED", "CONFIGURATION_REQUIRED")
    assert "PDF" in data["input_services"]
    assert "OCR" in data["input_services"]
    assert "VOICE" in data["input_services"]
    assert "BOM" in data["input_services"]
    assert "MANUAL" in data["input_services"]

    # Invariant: Zero Secret Leakage
    raw_str = str(data)
    for forbidden in ["sk-", "postgrespassword", "SECRET_KEY", "Bearer"]:
        assert forbidden not in raw_str


# 2. PyMuPDF Real Runtime Document Ingestion
def test_pymupdf_real_runtime_execution(tmp_path):
    import pymupdf

    test_pdf = tmp_path / "spec_test.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=300)
    page.insert_text((50, 50), "IS 17526:2021 Stainless Steel Vacuum Flask Specification")
    page.insert_text((50, 80), "Material Grade: SS 304. Nominal Capacity: 750 ml.")
    doc.save(str(test_pdf))
    doc.close()

    result = extract_pdf_content(str(test_pdf), enable_ocr=False)
    assert result.total_pages == 1
    assert "IS 17526:2021" in result.pages[0].text
    assert "750 ml" in result.pages[0].text
    assert result.pages[0].extraction_method == "TEXT"


# 3. Scanned PDF & OCR Fallback Runtime Handling
def test_scanned_pdf_and_ocr_fallback():
    # Empty text with image presence simulates scanned document
    assert is_scanned_page(text="", image_count=1) is True
    assert is_scanned_page(text="This page contains sufficient vector text.", image_count=1) is False

    # Test OCR fallback on dummy bytes
    dummy_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    txt, ok = extract_text_from_image_bytes(dummy_bytes)
    # Even if Tesseract binary is absent on host, it handles gracefully without crashing
    assert isinstance(txt, str)
    assert isinstance(ok, bool)


# 4. Voice STT Runtime Ingestion & Acoustic Processor
def test_voice_stt_runtime_execution(monkeypatch):
    import asyncio
    from backend.app.core.config import settings

    # Valid audio bytes in real mode: accurately reports VOICE_CLOUD_NOT_CONFIGURED if API key is not present
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    audio_sample = b"RIFF" + b"\x00" * 4000
    res = asyncio.run(voice_transcription_service.transcribe_audio(audio_sample, "query.wav"))
    assert res["status"] in ("VOICE_CLOUD_NOT_CONFIGURED", "FUNCTIONAL")
    assert res.get("detected_format") == "WAV" or res.get("language") == "en"

    # In DEMO MODE: deterministic acoustic fixture active
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    demo_res = asyncio.run(voice_transcription_service.transcribe_audio(audio_sample, "query.wav"))
    assert demo_res["success"] is True
    assert demo_res["provider"] == "DEMO_FIXTURE"
    assert len(demo_res["text"]) > 0

    # Empty audio handling
    empty_res = asyncio.run(voice_transcription_service.transcribe_audio(b"", "empty.wav"))
    assert empty_res["success"] is False
    assert "empty" in empty_res["error"].lower()


# 5. BOM Real Parsing (CSV & JSON)
def test_bom_csv_and_json_parsing():
    # Valid CSV BOM
    csv_payload = (
        "Part ID,Component,Material,Specification,Quantity\n"
        "P1,Inner Flask,SS 304,Food grade double wall,1\n"
        "P2,Lid Stopper,Polypropylene,BPA-Free,1\n"
    )
    res_csv = bom_parser_service.parse_bom_content(csv_payload, "bom.csv")
    assert res_csv["total_parts"] == 2
    assert "SS 304" in res_csv["materials"]

    # Valid JSON BOM
    json_payload = '[{"part_number": "P1", "name": "Element", "material": "Copper", "rating": "1500W"}]'
    res_json = bom_parser_service.parse_bom_content(json_payload, "bom.json")
    assert res_json["total_parts"] == 1
    assert "Copper" in res_json["materials"]

    # Incomplete / Empty BOM
    empty_res = bom_parser_service.parse_bom_content("", "empty.csv")
    assert empty_res["total_parts"] == 0


# 6. Database Connection & Credential Safety
def test_database_connection_and_safety():
    from backend.app.database.session import engine, test_db_connectivity
    import asyncio

    # Test connection without hanging
    connected = asyncio.run(test_db_connectivity(retries=1, delay_sec=0.1))
    assert isinstance(connected, bool)

    # Ensure engine URL does not expose raw secrets
    url_str = str(engine.url)
    assert "postgrespassword" not in url_str or "sqlite" in url_str


# 7. Embedding Engine & Vector RAG Execution
def test_embedding_and_hybrid_rag():
    emb = default_embedding_provider.embed_query("Immersion water heater electrical safety")
    assert len(emb) > 0
    assert isinstance(emb[0], float)

    # Hybrid RAG search
    rag_res = layer6_clause_rag.search(
        ClauseRAGSearchRequest(
            query="drop test leakage thermal",
            standard_filter="IS 17526:2021",
            top_k=3,
        )
    )
    assert len(rag_res.results) > 0
    assert rag_res.results[0].standard_number == "IS 17526:2021"


# 8. Diagnostics Engine Standalone Inspection
def test_diagnostics_engine_standalone():
    diag = check_all_dependencies()
    assert len(diag.dependencies) >= 8
    names = [d.name for d in diag.dependencies]
    assert "PyMuPDF" in names
    assert "BOM Parser Engine" in names
    assert any("Database" in n for n in names)
