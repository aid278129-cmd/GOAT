from typing import Any, Dict, List
from backend.app.schemas.product_dna import ProductDNACore


def _get_field_value(dna: ProductDNACore, field_name: str) -> Any:
    """Retrieve field value from core DNA or from dynamic attributes list."""
    if hasattr(dna, field_name):
        return getattr(dna, field_name)
    for attr in dna.attributes:
        if attr.name == field_name:
            return attr.value
    return None


def evaluate_condition(condition: Dict[str, Any], dna: ProductDNACore) -> bool:
    """Recursively evaluate declarative boolean condition against Product DNA."""
    if "all" in condition:
        return all(evaluate_condition(c, dna) for c in condition["all"])

    if "any" in condition:
        return any(evaluate_condition(c, dna) for c in condition["any"])

    if "not" in condition:
        return not evaluate_condition(condition["not"], dna)

    field = condition.get("field")
    operator = condition.get("operator")
    expected = condition.get("value")

    actual = _get_field_value(dna, field)
    if actual is None:
        return operator == "not_exists"

    if operator == "equals":
        return str(actual).lower() == str(expected).lower() if isinstance(expected, str) else actual == expected

    if operator == "contains":
        if isinstance(actual, list):
            return any(str(expected).lower() in str(item).lower() for item in actual)
        return str(expected).lower() in str(actual).lower()

    if operator == "in":
        if isinstance(expected, list):
            return actual in expected
        return str(actual) in str(expected)

    if operator == "greater_than":
        try:
            return float(actual) > float(expected)
        except (ValueError, TypeError):
            return False

    if operator == "less_than":
        try:
            return float(actual) < float(expected)
        except (ValueError, TypeError):
            return False

    if operator == "exists":
        return actual is not None

    return False
