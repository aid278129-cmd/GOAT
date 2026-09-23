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


        # 2. General BIS Information Intent
        if (
            re.search(r"\bwhat\s+(?:is|are)\s+is\s*\d+", q_lower)
            or re.search(r"\bwhat\s+does\s+(?:this|the|is\s*\d+)?\s*standard\s+cover\b", q_lower)
            or re.search(r"\bscope\s+of\s+(?:is\s*\d+|this\s+standard)\b", q_lower)
            or re.search(r"\btell\s+me\s+about\s+is\s*\d+\b", q_lower)
            or any(phrase in q_lower for phrase in [
                "certification scheme", "bis scheme", "difference between scheme", "scheme i and scheme ii",
                "scheme 1 and scheme 2", "scheme i vs scheme ii", "scheme 1 vs scheme 2", "what is scheme i",
                "what is scheme ii", "what is a bis certification scheme", "what is crs",
                "which bis certification scheme applies", "which scheme applies", "what scheme applies",
                "which certification scheme applies", "which scheme", "what is scheme", "explain scheme",
                "bis service", "bis services", "services are available", "services available",
                "what services does bis", "how does bis certification work", "how does certification work",
                "general bis certification process", "certification process", "certification workflow",
                "what documents are generally required", "what documents are required", "documents required for",
                "documents generally required", "documents needed", "what documents are needed",
                "major testing", "application steps", "testing steps", "testing/application steps",
                "testing and application steps", "major testing/application steps",
                "offline paper", "physical application", "manual submission", "paper form",
                "branch office submission", "offline submission",
            ])
            or (bool(re.search(r"\bscheme\s+([a-zA-Z0-9]+)\b", q_lower)) and not any(w in q_lower for w in ["my product", "our product", "compliant"]))
        ):
            return OrchestratorIntent.GENERAL_BIS_INFORMATION, sanitized, []

        # 2.4 BIS Hallmarking Assistance Intent (Milestone M25.4D)
        if any(phrase in q_lower for phrase in [
            "hallmark", "hallmarking", "bis hallmarking", "what is bis hallmarking",
            "what is hallmarking", "huid", "verify huid", "huid verification",
            "what is huid", "huid meaning", "meaning of huid", "gold hallmark",
            "gold hallmarking", "hallmark gold", "gold purity", "gold purity grade",
            "silver hallmark", "silver hallmarking", "hallmark silver", "silver purity",
            "silver purity grade", "22k916", "18k750", "14k585", "24k995", "23k958", "20k833",
            "is 1417", "is 2112", "is 15820", "is 1418", "is 2113", "assaying and hallmarking",
            "hallmarking centre", "hallmarking center", "hallmarking registration",
            "jeweller registration", "jeweler registration", "consumer hallmark",
            "hallmark compensation", "hallmarking fee", "hallmarking process",
            "how does hallmarking work", "hallmark services", "hallmarking service",
            "mandatory hallmarking", "gold jewellery hallmark", "gold jewelry hallmark",
            "silver jewellery hallmark", "silver jewelry hallmark", "gold rate", "gold price",
            "silver rate", "silver price", "regulation 18", "ahc",
        ]) or (
            any(w in q_lower for w in ["jewellery", "jewelry", "gold", "silver"])
            and any(w in q_lower for w in ["purity", "hallmark", "huid", "test", "testing", "compensation", "ahc"])
        ):
            return OrchestratorIntent.HALLMARKING, sanitized, []

        # 2.5 BIS Consumer Assistance Intent (Milestone M25.4C)
        if any(phrase in q_lower for phrase in [
            "verify a bis", "verify bis", "verify isi", "verify a isi", "verify an isi",
            "verify mark", "verify the mark", "check bis mark", "check isi mark", "how to verify",
            "how can i verify", "verify licence", "verify license", "verify registration",
            "check a bis licence", "check a bis license", "check bis licence", "check bis license",
            "check a registration", "check registration", "search a licence", "search license",
            "is the licence valid", "is the license valid", "licence status", "license status",
            "how do i check a bis licence", "how do i check a bis license",
            "raise a bis consumer complaint", "raise a complaint", "consumer complaint",
            "file a complaint", "register a complaint", "lodge a complaint", "how to complain",
            "how can i raise a bis consumer complaint", "report substandard", "complaint against bis",
            "bis care complaint", "complain about product", "suspected non-conforming",
            "non-conforming product", "defective product", "fake isi", "fake mark", "counterfeit mark",
            "substandard product", "suspected product", "what should a consumer do about a suspected",
            "what should a consumer do", "found fake mark", "fake bis", "what does a bis mark indicate",
            "what does bis mark mean", "what does isi mark indicate", "meaning of bis mark",
            "significance of bis mark", "what does a mark indicate", "why bis mark", "importance of bis mark",
            "bis care", "cml number", "r-number", "refund from bis", "bis cash refund", "whatsapp complaint",
        ]):
            return OrchestratorIntent.CONSUMER_ASSISTANCE, sanitized, []

        # 3. Query Requirement Intent
        if any(w in q_lower for w in ["what does clause", "requirement", "specification", "test limit", "mandate", "standard require", "permissible", "temperature rise limit", "leakage current limit"]):
            return OrchestratorIntent.QUERY_REQUIREMENT, sanitized, []

        # 4. Explain Gap Intent
        if any(w in q_lower for w in ["why is", "why gap", "missing evidence", "not satisfied", "failed", "unfulfilled", "action required", "how to resolve"]):
            return OrchestratorIntent.EXPLAIN_GAP, sanitized, []

        # 5. Clarify Product Intent
        if any(w in q_lower for w in ["what is the rated", "wattage", "voltage", "material", "capacity", "clarification", "parameter", "sheath", "handle"]):
            return OrchestratorIntent.CLARIFY_PRODUCT, sanitized, []

        # 6. Audit Trace Intent
        if any(w in q_lower for w in ["evidence", "lab report", "test report", "proof", "provenance", "source document", "nabl", "certificate"]):
            return OrchestratorIntent.AUDIT_TRACE, sanitized, []

        # 7. General Guidance Intent
        if any(w in q_lower for w in ["how to apply", "process", "timeline", "fees", "gazette", "qco"]):
            return OrchestratorIntent.GENERAL_GUIDANCE, sanitized, []

        return OrchestratorIntent.QUERY_REQUIREMENT, sanitized, []


intent_router = IntentRouter()
