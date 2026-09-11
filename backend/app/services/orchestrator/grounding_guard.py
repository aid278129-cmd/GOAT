"""Citation and Grounding Guard for Layer 3 AI Orchestrator.

Enforces Technology Pillar 05 & Layer 8 Citation Guard principles:
- NO VERIFIED SOURCE -> NO REGULATORY CLAIM
- NO RETRIEVED EVIDENCE -> DO NOT ANSWER AS FACT
- LLM COMPLIANCE AUTHORITY = 0%

Actively suppresses ungrounded claims, hallucinated standards, and regulatory verdicts.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.services.orchestrator.schemas import (
    CitationItem,
    GroundingStatus,
    OrchestratedAIResponse,
)
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG
from backend.app.core.logging import logger

PROHIBITED_LLM_VERDICTS = [
    re.compile(r"\bthis\s+product\s+is\s+(?:fully\s+)?(?:compliant|satisfied|certified)\b", re.IGNORECASE),
    re.compile(r"\bverdict\s*:\s*(?:satisfied|compliant)\b", re.IGNORECASE),
    re.compile(r"\bi\s+(?:hereby\s+)?certify\b", re.IGNORECASE),
    re.compile(r"\bcompliance\s+granted\b", re.IGNORECASE),
]


class GroundingGuard:
    """Inspects AI generated text, validates citations, and strips illegal compliance declarations."""

    @classmethod
    def validate_citations(
        cls,
        text: str,
        target_standard: Optional[str] = None,
    ) -> Tuple[List[CitationItem], List[str]]:
        """Extract and verify all Indian Standard citations from generated text."""
        citations: List[CitationItem] = []
        suppressed: List[str] = []

        # Find IS citations
        std_matches = re.finditer(r"\bIS\s*(\d+(?:-\d+)*(?:-\d+)*)(?::(\d{4}))?\b", text, re.IGNORECASE)
        for sm in std_matches:
            raw_std = sm.group(0)
            std_num = sm.group(1)

            # Check in verified catalog
            matched_key = None
            for cat_key in VERIFIED_STANDARDS_CATALOG:
                if std_num in cat_key:
                    matched_key = cat_key
                    break

            if matched_key:
                # Look for associated clause
                clause_match = re.search(r"clause\s*(\d+(?:\.\d+)+)", text[sm.end():sm.end()+50], re.IGNORECASE)
                cl_num = clause_match.group(1) if clause_match else None
                cl_data = None
                if cl_num:
                    cl_data = VERIFIED_STANDARDS_CATALOG[matched_key]["clauses"].get(cl_num)

                citations.append(
                    CitationItem(
                        standard_number=matched_key,
                        clause_number=cl_num,
                        clause_title=cl_data.get("title") if cl_data else None,
                        verified=True,
                    )
                )
            else:
                suppressed.append(f"Unverified standard citation intercepted and suppressed: '{raw_std}'")

        return citations, suppressed

    @classmethod
    def sanitize_regulatory_assertions(cls, text: str) -> Tuple[str, bool]:
        """Strip any attempt by LLM to declare compliance or SATISFIED status."""
        sanitized = text
        stripped_any = False

        for pat in PROHIBITED_LLM_VERDICTS:
            if pat.search(sanitized):
                stripped_any = True
                sanitized = pat.sub(
                    "[COMPLIANCE_CONCLUSION_SUPPRESSED: Compliance can only be computed deterministically by downstream engines]",
                    sanitized,
                )

        return sanitized, stripped_any


grounding_guard = GroundingGuard()
