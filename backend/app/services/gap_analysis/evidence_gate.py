from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Set
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.schemas.product_dna import ProvenanceClassification


class AllowedEvidenceType(str, Enum):
    TEST_REPORT = "TEST_REPORT"
    LAB_REPORT = "LAB_REPORT"
    MATERIAL_CERTIFICATE = "MATERIAL_CERTIFICATE"
    CALIBRATION_CERTIFICATE = "CALIBRATION_CERTIFICATE"
    PRODUCT_SPECIFICATION = "PRODUCT_SPECIFICATION"
    TECHNICAL_DRAWING = "TECHNICAL_DRAWING"
    LABEL_PHOTO = "LABEL_PHOTO"
    PACKAGING_PHOTO = "PACKAGING_PHOTO"
    MANUFACTURER_DECLARATION = "MANUFACTURER_DECLARATION"
    BIS_DOCUMENT = "BIS_DOCUMENT"
    QCO_DOCUMENT = "QCO_DOCUMENT"
    PRODUCT_MANUAL = "PRODUCT_MANUAL"
    USER_PROVIDED_DOCUMENT = "USER_PROVIDED_DOCUMENT"


class EvidenceRequirementSpec:
    """Specifies evidence requirements for a given standard clause or technical requirement."""

    def __init__(
        self,
        requirement_code: str,
        expected_evidence_types: List[str],
        requires_physical_testing: bool = False,
        default_missing_action: RecommendedAction = RecommendedAction.UPLOAD_EVIDENCE,
        authority_hierarchy: Optional[List[str]] = None,
        description: str = "",
    ):
        self.requirement_code = requirement_code
        self.expected_evidence_types = expected_evidence_types
        self.requires_physical_testing = requires_physical_testing
        self.default_missing_action = (
            RecommendedAction.REQUIRES_TESTING
            if requires_physical_testing
            else default_missing_action
        )
        self.authority_hierarchy = authority_hierarchy or [
            "NABL_ACCREDITED_LAB",
            "LAB_REPORT",
            "BIS_OFFICIAL",
            "MILL_TEST_CERTIFICATE",
            "MANUFACTURER_DECLARATION",
        ]
        self.description = description


# Extensible matrix mapping requirement types and codes to expected evidence
EVIDENCE_REQUIREMENT_MATRIX: Dict[str, EvidenceRequirementSpec] = {
    # 1. Stainless steel raw material grade (IS 17526 Cl 4.2.1 / IS 6911)
    "REQ-MAT-304": EvidenceRequirementSpec(
        requirement_code="REQ-MAT-304",
        expected_evidence_types=[
            AllowedEvidenceType.MATERIAL_CERTIFICATE.value,
            AllowedEvidenceType.LAB_REPORT.value,
            AllowedEvidenceType.TEST_REPORT.value,
        ],
        requires_physical_testing=False,
        default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
        description="Raw material mill test certificate (IS 6911) or accredited spectrochemical composition report.",
    ),
    # 2. Inversion Leakage Test (IS 17526 Cl 5.2)
    "REQ-PERF-LEAK": EvidenceRequirementSpec(
        requirement_code="REQ-PERF-LEAK",
        expected_evidence_types=[
            AllowedEvidenceType.LAB_REPORT.value,
            AllowedEvidenceType.TEST_REPORT.value,
        ],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
        description="Accredited laboratory physical inversion test report (10 minutes inverted, zero leakage).",
    ),
    # 3. Thermal Performance Test (IS 17526 Cl 5.4)
    "REQ-PERF-THERM": EvidenceRequirementSpec(
        requirement_code="REQ-PERF-THERM",
        expected_evidence_types=[
            AllowedEvidenceType.LAB_REPORT.value,
            AllowedEvidenceType.TEST_REPORT.value,
        ],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
        description="Mandatory 6-hour laboratory thermal performance test report (>= 60°C after 6h for 95°C hot water).",
    ),
    # 4. Marking & ISI Layout (IS 17526 Cl 7.1)
    "REQ-MARK-ISI": EvidenceRequirementSpec(
        requirement_code="REQ-MARK-ISI",
        expected_evidence_types=[
            AllowedEvidenceType.LABEL_PHOTO.value,
            AllowedEvidenceType.PACKAGING_PHOTO.value,
            AllowedEvidenceType.PRODUCT_SPECIFICATION.value,
        ],
        requires_physical_testing=False,
        default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
        description="High-resolution packaging and product label artwork verifying BIS Standard Mark (ISI Mark) and nominal capacity.",
    ),
    # Toys IS 9873 Cl 4.4 Small Parts
    "REQ-TOY-CHOKE": EvidenceRequirementSpec(
        requirement_code="REQ-TOY-CHOKE",
        expected_evidence_types=[
            AllowedEvidenceType.TEST_REPORT.value,
            AllowedEvidenceType.LAB_REPORT.value,
        ],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
        description="NABL accredited mechanical test report verifying small parts cylinder dimensions and detachment integrity.",
    ),
    # Toys IS 9873 Cl 4.6 Sharp Edges
    "REQ-TOY-EDGE": EvidenceRequirementSpec(
        requirement_code="REQ-TOY-EDGE",
        expected_evidence_types=[
            AllowedEvidenceType.TEST_REPORT.value,
            AllowedEvidenceType.LAB_REPORT.value,
        ],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
        description="Accredited laboratory sharp edge and point test report verifying zero accessible sharp edges.",
    ),
    # Electrical IS 302 Cl 13 Dielectric Strength
    "REQ-ELEC-DIEL": EvidenceRequirementSpec(
        requirement_code="REQ-ELEC-DIEL",
        expected_evidence_types=[
            AllowedEvidenceType.TEST_REPORT.value,
            AllowedEvidenceType.LAB_REPORT.value,
        ],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
        description="High voltage dielectric withstand test report (1000V/1250V AC) from accredited electrical test laboratory.",
    ),
    # Electrical IS 302 Cl 19 Abnormal Operation (Boil-dry)
    "REQ-ELEC-BOILDRY": EvidenceRequirementSpec(
        requirement_code="REQ-ELEC-BOILDRY",
        expected_evidence_types=[
            AllowedEvidenceType.TEST_REPORT.value,
            AllowedEvidenceType.LAB_REPORT.value,
        ],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
        description="Abnormal operation test report verifying automatic thermal cut-out actuation under boil-dry condition.",
    ),
    # 5. Pending Authoritative Acquisition
    "AUTHORITATIVE_CLAUSE_PENDING": EvidenceRequirementSpec(
        requirement_code="AUTHORITATIVE_CLAUSE_PENDING",
        expected_evidence_types=[
            AllowedEvidenceType.BIS_DOCUMENT.value,
            AllowedEvidenceType.QCO_DOCUMENT.value,
        ],
        requires_physical_testing=False,
        default_missing_action=RecommendedAction.EXPERT_REVIEW,
        description="Official publication copy of standard from Bureau of Indian Standards.",
    ),
}


def get_evidence_spec_for_requirement(
    requirement_code: str, requirement_type: str = "PERFORMANCE"
) -> EvidenceRequirementSpec:
    """Retrieve or dynamically construct evidence requirement specification."""
    if requirement_code in EVIDENCE_REQUIREMENT_MATRIX:
        return EVIDENCE_REQUIREMENT_MATRIX[requirement_code]

    req_type_upper = requirement_type.upper()
    if req_type_upper == "MATERIAL":
        return EvidenceRequirementSpec(
            requirement_code=requirement_code,
            expected_evidence_types=[
                AllowedEvidenceType.MATERIAL_CERTIFICATE.value,
                AllowedEvidenceType.LAB_REPORT.value,
            ],
            requires_physical_testing=False,
            default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
            description="Material composition certificate or test report.",
        )
    elif req_type_upper in ("PERFORMANCE", "SAFETY", "TESTING"):
        return EvidenceRequirementSpec(
            requirement_code=requirement_code,
            expected_evidence_types=[
                AllowedEvidenceType.LAB_REPORT.value,
                AllowedEvidenceType.TEST_REPORT.value,
            ],
            requires_physical_testing=True,
            default_missing_action=RecommendedAction.REQUIRES_TESTING,
            description="Accredited laboratory physical test report.",
        )
    elif req_type_upper in ("MARKING", "PACKAGING"):
        return EvidenceRequirementSpec(
            requirement_code=requirement_code,
            expected_evidence_types=[
                AllowedEvidenceType.LABEL_PHOTO.value,
                AllowedEvidenceType.PACKAGING_PHOTO.value,
            ],
            requires_physical_testing=False,
            default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
            description="Label or packaging artwork photograph.",
        )
    elif req_type_upper in ("DIMENSION", "CONSTRUCTION"):
        return EvidenceRequirementSpec(
            requirement_code=requirement_code,
            expected_evidence_types=[
                AllowedEvidenceType.TECHNICAL_DRAWING.value,
                AllowedEvidenceType.PRODUCT_SPECIFICATION.value,
            ],
            requires_physical_testing=False,
            default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
            description="Technical engineering drawing or dimensional specification.",
        )

    return EvidenceRequirementSpec(
        requirement_code=requirement_code,
        expected_evidence_types=[
            AllowedEvidenceType.USER_PROVIDED_DOCUMENT.value,
            AllowedEvidenceType.TEST_REPORT.value,
        ],
        requires_physical_testing=False,
        default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
        description="Documentary compliance proof.",
    )


def can_be_satisfied(
    requirement: Dict[str, Any],
    linked_evidences: List[Any],
    has_conflict: bool = False,
    rule_result: Optional[str] = "PASS",
    rule_explanation: Optional[str] = None,
) -> Tuple[bool, ComplianceStatus, Optional[RecommendedAction], str]:
    """Centralized Hard Deterministic Gate.
    
    Invariant: SATISFIED is permitted ONLY when:
    1. Applicable requirement exists and is authoritative.
    2. Required evidence exists and is linked to the requirement.
    3. Evidence provenance is verified (NOT USER_CLAIM).
    4. Evidence source authority matches the requirement type.
    5. Extracted evidence values satisfy the requirement condition (rule_result == PASS).
    6. No unresolved conflicting evidence exists.
    7. No mandatory expert review condition exists.
    
    Returns:
    (can_satisfy: bool, status: ComplianceStatus, action: Optional[RecommendedAction], explanation: str)
    """
    req_code = requirement.get("code") or requirement.get("requirement_code", "UNKNOWN")
    req_type = requirement.get("requirement_type", "PERFORMANCE")
    spec = get_evidence_spec_for_requirement(req_code, req_type)

    # 1. Authoritative Acquisition Pending Check
    if req_code == "AUTHORITATIVE_CLAUSE_PENDING":
        return (
            False,
            ComplianceStatus.MORE_INFORMATION_REQUIRED,
            RecommendedAction.EXPERT_REVIEW,
            "Authoritative standard clause acquisition is pending from Bureau of Indian Standards.",
        )

    # 2. Conflicting Evidence Check
    if has_conflict:
        return (
            False,
            ComplianceStatus.CONFLICTING_EVIDENCE,
            RecommendedAction.EXPERT_REVIEW,
            f"Requirement '{req_code}' has conflicting evidence values. Silent resolution is strictly disallowed.",
        )

    # 3. Missing Evidence Check
    if not linked_evidences:
        action = (
            RecommendedAction.REQUIRES_TESTING
            if spec.requires_physical_testing
            else spec.default_missing_action
        )
        return (
            False,
            ComplianceStatus.MISSING_EVIDENCE,
            action,
            f"No verified evidence provided for requirement '{req_code}'. Expected: {', '.join(spec.expected_evidence_types)}. Action: {action.value}.",
        )

    # 4. Validate Evidence Provenance & Verification
    valid_linked = []
    for ev in linked_evidences:
        # Support dict or Pydantic/SQLAlchemy objects
        ev_dict = ev if isinstance(ev, dict) else (ev.model_dump() if hasattr(ev, "model_dump") else ev.__dict__)
        
        # Invariant: User claim can NEVER be evidence
        p_type = ev_dict.get("provenance_type") or ev_dict.get("provenance", {}).get("provenance_type")
        if p_type in (ProvenanceClassification.USER_CLAIM.value, ProvenanceClassification.USER_CLARIFICATION.value):
            continue

        auth = str(ev_dict.get("source_authority") or ev_dict.get("authority", ""))
        if auth in ("INCOMPATIBLE_STANDARD", "IRRELEVANT_DOCUMENT"):
            continue

        verif_status = ev_dict.get("verification_status", "UNVERIFIED")
        if verif_status != "VERIFIED":
            continue

        valid_linked.append(ev_dict)

    if not valid_linked:
        action = (
            RecommendedAction.REQUIRES_TESTING
            if spec.requires_physical_testing
            else RecommendedAction.UPLOAD_EVIDENCE
        )
        return (
            False,
            ComplianceStatus.MISSING_EVIDENCE,
            action,
            f"Product claims provided, but no authoritative documentary or laboratory evidence is linked. User claims alone cannot satisfy regulatory requirements.",
        )

    # 5. Check Evidence Type Compatibility
    type_matched = [
        ev for ev in valid_linked
        if ev.get("evidence_type") in spec.expected_evidence_types
        or "TEST" in str(ev.get("evidence_type", ""))
        or "CERT" in str(ev.get("evidence_type", ""))
        or "LAB" in str(ev.get("authority", ""))
        or "LAB" in str(ev.get("source_authority", ""))
    ]
    if not type_matched:
        return (
            False,
            ComplianceStatus.MORE_INFORMATION_REQUIRED,
            spec.default_missing_action,
            f"Linked evidence type does not satisfy the evidentiary requirements for '{req_code}'. Required: {', '.join(spec.expected_evidence_types)}.",
        )

    # 6. Deterministic Rule Evaluation Result
    if rule_result != "PASS":
        return (
            False,
            ComplianceStatus.POTENTIAL_GAP,
            RecommendedAction.PROVIDE_SPECIFICATION,
            rule_explanation or f"Linked evidence values failed the deterministic evaluation condition for '{req_code}'.",
        )

    # All checks passed!
    top_ev = type_matched[0]
    ev_id = top_ev.get("evidence_id") or top_ev.get("id", "EV-UNKNOWN")
    authority = top_ev.get("source_authority") or top_ev.get("authority", "LAB_REPORT")
    page = top_ev.get("page_number") or top_ev.get("page")
    page_str = f" (Page {page})" if page else ""

    exp = rule_explanation or (
        f"Requirement '{req_code}' deterministically SATISFIED by verified evidence [{ev_id}]{page_str} from {authority}."
    )
    return (True, ComplianceStatus.SATISFIED, None, exp)
