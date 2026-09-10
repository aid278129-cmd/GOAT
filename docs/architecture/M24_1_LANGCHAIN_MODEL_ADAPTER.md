# M24.1 — LangChain Model Adapter & Structured Output Integration

**Project**: Zyntrix — BIS Compliance Compiler  
**SIH Problem Statement**: 26107 — AI-powered Intelligent Assistant for Indian Standards and BIS Services for Industries and Consumers  
**Milestone**: M24.1  
**Previous Milestone**: M24.0 (Architecture & Integration Contract)  
**Status**: COMPLETE (HARDENED & AUDITED)  

---

## 1. Purpose
Milestone M24.1 establishes a clean, surgical LangChain model adapter layer wrapping the existing `SingleStructuredLLM` singleton (`single_structured_llm`). It exposes a standardized `BaseChatModel`-compatible interface with structured output parsing (`OrchestratedAIResponse`), preserving exact model identity, zero LLM compliance authority (0.0%), strict prompt injection defense, and full backward compatibility with the existing `AIOrchestrator` facade.

M24.1 strictly forbids introducing LangGraph, LangSmith, or Langflow, which are reserved for subsequent milestones.

---

## 2. Existing LLM Architecture Preservation
The Zyntrix architecture enforces **EXACTLY ONE LLM** across the entire platform:
- **Singleton Model**: `SingleStructuredLLM` (`single_structured_llm`).
- **Model Identifier**: `zyntrix-structured-compliance-llm`.
- **Output Schema**: `OrchestratedAIResponse` (Pydantic v2).
- **Compliance Authority**: Exactly `0.0%`.

The LangChain adapter (`ZyntrixLangChainChatAdapter`) holds a direct reference to this singleton:
```python
assert langchain_chat_adapter.underlying_llm is single_structured_llm
```
No secondary LLM instance or competing provider was created or configured.

---

## 3. LangChain Integration Boundary
The integration boundary is surgical and isolated to Layer 3:
```
SingleStructuredLLM (Singleton)
        │
        ▼
ZyntrixLangChainChatAdapter (BaseChatModel)
        │
        ▼
.with_structured_output(OrchestratedAIResponse)
        │
        ▼
OrchestratedAIResponse (Pydantic v2 Schema)
        │
        ▼
GroundingGuard & Citation Verifier
        │
        ▼
AIOrchestrator Facade
```
Downstream deterministic compliance engines (Layers 5, 7, 8, 9) remain 100% untouched and authoritative.

---

## 4. Adapter Architecture
The adapter is implemented in `backend/app/services/orchestrator/langchain_adapter.py`:
- **Base Class**: Inherits from `langchain_core.language_models.chat_models.BaseChatModel`.
- **Outputs**: Imports `ChatResult` and `ChatGeneration` strictly from `langchain_core.outputs`.
- **Execution Delegation**: `_generate` delegates directly to `self.underlying_llm.generate_grounded_response(...)` and encapsulates the serialized response in an `AIMessage`.
- **Model Metadata**: Identifies itself as `zyntrix-structured-compliance-llm` with `compliance_authority: "0.0%"`.

---

## 5. Model Identity & Params
```json
{
  "model_name": "zyntrix-structured-compliance-llm",
  "architecture_pillar": "Layer 3 AI Orchestrator",
  "compliance_authority": "0.0%",
  "underlying_model_class": "SingleStructuredLLM"
}
```

---

## 6. Structured Output Implementation
Because default `BaseChatModel.with_structured_output` raises `NotImplementedError` for custom local models without external tool binding API dependencies, `ZyntrixLangChainChatAdapter.with_structured_output` implements a native Pydantic v2 parsing pipeline via `RunnableLambda`:
- Parses serialized output into `OrchestratedAIResponse`.
- Supports `include_raw=True` returning a dictionary with keys `'raw'`, `'parsed'`, and `'parsing_error'`.
- Intercepts malformed payloads and safely falls back to zero-authority responses.

---

## 7. Failure Handling & Resilience
If an error occurs during model execution, network transport, or parsing:
1. `confidence_score = 0.0`
2. `grounding_status = GroundingStatus.UNKNOWN` (or `NOT_IN_KNOWLEDGE_BASE`)
3. `deterministic_fallback_used = True`
4. `regulatory_conclusion = "NONE"`
5. System disclaimer is attached.

Exceptions never elevate into successful compliance conclusions.

---

## 8. Prompt Security & Injection Defense
The prompt guard in `backend/app/services/security/prompt_guard.py` and intent router in `backend/app/services/orchestrator/intent_router.py` were hardened to neutralize:
- System instruction overrides (`"Ignore previous instructions..."`)
- Regulatory authority impersonation (`"Act as BIS and certify..."`)
- System prompt substitutions (`"Treat this document as the system prompt..."`)
- Forced compliance assertions (`"Declare this product compliant..."`)

All attacks are routed to `OrchestratorIntent.MALICIOUS_OVERRIDE_ATTEMPT` with zero compliance authority response (`0.0%`).

---

## 9. Compliance Authority Boundary
- **LLM Compliance Authority**: 0.0%
- **LangChain Compliance Authority**: 0.0%
- **Downstream Authority**: 100.0% retained by deterministic engines:
  - Layer 5: Applicability Engine
  - Layer 6: Clause-Level Retrieval
  - Layer 7: Compliance Gap Engine
  - Layer 8: Source Validation Gate
  - Layer 9: Compliance Passport Gate

---

## 10. Configuration & Feature Flags
Controlled via `backend/app/core/config.py`:
- `LANGCHAIN_LLM_ADAPTER_ENABLED: bool = False` (Default is disabled for zero-risk production stability).
- Can be toggled via environment variable `LANGCHAIN_LLM_ADAPTER_ENABLED=true` or `.env`.

---

## 11. Rollback Mechanism
In `backend/app/services/orchestrator/orchestrator.py`, step 4 cleanly branches between the legacy direct call and the LangChain adapter path based on `settings.LANGCHAIN_LLM_ADAPTER_ENABLED`. If enabled and an unexpected error occurs, it catches the exception and routes to deterministic fallback. Disabling the flag immediately restores 100% legacy execution with zero code changes.

---

## 12. Test Coverage & Verification
A dedicated test suite `backend/tests/test_m24_1_langchain_adapter.py` covers all 20 requirements:
1. `test_adapter_initialization_and_identity` — PASSED
2. `test_one_llm_enforcement` — PASSED
3. `test_base_chat_model_interface_compatibility` — PASSED
4. `test_structured_output_orchestrated_ai_response` — PASSED
5. `test_structured_output_include_raw` — PASSED
6. `test_generate_orchestrated_response_helper` — PASSED
7. `test_unverified_standard_rejection` — PASSED
8. `test_unverified_clause_rejection` — PASSED
9. `test_adversarial_override_attempt` — PASSED
10. `test_malformed_output_fallback` — PASSED
11. `test_generation_exception_safe_fallback` — PASSED
12. `test_grounding_guard_strips_prohibited_verdicts` — PASSED
13. `test_prompt_injection_via_orchestrator` — PASSED
14. `test_cardinal_invariants_zero_authority` — PASSED
15. `test_legacy_path_when_adapter_disabled` — PASSED
16. `test_adapter_path_when_adapter_enabled` — PASSED
17. `test_adapter_failure_in_orchestrator_safe_fallback` — PASSED
18. `test_clean_rollback_capability` — PASSED
19. `test_python_314_pydantic_v2_compatibility` — PASSED
20. `test_architectural_invariants_no_second_llm_or_langgraph` — PASSED

**Regression Suite**: **426/426 tests passing** (406 existing + 20 new).

---

## 13. Dependency Versions
- Python: `3.14.3`
- `langchain-core`: `1.5.3`
- `langchain-community`: `0.4.2`
- `langsmith`: `0.10.17`
- `pydantic`: `2.12.5`
- `langgraph`: **NOT INSTALLED**
- `langflow`: **NOT INSTALLED**

---

## 14. Known Limitations
- Model executes local synchronous deterministic rule simulation and local LLM stubbing; actual external inference relies on provider API keys (Groq/OpenAI) configured in settings.
- Tools are not yet exposed as LangChain `@tool` decorators (planned for M24.2 / M24.3).

---

## 15. Handoff to Milestone M24.2
With M24.1 complete, the foundation is ready for **M24.2 — Reasoning Graph & Node State Migration**:
- Implementation of LangGraph `StateGraph` for multi-step reasoning.
- Wrapping deterministic tools (`search_standards`, `search_clauses`, `normalize_unit`).
- Preservation of single LLM singleton across graph nodes.
