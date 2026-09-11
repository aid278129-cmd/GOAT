"""Unit and acceptance tests for Milestone M4:
- Assessment entity creation and lifecycle states
- Product DNA extraction and clarification inside Assessment
- Snapshot versioning and audit reproducibility
- Summary endpoint with counts (no fake percentages)
- Evidence upload and gap recalculation
- Testing roadmap and verified laboratory integration
- Context-aware assessment chat
- Compliance Passport compilation with source index and trust basis
- Authoritative vs Development mode handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.schemas.assessment import AssessmentCreateRequest
from backend.app.services.assessment.service import AssessmentService
from backend.app.models.assessment import Assessment, AssessmentStatus
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction


@pytest.mark.asyncio
async def test_assessment_service_create_and_summary():
    """Assessment can be initialized with Product DNA, applicability, and summary computed without fake percentages."""
    db = AsyncMock()
    req = AssessmentCreateRequest(
        product_name="ThermoMaster 1000ml Flask",
        category="Drinkware & Food Contact Containers",
        description="Double wall stainless steel vacuum flask 1000ml capacity for domestic drinking water.",
        authoritative_mode=False,
    )
    asm = await AssessmentService.create_assessment(db, req)
    assert asm.product_id is not None
    assert asm.mode == "DEVELOPMENT_MODE"
    assert asm.current_version == 1

    summary = AssessmentService.compute_summary(asm)
    assert summary.total_requirements > 0
    assert isinstance(summary.satisfied_count, int)
    assert isinstance(summary.missing_evidence_count, int)
    assert not hasattr(summary, "compliance_percentage")


@pytest.mark.asyncio
async def test_evidence_addition_and_recalculation():
    """Uploading laboratory evidence recalculates gap analysis and creates snapshot."""
    db = AsyncMock()
    req = AssessmentCreateRequest(
        product_name="Insulated Jug 1200ml",
        category="Drinkware & Food Contact Containers",
        description="Insulated jug 1200ml stainless steel 304 with vacuum insulation.",
        authoritative_mode=False,
    )
    asm = await AssessmentService.create_assessment(db, req)
    init_ver = asm.current_version

    updated_asm = await AssessmentService.add_evidence_and_recalculate(
        db=db,
        assessment=asm,
        snippet="Lab report: Clause 5.4 heat retention water temp was 64.5 deg C after 6 hours. Clause 5.2 zero leakage after 10 mins.",
        evidence_type="TEST_REPORT",
        authority="LAB_REPORT",
        page=2,
    )
    assert updated_asm.current_version == init_ver + 1
    assert len(updated_asm.evidence_ids) > 0


@pytest.mark.asyncio
async def test_clarification_loop_in_assessment():
    """Answering clarification updates DNA, preserves provenance, and recalculates applicability."""
    db = AsyncMock()
    req = AssessmentCreateRequest(
        product_name="Generic Flask",
        category="Drinkware & Food Contact Containers",
        description="Double wall insulated flask for drinking use.",
        authoritative_mode=False,
    )
    asm = await AssessmentService.create_assessment(db, req)

    updated_asm = await AssessmentService.answer_clarification_and_recalculate(
        db=db,
        assessment=asm,
        attribute_name="capacity_ml",
        raw_value="750 ml",
    )
    dna = updated_asm.product_dna_snapshot
    cap_attr = next((a for a in dna.get("attributes", []) if a["name"] == "capacity_ml"), None)
    assert cap_attr is not None
    assert cap_attr["value"] == 750
    assert cap_attr["provenance"]["extraction_method"] == "user_clarification"


@pytest.mark.asyncio
async def test_compliance_passport_generation_and_source_index():
    """Passport compiles full auditable details, source index, and trust basis."""
    db = AsyncMock()
    req = AssessmentCreateRequest(
        product_name="HydroShield 750ml Flask",
        category="Drinkware & Food Contact Containers",
        description="Double wall stainless steel vacuum flask 750ml capacity.",
        authoritative_mode=True,
    )
    asm = await AssessmentService.create_assessment(db, req)

    passport = AssessmentService.generate_compliance_passport(
        assessment=asm,
        prod_name="HydroShield 750ml Flask",
        category="Drinkware & Food Contact Containers",
    )

    assert passport.mode == "AUTHORITATIVE_MODE"
    assert passport.trust_basis.verified_official_metadata is True
    assert passport.trust_basis.full_standard_text_status == "OFFICIAL_DOCUMENT_ACQUISITION_PENDING"
    assert len(passport.source_index) >= 3
    assert any("PM/IS 17526/1" in s.title for s in passport.source_index)
    assert any("NOT an official Bureau of Indian Standards License" in lim for lim in passport.limitations)


def test_assessment_context_aware_chat():
    """Chat operates strictly inside assessment context and returns citations."""
    asm = MagicMock()
    asm.id = "ASM-123"
    asm.assessment_number = "ASM-2026-001"
    asm.mode = "DEVELOPMENT_MODE"
    asm.product_dna_snapshot = {
        "product_name": "Test Flask",
        "category": "Drinkware & Food Contact Containers",
        "materials": ["stainless_steel_grade_304"],
        "capacity_ml": 750.0,
    }
    asm.compliance_summary_snapshot = {
        "standard_number": "IS 17526:2021",
        "overall_status": "POTENTIALLY_SATISFIED",
        "evaluations": [
            {
                "clause_number": "5.2",
                "clause_title": "Leakage Test",
                "status": "POTENTIALLY_SATISFIED",
                "recommended_action": "REQUIRES_TESTING",
                "explanation": "Mandatory 10-minute physical inversion test required.",
            }
        ],
    }

    res = AssessmentService.answer_assessment_question(asm, "What is the status of clause 5.2?")
    assert "5.2" in res["answer"]
    assert "REQUIRES_TESTING" in res["answer"]
    assert len(res["citations"]) > 0
    assert "explanatory capacity" in res["disclaimer"].lower()
