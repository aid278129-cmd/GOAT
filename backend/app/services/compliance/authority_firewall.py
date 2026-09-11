"""Compliance Authority Firewall (Milestone M24.4).

Centralized enforcement of regulatory authority invariants:
1. Validates that compliance decisions originate ONLY from authorized deterministic engines:
   - Layer 5 -> APPLICABILITY
   - Layer 7 -> GAP_EVALUATION / SATISFIED
   - Layer 8 -> EVIDENCE_VERIFICATION
   - Layer 9 -> PASSPORT_CERTIFICATION
2. Strips and neutralizes compliance assertions from untrusted inputs:
   - LLM text
   - Tools
   - User inputs
   - Client API payloads
   - OCR / PDF / Voice
3. Enforces valid authority transitions.
"""

import re
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, timezone

from backend.app.services.compliance.authority_types import (
    AuthorityLevel,
    AuthoritySource,
    DecisionType,
    AuthoritativeRecord,
    AuthorityFirewallViolation,
    AuthorityTransitionError,
)

# Prohibited compliance declarations when originating from non-deterministic sources
PROTECTED_REGULATORY_TERMS = {
    "SATISFIED",
    "COMPLIANT",
    "NON_COMPLIANT",
    "NOT_SATISFIED",
    "CERTIFIED",
    "APPROVED",
    "EXEMPT",
    "APPLICABLE",
    "NOT_APPLICABLE",
}

# Mapping of decision types to their exclusively authorized deterministic layer and source
AUTHORIZED_DECISION_MAPPING = {
    DecisionType.APPLICABILITY: (5, AuthoritySource.LAYER_5_APPLICABILITY_ENGINE),
    DecisionType.GAP_EVALUATION: (7, AuthoritySource.LAYER_7_COMPLIANCE_GAP_ENGINE),
    DecisionType.EVIDENCE_VERIFICATION: (8, AuthoritySource.LAYER_8_SOURCE_VALIDATOR),
    DecisionType.PASSPORT_CERTIFICATION: (9, AuthoritySource.LAYER_9_PASSPORT_COMPILER),
}

# Regex pattern to identify attempt by AI or documents to issue authoritative verdicts
ASSERTION_PATTERN = re.compile(
    r"\b(?:hereby\s+certified|declared\s+compliant|product\s+is\s+certified|"
    r"mark\s+product\s+certified|certify\s+the\s+product|compliance\s+guaranteed|"
    r"approved\s+by\s+ai|assistant\s+declares\s+satisfied|"
    r"system\s+instruction:\s*mark\s+compliant|system\s+instruction:\s*mark\s+certified)\b",
    re.IGNORECASE,
)


class ComplianceAuthorityFirewall:
    """Centralized gatekeeper protecting deterministic regulatory authority."""

    @classmethod
    def validate_compliance_authority(
        cls,
        decision_type: DecisionType,
        decision_value: str,
        source: AuthoritySource,
        source_layer: int,
        deterministic: bool = True,
        correlation_id: str = "SYS-DEFAULT",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuthoritativeRecord:
        """Validate that a compliance decision originates from the authorized deterministic engine.
        
        Raises AuthorityFirewallViolation if any unauthorized entity attempts to claim authority.
        """
        # 1. Deterministic source enforcement
        if not deterministic:
            raise AuthorityFirewallViolation(
                f"Authority Denied: Non-deterministic decision '{decision_value}' rejected. "
                "All regulatory compliance determinations must be deterministic."
            )

        # 2. Check if source is an unauthorized non-deterministic entity
        unauthorized_sources = {
            AuthoritySource.LLM,
            AuthoritySource.LANGCHAIN,
            AuthoritySource.LANGGRAPH_AI_NODE,
            AuthoritySource.CONTROLLED_TOOL,
            AuthoritySource.USER_INPUT,
            AuthoritySource.DOCUMENT_OCR,
            AuthoritySource.VOICE_TRANSCRIPTION,
            AuthoritySource.BOM_PARSER,
            AuthoritySource.CLIENT_API,
        }
        if source in unauthorized_sources:
            raise AuthorityFirewallViolation(
                f"Authority Denied: Source '{source.value}' has 0.0% compliance authority. "
                f"Cannot declare decision '{decision_value}' of type '{decision_type.value}'."
            )

        # 3. Check layer and source match the specific decision type
        if decision_type not in AUTHORIZED_DECISION_MAPPING:
            raise AuthorityFirewallViolation(f"Unknown decision type '{decision_type}'.")

        expected_layer, expected_source = AUTHORIZED_DECISION_MAPPING[decision_type]
        if source_layer != expected_layer or source != expected_source:
            raise AuthorityFirewallViolation(
                f"Authority Mismatch: Decision type '{decision_type.value}' can ONLY be declared "
                f"by Layer {expected_layer} ({expected_source.value}), but received Layer {source_layer} ({source.value})."
            )

        # 4. Return validated AuthoritativeRecord
        return AuthoritativeRecord(
            decision_type=decision_type,
            decision_value=decision_value,
            authority_source=source,
            source_layer=source_layer,
            deterministic=True,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    @classmethod
    def sanitize_untrusted_compliance_claims(cls, text: str) -> Tuple[str, List[str]]:
        """Sanitize text from LLM, users, or documents to strip pseudo-regulatory assertions."""
        stripped_claims: List[str] = []
        if not text:
            return "", stripped_claims

        def _replace_match(match):
            claim = match.group(0)
            stripped_claims.append(claim)
            return "[Non-authoritative statement suppressed by Compliance Authority Firewall]"

        sanitized = ASSERTION_PATTERN.sub(_replace_match, text)
        return sanitized, stripped_claims

    @classmethod
    def validate_authority_transition(
        cls,
        current_level: AuthorityLevel,
        target_level: AuthorityLevel,
    ) -> None:
        """Enforce strict progressive authority transitions.
        
        Permitted sequence:
        UNTRUSTED_INPUT -> AI_DERIVED -> CANDIDATE -> VERIFIED_EVIDENCE -> DETERMINISTIC_EVALUATION -> AUTHORITATIVE_RESULT
        """
        # Forbidden direct jumps
        forbidden_jumps = {
            (AuthorityLevel.UNTRUSTED_INPUT, AuthorityLevel.AUTHORITATIVE_RESULT),
            (AuthorityLevel.UNTRUSTED_INPUT, AuthorityLevel.DETERMINISTIC_EVALUATION),
            (AuthorityLevel.UNTRUSTED_INPUT, AuthorityLevel.VERIFIED_EVIDENCE),
            (AuthorityLevel.AI_DERIVED, AuthorityLevel.AUTHORITATIVE_RESULT),
            (AuthorityLevel.AI_DERIVED, AuthorityLevel.DETERMINISTIC_EVALUATION),
            (AuthorityLevel.CANDIDATE, AuthorityLevel.AUTHORITATIVE_RESULT),
        }
        if (current_level, target_level) in forbidden_jumps:
            raise AuthorityTransitionError(
                f"Illegal Authority Transition: Cannot transition directly from "
                f"'{current_level.value}' to '{target_level.value}'."
            )

    @classmethod
    def sanitize_client_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Strip client-submitted authority claims to prevent client self-certification."""
        sanitized = dict(payload)
        # Strip self-declared authority metadata from client requests
        for key in ["authority_source", "source_layer", "deterministic", "is_authoritative"]:
            if key in sanitized:
                sanitized.pop(key, None)
        return sanitized


# Global singleton instance
compliance_firewall = ComplianceAuthorityFirewall()
