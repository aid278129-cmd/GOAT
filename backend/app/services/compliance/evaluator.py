from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import uuid

from backend.app.services.compliance.unit_normalizer import (
    parse_numeric_value,
    parse_value_and_unit,
    normalize_pair,
    are_units_compatible,
)
from backend.app.services.compliance.applicability_engine import (
    evaluate_applicability,
    find_dna_parameter,
    ApplicabilityState,
)


class AssessmentState:
    NOT_ASSESSED = "NOT_ASSESSED"
    DATA_REQUIRED = "DATA_REQUIRED"
    CONFLICT = "CONFLICT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ENGINEERING_PASS = "ENGINEERING_PASS"
    ENGINEERING_GAP = "ENGINEERING_GAP"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class DeterministicComplianceEvaluator:
    """Backend-authoritative deterministic regulatory assessment engine.
    
    Evaluates:
      Product DNA + Applicable Standard + Clause + Structured Requirement + Accepted Evidence
      --> Deterministic Engineering Assessment
    """

    ENGINE_VERSION = "v2.0-deterministic"

    @classmethod
    def evaluate_requirement(
        cls,
        requirement: Dict[str, Any],
        product_dna_facts: Dict[str, Dict[str, Any]],
        evidence_map: Dict[str, Dict[str, Any]],
        conflicts: Optional[List[Dict[str, Any]]] = None,
        evaluated_by: Optional[str] = "Deterministic Evaluator Engine",
    ) -> Dict[str, Any]:
        """Deterministically evaluate a single JobRequirement."""
        now = datetime.now(timezone.utc)
        req_id = requirement.get("id") or str(uuid.uuid4())
        clause_ref = requirement.get("clause_reference") or requirement.get("clause_number") or ""
        param_key = requirement.get("parameter_key") or ""
        req_type = (requirement.get("requirement_type") or "NUMERIC").upper()
        op = (requirement.get("comparison_operator") or ">=").strip()

        trace: Dict[str, Any] = {
            "standard_id": requirement.get("standard_id"),
            "clause_reference": clause_ref,
            "requirement_id": req_id,
            "requirement_text": requirement.get("requirement_text") or requirement.get("description") or "",
            "requirement_type": req_type,
            "operator": op,
            "expected_unit": requirement.get("expected_unit") or requirement.get("unit"),
            "threshold_min": requirement.get("threshold_min") or requirement.get("limit_min"),
            "threshold_max": requirement.get("threshold_max") or requirement.get("limit_max"),
            "expected_value": requirement.get("expected_value"),
            "allowed_values": requirement.get("allowed_values") or [],
            "source_reference": requirement.get("source_reference"),
        }

        # 1. Evaluate Applicability
        app_res = evaluate_applicability(
            condition=requirement.get("applicability_condition"),
            product_dna_facts=product_dna_facts,
            conflicts=conflicts,
        )
        trace["applicability"] = app_res

        if app_res["state"] == ApplicabilityState.NOT_APPLICABLE:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.NOT_APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.NOT_APPLICABLE,
                "observed_value": None,
                "observed_unit": None,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Applicability condition not met: {app_res['reason']}",
                "source_evidence_id": None,
                "source_dna_id": None,
                "explanation": f"Clause is not applicable to this product scope ({app_res['reason']}).",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        if app_res["state"] in {ApplicabilityState.DATA_REQUIRED, ApplicabilityState.CONFLICT}:
            state = AssessmentState.DATA_REQUIRED if app_res["state"] == ApplicabilityState.DATA_REQUIRED else AssessmentState.CONFLICT
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": app_res["state"],
                "applicability_reason": app_res["reason"],
                "assessment_state": state,
                "observed_value": None,
                "observed_unit": None,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Applicability evaluation halted: {app_res['reason']}",
                "source_evidence_id": None,
                "source_dna_id": None,
                "explanation": app_res["reason"],
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # 2. Check Requirement Types requiring Human / Qualitative review
        if req_type == "GEOMETRY":
            # If explicitly marked as ambiguous or requiring visual inspection, route to human review
            selection_rule = str(requirement.get("selection_rule") or "").upper()
            verification_method = str(requirement.get("verification_method") or "").upper()
            if selection_rule in {"AMBIGUOUS", "UNCLEAR_DATUM", "HUMAN_REVIEW"} or verification_method == "VISUAL_INSPECTION":
                return {
                    "requirement_id": req_id,
                    "clause_number": clause_ref,
                    "parameter_key": param_key,
                    "applicability_state": ApplicabilityState.APPLICABLE,
                    "applicability_reason": app_res["reason"],
                    "assessment_state": AssessmentState.HUMAN_REVIEW_REQUIRED,
                    "observed_value": None,
                    "observed_unit": None,
                    "normalized_value": None,
                    "normalized_unit": None,
                    "expected_value": requirement.get("expected_value"),
                    "expected_unit": requirement.get("expected_unit"),
                    "threshold_min": requirement.get("threshold_min"),
                    "threshold_max": requirement.get("threshold_max"),
                    "comparison_operator": op,
                    "evaluation_expression": f"CAD geometry requires human review (selection_rule={selection_rule or 'N/A'}, verification_method={verification_method}).",
                    "source_evidence_id": None,
                    "source_dna_id": None,
                    "explanation": "Ambiguous geometry or visual inspection requirement: Human review required.",
                    "trace_details": trace,
                    "engine_version": cls.ENGINE_VERSION,
                    "evaluated_at": now,
                    "evaluated_by": evaluated_by,
                }
            # Otherwise, allow deterministic evaluation via Product DNA and CAD measurements below
        elif req_type in {"HUMAN_REVIEW", "TEXT_REVIEW", "DOCUMENT"}:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.HUMAN_REVIEW_REQUIRED,
                "observed_value": None,
                "observed_unit": None,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Requirement type is {req_type}. Human engineering review required.",
                "source_evidence_id": None,
                "source_dna_id": None,
                "explanation": f"Qualitative requirement ({req_type}): Human review required.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        if op == "NOT_APPLICABLE":
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.NOT_APPLICABLE,
                "applicability_reason": "Operator designated as NOT_APPLICABLE",
                "assessment_state": AssessmentState.NOT_APPLICABLE,
                "observed_value": None,
                "observed_unit": None,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": None,
                "expected_unit": None,
                "threshold_min": None,
                "threshold_max": None,
                "comparison_operator": op,
                "evaluation_expression": "Clause operator marked as NOT_APPLICABLE",
                "source_evidence_id": None,
                "source_dna_id": None,
                "explanation": "Requirement operator explicitly configured as NOT_APPLICABLE.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # 3. Resolve Product DNA Parameter
        if not param_key:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": None,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.DATA_REQUIRED,
                "observed_value": None,
                "observed_unit": None,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": "No parameter key mapped to requirement",
                "source_evidence_id": None,
                "source_dna_id": None,
                "explanation": "Requirement does not define a canonical parameter key for evaluation.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # Check for active parameter conflicts
        if conflicts:
            for c in conflicts:
                c_key = c.get("parameter_key") or c.get("parameter") or ""
                if c_key.lower() == param_key.lower() and not c.get("resolved", False):
                    trace["conflict_record"] = c
                    return {
                        "requirement_id": req_id,
                        "clause_number": clause_ref,
                        "parameter_key": param_key,
                        "applicability_state": ApplicabilityState.APPLICABLE,
                        "applicability_reason": app_res["reason"],
                        "assessment_state": AssessmentState.CONFLICT,
                        "observed_value": None,
                        "observed_unit": None,
                        "normalized_value": None,
                        "normalized_unit": None,
                        "expected_value": requirement.get("expected_value"),
                        "expected_unit": requirement.get("expected_unit"),
                        "threshold_min": requirement.get("threshold_min"),
                        "threshold_max": requirement.get("threshold_max"),
                        "comparison_operator": op,
                        "evaluation_expression": f"Parameter '{param_key}' has unresolved evidence conflict",
                        "source_evidence_id": None,
                        "source_dna_id": None,
                        "explanation": f"Active conflict detected for parameter '{param_key}'. Human resolution required.",
                        "trace_details": trace,
                        "engine_version": cls.ENGINE_VERSION,
                        "evaluated_at": now,
                        "evaluated_by": evaluated_by,
                    }

        found_key, dna_fact = find_dna_parameter(param_key, product_dna_facts)
        if not dna_fact:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.DATA_REQUIRED,
                "observed_value": None,
                "observed_unit": None,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Parameter '{param_key}' missing in Product DNA",
                "source_evidence_id": None,
                "source_dna_id": None,
                "explanation": f"Required statutory parameter [{param_key}] is not populated in Product DNA. Upload and accept evidence.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        trace["dna_fact"] = dna_fact
        meta = dna_fact.get("metadata_json") or {}
        if isinstance(meta, dict) and "cad_model_id" in meta:
            trace["cad_provenance"] = {
                "cad_model_id": meta.get("cad_model_id"),
                "cad_measurement_id": meta.get("cad_measurement_id"),
                "source_geometry_reference": meta.get("source_geometry_reference"),
                "kernel_name": meta.get("kernel_name"),
                "kernel_version": meta.get("kernel_version"),
                "snapshot_id": meta.get("snapshot_id"),
                "verification_timestamp": meta.get("verification_timestamp"),
            }
        source_ev_id = dna_fact.get("source_evidence_id")
        source_dna_id = dna_fact.get("id")
        raw_obs_val = dna_fact.get("value")
        raw_obs_unit = dna_fact.get("unit") or ""

        # 4. Strict Evidence Gating Check
        if not source_ev_id:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.DATA_REQUIRED,
                "observed_value": str(raw_obs_val),
                "observed_unit": raw_obs_unit,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": "Parameter lacks backed source evidence ID",
                "source_evidence_id": None,
                "source_dna_id": source_dna_id,
                "explanation": f"Parameter [{param_key}] has no backing evidence artifact recorded.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        evidence = evidence_map.get(source_ev_id)
        if not evidence:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.DATA_REQUIRED,
                "observed_value": str(raw_obs_val),
                "observed_unit": raw_obs_unit,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Backing evidence '{source_ev_id}' not found in datastore",
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": f"Source evidence artifact '{source_ev_id}' could not be resolved.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        ev_status = evidence.get("acceptance_status") or evidence.get("status")
        trace["evidence_artifact"] = {
            "id": evidence.get("id"),
            "file_name": evidence.get("file_name"),
            "sha256": evidence.get("sha256_hash") or evidence.get("sha256"),
            "acceptance_status": ev_status,
        }

        if ev_status != "ACCEPTED":
            # Gating violation!
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.DATA_REQUIRED,
                "observed_value": str(raw_obs_val),
                "observed_unit": raw_obs_unit,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": requirement.get("expected_unit"),
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Evidence gating violation: artifact '{evidence.get('file_name')}' status is '{ev_status}' (not ACCEPTED)",
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": (
                    f"Evidence gating violation: Backing evidence '{evidence.get('file_name')}' is in state '{ev_status}'. "
                    f"Only ACCEPTED evidence may contribute to authoritative engineering assessment."
                ),
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # 5. Evaluate Boolean & Enumeration Types
        if req_type == "BOOLEAN" or op == "BOOLEAN":
            exp_val = str(requirement.get("expected_value") or "").strip().lower()
            obs_b = str(raw_obs_val).strip().lower()
            is_pass = obs_b in {"true", "yes", "1", "present", "compliant"} if exp_val in {"true", "yes", "1"} else obs_b in {"false", "no", "0", "absent"}
            state = AssessmentState.ENGINEERING_PASS if is_pass else AssessmentState.ENGINEERING_GAP
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": state,
                "observed_value": str(raw_obs_val),
                "observed_unit": None,
                "normalized_value": 1.0 if obs_b in {"true", "yes", "1"} else 0.0,
                "normalized_unit": "boolean",
                "expected_value": requirement.get("expected_value"),
                "expected_unit": None,
                "threshold_min": None,
                "threshold_max": None,
                "comparison_operator": "BOOLEAN",
                "evaluation_expression": f"Boolean match: observed '{raw_obs_val}' == expected '{requirement.get('expected_value')}' -> {is_pass}",
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": f"Boolean condition {'satisfied' if is_pass else 'failed'}: observed '{raw_obs_val}', expected '{requirement.get('expected_value')}'.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        if req_type == "ENUMERATION" or op == "ENUMERATION":
            allowed = requirement.get("allowed_values") or []
            allowed_norm = [str(x).strip().lower() for x in allowed]
            obs_str = str(raw_obs_val).strip().lower()
            is_pass = obs_str in allowed_norm
            state = AssessmentState.ENGINEERING_PASS if is_pass else AssessmentState.ENGINEERING_GAP
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": state,
                "observed_value": str(raw_obs_val),
                "observed_unit": None,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": ", ".join(allowed),
                "expected_unit": None,
                "threshold_min": None,
                "threshold_max": None,
                "comparison_operator": "ENUMERATION",
                "evaluation_expression": f"Enumeration check: observed '{raw_obs_val}' in {allowed} -> {is_pass}",
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": f"Value '{raw_obs_val}' is {'allowed' if is_pass else 'not allowed in statutory set'} {allowed}.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # 6. Parse and Normalize Numeric Values
        expected_unit = requirement.get("expected_unit") or requirement.get("unit") or raw_obs_unit
        obs_num, obs_unit = parse_value_and_unit(raw_obs_val, fallback_unit=raw_obs_unit)

        if obs_num is None:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.DATA_REQUIRED,
                "observed_value": str(raw_obs_val),
                "observed_unit": raw_obs_unit,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": requirement.get("expected_value"),
                "expected_unit": expected_unit,
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Could not parse numeric value from observed '{raw_obs_val}'",
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": f"Observed parameter value [{raw_obs_val}] could not be converted to a numeric dimension.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # Handle Range Operator: [threshold_min, threshold_max]
        if op == "RANGE":
            min_val_str = requirement.get("threshold_min") or requirement.get("limit_min")
            max_val_str = requirement.get("threshold_max") or requirement.get("limit_max")
            min_num, min_unit = parse_value_and_unit(min_val_str, fallback_unit=expected_unit)
            max_num, max_unit = parse_value_and_unit(max_val_str, fallback_unit=expected_unit)

            if min_num is None and max_num is None:
                return {
                    "requirement_id": req_id,
                    "clause_number": clause_ref,
                    "parameter_key": param_key,
                    "applicability_state": ApplicabilityState.APPLICABLE,
                    "applicability_reason": app_res["reason"],
                    "assessment_state": AssessmentState.DATA_REQUIRED,
                    "observed_value": f"{obs_num} {obs_unit}",
                    "observed_unit": obs_unit,
                    "normalized_value": None,
                    "normalized_unit": None,
                    "expected_value": f"[{min_val_str}, {max_val_str}]",
                    "expected_unit": expected_unit,
                    "threshold_min": min_val_str,
                    "threshold_max": max_val_str,
                    "comparison_operator": "RANGE",
                    "evaluation_expression": "Missing min and max threshold values for RANGE operator",
                    "source_evidence_id": source_ev_id,
                    "source_dna_id": source_dna_id,
                    "explanation": "Statutory range bounds are not defined.",
                    "trace_details": trace,
                    "engine_version": cls.ENGINE_VERSION,
                    "evaluated_at": now,
                    "evaluated_by": evaluated_by,
                }

            # Check unit compatibility with range bounds
            if min_unit and not are_units_compatible(obs_unit, min_unit):
                return {
                    "requirement_id": req_id,
                    "clause_number": clause_ref,
                    "parameter_key": param_key,
                    "applicability_state": ApplicabilityState.APPLICABLE,
                    "applicability_reason": app_res["reason"],
                    "assessment_state": AssessmentState.CONFLICT,
                    "observed_value": f"{obs_num} {obs_unit}",
                    "observed_unit": obs_unit,
                    "normalized_value": None,
                    "normalized_unit": None,
                    "expected_value": f"[{min_val_str}, {max_val_str}]",
                    "expected_unit": expected_unit,
                    "threshold_min": min_val_str,
                    "threshold_max": max_val_str,
                    "comparison_operator": "RANGE",
                    "evaluation_expression": f"Incompatible units: observed '{obs_unit}' vs range unit '{min_unit}'",
                    "source_evidence_id": source_ev_id,
                    "source_dna_id": source_dna_id,
                    "explanation": f"Incompatible units: observed '{obs_unit}' vs range bounds '{min_unit}'.",
                    "trace_details": trace,
                    "engine_version": cls.ENGINE_VERSION,
                    "evaluated_at": now,
                    "evaluated_by": evaluated_by,
                }

            # Normalize min and max bounds to common base
            norm_obs = normalize_pair(obs_num, obs_unit, obs_num, obs_unit)
            base_obs = norm_obs["observed_normalized"]
            base_u = norm_obs["base_unit"]

            base_min = normalize_pair(min_num, min_unit or obs_unit, min_num, min_unit or obs_unit)["observed_normalized"] if min_num is not None else float("-inf")
            base_max = normalize_pair(max_num, max_unit or obs_unit, max_num, max_unit or obs_unit)["observed_normalized"] if max_num is not None else float("inf")

            is_pass = (base_min <= base_obs <= base_max)
            state = AssessmentState.ENGINEERING_PASS if is_pass else AssessmentState.ENGINEERING_GAP
            expr = f"{base_min:.4g} {base_u} <= {base_obs:.4g} {base_u} <= {base_max:.4g} {base_u} -> {is_pass}"

            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": state,
                "observed_value": str(raw_obs_val),
                "observed_unit": obs_unit,
                "normalized_value": base_obs,
                "normalized_unit": base_u,
                "expected_value": f"[{min_val_str}, {max_val_str}]",
                "expected_unit": expected_unit,
                "threshold_min": min_val_str,
                "threshold_max": max_val_str,
                "comparison_operator": "RANGE",
                "evaluation_expression": expr,
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": (
                    f"Measured value {obs_num} {obs_unit} ({base_obs:.4g} {base_u}) "
                    f"{'is within' if is_pass else 'is outside'} statutory envelope "
                    f"[{min_val_str or '-∞'}, {max_val_str or '+∞'}]."
                ),
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # 7. Standard Numeric Comparisons: >, >=, <, <=, ==
        target_raw = requirement.get("threshold_min") if op in {">", ">="} else (
            requirement.get("threshold_max") if op in {"<", "<="} else requirement.get("expected_value")
        )
        if target_raw is None:
            target_raw = requirement.get("expected_value") or requirement.get("threshold_min") or requirement.get("threshold_max")

        target_num, target_unit = parse_value_and_unit(target_raw, fallback_unit=expected_unit)

        if target_num is None:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.DATA_REQUIRED,
                "observed_value": f"{obs_num} {obs_unit}",
                "observed_unit": obs_unit,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": str(target_raw),
                "expected_unit": expected_unit,
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Requirement threshold could not be parsed: '{target_raw}'",
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": f"Statutory requirement threshold [{target_raw}] is missing or non-numeric.",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        # Unit Normalization & Incompatibility Check
        norm_result = normalize_pair(
            observed_value=obs_num,
            observed_unit=obs_unit,
            expected_value=target_num,
            expected_unit=target_unit or expected_unit,
        )

        trace["unit_normalization"] = norm_result

        if not norm_result["compatible"]:
            return {
                "requirement_id": req_id,
                "clause_number": clause_ref,
                "parameter_key": param_key,
                "applicability_state": ApplicabilityState.APPLICABLE,
                "applicability_reason": app_res["reason"],
                "assessment_state": AssessmentState.CONFLICT,
                "observed_value": f"{obs_num} {obs_unit}",
                "observed_unit": obs_unit,
                "normalized_value": None,
                "normalized_unit": None,
                "expected_value": f"{target_num} {target_unit or expected_unit}",
                "expected_unit": expected_unit,
                "threshold_min": requirement.get("threshold_min"),
                "threshold_max": requirement.get("threshold_max"),
                "comparison_operator": op,
                "evaluation_expression": f"Unit dimension mismatch: observed '{obs_unit}' vs expected '{target_unit or expected_unit}'",
                "source_evidence_id": source_ev_id,
                "source_dna_id": source_dna_id,
                "explanation": f"Unit incompatibility: Observed [{obs_unit}] cannot be converted to expected dimension [{target_unit or expected_unit}].",
                "trace_details": trace,
                "engine_version": cls.ENGINE_VERSION,
                "evaluated_at": now,
                "evaluated_by": evaluated_by,
            }

        v_obs = norm_result["observed_normalized"]
        v_exp = norm_result["expected_normalized"]
        base_unit = norm_result["base_unit"]

        # Deterministic Mathematical Comparison
        is_pass = False
        if op == ">":
            is_pass = v_obs > v_exp
        elif op == ">=":
            is_pass = v_obs >= v_exp
        elif op == "<":
            is_pass = v_obs < v_exp
        elif op == "<=":
            is_pass = v_obs <= v_exp
        elif op in {"==", "="}:
            is_pass = abs(v_obs - v_exp) < 1e-6

        state = AssessmentState.ENGINEERING_PASS if is_pass else AssessmentState.ENGINEERING_GAP
        eval_expr = f"{v_obs:.6g} {base_unit} {op} {v_exp:.6g} {base_unit} -> {is_pass}"

        if is_pass:
            explanation = (
                f"Engineering data satisfies requirement: observed {obs_num} {obs_unit} "
                f"({v_obs:.4g} {base_unit}) is {op} statutory threshold {target_num} {target_unit or expected_unit} "
                f"({v_exp:.4g} {base_unit})."
            )
        else:
            explanation = (
                f"Engineering gap identified: observed {obs_num} {obs_unit} "
                f"({v_obs:.4g} {base_unit}) violates statutory threshold {op} {target_num} {target_unit or expected_unit} "
                f"({v_exp:.4g} {base_unit})."
            )

        return {
            "requirement_id": req_id,
            "clause_number": clause_ref,
            "parameter_key": param_key,
            "applicability_state": ApplicabilityState.APPLICABLE,
            "applicability_reason": app_res["reason"],
            "assessment_state": state,
            "observed_value": str(raw_obs_val),
            "observed_unit": obs_unit,
            "normalized_value": v_obs,
            "normalized_unit": base_unit,
            "expected_value": str(target_raw),
            "expected_unit": target_unit or expected_unit,
            "threshold_min": requirement.get("threshold_min"),
            "threshold_max": requirement.get("threshold_max"),
            "comparison_operator": op,
            "evaluation_expression": eval_expr,
            "source_evidence_id": source_ev_id,
            "source_dna_id": source_dna_id,
            "explanation": explanation,
            "trace_details": trace,
            "engine_version": cls.ENGINE_VERSION,
            "evaluated_at": now,
            "evaluated_by": evaluated_by,
        }
