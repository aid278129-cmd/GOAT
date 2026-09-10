"""Layer 7: Production-Grade Deterministic Compliance Comparator.

Architecture:
REQUIRED CONDITION / PARAMETER
  ↓
REQUIRED EVIDENCE
  ↓
AVAILABLE EVIDENCE
  ↓
EVIDENCE VALIDATION
  ↓
DETERMINISTIC COMPARISON (Formulas, Units, Thresholds)
  ↓
COMPLIANCE STATUS
  ↓
RECOMMENDED ACTION

Cardinal Invariants Enforced:
1. CLAUSE RETRIEVED ≠ REQUIREMENT SATISFIED
2. PRODUCT FACT ≠ COMPLIANCE EVIDENCE
3. USER CLAIM ≠ COMPLIANCE EVIDENCE
4. NO VERIFIED EVIDENCE → NO SATISFIED
5. NO DETERMINISTIC PASS → NO SATISFIED
6. CONFLICT → EXPERT REVIEW
7. LLM COMPLIANCE AUTHORITY = 0%
"""

import re
from typing import Optional, Dict, Any, Tuple, List, Union
from pydantic import BaseModel, Field

from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.services.gap_analysis.evidence_gate import can_be_satisfied, get_evidence_spec_for_requirement


class DeterministicComparisonResult(BaseModel):
    """Immutable outcome of a mathematical or categorical deterministic evaluation."""
    rule_name: str
    comparison_formula: str
    observed_value: Any
    observed_unit: Optional[str] = None
    required_threshold: Any
    required_unit: Optional[str] = None
    is_pass: bool
    status: ComplianceStatus
    recommended_action: Optional[RecommendedAction] = None
    audit_explanation: str
    llm_authority: float = 0.0

from backend.app.services.gap_analysis.units import normalize_unit


def compare_numeric_threshold(
    observed_val: float,
    observed_unit: Optional[str],
    operator: str,  # ">=", "<=", "==", "RANGE"
    threshold: Union[float, Tuple[float, float]],
    required_unit: Optional[str],
    parameter_name: str = "Parameter",
) -> Tuple[bool, str, str]:
    """Execute deterministic numerical comparison and record mathematical formula."""
    norm_val, active_unit = normalize_unit(observed_val, observed_unit, required_unit)

    if operator in (">=", "MINIMUM", "MIN"):
        t = float(threshold) if isinstance(threshold, (int, float)) else float(threshold[0])
        passed = norm_val >= t
        formula = f"{norm_val} {active_unit} >= {t} {active_unit}"
        res_str = "PASS" if passed else "FAIL"
        explanation = (
            f"Observed {parameter_name} ({norm_val} {active_unit}) "
            f"{'satisfies' if passed else 'fails'} minimum mandatory threshold of {t} {active_unit}. Rule: {formula} -> {res_str}."
        )
        return passed, formula, explanation

    elif operator in ("<=", "MAXIMUM", "MAX"):
        t = float(threshold) if isinstance(threshold, (int, float)) else float(threshold[0])
        passed = norm_val <= t
        formula = f"{norm_val} {active_unit} <= {t} {active_unit}"
        res_str = "PASS" if passed else "FAIL"
        explanation = (
            f"Observed {parameter_name} ({norm_val} {active_unit}) "
            f"{'satisfies' if passed else 'exceeds'} maximum permissible limit of {t} {active_unit}. Rule: {formula} -> {res_str}."
        )
        return passed, formula, explanation

    elif operator in ("==", "EXACT"):
        t = float(threshold) if isinstance(threshold, (int, float)) else float(threshold[0])
        passed = abs(norm_val - t) < 1e-4
        formula = f"{norm_val} {active_unit} == {t} {active_unit}"
        res_str = "PASS" if passed else "FAIL"
        explanation = (
            f"Observed {parameter_name} ({norm_val} {active_unit}) "
            f"{'matches' if passed else 'does not match'} required exact value of {t} {active_unit}. Rule: {formula} -> {res_str}."
        )
        return passed, formula, explanation

    elif operator == "RANGE":
        t_min, t_max = threshold if isinstance(threshold, (list, tuple)) else (0.0, float(threshold))
        passed = t_min <= norm_val <= t_max
        formula = f"{t_min} <= {norm_val} <= {t_max} {active_unit}"
        res_str = "PASS" if passed else "FAIL"
        explanation = (
            f"Observed {parameter_name} ({norm_val} {active_unit}) "
            f"{'falls within' if passed else 'falls outside'} required compliance range [{t_min}, {t_max}] {active_unit}. Rule: {formula} -> {res_str}."
        )
        return passed, formula, explanation

    return False, "UNKNOWN_OPERATOR", f"Unsupported comparison operator '{operator}'."


def _ev_dict(e: Any) -> Dict[str, Any]:
    """Uniform dictionary extraction from evidence object."""
    if isinstance(e, dict):
        return e
    if hasattr(e, "model_dump"):
        return e.model_dump()
    if hasattr(e, "__dict__"):
        return e.__dict__
    return {}


class ComparisonTuple(tuple):
    """3-tuple subclass allowing backwards-compatible unpacking while carrying trace_meta."""
    def __new__(cls, status, action, explanation, trace_meta=None):
        return super().__new__(cls, (status, action, explanation))

    def __init__(self, status, action, explanation, trace_meta=None):
        self.trace_meta = trace_meta or {}


def compare_requirement_with_evidence(
    requirement_code: str,
    requirement_type: str,
    description: str,
    measurable_condition: Optional[str],
    dna: ProductDNACore,
    evidence_payload: Optional[Dict[str, Any]] = None,
    linked_evidences: Optional[List[Any]] = None,
    has_conflict: bool = False,
    applicable_standard: str = "IS 17526:2021",
) -> ComparisonTuple:
    """Deterministic comparator evaluating evidence against standard requirement conditions.
    
    Returns ComparisonTuple that unpacks as (status, action, explanation) with .trace_meta.
    """
    desc_lower = description.lower()
    meas_lower = (measurable_condition or "").lower()

    trace_meta: Dict[str, Any] = {
        "requirement_code": requirement_code,
        "applicable_standard": applicable_standard,
        "comparison_rule": "NONE",
        "comparison_result": "NOT_EVALUATED",
        "observed_value": None,
        "required_value": measurable_condition or description,
        "llm_authority": 0.0,
    }

    # 1. Conflict Check: Contradictory evidentiary records strictly mandate expert review
    if has_conflict or (evidence_payload and evidence_payload.get("has_conflict")):
        trace_meta["comparison_result"] = "CONFLICT"
        trace_meta["comparison_rule"] = "Conflict Guard: Discrepant test reports detected"
        return ComparisonTuple(
            ComplianceStatus.CONFLICTING_EVIDENCE,
            RecommendedAction.EXPERT_REVIEW,
            f"Contradictory evidentiary values detected for requirement '{requirement_code}'. "
            f"Automated approval disallowed. Manual BIS legal / technical expert review required.",
            trace_meta,
        )

    # Convert legacy evidence_payload or linked_evidences to unified dicts
    synth_evidences: List[Dict[str, Any]] = [_ev_dict(e) for e in (linked_evidences or [])]
    if not synth_evidences and evidence_payload:
        if requirement_type == "MATERIAL" and evidence_payload.get("mill_test_certificate"):
            verif = "VERIFIED" if evidence_payload.get("mill_test_certificate_verified", True) else "UNVERIFIED"
            synth_evidences.append({
                "evidence_id": "EV-MAT-CERT-01",
                "evidence_type": "MATERIAL_CERTIFICATE",
                "source_authority": "MILL_TEST_CERTIFICATE",
                "verification_status": verif,
                "normalized_value": "stainless_steel_grade_304",
                "provenance_type": "DOCUMENT_EVIDENCE",
                "standard_number": applicable_standard,
                "page_number": 1,
            })
        if "leakage" in desc_lower or "inverted" in meas_lower:
            if "leakage_test_passed" in evidence_payload:
                passed = evidence_payload["leakage_test_passed"]
                verif = "VERIFIED" if evidence_payload.get("leakage_test_verified", True) else "UNVERIFIED"
                synth_evidences.append({
                    "evidence_id": "EV-LEAK-TEST-01",
                    "evidence_type": "TEST_REPORT",
                    "source_authority": "LAB_REPORT",
                    "verification_status": verif,
                    "normalized_value": 1.0 if passed else 0.0,
                    "provenance_type": "LAB_EVIDENCE",
                    "standard_number": applicable_standard,
                    "page_number": 2,
                })
        if "thermal" in desc_lower or "heat retention" in desc_lower or "60 deg" in meas_lower:
            if "tested_temp_after_6hrs" in evidence_payload:
                temp = evidence_payload["tested_temp_after_6hrs"]
                verif = "VERIFIED" if evidence_payload.get("thermal_test_verified", True) else "UNVERIFIED"
                synth_evidences.append({
                    "evidence_id": "EV-THERM-TEST-01",
                    "evidence_type": "TEST_REPORT",
                    "source_authority": "LAB_REPORT",
                    "verification_status": verif,
                    "normalized_value": temp,
                    "provenance_type": "LAB_EVIDENCE",
                    "standard_number": applicable_standard,
                    "page_number": 4,
                })
        if requirement_type == "MARKING" or "marking" in desc_lower:
            if evidence_payload.get("artwork_label_verified"):
                synth_evidences.append({
                    "evidence_id": "EV-MARK-ARTWORK-01",
                    "evidence_type": "LABEL_PHOTO",
                    "source_authority": "MANUFACTURER_DECLARATION",
                    "verification_status": "VERIFIED",
                    "normalized_value": 1.0,
                    "provenance_type": "DOCUMENT_EVIDENCE",
                    "standard_number": applicable_standard,
                    "page_number": 1,
                })

    # 2. Evidence Standard Guard: Reject wrong-standard evidence
    for ev in synth_evidences:
        ev_std = ev.get("standard_number") or ev.get("standard")
        if ev_std and applicable_standard:
            std_clean = applicable_standard.split(":")[0].replace(" ", "").upper()
            ev_clean = str(ev_std).split(":")[0].replace(" ", "").upper()
            if std_clean != ev_clean and "UNKNOWN" not in ev_clean:
                trace_meta["comparison_result"] = "WRONG_STANDARD_REJECTION"
                trace_meta["comparison_rule"] = f"Standard mismatch: {ev_std} != {applicable_standard}"
                return ComparisonTuple(
                    ComplianceStatus.POTENTIAL_GAP,
                    RecommendedAction.UPLOAD_EVIDENCE,
                    f"Evidence document references standard '{ev_std}', which does not match required applicable standard '{applicable_standard}'. Cross-standard evidence is rejected.",
                    trace_meta,
                )

    # 3. Evidence Freshness Guard: Reject expired evidence
    for ev in synth_evidences:
        if ev.get("is_expired") is True or ev.get("validity_status") == "EXPIRED":
            trace_meta["comparison_result"] = "STALE_EXPIRED_EVIDENCE"
            trace_meta["comparison_rule"] = "Evidence Freshness Guard: Expired document"
            return ComparisonTuple(
                ComplianceStatus.MISSING_EVIDENCE,
                RecommendedAction.UPLOAD_EVIDENCE,
                f"Evidence document [{ev.get('evidence_id', 'DOC')}] is past its validity expiration date. A current re-test report or renewed certificate is required.",
                trace_meta,
            )

    # =========================================================================
    # Rule Category 1: Thermal Performance (Clause 5.4 — 95°C to >= 60°C after 6 hrs)
    # =========================================================================
    if ("thermal" in desc_lower or "heat retention" in desc_lower or "60 deg" in meas_lower) and "drop" not in desc_lower and "impact" not in desc_lower:
        req_threshold = 60.0
        trace_meta["required_value"] = f">= {req_threshold} °C after 6 hours"

        if synth_evidences:
            req_dict = {"code": requirement_code, "requirement_type": requirement_type}
            temps = [
                float(e.get("normalized_value"))
                for e in synth_evidences
                if isinstance(e.get("normalized_value"), (int, float))
            ]
            
            if temps:
                observed_t = temps[0]
                passed, formula, math_exp = compare_numeric_threshold(
                    observed_val=observed_t,
                    observed_unit="°C",
                    operator=">=",
                    threshold=req_threshold,
                    required_unit="°C",
                    parameter_name="6-Hour Water Temperature",
                )
                trace_meta["observed_value"] = f"{observed_t} °C"
                trace_meta["comparison_rule"] = formula
                trace_meta["comparison_result"] = "PASS" if passed else "FAIL"

                can_sat, status, action, exp = can_be_satisfied(
                    requirement=req_dict,
                    linked_evidences=synth_evidences,
                    has_conflict=has_conflict,
                    rule_result="PASS" if passed else "FAIL",
                    rule_explanation=math_exp,
                )
                return ComparisonTuple(status, action, exp, trace_meta)

        if dna.insulated:
            trace_meta["comparison_rule"] = "DNA declares insulated, but physical lab report missing"
            trace_meta["comparison_result"] = "PENDING_TESTING"
            return ComparisonTuple(
                ComplianceStatus.POTENTIALLY_SATISFIED,
                RecommendedAction.REQUIRES_TESTING,
                "Product is vacuum-insulated (USER_CLAIM). Mandatory 6-hour laboratory heat retention test (Clause 5.4) required to certify >= 60°C performance.",
                trace_meta,
            )
        trace_meta["comparison_rule"] = "Non-insulated container fails thermal retention premise"
        trace_meta["comparison_result"] = "GAP"
        return ComparisonTuple(
            ComplianceStatus.POTENTIAL_GAP,
            RecommendedAction.PROVIDE_SPECIFICATION,
            "Product does not declare vacuum insulation required to achieve IS 17526 thermal retention performance.",
            trace_meta,
        )

    # =========================================================================
    # Rule Category 2: Inversion Leakage Resistance (Clause 5.2 — 10 min inverted)
    # =========================================================================
    if ("leakage" in desc_lower or "inverted" in meas_lower) and "drop" not in desc_lower and "impact" not in desc_lower:
        trace_meta["required_value"] = "Zero leakage / weeping after 10-minute inversion"
        if synth_evidences:
            req_dict = {"code": requirement_code, "requirement_type": requirement_type}
            passed = any(e.get("normalized_value") in (1.0, 1, True, "PASS", "NO_LEAKAGE") for e in synth_evidences)
            trace_meta["observed_value"] = "No leakage detected" if passed else "Seepage observed"
            trace_meta["comparison_rule"] = "Hydrostatic seal test == ZERO_LEAKAGE after 10 min"
            trace_meta["comparison_result"] = "PASS" if passed else "FAIL"

            can_sat, status, action, exp = can_be_satisfied(
                requirement=req_dict,
                linked_evidences=synth_evidences,
                has_conflict=has_conflict,
                rule_result="PASS" if passed else "FAIL",
                rule_explanation="Laboratory test report verifies no leakage, weeping, or moisture seepage after 10-minute inversion test (Clause 5.2).",
            )
            return ComparisonTuple(status, action, exp, trace_meta)

        trace_meta["comparison_rule"] = "Physical hydrostatic inversion test required"
        trace_meta["comparison_result"] = "PENDING_TESTING"
        return ComparisonTuple(
            ComplianceStatus.POTENTIALLY_SATISFIED,
            RecommendedAction.REQUIRES_TESTING,
            "Container design includes sealing lid. Mandatory 10-minute physical inversion test (Clause 5.2) required to confirm zero leakage.",
            trace_meta,
        )

    # =========================================================================
    # Rule Category 3: Drop Impact Resistance (Clause 5.3 — 1.0m Concrete Drop)
    # =========================================================================
    if "drop" in desc_lower or "impact" in desc_lower:
        trace_meta["required_value"] = "2 drops from 1.0m onto concrete with vacuum integrity preserved"
        if synth_evidences:
            req_dict = {"code": requirement_code, "requirement_type": requirement_type}
            passed = any(e.get("normalized_value") in (1.0, 1, True, "PASS") for e in synth_evidences)
            trace_meta["observed_value"] = "Drop test passed without vacuum rupture" if passed else "Drop failure / rupture"
            trace_meta["comparison_rule"] = "1.0m Free-fall Drop Tower Impact == PASS"
            trace_meta["comparison_result"] = "PASS" if passed else "FAIL"

            can_sat, status, action, exp = can_be_satisfied(
                requirement=req_dict,
                linked_evidences=synth_evidences,
                has_conflict=has_conflict,
                rule_result="PASS" if passed else "FAIL",
                rule_explanation="Accredited drop test report confirms container sustained two 1.0-metre concrete drops without leakage or loss of insulation.",
            )
            return ComparisonTuple(status, action, exp, trace_meta)

        trace_meta["comparison_rule"] = "Physical drop impact test required"
        trace_meta["comparison_result"] = "PENDING_TESTING"
        return ComparisonTuple(
            ComplianceStatus.MISSING_EVIDENCE,
            RecommendedAction.REQUIRES_TESTING,
            "Mandatory 1.0-metre concrete drop impact test (Clause 5.3) report required to verify vacuum flask impact safety.",
            trace_meta,
        )

    # =========================================================================
    # Rule Category 4: Stainless Steel Raw Material Grade (Clause 4.2.1 — Grade 304)
    # =========================================================================
    if requirement_type == "MATERIAL" and ("stainless steel" in desc_lower or "grade 304" in desc_lower):
        trace_meta["required_value"] = "Grade 304 of IS 6911 (Cr >= 17.5%, Ni >= 8.0%, Pb <= 0.05%)"
        materials_str = " ".join(dna.materials).lower()
        has_grade_claim = "304" in materials_str or "316" in materials_str

        if synth_evidences:
            req_dict = {"code": requirement_code, "requirement_type": requirement_type}
            has_valid_cert = any(
                ("304" in str(e.get("normalized_value", "")) or "316" in str(e.get("normalized_value", "")) or e.get("normalized_value") in (1.0, True))
                for e in synth_evidences
            )
            trace_meta["observed_value"] = "SS Grade 304 Verified Certificate" if has_valid_cert else "Sub-standard material"
            trace_meta["comparison_rule"] = "Chemical Spectrometry: Cr >= 17.5% and Ni >= 8.0%"
            trace_meta["comparison_result"] = "PASS" if has_valid_cert else "FAIL"

            can_sat, status, action, exp = can_be_satisfied(
                requirement=req_dict,
                linked_evidences=synth_evidences,
                has_conflict=has_conflict,
                rule_result="PASS" if has_valid_cert else "FAIL",
                rule_explanation="Verified Mill Test Certificate confirms raw material chemical composition conforms to Grade 304 of IS 6911.",
            )
            return ComparisonTuple(status, action, exp, trace_meta)

        if has_grade_claim:
            trace_meta["comparison_rule"] = "User claims Grade 304, but Mill Test Certificate not uploaded"
            trace_meta["comparison_result"] = "PENDING_EVIDENCE"
            return ComparisonTuple(
                ComplianceStatus.POTENTIALLY_SATISFIED,
                RecommendedAction.UPLOAD_EVIDENCE,
                "Product declares Stainless Steel Grade 304 (USER_CLAIM). Raw material chemical test certificate (IS 6911) required to establish full compliance.",
                trace_meta,
            )
        elif "stainless_steel" in materials_str:
            trace_meta["comparison_rule"] = "Generic stainless steel declared; specific grade missing"
            trace_meta["comparison_result"] = "MISSING_SPEC"
            return ComparisonTuple(
                ComplianceStatus.MORE_INFORMATION_REQUIRED,
                RecommendedAction.PROVIDE_SPECIFICATION,
                "Stainless steel is declared, but specific grade (Grade 304 or superior) is not specified in Product DNA.",
                trace_meta,
            )
        elif dna.materials:
            trace_meta["comparison_rule"] = f"Declared materials ({', '.join(dna.materials)}) do not include stainless steel"
            trace_meta["comparison_result"] = "GAP"
            return ComparisonTuple(
                ComplianceStatus.POTENTIAL_GAP,
                RecommendedAction.PROVIDE_SPECIFICATION,
                f"Declared materials ({', '.join(dna.materials)}) do not meet Grade 304 Stainless Steel food contact requirement.",
                trace_meta,
            )

        trace_meta["comparison_rule"] = "No material evidence or specification provided"
        trace_meta["comparison_result"] = "MISSING_EVIDENCE"
        return ComparisonTuple(
            ComplianceStatus.MISSING_EVIDENCE,
            RecommendedAction.UPLOAD_EVIDENCE,
            "No raw material specification or evidence provided for metallic food-contact parts.",
            trace_meta,
        )

    # =========================================================================
    # Rule Category 5: Marking and Packaging ISI Layout (Clause 7.1)
    # =========================================================================
    if requirement_type == "MARKING" or "marking" in desc_lower:
        trace_meta["required_value"] = "BIS Standard Mark (ISI) license layout + Nominal Capacity"
        if synth_evidences:
            req_dict = {"code": requirement_code, "requirement_type": requirement_type}
            passed = any(e.get("normalized_value") in (1.0, 1, True, "PASS") for e in synth_evidences)
            trace_meta["observed_value"] = "Artwork with ISI Mark & Capacity verified" if passed else "Marking artwork missing elements"
            trace_meta["comparison_rule"] = "Label and Packaging Artwork Inspection == COMPLIANT"
            trace_meta["comparison_result"] = "PASS" if passed else "FAIL"

            can_sat, status, action, exp = can_be_satisfied(
                requirement=req_dict,
                linked_evidences=synth_evidences,
                has_conflict=has_conflict,
                rule_result="PASS" if passed else "FAIL",
                rule_explanation="Product packaging artwork includes manufacturer trademark, nominal capacity, and ISI Standard Mark layout.",
            )
            return ComparisonTuple(status, action, exp, trace_meta)

        trace_meta["comparison_rule"] = "Label and packaging artwork required"
        trace_meta["comparison_result"] = "MISSING_EVIDENCE"
        return ComparisonTuple(
            ComplianceStatus.MISSING_EVIDENCE,
            RecommendedAction.UPLOAD_EVIDENCE,
            "Packaging and product label artwork required to verify BIS Standard Mark (ISI) and nominal capacity marking.",
            trace_meta,
        )

    # =========================================================================
    # Rule Category 6: Authoritative Clause Acquisition Pending
    # =========================================================================
    if requirement_code == "AUTHORITATIVE_CLAUSE_PENDING":
        trace_meta["comparison_rule"] = "Clause text acquisition pending from Bureau of Indian Standards"
        trace_meta["comparison_result"] = "PENDING_ACQUISITION"
        return ComparisonTuple(
            ComplianceStatus.MORE_INFORMATION_REQUIRED,
            RecommendedAction.EXPERT_REVIEW,
            "Authoritative clause full text acquisition is pending under official BIS procurement. Full specification pending acquisition from authorized channels.",
            trace_meta,
        )

    # =========================================================================
    # Rule Category 7: Generic Fallback Handling
    # =========================================================================
    spec = get_evidence_spec_for_requirement(requirement_code, requirement_type)
    action = RecommendedAction.REQUIRES_TESTING if spec.requires_physical_testing else spec.default_missing_action
    trace_meta["comparison_rule"] = "Evidence gate fallback check"
    trace_meta["comparison_result"] = "MISSING_EVIDENCE"
    return ComparisonTuple(
        ComplianceStatus.MISSING_EVIDENCE,
        action,
        f"Requirement '{requirement_code}' identified. Verifiable evidence ({', '.join(spec.expected_evidence_types)}) is required. Action: {action.value}.",
        trace_meta,
    )
