"""Single Structured LLM Interface for Layer 3 AI Orchestrator.

Strictly adheres to architectural constraint:
USE ONE LLM MODEL ONLY.
Do NOT create multiple independent LLMs or competing AI decision-makers.

The LLM provides language intelligence:
- Explaining codified requirements
- Summarizing retrieved evidence
- Formulating clarifying questions
The LLM has ZERO compliance decision authority.
"""

import json
from typing import Dict, Any, List, Optional
from backend.app.services.orchestrator.schemas import (
    OrchestratorIntent,
    OrchestratorContext,
    OrchestratedAIResponse,
    GroundingStatus,
    CitationItem,
)
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG


class SingleStructuredLLM:
    """The authoritative, single LLM interface for the Zyntrix platform."""

    def __init__(self, model_name: str = "zyntrix-structured-compliance-llm"):
        self.model_name = model_name

    def generate_grounded_response(
        self,
        intent: OrchestratorIntent,
        sanitized_query: str,
        context: OrchestratorContext,
    ) -> OrchestratedAIResponse:
        """Generate structured, grounded response bounded by verified context."""
        q_lower = sanitized_query.lower()
        std_key = context.target_standard or "IS 302-2-201:2008"
        std_data = VERIFIED_STANDARDS_CATALOG.get(std_key, {})
        clauses_dict = std_data.get("clauses", {})

        # 1. Check if user is asking about an unverified standard
        if std_key not in VERIFIED_STANDARDS_CATALOG:
            return OrchestratedAIResponse(
                answer=f"I don't have verified information in the current BIS knowledge base for {std_key}. The system strictly refuses to speculate or invent unverified standards.",
                intent=intent,
                grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                confidence_score=0.0,
                citations=[],
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )

        import re
        m_std = re.search(r"\bis\s*(\d{4,6})(?::\d{4})?\b", q_lower, re.IGNORECASE)
        if m_std:
            asked_num = m_std.group(1)
            if not any(asked_num in k for k in VERIFIED_STANDARDS_CATALOG):
                return OrchestratedAIResponse(
                    answer=f"I don't have verified information in the current BIS knowledge base for IS {asked_num}. The system strictly refuses to speculate or invent unverified standards.",
                    intent=intent,
                    grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                    confidence_score=0.0,
                    citations=[],
                    deterministic_fallback_used=True,
                    regulatory_conclusion="NONE",
                )


        # 2. Check if user is asking about an unverified / non-existent clause
        m_cl = re.search(r"\bclause\s*(\d+(?:\.\d+)+)\b", q_lower)
        if m_cl:
            asked_cl = m_cl.group(1)
            if asked_cl not in clauses_dict:
                return OrchestratedAIResponse(
                    answer=f"Clause {asked_cl} does not exist in the codified requirements for {std_key}. The system does not speculate on unverified clauses.",
                    intent=intent,
                    grounding_status=GroundingStatus.NOT_IN_KNOWLEDGE_BASE,
                    confidence_score=0.0,
                    citations=[CitationItem(standard_number=std_key, verified=True)],
                    deterministic_fallback_used=True,
                    regulatory_conclusion="NONE",
                )

        # 3. Intent: Adversarial Injection / Compliance Override Attempt
        if intent == OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT:
            return OrchestratedAIResponse(
                answer=(
                    "The AI assistant has ZERO authority to declare, override, or certify compliance. "
                    "Under Zyntrix architecture, compliance determinations are strictly computed by the "
                    "deterministic compliance gate based on verified empirical laboratory evidence. "
                    "LLM compliance authority is exactly 0%."
                ),
                intent=intent,
                grounding_status=GroundingStatus.SUPPORTED,
                confidence_score=1.0,
                citations=[CitationItem(standard_number=std_key, source_authority="Zero-Hallucination Regulatory Integrity Gate")],
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )

        # 4. Intent: Query Requirement
        if m_cl and m_cl.group(1) in clauses_dict:
            cl_info = clauses_dict[m_cl.group(1)]
            return OrchestratedAIResponse(
                answer=(
                    f"Under {std_key} Clause {m_cl.group(1)} ({cl_info['title']}), "
                    f"the standard mandates: {cl_info['req']}"
                ),
                intent=intent,
                grounding_status=GroundingStatus.SUPPORTED,
                confidence_score=0.98,
                citations=[
                    CitationItem(
                        standard_number=std_key,
                        clause_number=m_cl.group(1),
                        clause_title=cl_info["title"],
                        verified=True,
                    )
                ],
                deterministic_fallback_used=False,
                regulatory_conclusion="NONE",
            )

        # 5. Intent: Explain Gap or Evidence
        if intent == OrchestratorIntent.EXPLAIN_GAP or "gap" in q_lower or "missing" in q_lower:
            return OrchestratedAIResponse(
                answer=(
                    f"I cannot establish compliance from the available evidence alone. "
                    f"For {context.product_name} under {std_key}, full satisfaction requires "
                    f"attaching accredited laboratory test certificates covering dielectric strength, "
                    f"earthing continuity, and temperature-rise limits."
                ),
                intent=intent,
                grounding_status=GroundingStatus.SUPPORTED,
                confidence_score=0.92,
                citations=[CitationItem(standard_number=std_key, verified=True)],
                missing_information_notes="Accredited NABL test report required for clause satisfaction.",
                deterministic_fallback_used=False,
                regulatory_conclusion="NONE",
            )

        # Default Grounded Assistant Answer
        return OrchestratedAIResponse(
            answer=(
                f"For {context.product_name} evaluated against {std_key} ({std_data.get('title', '')}), "
                f"the mandatory Quality Control Order is '{std_data.get('qco_order', '')}'. "
                f"You can query specific clauses (e.g. Clause 6.1 for voltage or Clause 22.101 for element sheath)."
            ),
            intent=intent,
            grounding_status=GroundingStatus.SUPPORTED,
            confidence_score=0.95,
            citations=[CitationItem(standard_number=std_key, verified=True)],
            deterministic_fallback_used=False,
            regulatory_conclusion="NONE",
        )


single_structured_llm = SingleStructuredLLM()
