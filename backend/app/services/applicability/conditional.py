"""Deterministic Conditional Applicability Engine for Bureau of Indian Standards (BIS).

Evaluates typed conditions against Product DNA without heuristic inference:
- Evaluates numerical, boolean, set, and string predicates deterministically.
- Missing attribute -> MORE_INFORMATION_REQUIRED (Never guess or infer).
- Discrepant attribute -> UNMET condition.
- Produces structured ConditionalRequirementEvaluation records for full auditability.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.schemas.product_dna import ProductDNACore
from backend.app.services.applicability.applicability_models import (
    TypedCondition,
    ConditionalRequirementEvaluation,
    ProductConditionStatus,
)


# Controlled catalog of typed conditions per standard
STANDARD_CONDITIONAL_PROFILES: Dict[str, List[TypedCondition]] = {
    # Domestic Stainless Steel Vacuum Flasks (IS 17526:2021)
    "IS 17526:2021": [
        TypedCondition(
            condition_id="COND-FLASK-CAPACITY-01",
            description="Domestic container capacity must be between 200 ml and 5000 ml (0.2 L to 5.0 L).",
            field="capacity_ml",
            operator="between",
            expected_value=[200, 5000],
            unit="ml",
            is_mandatory_discriminator=False,
        ),
        TypedCondition(
            condition_id="COND-FLASK-INTENDED-USE-02",
            description="Intended for domestic food/beverage storage (excludes cryogenic / medical / industrial vessels).",
            field="intended_use",
            operator="in",
            expected_value=["domestic", "beverage", "food_storage", "household", "travel", "water", "tea_coffee", "personal"],
            is_mandatory_discriminator=False,
        ),
    ],

    # Electric Immersion Water Heaters (IS 302-2-201:2008)
    "IS 302-2-201:2008": [
        TypedCondition(
            condition_id="COND-EWH-VOLTAGE-01",
            description="Rated voltage must not exceed 250 V single-phase AC.",
            field="voltage",
            operator="less_than_or_equal",
            expected_value=250,
            unit="V",
            is_mandatory_discriminator=True,
        ),
        TypedCondition(
            condition_id="COND-EWH-APPLICATION-02",
            description="Appliance must be portable immersion type intended for domestic liquid heating.",
            field="sub_category",
            operator="contains",
            expected_value="immersion",
            is_mandatory_discriminator=False,
        ),
    ],

    # Appliances for Heating Liquids (IS 302-2-15:2009)
    "IS 302-2-15:2009": [
        TypedCondition(
            condition_id="COND-KETTLE-VOLTAGE-01",
            description="Rated voltage must not exceed 250 V AC.",
            field="voltage",
            operator="less_than_or_equal",
            expected_value=250,
            unit="V",
            is_mandatory_discriminator=False,
        ),
    ],
}


def _extract_dna_field_value(dna: ProductDNACore, field_name: str) -> Tuple[bool, Any]:
    """Retrieve field value from Product DNA, returning (is_present, value).
    
    Distinguishes an explicitly set None/false from a missing attribute.
    """
    if hasattr(dna, field_name):
        val = getattr(dna, field_name)
        if val is not None:
            return True, val

    for attr in dna.attributes:
        if attr.name == field_name:
            return True, attr.value

    return False, None


def evaluate_single_typed_condition(
    condition: TypedCondition,
    dna: ProductDNACore,
) -> ConditionalRequirementEvaluation:
    """Evaluate one typed condition against Product DNA deterministically."""
    present, actual = _extract_dna_field_value(dna, condition.field)

    if not present or actual is None or actual == "":
        return ConditionalRequirementEvaluation(
            condition_id=condition.condition_id,
            condition_description=condition.description,
            attribute_evaluated=condition.field,
            actual_value=None,
            expected_value=condition.expected_value,
            status="MISSING_ATTRIBUTE",
            explanation=(
                f"Attribute '{condition.field}' is required to evaluate condition '{condition.condition_id}' "
                f"({condition.description}). Deterministic engine refuses to guess missing specification."
            ),
        )

    op = condition.operator
    expected = condition.expected_value
    satisfied = False

    if op == "equals":
        satisfied = (str(actual).lower() == str(expected).lower()) if isinstance(expected, str) else (actual == expected)

    elif op == "not_equals":
        satisfied = (str(actual).lower() != str(expected).lower()) if isinstance(expected, str) else (actual != expected)

    elif op == "contains":
        if isinstance(actual, list):
            satisfied = any(str(expected).lower() in str(x).lower() for x in actual)
        else:
            satisfied = str(expected).lower() in str(actual).lower()

    elif op == "in":
        actual_str = str(actual).lower()
        if isinstance(expected, list):
            satisfied = any(actual_str == str(e).lower() or str(e).lower() in actual_str for e in expected)
        else:
            satisfied = actual_str in str(expected).lower()

    elif op == "greater_than":
        try:
            satisfied = float(actual) > float(expected)
        except (ValueError, TypeError):
            satisfied = False

    elif op == "less_than":
        try:
            satisfied = float(actual) < float(expected)
        except (ValueError, TypeError):
            satisfied = False

    elif op == "less_than_or_equal":
        try:
            satisfied = float(actual) <= float(expected)
        except (ValueError, TypeError):
            satisfied = False

    elif op == "greater_than_or_equal":
        try:
            satisfied = float(actual) >= float(expected)
        except (ValueError, TypeError):
            satisfied = False

    elif op == "between":
        try:
            low, high = expected[0], expected[1]
            satisfied = float(low) <= float(actual) <= float(high)
        except (ValueError, TypeError, IndexError):
            satisfied = False

    elif op == "exists":
        satisfied = actual is not None

    if satisfied:
        return ConditionalRequirementEvaluation(
            condition_id=condition.condition_id,
            condition_description=condition.description,
            attribute_evaluated=condition.field,
            actual_value=actual,
            expected_value=condition.expected_value,
            status="SATISFIED",
            explanation=f"Attribute '{condition.field}'={actual} satisfies condition '{condition.condition_id}'.",
        )
    else:
        return ConditionalRequirementEvaluation(
            condition_id=condition.condition_id,
            condition_description=condition.description,
            attribute_evaluated=condition.field,
            actual_value=actual,
            expected_value=condition.expected_value,
            status="UNMET",
            explanation=(
                f"Attribute '{condition.field}'={actual} fails condition '{condition.condition_id}' "
                f"(expected {condition.operator} {condition.expected_value})."
            ),
        )


def evaluate_standard_conditions(
    std_number: str,
    dna: ProductDNACore,
) -> Tuple[ProductConditionStatus, List[ConditionalRequirementEvaluation], List[str]]:
    """Evaluate all registered conditional rules for a candidate standard.
    
    Returns:
    - ProductConditionStatus
    - List of ConditionalRequirementEvaluation details
    - List of missing attribute names required to complete evaluation
    """
    clean_key = std_number.strip()
    prefix = clean_key.split(":")[0]

    conditions = STANDARD_CONDITIONAL_PROFILES.get(clean_key) or STANDARD_CONDITIONAL_PROFILES.get(prefix)
    if not conditions:
        return ProductConditionStatus.NOT_CONDITIONAL, [], []

    evaluations: List[ConditionalRequirementEvaluation] = []
    missing_attrs: List[str] = []
    has_unmet = False

    for cond in conditions:
        res = evaluate_single_typed_condition(cond, dna)
        evaluations.append(res)
        if res.status == "MISSING_ATTRIBUTE":
            if cond.is_mandatory_discriminator:
                missing_attrs.append(cond.field)
        elif res.status == "UNMET":
            has_unmet = True

    if missing_attrs:
        return ProductConditionStatus.CONDITIONS_PENDING_INFO, evaluations, missing_attrs
    if has_unmet:
        return ProductConditionStatus.CONDITIONS_UNMET, evaluations, []
    return ProductConditionStatus.CONDITIONS_SATISFIED, evaluations, []
