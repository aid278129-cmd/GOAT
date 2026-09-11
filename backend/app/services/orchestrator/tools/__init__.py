"""Controlled LangChain Tools for Layer 3 AI Orchestrator (Milestone M24.3)."""

from backend.app.services.orchestrator.tools.schemas import (
    SearchStandardsInput,
    SearchStandardsOutput,
    SearchClausesInput,
    SearchClausesOutput,
    GetVerifiedEvidenceInput,
    GetVerifiedEvidenceOutput,
    NormalizeUnitInput,
    NormalizeUnitOutput,
    GetProductFactsInput,
    GetProductFactsOutput,
)
from backend.app.services.orchestrator.tools.guards import (
    validate_tool_permission,
    sanitize_and_validate_argument,
    enforce_standard_isolation,
    validate_tool_output_authority,
    ToolSecurityError,
    PROHIBITED_TOOL_ACTIONS,
)
from backend.app.services.orchestrator.tools.bis_tools import (
    search_bis_standards,
    search_bis_clauses,
    get_verified_evidence,
    normalize_unit,
    get_product_facts,
)
from backend.app.services.orchestrator.tools.registry import (
    ALLOWED_TOOLS,
    ROLE_TOOL_PERMISSIONS,
    ControlledToolRegistry,
    tool_registry,
)

__all__ = [
    "search_bis_standards",
    "search_bis_clauses",
    "get_verified_evidence",
    "normalize_unit",
    "get_product_facts",
    "tool_registry",
    "ControlledToolRegistry",
    "ALLOWED_TOOLS",
    "ROLE_TOOL_PERMISSIONS",
    "ToolSecurityError",
    "validate_tool_permission",
    "enforce_standard_isolation",
    "validate_tool_output_authority",
]
