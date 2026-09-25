"""Milestone M26.3: Evidence-Backed Compliance Passport Generation Test Suite.

Rigorously verifies all M26.3 specifications, deterministic invariants, and authority boundaries:
1. Fully satisfied product generation:
   - All mandatory requirements verified by authentic evidence -> COMPLIANT verdict, FINALIZED lifecycle.
2. Partially satisfied product:
   - Preserves exact individual states, GAPS_IDENTIFIED, no compliance inflation.
3. Missing evidence handling:
   - Preserves MISSING_EVIDENCE, specific next action (LAB_TEST_REQUIRED / DOCUMENT_REQUIRED), zero invented values.
4. Failed requirement handling:
   - Physical/numerical failure yields NOT_SATISFIED, NON_COMPLIANT overall verdict, CORRECTIVE_ACTION_REQUIRED.
5. Conflicting evidence handling:
   - Contradictory evidence artifacts yield CONFLICTING, EXPERT_REVIEW_REQUIRED, UNDER_REVIEW lifecycle.
6. Expert-review requirement handling:
   - Ambiguous/borderline cases explicitly routed to expert review with safe abstention.
7. Source and version provenance:
   - Product DNA provenance, BIS standard and revision, ruleset version, knowledge version, lab source identity, SHA-256 hashes propagated.
8. SHA-256 reproducibility:
   - Two runs on identical inputs yield bit-for-bit identical integrity seal; input alteration mutates the seal.
9. BIS certification disclaimer & prohibited label rejection:
   - Strictly titled "Evidence-Backed Pre-Certification Compliance Assessment".
   - Non-negotiable disclaimer: "Compliance Passport ≠ BIS Certification".
   - Prohibited terms ("BIS Certificate", "Official Certification", "Guaranteed Compliance", etc.) strictly rejected.
10. Zero LLM compliance authority:
    - Layer 7 sole compliance authority, Layer 8 sole evidence authority, Layer 9 output authority.
    - LLM compliance authority is exactly 0.0%, regulatory_conclusion is "NONE".
11. No invented evidence or regulatory facts:
    - No unsupported lab names, fees, timelines, or synthetic clauses.
12. REST API endpoint integration:
    - Direct verification of /api/v1/passport/generate-evidence-backed and /api/v1/passport/invariants.
"""

import hashlib
import json
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.product_evidence import (
    EvidenceType,
    EvidenceHierarchyLevel,
    EvidenceVerificationStatus,
    SourceAuthenticity,
    ArtifactIntegrityStatus,
    EvidenceOntologyTier,
    ProductEvidenceRecord,
    StandardRequirementDefinition,
)
from backend.app.schemas.product_dna import (
    ProductDNACore,
    DNAAttribute,
    ProductFact,
    FactProvenanceType,
    FactCategory,
    FactVerificationState,
)
from backend.app.schemas.compliance import (
    RequirementGapStatus,
    GapNextAction,
    ComplianceGapItem,
    DeterministicGapAggregationResult,
)
from backend.app.schemas.compliance_passport import (
    PASSPORT_DOCUMENT_TITLE,
    PASSPORT_PROHIBITED_LABELS,
    STATUTORY_DISCLAIMER_TEXT,
    PassportProductIdentity,
    PassportStandardReference,
    PassportRequirementItem,
    PassportNextActionItem,
    PassportExpertReviewItem,
    PassportSourceReference,
    EvidenceBackedCompliancePassport,
)
from backend.app.services.compliance.gap_aggregation_service import (
    DeterministicGapAggregationEngine,
    gap_aggregation_service,
)
from backend.app.services.compliance.passport_generator_service import (
    DeterministicCompliancePassportGenerator,
    compliance_passport_generator,
)
from backend.app.services.passport.compiler import passport_compiler

client = TestClient(app)


def _make_evidence(
    evidence_id: str = "EVID-001",
    evidence_type: EvidenceType = EvidenceType.LABORATORY_TEST_REPORT,
    source_reference: str = "NABL_ACCREDITED_LAB_01/TR-2026-992.pdf",
    source_identity: str = "NABL_ACCREDITED_LAB_01",
    extracted_value: str = "64.5 C",
    normalized_value: Any = None,
    unit: str = "°C",
    attribute: str = "heat_retention",
    applicable_standard: str = "IS 17526:2021",
    applicable_clause: str = "5.4",
    applicable_requirement: str = "REQ-IS17526-5.4",
    hierarchy_level: EvidenceHierarchyLevel = EvidenceHierarchyLevel.VERIFIED_TEST_EVIDENCE,
    source_authenticity: SourceAuthenticity = SourceAuthenticity.REAL_AUTHORITATIVE,
    artifact_integrity: ArtifactIntegrityStatus = ArtifactIntegrityStatus.HASH_VALID,
    verified: bool = True,
    verification_status: EvidenceVerificationStatus = EvidenceVerificationStatus.VERIFIED,
    ontology_tier: EvidenceOntologyTier = EvidenceOntologyTier.VERIFIED_EVIDENCE,
    notes: str = "Tested per IS 17526 Clause 5.4",
) -> ProductEvidenceRecord:
    """Helper fixture factory for creating typed ProductEvidenceRecord instances."""
    raw_dummy = f"{evidence_id}-{source_reference}-{extracted_value}".encode("utf-8")
    sha256 = hashlib.sha256(raw_dummy).hexdigest()

    final_auth = source_authenticity
    if source_identity and "NABL" not in source_identity.upper() and source_authenticity == SourceAuthenticity.REAL_AUTHORITATIVE:
        final_auth = SourceAuthenticity.REAL_NON_AUTHORITATIVE

    return ProductEvidenceRecord(
        evidence_id=evidence_id,
        product_id="PROD-VACUUM-FLASK-01",
        evidence_type=evidence_type,
        hierarchy_level=hierarchy_level,
        source_type="PDF",
        source_reference=source_reference,
        source_location="Page 3, Table 2",
        extracted_value=extracted_value,
        normalized_value=normalized_value,
        unit=unit,
        attribute=attribute,
        extraction_method="PYMUPDF",
        confidence=1.0,
        provenance=f"Issued by {source_identity}, testing schedule verified",
        sha256=sha256,
        verified=verified,
        verification_status=verification_status,
        source_authenticity=final_auth,
        artifact_integrity=artifact_integrity,
        source_identity=source_identity,
        source_identity_verification="NABL_DIRECTORY",
        verification_method="NABL_DIRECTORY" if "NABL" in (source_identity or "").upper() else "BIS_CRS_PORTAL",
        applicable_requirement=applicable_requirement,
        applicable_standard=applicable_standard,
        applicable_clause=applicable_clause,
        ontology_tier=ontology_tier,
        regulatory_conclusion="NONE",
        notes=notes,
    )


def _make_all_8_satisfied_evidences() -> List[ProductEvidenceRecord]:
    """Helper returning 8 authentic verified evidence records satisfying all IS 17526:2021 requirements."""
    return [
        _make_evidence("EV-40", EvidenceType.PRODUCT_PHOTOGRAPH, extracted_value="Non-toxic food-safe construction", applicable_clause="4.0", applicable_requirement="REQ-IS17526-4.0"),
        _make_evidence("EV-41", EvidenceType.PRODUCT_PHOTOGRAPH, extracted_value="Free from sharp burrs and defects", applicable_clause="4.1", applicable_requirement="REQ-IS17526-4.1"),
        _make_evidence("EV-421", EvidenceType.DECLARATION, extracted_value="Food contact surfaces SS 304 conforming to IS 6911", applicable_clause="4.2.1", applicable_requirement="REQ-IS17526-4.2.1"),
        _make_evidence("EV-51", EvidenceType.MANUFACTURER_DATASHEET, extracted_value="1000 ml", normalized_value=1000, applicable_clause="5.1", applicable_requirement="REQ-IS17526-5.1"),
        _make_evidence("EV-52", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="PASS - Zero moisture droplets after 10 min inverted", applicable_clause="5.2", applicable_requirement="REQ-IS17526-5.2"),
        _make_evidence("EV-53", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="PASS - 1.0m concrete drop intact, vacuum retained", applicable_clause="5.3", applicable_requirement="REQ-IS17526-5.3"),
        _make_evidence("EV-54", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="64.5 C", normalized_value=64.5, applicable_clause="5.4", applicable_requirement="REQ-IS17526-5.4"),
        _make_evidence("EV-71", EvidenceType.LABEL_MARKING_EVIDENCE, extracted_value="IS 17526 CM/L-99887766 Model SS-1000", applicable_clause="7.1", applicable_requirement="REQ-IS17526-7.1"),
    ]


# =========================================================================
# 1. Fully Satisfied Product Test
# =========================================================================
def test_fully_satisfied_product_passport():
    """When all mandatory requirements are satisfied by authentic verified evidence, the passport reflects COMPLIANT."""
    evidences = _make_all_8_satisfied_evidences()
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-FLASK-SATISFIED",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )
    assert gap_result.overall_verdict == "COMPLIANT"

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-FLASK-SATISFIED",
        product_name="UltraThermal Vacuum Flask 1000ml",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
        source_snapshot_version="v1.2.0-gazette-verified",
        generated_at="2026-09-25T06:00:00Z",
    )

    # Core Assertions
    assert passport.document_title == PASSPORT_DOCUMENT_TITLE
    assert passport.overall_verdict == "COMPLIANT"
    assert passport.lifecycle_state == "FINALIZED"
    assert passport.total_requirements == 8
    assert passport.satisfied_count == 8
    assert passport.not_satisfied_count == 0
    assert passport.missing_evidence_count == 0
    assert passport.unverified_count == 0
    assert passport.conflicting_count == 0
    assert passport.expert_review_count == 0
    assert len(passport.required_next_actions) == 0
    assert len(passport.expert_review_items) == 0

    # Requirement rows evaluation
    assert len(passport.requirements_matrix) == 8
    for row in passport.requirements_matrix:
        assert row.status == RequirementGapStatus.SATISFIED
        assert row.deterministic_result == "PASS"
        assert row.evidence_id is not None
        assert row.evidence_status == "VERIFIED"
        assert row.required_next_action == GapNextAction.NO_ACTION_REQUIRED

    # Cryptographic integrity seal exists and is 64 hex characters
    assert len(passport.integrity_seal) == 64


# =========================================================================
# 2. Partially Satisfied Product Test
# =========================================================================
def test_partially_satisfied_product_passport():
    """When some requirements pass and some lack evidence, overall verdict is GAPS_IDENTIFIED."""
    # Only 3 evidences provided out of 8
    evidences = [
        _make_evidence("EV-40", EvidenceType.PRODUCT_PHOTOGRAPH, extracted_value="Non-toxic food-safe construction", applicable_clause="4.0", applicable_requirement="REQ-IS17526-4.0"),
        _make_evidence("EV-421", EvidenceType.DECLARATION, extracted_value="Food contact surfaces SS 304 conforming to IS 6911", applicable_clause="4.2.1", applicable_requirement="REQ-IS17526-4.2.1"),
        _make_evidence("EV-54", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="64.5 C", normalized_value=64.5, applicable_clause="5.4", applicable_requirement="REQ-IS17526-5.4"),
    ]
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-FLASK-PARTIAL",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )
    assert gap_result.overall_verdict == "GAPS_IDENTIFIED"

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-FLASK-PARTIAL",
        product_name="Partial Flask 750ml",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
    )

    # Invariant: A partially satisfied product must never be marked COMPLIANT
    assert passport.overall_verdict == "GAPS_IDENTIFIED"
    assert passport.lifecycle_state == "GAPS_IDENTIFIED"
    assert passport.satisfied_count == 3
    assert passport.missing_evidence_count == 5
    assert len(passport.required_next_actions) == 5

    # Check individual rows preserved
    row_54 = next(r for r in passport.requirements_matrix if r.clause_number == "5.4")
    assert row_54.status == RequirementGapStatus.SATISFIED
    assert row_54.deterministic_result == "PASS"

    row_52 = next(r for r in passport.requirements_matrix if r.clause_number == "5.2")
    assert row_52.status == RequirementGapStatus.MISSING_EVIDENCE
    assert row_52.deterministic_result == "GAP_IDENTIFIED"
    assert row_52.evidence_id is None
    assert row_52.observed_value is None


# =========================================================================
# 3. Missing Evidence Test
# =========================================================================
def test_missing_evidence_passport():
    """Mandatory requirement with no evidence is preserved as MISSING_EVIDENCE with specific next action."""
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-FLASK-NO-EVID",
        target_standard="IS 17526:2021",
        evidence_records=[],
    )
    assert gap_result.overall_verdict == "GAPS_IDENTIFIED"
    assert gap_result.missing_evidence_count == 8

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-FLASK-NO-EVID",
        product_name="Unverified Flask Zero Evidence",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=[],
    )

    assert passport.missing_evidence_count == 8
    assert passport.satisfied_count == 0
    assert len(passport.roadmap_lab_test) > 0

    # Verify no fabricated values
    for row in passport.requirements_matrix:
        assert row.status == RequirementGapStatus.MISSING_EVIDENCE
        assert row.evidence_id is None
        assert row.observed_value is None
        assert row.deterministic_result == "GAP_IDENTIFIED"


# =========================================================================
# 4. Failed Requirement Test
# =========================================================================
def test_failed_requirement_passport():
    """A measured temperature of 52.0 C (< 60.0 C) yields NOT_SATISFIED and NON_COMPLIANT overall."""
    evidences = [
        _make_evidence("EV-40", EvidenceType.PRODUCT_PHOTOGRAPH, extracted_value="Non-toxic food-safe construction", applicable_clause="4.0", applicable_requirement="REQ-IS17526-4.0"),
        _make_evidence("EV-41", EvidenceType.PRODUCT_PHOTOGRAPH, extracted_value="Free from sharp burrs and defects", applicable_clause="4.1", applicable_requirement="REQ-IS17526-4.1"),
        _make_evidence("EV-421", EvidenceType.DECLARATION, extracted_value="Food contact surfaces SS 304 conforming to IS 6911", applicable_clause="4.2.1", applicable_requirement="REQ-IS17526-4.2.1"),
        _make_evidence("EV-51", EvidenceType.MANUFACTURER_DATASHEET, extracted_value="1000 ml", normalized_value=1000, applicable_clause="5.1", applicable_requirement="REQ-IS17526-5.1"),
        _make_evidence("EV-52", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="PASS - Zero moisture droplets", applicable_clause="5.2", applicable_requirement="REQ-IS17526-5.2"),
        _make_evidence("EV-53", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="PASS - 1.0m concrete drop intact", applicable_clause="5.3", applicable_requirement="REQ-IS17526-5.3"),
        _make_evidence("EV-54-FAIL", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="52.0 C", normalized_value=52.0, applicable_clause="5.4", applicable_requirement="REQ-IS17526-5.4"),
        _make_evidence("EV-71", EvidenceType.LABEL_MARKING_EVIDENCE, extracted_value="IS 17526 CM/L-99887766 Model SS-1000", applicable_clause="7.1", applicable_requirement="REQ-IS17526-7.1"),
    ]
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-FAIL-01",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )
    assert gap_result.overall_verdict == "NON_COMPLIANT"

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-FAIL-01",
        product_name="Failing Flask 1000ml",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
    )

    assert passport.overall_verdict == "NON_COMPLIANT"
    assert passport.lifecycle_state == "NON_COMPLIANT"
    assert passport.not_satisfied_count == 1
    assert passport.satisfied_count == 7
    assert len(passport.roadmap_corrective_action) == 1

    row_fail = next(r for r in passport.requirements_matrix if r.clause_number == "5.4")
    assert row_fail.status == RequirementGapStatus.NOT_SATISFIED
    assert row_fail.deterministic_result == "FAIL"
    assert row_fail.required_next_action == GapNextAction.CORRECTIVE_ACTION_REQUIRED
    assert row_fail.observed_value == "52.0 C"


# =========================================================================
# 5. Conflicting Evidence Test
# =========================================================================
def test_conflicting_evidence_passport():
    """Contradictory test reports yield CONFLICTING, EXPERT_REVIEW_REQUIRED, and UNDER_REVIEW lifecycle."""
    ev_pass = _make_evidence("EV-PASS-01", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="64.5 C", normalized_value=64.5, applicable_clause="5.4", applicable_requirement="REQ-IS17526-5.4")
    ev_fail = _make_evidence("EV-FAIL-01", EvidenceType.LABORATORY_TEST_REPORT, extracted_value="54.0 C", normalized_value=54.0, applicable_clause="5.4", applicable_requirement="REQ-IS17526-5.4")

    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-CONFLICT-01",
        target_standard="IS 17526:2021",
        evidence_records=[ev_pass, ev_fail],
    )
    assert gap_result.conflicting_count == 1

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-CONFLICT-01",
        product_name="Conflicting Flask 1000ml",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=[ev_pass, ev_fail],
    )

    assert passport.conflicting_count == 1
    assert passport.lifecycle_state == "UNDER_REVIEW"
    assert len(passport.expert_review_items) >= 1
    assert passport.overall_verdict != "COMPLIANT"

    exp_item = passport.expert_review_items[0]
    assert exp_item.clause_number == "5.4"
    assert "conflicting" in exp_item.reason.lower() or "contradictory" in exp_item.reason.lower()


# =========================================================================
# 6. Expert-Review Requirement Test
# =========================================================================
def test_expert_review_requirement_passport():
    """Borderline/expert review requirement is explicitly preserved and surfaced in expert_review_items."""
    ev_ambiguous = _make_evidence(
        "EV-AMBIG-01",
        EvidenceType.LABORATORY_TEST_REPORT,
        extracted_value="60.0 C",
        normalized_value=60.0,
        applicable_clause="5.4",
        applicable_requirement="REQ-IS17526-5.4",
        notes="Borderline test result near ambient limit, expert review recommended",
    )
    # Manually create gap result with EXPERT_REVIEW_REQUIRED to test projection
    gap_item = ComplianceGapItem(
        standard="IS 17526",
        revision="2021",
        clause="5.4",
        requirement="REQ-IS17526-5.4",
        current_evidence="EV-AMBIG-01",
        evidence_status="VERIFIED",
        gap_status=RequirementGapStatus.EXPERT_REVIEW_REQUIRED,
        reason="Borderline thermal value exactly at threshold, expert adjudication required.",
        required_next_action=GapNextAction.EXPERT_REVIEW_REQUIRED,
        provenance="Lab report verified, measurement uncertainty requires expert review",
    )
    gap_result = DeterministicGapAggregationResult(
        aggregation_id="GAP-AGG-TEST-EXP",
        product_id="PROD-EXP-01",
        target_standard="IS 17526:2021",
        standard_revision="2021",
        overall_verdict="GAPS_IDENTIFIED",
        total_requirements=1,
        expert_review_count=1,
        gap_items=[gap_item],
        roadmap_expert_review=[gap_item],
    )

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-EXP-01",
        product_name="Expert Review Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=[ev_ambiguous],
    )

    assert passport.expert_review_count == 1
    assert len(passport.expert_review_items) == 1
    assert passport.lifecycle_state == "UNDER_REVIEW"
    assert passport.expert_review_items[0].clause_number == "5.4"


# =========================================================================
# 7. Source & Version Provenance Test
# =========================================================================
def test_source_and_version_provenance():
    """Validates that Product DNA provenance, standard revisions, and evidence sources propagate accurately."""
    dna = ProductDNACore(
        product_name="EcoSteel Flask",
        category="Domestic Vacuum Flasks",
        intended_use="Drinking Water",
        materials=["SS 304", "Polypropylene"],
        insulated=True,
        attributes=[
            DNAAttribute(name="volume_ml", value=750, data_type="integer", unit="ml"),
            DNAAttribute(name="lead_ppm", value=12, data_type="integer", unit="ppm"),
        ],
        facts=[
            ProductFact(
                fact_id="FACT-01",
                field_name="material",
                display_name="Material Grade",
                value="SS 304",
                provenance=FactProvenanceType.VERIFIED_DOCUMENT_FACT,
                fact_category=FactCategory.VERIFIED_DOCUMENTARY_EVIDENCE,
                verification_state=FactVerificationState.CONFIRMED,
            )
        ],
    )

    evidences = _make_all_8_satisfied_evidences()
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-PROV-01",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-PROV-01",
        product_name="EcoSteel Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
        product_dna=dna,
        source_snapshot_version="v1.3.0-snapshot-audited",
        ruleset_version="2026.04-gazette",
        knowledge_version="v1.3.0-bis-master",
    )

    # Product DNA provenance checks
    assert passport.product.product_dna_provenance == FactProvenanceType.VERIFIED_DOCUMENT_FACT.value
    assert len(passport.product.product_dna_digest) == 64
    assert passport.product.product_dna_attributes["materials"] == ["SS 304", "Polypropylene"]
    assert passport.product.product_dna_attributes["insulated"] is True

    # Standard and revision provenance checks
    assert len(passport.applicable_standards) == 1
    assert passport.applicable_standards[0].standard_code == "IS 17526"
    assert passport.applicable_standards[0].revision == "2021"
    assert "Cookware, Utensils and Canisters" in passport.applicable_standards[0].qco_order

    # Version tracking
    assert passport.source_snapshot_version == "v1.3.0-snapshot-audited"
    assert passport.ruleset_version == "2026.04-gazette"
    assert passport.knowledge_version == "v1.3.0-bis-master"

    # Evidence hashes propagation
    assert len(passport.evidence_hashes) == 8
    for ev in evidences:
        assert ev.evidence_id in passport.evidence_hashes
        assert passport.evidence_hashes[ev.evidence_id] == ev.sha256


# =========================================================================
# 8. SHA-256 Reproducibility Test
# =========================================================================
def test_sha256_reproducibility():
    """Identical deterministic inputs yield identical bit-for-bit SHA-256 seal. Alterations change it."""
    evidences = _make_all_8_satisfied_evidences()
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-REPRO-01",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )

    fixed_time = "2026-09-25T12:00:00Z"

    # Run 1
    p1 = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-REPRO-01",
        product_name="Reproducible Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
        generated_at=fixed_time,
    )

    # Run 2
    p2 = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-REPRO-01",
        product_name="Reproducible Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
        generated_at=fixed_time,
    )

    # Bit-for-bit seal reproducibility
    assert p1.integrity_seal == p2.integrity_seal
    assert len(p1.integrity_seal) == 64

    # Run 3 with mutated evidence record
    mutated_ev = list(evidences)
    mutated_ev[0] = _make_evidence("EV-40", EvidenceType.PRODUCT_PHOTOGRAPH, extracted_value="Slightly altered photo text", applicable_clause="4.0", applicable_requirement="REQ-IS17526-4.0")
    p3 = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-REPRO-01",
        product_name="Reproducible Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=mutated_ev,
        generated_at=fixed_time,
    )

    # Seal must change when evidence changes
    assert p3.integrity_seal != p1.integrity_seal


# =========================================================================
# 9. BIS Certification Disclaimer & Prohibited Labels Test
# =========================================================================
def test_bis_certification_disclaimer_and_prohibited_labels():
    """Passport strictly disclaims BIS certification and rejects prohibited marketing/statutory labels."""
    evidences = _make_all_8_satisfied_evidences()
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-DISCLAIM-01",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-DISCLAIM-01",
        product_name="Standard Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
    )

    # Required Title
    assert passport.document_title == "Evidence-Backed Pre-Certification Compliance Assessment"

    # Required Distinction: Compliance Passport != BIS Certification
    assert "Compliance Passport ≠ BIS Certification" in passport.statutory_disclaimer
    assert "statutory approval" in passport.statutory_disclaimer.lower()

    # Rejection of Prohibited Labels in product name or input
    with pytest.raises(ValueError, match="Prohibited regulatory certification claims detected"):
        compliance_passport_generator.generate_compliance_passport(
            product_id="PROD-BAD-01",
            product_name="Product with BIS Certificate Approved",
            category="Domestic Vacuum Flasks",
            target_standard="IS 17526:2021",
            gap_result=gap_result,
            evidence_records=evidences,
        )

    with pytest.raises(ValueError, match="Prohibited regulatory certification claims detected"):
        compliance_passport_generator.generate_compliance_passport(
            product_id="PROD-BAD-02",
            product_name="Flask Guaranteed Compliance",
            category="Domestic Vacuum Flasks",
            target_standard="IS 17526:2021",
            gap_result=gap_result,
            evidence_records=evidences,
        )


# =========================================================================
# 10. Zero LLM Compliance Authority Test
# =========================================================================
def test_zero_llm_compliance_authority():
    """Verifies that LLM has 0.0% authority and Layer 7/8/9 boundaries are strictly enforced."""
    evidences = _make_all_8_satisfied_evidences()
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-AUTH-01",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-AUTH-01",
        product_name="Safe Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
    )

    # Authority Boundary Invariants
    assert passport.compliance_authority == "LAYER_7_ONLY"
    assert passport.evidence_authority == "LAYER_8_ONLY"
    assert passport.output_integrity_authority == "LAYER_9_PASSPORT_COMPILER"
    assert passport.llm_compliance_authority == 0.0
    assert passport.regulatory_conclusion == "NONE"

    # Attempt to pass an unauthorized compliance authority triggers failure
    tampered_gap = gap_result.model_copy(update={"compliance_authority": "LLM_ANALYSIS_AGENT"})
    with pytest.raises(ValueError, match="Authority Violation"):
        compliance_passport_generator.generate_compliance_passport(
            product_id="PROD-TAMPER-01",
            product_name="Tampered Flask",
            category="Domestic Vacuum Flasks",
            target_standard="IS 17526:2021",
            gap_result=tampered_gap,
            evidence_records=evidences,
        )

    # Attempt to assign non-zero LLM authority triggers failure
    tampered_llm = gap_result.model_copy(update={"llm_compliance_authority": 0.85})
    with pytest.raises(ValueError, match="Authority Violation"):
        compliance_passport_generator.generate_compliance_passport(
            product_id="PROD-TAMPER-02",
            product_name="Tampered LLM Flask",
            category="Domestic Vacuum Flasks",
            target_standard="IS 17526:2021",
            gap_result=tampered_llm,
            evidence_records=evidences,
        )


# =========================================================================
# 11. No Invented Evidence or Regulatory Facts Test
# =========================================================================
def test_no_invented_evidence_or_regulatory_facts():
    """Asserts that missing evidence has NONE, no fake lab names, and no synthetic clauses."""
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-NO-INVENT-01",
        target_standard="IS 17526:2021",
        evidence_records=[],
    )

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id="PROD-NO-INVENT-01",
        product_name="No Invented Facts Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=[],
    )

    # Ensure no fabricated labs appear when zero lab evidence is submitted
    assert len(passport.recognized_laboratories) == 0

    # Ensure no fake evidence IDs or synthetic test values exist
    for r in passport.requirements_matrix:
        assert r.evidence_id is None
        assert r.evidence_type is None
        assert r.observed_value is None
        assert r.deterministic_result == "GAP_IDENTIFIED"
        assert r.status == RequirementGapStatus.MISSING_EVIDENCE


# =========================================================================
# 12. Compiler Delegation & REST API Endpoints Test
# =========================================================================
def test_compiler_delegation_and_rest_endpoints():
    """Validates passport_compiler delegation method and REST API endpoints."""
    evidences = _make_all_8_satisfied_evidences()
    gap_result = gap_aggregation_service.aggregate_compliance_gaps(
        product_id="PROD-COMPILER-01",
        target_standard="IS 17526:2021",
        evidence_records=evidences,
    )

    # Test passport_compiler.generate_evidence_backed_passport
    passport = passport_compiler.generate_evidence_backed_passport(
        product_id="PROD-COMPILER-01",
        product_name="Compiler Flask",
        category="Domestic Vacuum Flasks",
        target_standard="IS 17526:2021",
        gap_result=gap_result,
        evidence_records=evidences,
    )
    assert passport.overall_verdict == "COMPLIANT"
    assert passport.document_title == PASSPORT_DOCUMENT_TITLE

    # Test /api/v1/passport/invariants endpoint
    res_inv = client.get("/api/v1/passport/invariants")
    assert res_inv.status_code == 200
    inv_data = res_inv.json()
    assert inv_data["document_title"] == PASSPORT_DOCUMENT_TITLE
    assert "COMPLIANCE PASSPORT != BIS CERTIFICATION" in inv_data["invariants"]

    # Test /api/v1/passport/generate-evidence-backed endpoint
    res_gen = client.post(
        "/api/v1/passport/generate-evidence-backed",
        json={
            "product_id": "PROD-REST-01",
            "product_name": "REST API Flask",
            "category": "Domestic Vacuum Flasks",
            "target_standard": "IS 17526:2021",
            "gap_result": gap_result.model_dump(mode="json"),
            "evidence_records": [ev.model_dump(mode="json") for ev in evidences],
        },
    )
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["overall_verdict"] == "COMPLIANT"
    assert gen_data["document_title"] == PASSPORT_DOCUMENT_TITLE
    assert len(gen_data["integrity_seal"]) == 64
