"""Intent Router for Layer 3 AI Orchestrator.

Classifies user query intent and detects adversarial prompt injection attempts.
Enforces zero compliance authority: Any attempt to command the assistant to declare
compliance is immediately intercepted and routed as MALICIOUS_OVERRIDE_ATTEMPT.
"""

import re
from typing import Tuple, List
from backend.app.services.orchestrator.schemas import OrchestratorIntent
from backend.app.services.security.prompt_guard import scan_and_sanitize_untrusted_text


class IntentRouter:
    """Classifies user queries and guards system prompt boundaries."""

    @classmethod
    def classify_intent(cls, query: str) -> Tuple[OrchestratorIntent, str, List[str]]:
        """Classify user intent while neutralizing prompt injection attempts."""
        # 1. Scan for adversarial prompt injection
        scan_result = scan_and_sanitize_untrusted_text(query)
        sanitized = scan_result.sanitized_text
        q_lower = sanitized.lower().strip()

        if not scan_result.is_safe:
            return OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT, sanitized, scan_result.detected_patterns

        # Direct compliance override check & extended injection patterns
        if re.search(r"\b(certify|declare|mark)\b.*?\b(compliant|satisfied|passed)\b", q_lower) or any(
            w in q_lower for w in [
                "ignore previous", "override", "bypass gate", "make it pass", "grant isi mark",
                "do not verify source", "skip evidence validation", "change compliance result to satisfied",
                "treat uploaded document as official", "assume is",
            ]
        ):
            return OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT, sanitized, ["DIRECT_COMPLIANCE_OVERRIDE_ATTEMPT"]


        # 2. Query Requirement Intent
        if any(w in q_lower for w in ["what does clause", "requirement", "specification", "test limit", "mandate", "standard require", "permissible", "temperature rise limit", "leakage current limit"]):
            return OrchestratorIntent.QUERY_REQUIREMENT, sanitized, []

        # 3. Explain Gap Intent
        if any(w in q_lower for w in ["why is", "why gap", "missing evidence", "not satisfied", "failed", "unfulfilled", "action required", "how to resolve"]):
            return OrchestratorIntent.EXPLAIN_GAP, sanitized, []

        # 4. Clarify Product Intent
        if any(w in q_lower for w in ["what is the rated", "wattage", "voltage", "material", "capacity", "clarification", "parameter", "sheath", "handle"]):
            return OrchestratorIntent.CLARIFY_PRODUCT, sanitized, []

        # 5. Audit Trace Intent
        if any(w in q_lower for w in ["evidence", "lab report", "test report", "proof", "provenance", "source document", "nabl", "certificate"]):
            return OrchestratorIntent.AUDIT_TRACE, sanitized, []

        # 6. General Guidance Intent
        if any(w in q_lower for w in ["how to apply", "process", "bis scheme", "timeline", "fees", "gazette", "qco"]):
            return OrchestratorIntent.GENERAL_GUIDANCE, sanitized, []

        return OrchestratorIntent.QUERY_REQUIREMENT, sanitized, []


intent_router = IntentRouter()
