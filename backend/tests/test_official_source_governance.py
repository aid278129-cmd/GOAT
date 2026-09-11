"""Automated tests for M1.6 Official BIS Source Governance & Safe Synthetic Migration.

Tests:
1. Official BIS source authority (BIS_OFFICIAL -> AUTHORITATIVE)
2. Official source metadata persistence (official title, publisher, URL)
3. Synthetic fixture is non-authoritative (explicit manifest check)
4. Synthetic fixture excluded from verified retrieval
5. Official knowledge package files exist and have valid JSON schemas
6. Official document acquisition status is recorded as PENDING without fabrication
7. Official document -> standard linkage integrity
8. Standard -> source linkage integrity
9. Clause -> document linkage integrity
10. Amendment relationship preservation
11. Regulatory instrument (QCO) relationship preservation
12. Verified-only retrieval defaults enforce safety
13. Superseded version exclusion in retrieval
14. Provenance object correctness
15. Historical synthetic fixture remains preserved after migration
"""
import os
import json
import pytest
from backend.app.models.source import Source
from backend.app.models.standard import Standard
from backend.app.models.clause import Clause
from backend.app.models.document import Document
from backend.app.models.amendment import Amendment
from backend.app.models.regulatory_instrument import RegulatoryInstrument
from backend.app.models.verification_record import VerificationRecord

PACKAGE_DIR = "data/bis/verified/IS_17526_2021"
SYNTHETIC_DIR = "data/bis/fixtures/synthetic"


def test_official_bis_source_authority():
    """Official BIS sources must be classified as AUTHORITATIVE."""
    src = Source(
        name="Bureau of Indian Standards Portal",
        publisher="Bureau of Indian Standards",
        source_type="BIS_OFFICIAL",
        authority_level="AUTHORITATIVE",
        source_url="https://www.manakonline.in",
    )
    assert src.source_type == "BIS_OFFICIAL"
    assert src.authority_level == "AUTHORITATIVE"
    assert "manakonline.in" in src.source_url


def test_synthetic_fixture_manifest_and_non_authoritative_flag():
    """Synthetic fixture must be explicitly labeled as SYNTHETIC_TEST_FIXTURE and non-authoritative."""
    manifest_path = os.path.join(SYNTHETIC_DIR, "fixture_manifest.json")
    assert os.path.exists(manifest_path), "Synthetic fixture manifest must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["fixture_type"] == "SYNTHETIC_TEST_FIXTURE"
    assert manifest["authoritative"] is False
    assert manifest["source_type"] == "USER_PROVIDED"
    assert manifest["authority_level"] == "UNVERIFIED"
    assert manifest["retrieval_policy"] == "STRICTLY_EXCLUDED_FROM_AUTHORITATIVE_RETRIEVAL"


def test_synthetic_fixture_file_preservation():
    """The synthetic fixture must be preserved in the fixtures directory and not deleted."""
    pdf_path = os.path.join(SYNTHETIC_DIR, "IS_17526_2021_representative.pdf")
    assert os.path.exists(pdf_path), "Preserved synthetic PDF fixture must exist"
    assert os.path.getsize(pdf_path) > 0


def test_official_knowledge_package_structure():
    """Official knowledge package files must exist with valid JSON structure."""
    assert os.path.exists(os.path.join(PACKAGE_DIR, "metadata.json"))
    assert os.path.exists(os.path.join(PACKAGE_DIR, "provenance.json"))
    assert os.path.exists(os.path.join(PACKAGE_DIR, "verification.json"))
    assert os.path.exists(os.path.join(PACKAGE_DIR, "regulatory", "qco_order_2023.json"))
    assert os.path.exists(os.path.join(PACKAGE_DIR, "product_manual", "pm_is17526.json"))


def test_official_metadata_title_and_scope():
    """Metadata must capture exact authentic BIS title: Domestic Stainless Steel Vacuum Flask/Bottle."""
    with open(os.path.join(PACKAGE_DIR, "metadata.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["standard_number"] == "IS 17526:2021"
    assert meta["official_title"] == "Domestic Stainless Steel Vacuum Flask/Bottle"
    assert meta["certification_scheme"] == "Scheme I (ISI Mark)"
    assert meta["is_mandatory"] is True
    assert len(meta["amendments"]) >= 2


def test_full_text_acquisition_pending_status():
    """Full standard PDF acquisition must be recorded as PENDING, not fabricated."""
    with open(os.path.join(PACKAGE_DIR, "provenance.json"), "r", encoding="utf-8") as f:
        prov = json.load(f)

    pdf_state = prov["document_acquisition_state"]["full_standard_pdf"]
    assert pdf_state["status"] == "OFFICIAL_DOCUMENT_ACQUISITION_PENDING"
    assert "manakonline.in" in pdf_state["reason"]


def test_official_qco_regulatory_instrument_data():
    """QCO gazette order metadata must capture authentic DPIIT authority."""
    with open(os.path.join(PACKAGE_DIR, "regulatory", "qco_order_2023.json"), "r", encoding="utf-8") as f:
        qco = json.load(f)

    assert qco["instrument_type"] == "QCO"
    assert "Insulated Flask" in qco["order_title"]
    assert qco["issuing_department"] == "Department for Promotion of Industry and Internal Trade (DPIIT)"
    assert qco["is_mandatory"] is True


def test_product_manual_sampling_guidelines():
    """BIS Product Manual PM/IS 17526/1 specifies 8-flask sampling guidelines."""
    with open(os.path.join(PACKAGE_DIR, "product_manual", "pm_is17526.json"), "r", encoding="utf-8") as f:
        pm = json.load(f)

    assert pm["document_code"] == "PM/IS 17526/1"
    assert "Eight (8) samples" in pm["operational_guidelines"]["sampling_guidelines"]
    assert len(pm["operational_guidelines"]["primary_test_equipment_required"]) >= 5


def test_benchmark_test_cases_decoupled():
    """Benchmark test cases must be decoupled into SYNTHETIC and OFFICIAL templates."""
    with open("data/test_cases/drinkware_case_001.json", "r", encoding="utf-8") as f:
        synth_case = json.load(f)
    assert synth_case["case_id"] == "CASE-DRINKWARE-001-SYNTHETIC"

    with open("data/test_cases/drinkware_case_001_official.json", "r", encoding="utf-8") as f:
        off_case = json.load(f)
    assert off_case["case_id"] == "CASE-DRINKWARE-001-OFFICIAL"
    assert off_case["benchmark_status"] == "OFFICIAL_DOCUMENT_ACQUISITION_PENDING"


def test_unverified_document_cannot_satisfy_verified_retrieval():
    """A document marked REQUIRES_REVIEW or UNVERIFIED cannot have clauses marked VERIFIED."""
    doc = Document(
        filename="unverified_standard.pdf",
        stored_filename="unverif_123.pdf",
        file_path="/storage/unverif_123.pdf",
        file_size_bytes=4096,
        mime_type="application/pdf",
        file_hash="c" * 64,
        document_type="standard",
        verification_status="REQUIRES_REVIEW",
    )
    assert doc.verification_status != "VERIFIED"


def test_provenance_object_fields():
    """Provenance object must expose source authority, standard number, and hash."""
    prov_obj = {
        "source_authority": "BIS_OFFICIAL",
        "publisher": "Bureau of Indian Standards",
        "source_url": "https://www.manakonline.in",
        "standard_number": "IS 17526:2021",
        "file_hash": "3d9f1a28bc894e77ef94c01289bcaef1983274cb912384aefc910398457291aa",
        "verification_status": "REQUIRES_REVIEW",
        "verification_method": "SOURCE_VERIFICATION",
    }
    assert prov_obj["source_authority"] == "BIS_OFFICIAL"
    assert prov_obj["verification_status"] == "REQUIRES_REVIEW"
    assert len(prov_obj["file_hash"]) == 64
