import re
import ast
from typing import Dict, Any, Optional, List, Tuple
from backend.app.services.compliance.unit_normalizer import (
    parse_value_and_unit,
    normalize_pair,
    are_units_compatible,
)


class ApplicabilityState:
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    DATA_REQUIRED = "DATA_REQUIRED"
    CONFLICT = "CONFLICT"


def _canonicalize_key(key: str) -> str:
    """Normalize parameter key for case-insensitive and snake/space-insensitive matching."""
    return re.sub(r"[^a-zA-Z0-9]", "", key).lower()


def find_dna_parameter(
    param_key: str,
    product_dna_facts: Dict[str, Dict[str, Any]],
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Find a DNA fact matching param_key either directly or via canonical key lookup."""
    if param_key in product_dna_facts:
        return param_key, product_dna_facts[param_key]
    
    canon_target = _canonicalize_key(param_key)
    for k, v in product_dna_facts.items():
        if _canonicalize_key(k) == canon_target:
            return k, v
        if isinstance(v, dict) and "parameter" in v and _canonicalize_key(v["parameter"]) == canon_target:
            return k, v
        if isinstance(v, dict) and "name" in v and _canonicalize_key(v["name"]) == canon_target:
            return k, v

    return None, None


def evaluate_applicability(
    condition: Optional[str],
    product_dna_facts: Dict[str, Any],
    conflicts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Deterministically evaluate whether a clause requirement applies to the given product.
    
    Returns dict:
        {
            "state": APPLICABLE | NOT_APPLICABLE | DATA_REQUIRED | CONFLICT,
            "reason": str,
            "condition": str,
            "evaluated_parameter": str,
            "observed_value": Any,
        }
    """
    if not condition or not condition.strip():
        return {
            "state": ApplicabilityState.APPLICABLE,
            "reason": "Unconditional statutory requirement applies universally to all products in scope",
            "condition": "",
            "evaluated_parameter": None,
            "observed_value": None,
        }

    cond = condition.strip()
    if cond.lower().startswith("if "):
        cond = cond[3:].strip()
    if " then " in cond.lower():
        cond = re.split(r"\s+then\s+", cond, flags=re.IGNORECASE)[0].strip()

    # Check for IN condition: <key> IN [...] or <key> in [...]
    in_match = re.match(r"^([\w\s_-]+?)\s+(?:NOT\s+IN|not\s+in|IN|in)\s+(\[.*\]|\(.*\))$", cond)
    if in_match:
        param_key = in_match.group(1).strip()
        is_negated = "not" in cond.lower()
        raw_list = in_match.group(2).strip()
        try:
            target_list = ast.literal_eval(raw_list)
            target_set = {str(item).strip().lower() for item in target_list}
        except Exception:
            # Fallback simple split
            items = raw_list.strip("[]()").split(",")
            target_set = {i.strip().strip("'\"").lower() for i in items if i.strip()}

        found_key, fact = find_dna_parameter(param_key, product_dna_facts)
        if not fact:
            return {
                "state": ApplicabilityState.DATA_REQUIRED,
                "reason": f"Cannot determine applicability: required parameter '{param_key}' is missing in Product DNA",
                "condition": condition,
                "evaluated_parameter": param_key,
                "observed_value": None,
            }

        val = str(fact.get("value", "")).strip().lower()
        matched = val in target_set
        applicable = not matched if is_negated else matched
        state = ApplicabilityState.APPLICABLE if applicable else ApplicabilityState.NOT_APPLICABLE
        verb = "not in" if is_negated else "in"
        return {
            "state": state,
            "reason": f"Parameter '{param_key}' ({val}) {verb} {target_set} -> {state}",
            "condition": condition,
            "evaluated_parameter": param_key,
            "observed_value": fact.get("value"),
        }

    # Standard binary comparison: <key> <operator> <value>
    # Operators: >=, <=, !=, ==, =, >, <
    comp_match = re.match(r"^([\w\s_-]+?)\s*(>=|<=|!=|==|=|>|<)\s*(.+)$", cond)
    if not comp_match:
        # Check simple boolean presence: "battery_present"
        param_key = cond.strip()
        found_key, fact = find_dna_parameter(param_key, product_dna_facts)
        if not fact:
            return {
                "state": ApplicabilityState.DATA_REQUIRED,
                "reason": f"Cannot determine applicability: parameter '{param_key}' is missing in Product DNA",
                "condition": condition,
                "evaluated_parameter": param_key,
                "observed_value": None,
            }
        val_str = str(fact.get("value", "")).strip().lower()
        is_true = val_str in {"true", "yes", "1", "present", "included"}
        state = ApplicabilityState.APPLICABLE if is_true else ApplicabilityState.NOT_APPLICABLE
        return {
            "state": state,
            "reason": f"Boolean flag '{param_key}' is {val_str} -> {state}",
            "condition": condition,
            "evaluated_parameter": param_key,
            "observed_value": fact.get("value"),
        }

    param_key = comp_match.group(1).strip()
    op = comp_match.group(2).strip()
    if op == "=":
        op = "=="
    raw_target = comp_match.group(3).strip()

    # Check for conflicts in DNA parameter
    if conflicts:
        for c in conflicts:
            c_key = c.get("parameter_key") or c.get("parameter") or ""
            if _canonicalize_key(c_key) == _canonicalize_key(param_key) and not c.get("resolved", False):
                return {
                    "state": ApplicabilityState.CONFLICT,
                    "reason": f"Condition parameter '{param_key}' has unresolved conflict in Product DNA",
                    "condition": condition,
                    "evaluated_parameter": param_key,
                    "observed_value": None,
                }

    found_key, fact = find_dna_parameter(param_key, product_dna_facts)
    if not fact:
        return {
            "state": ApplicabilityState.DATA_REQUIRED,
            "reason": f"Cannot determine applicability: required parameter '{param_key}' is missing in Product DNA",
            "condition": condition,
            "evaluated_parameter": param_key,
            "observed_value": None,
        }

    fact_val = fact.get("value")
    fact_unit = fact.get("unit") or ""

    # Parse numeric or string comparison
    target_num, target_unit = parse_value_and_unit(raw_target)
    obs_num, obs_unit = parse_value_and_unit(fact_val, fallback_unit=fact_unit)

    if obs_num is not None and target_num is not None:
        # Both numeric -> apply unit normalization
        eff_target_unit = target_unit or obs_unit
        norm = normalize_pair(obs_num, obs_unit, target_num, eff_target_unit)
        if not norm["compatible"]:
            return {
                "state": ApplicabilityState.DATA_REQUIRED,
                "reason": f"Cannot evaluate condition '{condition}': unit incompatibility between observed '{obs_unit}' and condition target '{eff_target_unit}'",
                "condition": condition,
                "evaluated_parameter": param_key,
                "observed_value": f"{fact_val} {fact_unit}".strip(),
            }

        v1 = norm["observed_normalized"]
        v2 = norm["expected_normalized"]

        if op == ">":
            applies = v1 > v2
        elif op == ">=":
            applies = v1 >= v2
        elif op == "<":
            applies = v1 < v2
        elif op == "<=":
            applies = v1 <= v2
        elif op == "==":
            applies = abs(v1 - v2) < 1e-6
        elif op == "!=":
            applies = abs(v1 - v2) >= 1e-6
        else:
            applies = False

        state = ApplicabilityState.APPLICABLE if applies else ApplicabilityState.NOT_APPLICABLE
        reason = (
            f"Condition '{param_key} {op} {raw_target}' evaluates to {applies} "
            f"(Observed: {obs_num} {obs_unit} -> {v1:.4g} {norm['base_unit']}, Target: {v2:.4g} {norm['base_unit']})"
        )
        return {
            "state": state,
            "reason": reason,
            "condition": condition,
            "evaluated_parameter": param_key,
            "observed_value": f"{fact_val} {fact_unit}".strip(),
        }

    # String / Categorical / Boolean comparison
    s_obs = str(fact_val).strip().strip("'\"").lower()
    s_target = raw_target.strip().strip("'\"").lower()

    if op == "==":
        applies = s_obs == s_target
    elif op == "!=":
        applies = s_obs != s_target
    else:
        applies = False

    state = ApplicabilityState.APPLICABLE if applies else ApplicabilityState.NOT_APPLICABLE
    reason = f"Condition '{param_key} {op} {raw_target}' evaluates to {applies} (Observed: '{fact_val}')"
    return {
        "state": state,
        "reason": reason,
        "condition": condition,
        "evaluated_parameter": param_key,
        "observed_value": fact_val,
    }


class DeterministicApplicabilityEngine:
    """Deterministic Applicability Engine utility class."""

    @staticmethod
    def evaluate_condition(
        condition: Optional[str],
        product_dna_facts: Dict[str, Any],
        conflicts: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return evaluate_applicability(condition, product_dna_facts, conflicts)
