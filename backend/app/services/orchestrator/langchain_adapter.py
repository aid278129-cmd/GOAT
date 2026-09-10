"""LangChain Model Adapter for Layer 3 AI Orchestrator (Milestone M24.1).

Architectural Invariants Strictly Enforced:
1. EXACTLY ONE LLM: Wraps the existing SingleStructuredLLM singleton (single_structured_llm).
   Does NOT create a second LLM, second model instance, or alternative provider.
2. ZERO COMPLIANCE AUTHORITY: LangChain compliance authority = 0.0%.
   All compliance determinations remain 100% computed by downstream deterministic engines.
3. OUTPUT CONTRACT PRESERVATION: Outputs are validated against the exact same
   OrchestratedAIResponse Pydantic v2 schema.
4. Python 3.14 + langchain-core 1.5.3 Compatibility:
   - Uses Pydantic v2 schemas exclusively.
   - ChatResult and ChatGeneration imported from langchain_core.outputs.
   - Custom with_structured_output implementation bypassing unsupported bind_tools.
"""

import json
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.runnables import Runnable, RunnableLambda

from backend.app.services.orchestrator.llm_interface import (
    SingleStructuredLLM,
    single_structured_llm,
)
from backend.app.services.orchestrator.schemas import (
    CitationItem,
    GroundingStatus,
    OrchestratedAIResponse,
    OrchestratorContext,
    OrchestratorIntent,
)
from backend.app.core.logging import logger


class ZyntrixLangChainChatAdapter(BaseChatModel):
    """LangChain BaseChatModel adapter wrapping Zyntrix SingleStructuredLLM."""

    model_name: str = Field(default="zyntrix-structured-compliance-llm")
    underlying_llm: SingleStructuredLLM = Field(default_factory=lambda: single_structured_llm)

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @property
    def _llm_type(self) -> str:
        return "zyntrix-structured-compliance-llm"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "architecture_pillar": "Layer 3 AI Orchestrator",
            "compliance_authority": "0.0%",
            "underlying_model_class": self.underlying_llm.__class__.__name__,
        }

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Execute chat generation by delegating to the single underlying LLM.
        
        Serializes the generated OrchestratedAIResponse as JSON into an AIMessage.
        """
        intent = kwargs.get("intent", OrchestratorIntent.QUERY_REQUIREMENT)
        context = kwargs.get("context")

        user_query = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
                user_query = str(msg.content)
                break
            elif isinstance(msg, BaseMessage) and not isinstance(msg, SystemMessage):
                user_query = str(msg.content)
                break

        if not context:
            context = OrchestratorContext(
                product_name="Evaluated Product",
                category="General",
            )

        try:
            structured_res = self.underlying_llm.generate_grounded_response(
                intent=intent,
                sanitized_query=user_query,
                context=context,
            )
            content_json = structured_res.model_dump_json()
        except Exception as exc:
            logger.error(f"[LangChainAdapter] Underling LLM generation failed: {exc}")
            fallback_res = OrchestratedAIResponse(
                answer="An unexpected error occurred during language processing. The system strictly refuses to guess compliance requirements.",
                intent=intent,
                grounding_status=GroundingStatus.UNKNOWN,
                confidence_score=0.0,
                citations=[],
                deterministic_fallback_used=True,
                regulatory_conclusion="NONE",
            )
            content_json = fallback_res.model_dump_json()

        generation = ChatGeneration(message=AIMessage(content=content_json))
        return ChatResult(generations=[generation])

    def with_structured_output(
        self,
        schema: Union[Dict[str, Any], Type[BaseModel]],
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Runnable[Any, Any]:
        """Wrap model with structured output parsing compliant with langchain-core 1.5.3.
        
        Bypasses bind_tools (which raises NotImplementedError for custom local LLMs)
        and parses the serialized JSON into the requested Pydantic v2 schema instance.
        """
        def _parse_output(input_val: Any) -> Any:
            if isinstance(input_val, ChatResult):
                raw_msg = input_val.generations[0].message
            elif isinstance(input_val, AIMessage):
                raw_msg = input_val
            elif isinstance(input_val, BaseMessage):
                raw_msg = input_val
            else:
                raw_msg = AIMessage(content=str(input_val))

            parsed_obj = None
            parsing_err = None

            try:
                if isinstance(schema, type) and issubclass(schema, BaseModel):
                    parsed_obj = schema.model_validate_json(raw_msg.content)
                elif isinstance(schema, dict):
                    parsed_obj = json.loads(raw_msg.content)
                else:
                    parsed_obj = json.loads(raw_msg.content)
            except Exception as e:
                logger.error(f"[LangChainAdapter] Output parsing failed: {e}")
                parsing_err = e
                if not include_raw:
                    if schema is OrchestratedAIResponse or (isinstance(schema, type) and issubclass(schema, OrchestratedAIResponse)):
                        return OrchestratedAIResponse(
                            answer="Malformed response payload intercepted. Enforcing deterministic zero-authority fallback.",
                            intent=OrchestratorIntent.UNKNOWN_INTENT,
                            grounding_status=GroundingStatus.UNKNOWN,
                            confidence_score=0.0,
                            citations=[],
                            deterministic_fallback_used=True,
                            regulatory_conclusion="NONE",
                        )
                    raise e

            if include_raw:
                return {
                    "raw": raw_msg,
                    "parsed": parsed_obj,
                    "parsing_error": parsing_err,
                }
            return parsed_obj

        return self | RunnableLambda(_parse_output)

    def generate_orchestrated_response(
        self,
        intent: OrchestratorIntent,
        sanitized_query: str,
        context: OrchestratorContext,
    ) -> OrchestratedAIResponse:
        """High-level invocation helper returning a fully-validated OrchestratedAIResponse."""
        messages = [
            SystemMessage(content=context.system_guardrails),
            HumanMessage(content=sanitized_query),
        ]
        structured_runnable = self.with_structured_output(OrchestratedAIResponse)
        response: OrchestratedAIResponse = structured_runnable.invoke(
            messages,
            intent=intent,
            context=context,
        )
        return response


langchain_chat_adapter = ZyntrixLangChainChatAdapter(
    model_name=single_structured_llm.model_name,
    underlying_llm=single_structured_llm,
)
