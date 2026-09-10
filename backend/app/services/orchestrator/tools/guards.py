"""Security & Permission Boundaries for Controlled LangChain Tools (M24.3).

Enforces:
1. Rejection of unauthorized / arbitrary system tools.
2. Rejection of arbitrary code execution, SQL injection, arbitrary filesystem access, and HTTP calls.
3. Enforcement of standard isolation (prevents cross-standard leakage).
4. Argument sanitization and bounds enforcement.
"""

import re
from typing import Set, List, Dict, Any


# Forbidden tool action attempts (must be rejected)
PROHIBITED_TOOL_ACTIONS = {
    "set_compliance_status",
    "mark_satisfied",
    "approve_product",
    "certify_product",
    "override_applicability",
    "modify_gap_result",
    "modify_evidence_trust",
    "approve_source",
    "write_passport",
    "execute_sql",
    "execute_python",
    "read_file",
    "write_file",
    "fetch_url",
}

# Dangerous query patterns
DANGEROUS_PATTERNS = [
    re.compile(r"\b(?:drop|alter|insert|delete|update)\s+(?:table|database)\b", re.IGNORECASE),
    re.compile(r"\.\./", re.IGNORECASE),
    re.compile(r"(?:/etc/|c:\\windows)", re.IGNORECASE),
    re.compile(r"(?:__import__|exec|eval|os\.system|subprocess)", re.IGNORECASE),
]


class ToolSecurityError(ValueError):
    """Raised when a tool argument or invocation violates the security boundary."""
    pass


def validate_tool_permission(tool_name: str, allowed_tools: Set[str]) -> None:
    """Ensure tool is registered and permitted."""
    if tool_name in PROHIBITED_TOOL_ACTIONS:
        raise ToolSecurityError(f"Access Denied: Tool '{tool_name}' is explicitly prohibited. Tools have 0% compliance write authority.")
    if tool_name not in allowed_tools:
        raise ToolSecurityError(f"Access Denied: Tool '{tool_name}' is not recognized or permitted in this execution context.")


def sanitize_and_validate_argument(arg_val: str, field_name: str) -> str:
    """Check string arguments for SQL/filesystem/code injection."""
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(arg_val):
            raise ToolSecurityError(f"Malicious parameter detected in '{field_name}': Pattern match rejected.")
    return arg_val.strip()


def enforce_standard_isolation(target_standard: str, queried_standard: str) -> None:
    """Prevent cross-standard leakage when standard isolation is enforced."""
    t_clean = target_standard.strip().lower()
    q_clean = queried_standard.strip().lower()

    # Extract base standard number e.g. "is 17526"
    m_t = re.search(r"\bis\s*\d+(?:-\d+)*", t_clean)
    m_q = re.search(r"\bis\s*\d+(?:-\d+)*", q_clean)

    if m_t and m_q and m_t.group(0) != m_q.group(0):
        raise ToolSecurityError(
            f"Standard Isolation Violation: Cannot access clauses from '{queried_standard}' "
            f"while evaluating target standard '{target_standard}'."
        )
