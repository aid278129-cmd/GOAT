# M24.5 — LangSmith Observability & LangStudio Graph Visualization

**Project:** Zyntrix — BIS Compliance Compiler  
**Milestone:** M24.5  
**Status:** IMPLEMENTED & VERIFIED  
**Baseline Test Count:** 550 passed  
**Total Test Count:** 564 passed (+14 comprehensive observability & privacy tests)  

---

## 1. Architectural Overview

M24.5 adds production-grade observability and runtime visualization to the existing Zyntrix LangGraph reasoning graph (Layer 3 Orchestration) without altering its 11-node, 16-edge topology, without adding agents, and without violating the cardinal compliance authority rules.

```
+----------------------------------------------------------------------------------------------------+
|                                    Zyntrix LangGraph Runtime                                       |
|                                                                                                    |
|  [__start__] -> [request_understanding] -> ... -> [deterministic_compliance_gate] -> [__end__]    |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
                                                   | Execution callbacks & metadata
                                                   v
                             +--------------------------------------------+
                             |       M24.5 Privacy-Preserving Engine      |
                             |  - Deterministic Credential Redaction      |
                             |  - PII Masking (Aadhaar, Phone, Email)     |
                             |  - Database URL & Password Stripping       |
                             |  - Proprietary BOM Hashing (SHA-256)       |
                             +---------------------+----------------------+
                                                   |
                        +--------------------------+--------------------------+
                        | Tracing Disabled (Default)| Tracing Enabled (Flagged)
                        v                          v
             +-----------------------+   +------------------------------------+
             | InMemoryCallback      |   | LangChainTracer (LangSmith)        |
             | - Local inspectability|   | - Project: zyntrix-bis-compliance  |
             | - 0 network emissions |   | - Correlation ID tagged            |
             | - 0 external overhead |   | - Resilient failure isolation      |
             +-----------------------+   +------------------------------------+
                                                   |
                                                   v
             +----------------------------------------------------------------+
             |                     LangGraph Studio Visualizer                |
             | - Target: compliance_graph_studio (checkpointer=False)         |
             | - Interactive canvas: 11 nodes, 16 edges, branch conditions    |
             | - Studio runner: start_studio.bat (UTF-8 console encoding)     |
             +----------------------------------------------------------------+
```

---

## 2. Cardinal Principles Preserved

1. **Topology Invariant**: The canonical graph topology remains strictly untouched: 11 nodes, 16 edges, 0 cycles (strict DAG).
2. **Single LLM Invariant**: No additional LLMs or sub-models are introduced. `SingleStructuredLLM` remains the sole model.
3. **Downstream Authority Preservation**: Observability tools, traces, and handlers possess **0.0% compliance authority**. Compliance determination authority resides exclusively in Layers 5 and 7, evidence authority in Layer 8, and output/passport integrity in Layer 9. Traces are purely analytical artifacts.
4. **Privacy-by-Default**: Tracing is disabled by default (`LANGSMITH_TRACING=false`). No traces, tokens, or network requests are emitted unless explicitly configured.
5. **Deterministic Redaction**: All trace payloads pass through deterministic sanitization to redact API keys, database credentials, PII (Aadhaar, phone, email), and raw proprietary BOM data prior to ingestion.
6. **Failure Isolation**: An unreachable LangSmith endpoint, network timeout, rate limit, or invalid API key **NEVER** aborts or degrades compliance graph execution.

---

## 3. Implementation Components

### 3.1 Tracing Service (`backend/app/services/orchestrator/graph/tracing.py`)

- **`is_tracing_enabled()`**: Reads environment configuration (`LANGSMITH_TRACING` or `LANGCHAIN_TRACING_V2`). Returns `False` when unset or set to `false`.
- **`redact_sensitive_text(text: str)`**: Deterministic regular expression scrubbing:
  - API keys (`ak_...`, `sk-...`, `gsk_...`, Bearer tokens, passwords)
  - Connection URIs (`postgresql://user:pass@host/db`, `mongodb://...`, `redis://...`)
  - PII (Indian phone numbers, email addresses, 12-digit Aadhaar numbers)
- **`compute_content_hash(data)`**: Computes SHA-256 fingerprint for proprietary payloads (such as Bill of Materials) preserving auditability while suppressing confidential supply-chain formulas.
- **`sanitize_trace_payload(data)`**: Recursively traverses nested dicts, lists, strings, and Pydantic models to redact sensitive information and mask proprietary BOMs with `[PROTECTED_BOM_HASH:<sha256>]`.
- **`PrivacyPreservingCallbackHandler`**: Local callback handler that stores sanitized node runs in memory for testing and audit purposes.
- **`get_langsmith_config(...)`**: Generates the LangChain `RunnableConfig` containing `LangChainTracer` (if enabled) wrapped in failure-isolation try/except blocks. Injects tags (`layer:3`, `compiler:zyntrix`, `runtime:langgraph`) and metadata (`correlation_id`, `node_authority`, `app_name`).

### 3.2 Orchestrator Graph Runner (`backend/app/services/orchestrator/graph/runner.py`)

- Injects `get_langsmith_config(...)` into `compliance_graph.invoke(initial_state, config=config)`.
- If an unhandled exception occurs inside callback dispatch, the runner gracefully falls back to untraced execution to ensure zero business disruption.

### 3.3 Studio Configuration (`langgraph.json` & `start_studio.bat`)

- **`langgraph.json`**: Points to `./backend/app/services/orchestrator/graph/builder.py:compliance_graph_studio`.
- **`compliance_graph_studio`**: Compiled graph with `checkpointer=False` to prevent conflicts with LangGraph Studio API's managed checkpointer.
- **`start_studio.bat`**: Startup script with `PYTHONIOENCODING=utf-8` to guarantee proper rendering of LangGraph CLI Unicode output on Windows cmd/PowerShell.

---

## 4. Redaction Specification

| Category | Regex / Pattern | Replacement Output |
|---|---|---|
| OpenAI / Generic SK | `\bsk-[A-Za-z0-9_-]{20,}\b` | `[REDACTED_API_KEY]` |
| Composio Key | `\bak_[A-Za-z0-9_-]{16,}\b` | `[REDACTED_API_KEY]` |
| Groq Key | `\bgsk_[A-Za-z0-9_-]{20,}\b` | `[REDACTED_API_KEY]` |
| Bearer Token | `Bearer\s+[A-Za-z0-9_\-\.]+` | `Bearer [REDACTED_TOKEN]` |
| Database Password | `(postgresql|postgres|mysql|mongodb)://[^:]+:[^@]+@` | `\1://[REDACTED_USER]:[REDACTED_PASS]@` |
| Email Address | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b` | `[REDACTED_EMAIL]` |
| Indian Phone Number | `(\+91[\-\s]?)?[6-9]\d{9}\b` | `[REDACTED_PHONE]` |
| Aadhaar Number | `\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b` | `[REDACTED_AADHAAR]` |
| Proprietary BOM | Identified by `components` / `materials` keys | `[PROTECTED_BOM_HASH:<sha256>]` |

---

## 5. Verification & Test Suite

The test suite in `backend/tests/test_m24_5_langsmith_observability.py` verifies all M24.5 invariants:

1. `test_tracing_disabled_by_default`: Confirms `is_tracing_enabled()` is false and returns empty callbacks when environment is unset.
2. `test_tracing_enabled_detection`: Validates proper activation under `LANGSMITH_TRACING=true`.
3. `test_real_graph_trace_creation_and_node_metadata`: Validates execution callbacks, run metadata, and node tracking across actual compliance graph invocations.
4. `test_tool_trace_metadata_collection`: Confirms tool execution spans capture arguments and status without credential leakage.
5. `test_correlation_id_propagation`: Verifies correlation IDs route through all run configurations and metadata tags.
6. `test_deterministic_redaction_api_keys_and_secrets`: Validates deterministic removal of OpenAI, Composio, Groq, Bearer, and generic secrets.
7. `test_deterministic_redaction_database_urls`: Validates scrubbing of connection credentials in PostgreSQL and other DB URIs.
8. `test_deterministic_redaction_pii`: Validates masking of emails, phone numbers, and Aadhaar numbers.
9. `test_sanitize_trace_payload_recursive_and_bom_protection`: Validates recursive payload traversal and SHA-256 BOM protection.
10. `test_langsmith_failure_isolation_network_error`: Simulates total LangSmith endpoint outage and validates uninterrupted compliance graph completion.
11. `test_observability_zero_compliance_authority`: Enforces that callback handlers and traces cannot alter graph state, decisions, or Layer 7/9 outputs.
12. `test_one_llm_invariant_preserved`: Verifies no additional LLMs were introduced into the codebase.
13. `test_graph_topology_unchanged`: Verifies the 11 nodes and 16 edges remain strictly unmodified.
14. `test_langstudio_configuration_file`: Verifies `langgraph.json` syntax, paths, and graph export integrity.

---

## 6. How to Run LangGraph Studio

To visualize the graph in LangGraph Studio:
1. Ensure the workspace root has `langgraph.json`.
2. Run `start_studio.bat` or execute in terminal:
   ```powershell
   $env:PYTHONIOENCODING="utf-8"
   langgraph dev --port 2024
   ```
3. Open `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024` in your browser.
