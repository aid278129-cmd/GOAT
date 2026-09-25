"""Evidence Eligibility Engine (Milestone M25.2A).

Enforces Cardinal Non-Negotiables:
1. Requirement -> Permitted Evidence Types -> Eligibility -> Evaluation.
2. A Manufacturer Datasheet CANNOT satisfy a laboratory test requirement.
3. User Claims CANNOT satisfy any technical or regulatory requirement.
4. Level 2 Documentary Evidence is NOT universally sufficient for all requirements.
5. NOT_ELIGIBLE != NON_COMPLIANT; MISSING_REQUIRED_EVIDENCE != FAILED_REQUIREMENT.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from backend.app.schemas.product_evidence import (
    EvidenceType,
    EvidenceHierarchyLevel,
    EvidenceVerificationStatus,
    SourceAuthenticity,
    ProductEvidenceRecord,
)


class EligibilityStatus(str, Enum):
    """Deterministic eligibility states for evidence against requirements."""
    ELIGIBLE = "ELIGIBLE"
    PARTIALLY_ELIGIBLE = "PARTIALLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    MISSING_REQUIRED_EVIDENCE = "MISSING_REQUIRED_EVIDENCE"
    UNVERIFIED_EVIDENCE = "UNVERIFIED_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    EXPERT_REVIEW_REQUIRED = "EXPERT_REVIEW_REQUIRED"


class RequirementClass(str, Enum):
    """Taxonomy of compliance requirements determining permissible evidence types."""
    TECHNICAL_SPECIFICATION = "TECHNICAL_SPECIFICATION"   # Voltage, power, capacity, materials
    LAB_TEST_REQUIREMENT = "LAB_TEST_REQUIREMENT"         # Insulation resistance, leakage, pressure proof
    CERTIFICATION_RECORD = "CERTIFICATION_RECORD"         # BIS license, ISO cert, CRS registration
    PHYSICAL_MARKING = "PHYSICAL_MARKING"                 # Rating plate, ISI mark label, safety warnings
    BILL_OF_MATERIALS = "BILL_OF_MATERIALS"               # Component specs, subcomponent standards
    DECLARATION_REQUIREMENT = "DECLARATION_REQUIREMENT"   # Declaration of conformity, food-grade affidavit
    VISUAL_CONSTRUCTION = "VISUAL_CONSTRUCTION"           # Visual inspection, workmanship, physical finish


# Permissible evidence type matrix
PERMITTED_EVIDENCE_TYPES: Dict[RequirementClass, Set[EvidenceType]] = {
    RequirementClass.TECHNICAL_SPECIFICATION: {
        EvidenceType.PRODUCT_SPECIFICATION,
        EvidenceType.DATASHEET,
        EvidenceType.MANUFACTURER_DATASHEET,
        EvidenceType.USER_MANUAL,
        EvidenceType.TECHNICAL_DRAWING,
        EvidenceType.BOM,
        EvidenceType.MANUFACTURER_DOCUMENT,
        EvidenceType.DECLARATION,
        EvidenceType.TEST_REPORT,  # Test reports can corroborate specifications
        EvidenceType.LABORATORY_TEST_REPORT,
    },
    RequirementClass.LAB_TEST_REQUIREMENT: {
        EvidenceType.TEST_REPORT,  # Strictly requires accredited or certified lab test report
        EvidenceType.LABORATORY_TEST_REPORT,
    },
    RequirementClass.CERTIFICATION_RECORD: {
        EvidenceType.CERTIFICATE_REFERENCE,
        EvidenceType.CERTIFICATE,
        EvidenceType.DECLARATION,
    },
    RequirementClass.PHYSICAL_MARKING: {
        EvidenceType.LABEL_PHOTO,
        EvidenceType.RATING_PLATE_PHOTO,
        EvidenceType.LABEL_MARKING_EVIDENCE,
        EvidenceType.PRODUCT_PHOTOGRAPH,
        EvidenceType.TECHNICAL_DRAWING,
    },
    RequirementClass.BILL_OF_MATERIALS: {
        EvidenceType.BOM,
        EvidenceType.TECHNICAL_DRAWING,
        EvidenceType.PRODUCT_SPECIFICATION,
    },
    RequirementClass.DECLARATION_REQUIREMENT: {
        EvidenceType.DECLARATION,
        EvidenceType.MANUFACTURER_DOCUMENT,
    },
    RequirementClass.VISUAL_CONSTRUCTION: {
        EvidenceType.PRODUCT_PHOTOGRAPH,
        EvidenceType.LABEL_MARKING_EVIDENCE,
        EvidenceType.TECHNICAL_DRAWING,
        EvidenceType.LABEL_PHOTO,
        EvidenceType.RATING_PLATE_PHOTO,
    },
}


class EligibilityEvaluationResult(BaseModel):
    """Result of evaluating an evidence artifact against a specific requirement."""
    requirement_id: str
    requirement_class: RequirementClass
    required_evidence_type: str
    provided_evidence_id: Optional[str] = None
    provided_evidence_type: Optional[EvidenceType] = None
    status: EligibilityStatus
    is_eligible: bool
    reason: str
    permitted_types: List[str] = Field(default_factory=list)


class EvidenceEligibilityEngine:
    """Deterministic engine evaluating whether evidence artifacts qualify for given requirements."""

    @classmethod
    def infer_requirement_class(cls, requirement_name: str, attribute: str = "") -> RequirementClass:
        """Deterministically infer requirement class from requirement identifier and product attribute."""
        combined = f"{requirement_name} {attribute}".lower()

        # Lab test indicators
        if any(kw in combined for kw in (
            "test", "leakage", "resistance", "hydrostatic", "pressure_proof", "proof_pressure",
            "dielectric", "withstand", "flame", "impact_test", "temperature_rise",
            "earthing_continuity", "conductor_resistance", "insulation_resistance",
            "thermal_performance", "hot_water_retention", "thermal", "drop_test",
        )):
            return RequirementClass.LAB_TEST_REQUIREMENT

        # Marking / Rating plate indicators
        if any(kw in combined for kw in ("marking", "label", "plate", "nameplate", "rating_plate")):
            return RequirementClass.PHYSICAL_MARKING

        # Visual / Workmanship / Photograph indicators
        if any(kw in combined for kw in ("visual", "photo", "photograph", "workmanship", "finish", "construction")):
            return RequirementClass.VISUAL_CONSTRUCTION

        # Declaration indicators
        if any(kw in combined for kw in ("declaration", "affidavit", "self_declaration", "doc_conformity")):
            return RequirementClass.DECLARATION_REQUIREMENT

        # Certification indicators
        if any(kw in combined for kw in ("certificate", "license", "licence", "registration", "crs_no")):
            return RequirementClass.CERTIFICATION_RECORD

        # BOM indicators
        if any(kw in combined for kw in ("bom", "bill_of_materials", "subcomponent", "raw_material_spec")):
            return RequirementClass.BILL_OF_MATERIALS

        # Default to technical specification
        return RequirementClass.TECHNICAL_SPECIFICATION

    @classmethod
    def check_eligibility(
        cls,
        requirement_id: str,
        requirement_name: str,
        evidence: Optional[ProductEvidenceRecord],
        explicit_class: Optional[RequirementClass] = None,
    ) -> EligibilityEvaluationResult:
        """Check whether the provided evidence is eligible to evaluate this requirement."""
        req_class = explicit_class or cls.infer_requirement_class(
            requirement_id,
            evidence.attribute if evidence else "",
        )
        permitted = PERMITTED_EVIDENCE_TYPES.get(req_class, set())
        permitted_names = [t.value for t in permitted]

        # Case 1: Missing evidence
        if evidence is None or evidence.evidence_type == EvidenceType.MISSING_EVIDENCE:
            return EligibilityEvaluationResult(
                requirement_id=requirement_id,
                requirement_class=req_class,
                required_evidence_type=req_class.value,
                provided_evidence_id=None,
                provided_evidence_type=EvidenceType.MISSING_EVIDENCE if evidence else None,
                status=EligibilityStatus.MISSING_REQUIRED_EVIDENCE,
                is_eligible=False,
                reason=f"No evidence artifact provided for requirement '{requirement_id}'.",
                permitted_types=permitted_names,
            )

        # Case 2: Untrusted user claim (USER CLAIM != DOCUMENT != VERIFIED EVIDENCE)
        if evidence.evidence_type in (EvidenceType.USER_PROVIDED_CLAIM, EvidenceType.USER_CLAIM):
            return EligibilityEvaluationResult(
                requirement_id=requirement_id,
                requirement_class=req_class,
                required_evidence_type=req_class.value,
                provided_evidence_id=evidence.evidence_id,
                provided_evidence_type=evidence.evidence_type,
                status=EligibilityStatus.NOT_ELIGIBLE,
                is_eligible=False,
                reason="User provided claim (Level 0) cannot serve as authoritative regulatory evidence.",
                permitted_types=permitted_names,
            )

        # Case 3: Conflicting evidence
        if (
            evidence.evidence_type == EvidenceType.CONFLICTING_EVIDENCE
            or evidence.verification_status == EvidenceVerificationStatus.CONFLICTING
        ):
            return EligibilityEvaluationResult(
                requirement_id=requirement_id,
                requirement_class=req_class,
                required_evidence_type=req_class.value,
                provided_evidence_id=evidence.evidence_id,
                provided_evidence_type=evidence.evidence_type,
                status=EligibilityStatus.CONFLICTING_EVIDENCE,
                is_eligible=False,
                reason="Evidence artifact is flagged as conflicting; requires expert resolution.",
                permitted_types=permitted_names,
            )

        # Case 4: Unsupported / unverified artifact
        if evidence.evidence_type == EvidenceType.UNSUPPORTED_ARTIFACT:
            return EligibilityEvaluationResult(
                requirement_id=requirement_id,
                requirement_class=req_class,
                required_evidence_type=req_class.value,
                provided_evidence_id=evidence.evidence_id,
                provided_evidence_type=evidence.evidence_type,
                status=EligibilityStatus.UNVERIFIED_EVIDENCE,
                is_eligible=False,
                reason=f"Unsupported or unverified artifact '{evidence.evidence_id}' cannot satisfy requirement.",
                permitted_types=permitted_names,
            )

        # Case 5: Strict Lab Test Gating
        # Invariant: A manufacturer datasheet CANNOT satisfy an empirical laboratory-test requirement
        # unless an existing deterministic evidence rule explicitly permits it.
        if req_class == RequirementClass.LAB_TEST_REQUIREMENT and evidence.evidence_type in (
            EvidenceType.MANUFACTURER_DATASHEET,
            EvidenceType.DATASHEET,
            EvidenceType.PRODUCT_SPECIFICATION,
            EvidenceType.DECLARATION,
            EvidenceType.MANUFACTURER_DOCUMENT,
            EvidenceType.USER_MANUAL,
        ):
            return EligibilityEvaluationResult(
                requirement_id=requirement_id,
                requirement_class=req_class,
                required_evidence_type=req_class.value,
                provided_evidence_id=evidence.evidence_id,
                provided_evidence_type=evidence.evidence_type,
                status=EligibilityStatus.NOT_ELIGIBLE,
                is_eligible=False,
                reason=(
                    f"Evidence type '{evidence.evidence_type.value}' is NOT eligible for requirement class '{req_class.value}'. "
                    f"Manufacturer datasheet/document cannot satisfy empirical laboratory-test requirement '{requirement_id}' "
                    f"unless an existing deterministic evidence rule explicitly permits it. Accredited laboratory test report required."
                ),
                permitted_types=permitted_names,
            )

        # Case 6: Incompatible evidence class
        if evidence.evidence_type not in permitted:
            return EligibilityEvaluationResult(
                requirement_id=requirement_id,
                requirement_class=req_class,
                required_evidence_type=req_class.value,
                provided_evidence_id=evidence.evidence_id,
                provided_evidence_type=evidence.evidence_type,
                status=EligibilityStatus.NOT_ELIGIBLE,
                is_eligible=False,
                reason=(
                    f"Evidence type '{evidence.evidence_type.value}' is NOT eligible for "
                    f"requirement class '{req_class.value}'. Permitted: {', '.join(permitted_names)}."
                ),
                permitted_types=permitted_names,
            )

        # Case 7: Unverified evidence
        if not evidence.verified or evidence.verification_status != EvidenceVerificationStatus.VERIFIED:
            return EligibilityEvaluationResult(
                requirement_id=requirement_id,
                requirement_class=req_class,
                required_evidence_type=req_class.value,
                provided_evidence_id=evidence.evidence_id,
                provided_evidence_type=evidence.evidence_type,
                status=EligibilityStatus.UNVERIFIED_EVIDENCE,
                is_eligible=False,
                reason=f"Evidence artifact '{evidence.evidence_id}' has unverified status: {evidence.verification_status.value}.",
                permitted_types=permitted_names,
            )

        # Case 8: Fully eligible
        return EligibilityEvaluationResult(
            requirement_id=requirement_id,
            requirement_class=req_class,
            required_evidence_type=req_class.value,
            provided_evidence_id=evidence.evidence_id,
            provided_evidence_type=evidence.evidence_type,
            status=EligibilityStatus.ELIGIBLE,
            is_eligible=True,
            reason=f"Evidence artifact '{evidence.evidence_id}' ({evidence.evidence_type.value}) is eligible for requirement evaluation.",
            permitted_types=permitted_names,
        )

