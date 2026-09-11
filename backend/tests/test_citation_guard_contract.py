import pytest
from backend.app.schemas.evidence import (
    CitationGuardCheckRequest,
    CitationGuardCheckResponse,
    ValidationStatus,
)


def test_citation_guard_contract_types():
    req = CitationGuardCheckRequest(
        claim="Product insulation must retain temperature above 60C for 6 hours",
        target_standard="IS 17526:2021",
        target_clause="5.4",
        extracted_evidence_text="When tested as per 5.4, the temperature of water after 6 h shall not be less than 60 deg C.",
    )
    assert req.target_standard == "IS 17526:2021"
    assert req.target_clause == "5.4"

    res = CitationGuardCheckResponse(
        is_valid=True,
        status=ValidationStatus.SUPPORTED,
        reasoning="Extracted test requirement directly matches authoritative clause 5.4 thermal performance text.",
        matched_clause_text=req.extracted_evidence_text,
        confidence=0.99,
    )
    assert res.is_valid is True
    assert res.status == ValidationStatus.SUPPORTED
    assert res.confidence >= 0.90
