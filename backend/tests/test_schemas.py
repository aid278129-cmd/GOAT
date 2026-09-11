import pytest
from pydantic import ValidationError
from backend.app.schemas.product_dna import (
    ProductDNACore,
    DNAAttribute,
    AttributeProvenance,
    ClarificationRequirement,
)
from backend.app.schemas.compliance import (
    ComplianceStatus,
    ApplicabilityStatus,
    ComplianceAssessmentItem,
    ProvenanceCitation,
)
from backend.app.schemas.evidence import (
    ValidationStatus,
    EvidenceItem,
    CitationGuardCheckResponse,
)


def test_product_dna_schema_valid():
    dna = ProductDNACore(
        product_name="Insulated Stainless Steel Flask",
        category="Drinkware",
        sub_category="Vacuum Flasks",
        materials=["Stainless Steel 304", "Polypropylene Cap"],
        insulated=True,
        electrical=False,
        attributes=[
            DNAAttribute(
                name="nominal_capacity_ml",
                value=750,
                data_type="integer",
                unit="ml",
                provenance=AttributeProvenance(
                    source_document="catalog_spec_2024.pdf",
                    page=3,
                    source_text="Capacity: 750ml nominal",
                    confidence=0.98,
                    extraction_method="parsed",
                ),
            )
        ],
    )
    assert dna.product_name == "Insulated Stainless Steel Flask"
    assert dna.attributes[0].value == 750
    assert dna.attributes[0].provenance.confidence == 0.98


def test_product_dna_clarification_handling():
    dna = ProductDNACore(
        product_name="Generic Electric Kettle",
        category="Household Appliances",
        electrical=True,
        pending_clarifications=[
            ClarificationRequirement(
                attribute_name="operating_voltage",
                reason="Mandatory for IS 302-2-15 applicability check",
                options=["230V AC", "110V AC"],
                criticality="HIGH",
            )
        ],
    )
    assert len(dna.pending_clarifications) == 1
    assert dna.pending_clarifications[0].attribute_name == "operating_voltage"


def test_compliance_status_enums():
    # Rich multi-state audit-compliant statuses (8 states)
    assert ComplianceStatus.SATISFIED.value == "SATISFIED"
    assert ComplianceStatus.POTENTIALLY_SATISFIED.value == "POTENTIALLY_SATISFIED"
    assert ComplianceStatus.MISSING_EVIDENCE.value == "MISSING_EVIDENCE"
    assert ComplianceStatus.MORE_INFORMATION_REQUIRED.value == "MORE_INFORMATION_REQUIRED"
    assert ComplianceStatus.POTENTIAL_GAP.value == "POTENTIAL_GAP"
    assert ComplianceStatus.NOT_APPLICABLE.value == "NOT_APPLICABLE"
    assert ComplianceStatus.CONFLICTING_EVIDENCE.value == "CONFLICTING_EVIDENCE"
    assert ComplianceStatus.REQUIRES_EXPERT_REVIEW.value == "REQUIRES_EXPERT_REVIEW"

    # Expressive decoupled action recommendations (4 actions)
    from backend.app.schemas.compliance import RecommendedAction
    assert RecommendedAction.REQUIRES_TESTING.value == "REQUIRES_TESTING"
    assert RecommendedAction.UPLOAD_EVIDENCE.value == "UPLOAD_EVIDENCE"
    assert RecommendedAction.PROVIDE_SPECIFICATION.value == "PROVIDE_SPECIFICATION"
    assert RecommendedAction.EXPERT_REVIEW.value == "EXPERT_REVIEW"

    assert ApplicabilityStatus.LIKELY_APPLICABLE.value == "LIKELY_APPLICABLE"


def test_provenance_citation_schema():
    citation = ProvenanceCitation(
        claim="Product material must resist corrosion according to standard clause",
        document_name="IS_17526_2021.pdf",
        standard_number="IS 17526:2021",
        clause_number="4.2",
        page_number=5,
        supporting_text="Stainless steel parts in contact with liquid shall conform to Grade 304...",
        validation_status="SUPPORTED",
    )
    item = ComplianceAssessmentItem(
        clause_number="4.2",
        clause_title="Material Requirements",
        status=ComplianceStatus.SATISFIED,
        explanation="Product uses Grade 304 Stainless Steel matching clause 4.2",
        citation=citation,
    )
    assert item.citation.clause_number == "4.2"
    assert item.status == ComplianceStatus.SATISFIED
