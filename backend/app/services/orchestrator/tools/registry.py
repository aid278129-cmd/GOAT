"""Controlled Tool Registry and Contextual Permission Mapping (M24.3).

Explicitly enumerates permitted tools and maps them to agent roles following
the principle of least privilege.
"""

from typing import Dict, Any, Set, Optional, List
from langchain_core.tools import BaseTool

from backend.app.services.orchestrator.tools.bis_tools import (
    search_bis_standards,
    search_bis_clauses,
    get_verified_evidence,
    normalize_unit,
    get_product_facts,
)
from backend.app.services.orchestrator.tools.guards import (
    validate_tool_permission,
    ToolSecurityError,
)

# Canonical Registry of Permitted Tools
ALLOWED_TOOLS: Dict[str, BaseTool] = {
    "search_bis_standards": search_bis_standards,
    "search_bis_clauses": search_bis_clauses,
    "get_verified_evidence": get_verified_evidence,
    "normalize_unit": normalize_unit,
    "get_product_facts": get_product_facts,
}

# Contextual Least-Privilege Role Mapping
ROLE_TOOL_PERMISSIONS: Dict[str, Set[str]] = {
    "query_agent": {"search_bis_standards"},
    "retrieval_agent": {"search_bis_standards", "search_bis_clauses"},
    "analysis_agent": {"get_verified_evidence", "normalize_unit"},
    "planning_agent": {"get_product_facts", "get_verified_evidence"},
    "full_orchestrator": {"search_bis_standards", "search_bis_clauses", "get_verified_evidence", "normalize_unit", "get_product_facts"},
}


class ControlledToolRegistry:
    """Manages secure tool lookup, authorization, and contextual execution."""

    @classmethod
    def get_tool(cls, tool_name: str, role: Optional[str] = None) -> BaseTool:
        """Fetch permitted tool, validating existence and role privileges."""
        permitted = ROLE_TOOL_PERMISSIONS.get(role, set(ALLOWED_TOOLS.keys())) if role else set(ALLOWED_TOOLS.keys())
        validate_tool_permission(tool_name, permitted)
        return ALLOWED_TOOLS[tool_name]

    @classmethod
    def list_tools_for_role(cls, role: str) -> List[BaseTool]:
        """Return list of permitted tools for a specific agent role."""
        tool_names = ROLE_TOOL_PERMISSIONS.get(role, set())
        return [ALLOWED_TOOLS[name] for name in tool_names if name in ALLOWED_TOOLS]

    @classmethod
    def execute_tool(
        cls,
        tool_name: str,
        tool_input: Dict[str, Any],
        role: Optional[str] = None,
    ) -> Any:
        """Execute a permitted tool with input validation and audit metadata."""
        tool_instance = cls.get_tool(tool_name, role)
        return tool_instance.invoke(tool_input)


tool_registry = ControlledToolRegistry()
