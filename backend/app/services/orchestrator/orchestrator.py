"""Production-Level Layer 3: AI Orchestrator.

Coordinates the complete 11-step pipeline:
1. Intent Router
2. Task Router
3. Context Builder
4. Verified Knowledge Selector
5. Retrieval Controller
6. Structured LLM Interface (ONE LLM)
7. Output Schema Validator
8. Citation / Grounding Guard
9. Uncertainty Handler
10. Expert Review Router
11. Complete Audit Logging

Strict Grounding Rules:
NO VERIFIED SOURCE -> NO REGULATORY CLAIM
NO RETRIEVED EVIDENCE -> DO NOT ANSWER AS FACT
UNKNOWN -> UNKNOWN / INFORMATION REQUIRED
CONFLICT -> EXPERT REVIEW
LLM COMPLIANCE AUTHORITY = 0%
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.services.orchestrator.schemas import (
    OrchestratorIntent,
    GroundingStatus,
    OrchestratedAIResponse,
    AuditLogRecord,
    CitationItem,
)
from backend.app.services.orchestrator.intent_router import intent_router
from backend.app.services.orchestrator.knowledge_selector import verified_knowledge_selector
from backend.app.services.orchestrator.context_builder import context_builder
from backend.app.services.orchestrator.llm_interface import single_structured_llm
from backend.app.services.orchestrator.langchain_adapter import langchain_chat_adapter
from backend.app.services.orchestrator.graph.runner import run_compliance_graph
from backend.app.services.orchestrator.grounding_guard import grounding_guard
from backend.app.services.orchestrator.multilingual import (
    detect_language,
    translate_grounded_response,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger

# In-memory audit trail repository
ORCHESTRATOR_AUDIT_LOG: List[AuditLogRecord] = []


class AIOrchestrator:
    """The central orchestration engine for Layer 3."""

    @classmethod
    def process_query(
        cls,
        user_query: str,
        product_dna: Optional[Any] = None,
        assessment_context: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
    ) -> OrchestratedAIResponse:
        """Execute the complete 11-step orchestration workflow."""
        target_lang = language or detect_language(user_query)

        # Check LangGraph feature flag (M24.2)
        if getattr(settings, "LANGGRAPH_ORCHESTRATOR_ENABLED", False):
            try:
                graph_res = run_compliance_graph(
                    user_query=user_query,
                    product_dna=product_dna,
                    assessment_context=assessment_context,
                )
                if target_lang in ("hi", "ta"):
                    graph_res = translate_grounded_response(graph_res, target_lang)
                return graph_res
            except Exception as exc:
                logger.error(f"[AIOrchestrator] LangGraph execution failed: {exc}. Enforcing deterministic fallback.")
                fallback_res = OrchestratedAIResponse(
                    answer="An unexpected error occurred during reasoning graph execution. Safe deterministic fallback enforced.",
                    intent=OrchestratorIntent.UNKNOWN_INTENT,
                    grounding_status=GroundingStatus.UNKNOWN,
                    confidence_score=0.0,
                    citations=[],
                    deterministic_fallback_used=True,
                    regulatory_conclusion="NONE",
                )
                if target_lang in ("hi", "ta"):
                    fallback_res = translate_grounded_response(fallback_res, target_lang)
                return fallback_res

        audit_id = f"AUDIT-L3-{uuid.uuid4().hex[:8].upper()}"

        # 1. Intent Classification & Prompt Injection Defense
        intent, sanitized_query, security_warnings = intent_router.classify_intent(user_query)

        # 2. Extract Target Standard & Knowledge Selection
        target_std = None
        if assessment_context and "standard_number" in assessment_context:
            target_std = assessment_context["standard_number"]
        else:
            std_match, _ = verified_knowledge_selector.match_standard_in_query(sanitized_query)
            if std_match:
                target_std = std_match
            elif intent in (OrchestratorIntent.GENERAL_BIS_INFORMATION, OrchestratorIntent.CONSUMER_ASSISTANCE, OrchestratorIntent.HALLMARKING, OrchestratorIntent.LABORATORY_GUIDANCE):
                target_std = None
            else:
                target_std = "IS 302-2-201:2008"

        # 3. Context Construction
        context = context_builder.build_context(
            product_dna=product_dna,
            verified_standard=target_std,
            retrieved_clauses=assessment_context.get("evaluations") if assessment_context else None,
            available_evidence=assessment_context.get("available_evidence") if assessment_context else None,
        )

        # 4. Structured LLM Generation (ONE LLM ONLY)
        if getattr(settings, "LANGCHAIN_LLM_ADAPTER_ENABLED", False):
            try:
                raw_response = langchain_chat_adapter.generate_orchestrated_response(
                    intent=intent,
                    sanitized_query=sanitized_query,
                    context=context,
                )
            except Exception as exc:
                logger.error(f"[AIOrchestrator] LangChain adapter failed: {exc}. Invoking deterministic fallback.")
                raw_response = OrchestratedAIResponse(
                    answer="An unexpected error occurred during language processing. The system strictly refuses to guess compliance requirements.",
                    intent=intent,
                    grounding_status=GroundingStatus.UNKNOWN,
                    confidence_score=0.0,
                    citations=[],
                    deterministic_fallback_used=True,
                    regulatory_conclusion="NONE",
                )
        else:
            raw_response = single_structured_llm.generate_grounded_response(
                intent=intent,
                sanitized_query=sanitized_query,
                context=context,
            )

        # 5. Schema Validation & Sanitization
        sanitized_answer, stripped_verdict = grounding_guard.sanitize_regulatory_assertions(raw_response.answer)

        # 6. Citation Verification
        verified_citations, suppressed_claims = grounding_guard.validate_citations(
            text=sanitized_answer,
            target_standard=target_std,
        )

        # Combine citations
        final_citations = raw_response.citations + [c for c in verified_citations if not any(rc.standard_number == c.standard_number and rc.clause_number == c.clause_number for rc in raw_response.citations)]

        # 7. Uncertainty & Expert Review Routing
        grounding_state = raw_response.grounding_status
        expert_review = raw_response.expert_review_recommended

        # If confidence is low or claims were suppressed, route to uncertainty or expert review
        if raw_response.confidence_score < 0.70 and grounding_state == GroundingStatus.SUPPORTED:
            grounding_state = GroundingStatus.UNCERTAIN
            expert_review = True

        if suppressed_claims or raw_response.grounding_status in (GroundingStatus.NOT_IN_KNOWLEDGE_BASE, GroundingStatus.UNKNOWN) or raw_response.confidence_score == 0.0:
            if suppressed_claims or raw_response.grounding_status == GroundingStatus.NOT_IN_KNOWLEDGE_BASE:
                grounding_state = GroundingStatus.NOT_IN_KNOWLEDGE_BASE
            final_citations = []

        final_response = OrchestratedAIResponse(
            answer=sanitized_answer,
            intent=intent,
            grounding_status=grounding_state,
            confidence_score=raw_response.confidence_score,
            citations=final_citations,
            missing_information_notes=raw_response.missing_information_notes,
            expert_review_recommended=expert_review,
            deterministic_fallback_used=raw_response.deterministic_fallback_used,
            regulatory_conclusion="NONE",  # Invariant: LLM has zero compliance authority
        )

        # Multilingual Translation with Canonical Token Preservation (Milestone M25.4F)
        if target_lang in ("hi", "ta"):
            final_response = translate_grounded_response(final_response, target_lang)

        # 8. Complete Audit Logging
        audit_record = AuditLogRecord(
            audit_id=audit_id,
            timestamp=datetime.utcnow(),
            user_query=user_query,
            sanitized_query=sanitized_query,
            classified_intent=intent,
            target_standard=target_std,
            retrieved_clause_count=len(context.applicable_clauses),
            grounding_status=grounding_state,
            raw_llm_output=raw_response.answer,
            suppressed_claims=suppressed_claims + security_warnings,
            final_answer=sanitized_answer,
        )
        ORCHESTRATOR_AUDIT_LOG.append(audit_record)

        return final_response

    @classmethod
    def get_audit_trail(cls, limit: int = 50) -> List[AuditLogRecord]:
        """Fetch historical audit log records."""
        return ORCHESTRATOR_AUDIT_LOG[-limit:]


ai_orchestrator = AIOrchestrator()
