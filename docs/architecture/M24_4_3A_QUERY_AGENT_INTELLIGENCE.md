# Milestone M24.4.3A: Advanced Query Agent Intelligence Upgrade

## Core Cardinal Mandate
> **"The Query Agent understands the request. It does not decide compliance."**

---

## 1. Architectural Invariants Strictly Enforced

1. **ONE LLM ONLY**: All language intelligence delegates strictly to the single LLM singleton (`SingleStructuredLLM` / `ZyntrixLangChainChatAdapter`). No secondary or competing LLM is introduced.
2. **ZERO COMPLIANCE AUTHORITY (0.0%)**:
   - Query Agent compliance authority is exactly 0.0%.
   - Authority level is strictly `AI_DERIVED`.
   - The Query Agent must never determine whether a product is compliant, never mark a requirement `SATISFIED`, and never invent BIS standards, clauses, or thresholds.
3. **AUTHORITY FIREWALL PRESERVATION**:
   - Layer 5 remains the sole applicability authority.
   - Layer 7 remains the sole compliance evaluation authority.
   - Layer 8 remains the sole evidence and source trust authority.
   - Layer 9 remains the sole output and passport integrity authority.
4. **CARDINAL TRUTHS PRESERVED**:
   - `USER_TEXT != EVIDENCE != COMPLIANCE`
   - `NO VERIFIED SOURCE -> NO REGULATORY CLAIM`
   - `NO VERIFIED EVIDENCE -> NO SATISFIED`
   - `NO SUFFICIENT INFORMATION -> ASK / UNKNOWN`
   - `CONFLICT -> EXPERT REVIEW`
5. **DETERMINISTIC TOPOLOGY PRESERVATION**:
   - The compiled LangGraph retains all 11 canonical worker nodes and 16 directed edges.
   - No autonomous loops, no dynamic routing by the LLM.

---

## 2. Request Flow Architecture

```
USER REQUEST
      ↓
DETERMINISTIC QUERY PREPROCESSING (Regex, Unicode/Whitespace, Injection, OOD)
      ↓
QUERY AGENT (Sanitization, Classification, Decomposition, Hints, Ambiguity)
      ↓
STRUCTURED QUERY UNDERSTANDING (QueryUnderstanding Pydantic v2 Contract)
      ↓
LANGGRAPH DETERMINISTIC ROUTING (route_after_request_understanding)
      ↓
RETRIEVAL / ANALYSIS / PLANNING (Downstream Controlled Execution)
```

---

## 3. Existing Query Agent vs. Upgraded M24.4.3A Architecture

| Capability | Previous Implementation | Upgraded M24.4.3A Implementation |
| :--- | :--- | :--- |
| **Role & Scope** | Basic substring matching in `intent_router.py` | Full Query Agent with deterministic preprocessing + structured decomposition + ambiguity detection |
| **Task Decomposition** | None (monolithic intent string) | Bounded subtask plan (max 8 steps, anti-recursive, typed `SubtaskPlanItem`) |
| **Ambiguity Detection** | Basic product DNA check only at Node 2 | Request-level ambiguity detection for underspecified requests before model execution |
| **Standard & Clause Extraction** | Ad-hoc regex in caller code | Exact standard regex (preserving year, part, subpart) and clause numbering |
| **Adversarial Security** | 9 static prompt guard patterns | Extended injection scanner detecting source bypass, forced pass, gate skip, and impersonation |
| **Out-of-Domain Detection** | None at request understanding stage | Fast-path deterministic OOD detection routing to polite, zero-authority controlled refusal |
| **Retrieval Hints** | None | Typed `RetrievalHintItem` generated for the Retrieval Agent (authority: `AI_DERIVED`) |
| **Data Contract** | `RequestUnderstandingContract` (5 fields) | Extended `RequestUnderstandingContract` (15 fields) + `QueryUnderstanding` schema |

---

## 4. `QueryUnderstanding` Pydantic v2 Schema

The Query Agent returns a strongly typed, immutable output validated by Pydantic v2:

```python
class QueryUnderstanding(BaseModel):
    original_query: str
    normalized_query: str
    request_type: RequestType                     # Enum: INFORMATION_REQUEST, COMPLIANCE_ASSESSMENT, etc.
    intent: OrchestratorIntent                   # Enum: QUERY_REQUIREMENT, EXPLAIN_GAP, etc.
    complexity: QueryComplexity                  # Enum: SIMPLE, MODERATE, COMPLEX
    extracted_entities: List[ExtractedEntity]     # Typed with EntityProvenance (USER_PROVIDED / AI_DERIVED)
    explicit_standard_refs: List[str]            # Preserved exact IS strings (e.g. "IS 17526:2021")
    explicit_clause_refs: List[str]              # Preserved clause numbers (e.g. "22.101")
    detected_document_types: List[str]           # e.g. "NABL_ACCREDITED_REPORT", "TEST_CERTIFICATE"
    task_list: List[SubtaskPlanItem]             # Max 8 subtasks, anti-recursive, authority='AI_DERIVED'
    retrieval_hints: List[RetrievalHintItem]     # Guidance hints for Retrieval Agent
    missing_information: List[str]               # Specific missing technical attributes
    clarification_required: bool                 # Request-level ambiguity flag
    security_flags: List[str]                    # Security patterns detected
    is_safe: bool                                # Safety verdict
    out_of_domain: bool                          # Domain classification
    preprocessing_latency_ms: float              # Latency of deterministic scanner
    llm_invoked: bool                            # Tracking LLM usage
    confidence: float                            # STRICTLY query understanding confidence (0.0 to 1.0)
    authority: AuthorityLevel = AuthorityLevel.AI_DERIVED # Invariant: Never VERIFIED or AUTHORITATIVE
    regulatory_conclusion: str = "NONE"          # Invariant: Always "NONE"
    llm_compliance_authority: float = 0.0        # Invariant: Always 0.0
```

---

## 5. Deterministic Preprocessing Operations

To maximize performance, reduce costs, and guarantee safety, deterministic preprocessing executes before invoking the model:

1. **Whitespace & Control Normalization**: Strips non-printable ASCII and unifies spacing while preserving the original query in `original_query`.
2. **Standard Number Detection**: Extracts `IS \d{3,6}(?:-\d+(?:-\d+)?)?(?::\d{4})?` preserving part numbers and gazette years.
3. **Clause Extraction**: Extracts clause and subclause numbers `(?:clause|section|cl\.?)\s*(\d+(?:\.\d+)*)`.
4. **Document Type Detection**: Identifies references to NABL reports, lab test reports, test certificates, factory audits, datasheets, QCOs, and declarations.
5. **Adversarial & Injection Detection**: Detects instruction overrides, forced compliance commands, source verification bypass attempts, and authority impersonation.
6. **Out-of-Domain Classification**: Flags non-regulatory queries (games, sports, cooking, weather, general software development).
7. **Ambiguity Heuristics**: Evaluates whether essential parameters (product identity, standard, rating, material) are missing for broad queries (e.g., *"Is my flask compliant?"*).
8. **Complexity Categorization**: Classifies requests into `SIMPLE` (single lookup), `MODERATE` (product + standard), or `COMPLEX` (multi-step compliance + gap + documentation).

---

## 6. Authority & Security Controls

- **Enforced Non-Authority**: Pydantic field validators forcefully override any attempted pseudo-compliance claims (`regulatory_conclusion` is hard-pinned to `"NONE"`, `llm_compliance_authority` is hard-pinned to `0.0`, and `authority` is restricted to `AI_DERIVED`).
- **Prompt Injection Defense**: Adversarial attempts immediately set `security_flag = True`, leading deterministically to `controlled_refusal_node` which returns a 0% authority response.
- **Controlled Refusal for Out-of-Domain**: Out-of-domain requests are routed to `controlled_refusal_node` which provides a polite domain-boundary refusal without calling retrieval or evaluation engines.
- **Least-Privilege Tool Access**: The Query Agent is permitted access only to `search_bis_standards` in `ROLE_TOOL_PERMISSIONS["query_agent"]`, with 0 tool calls executed during default request understanding.

---

## 7. LangGraph Integration & Node Contracts

The Query Agent is seamlessly integrated into `request_understanding_node` in `backend/app/services/orchestrator/graph/nodes.py`:
- Populates `state["query_understanding"]`, `state["sanitized_query"]`, `state["user_intent"]`, `state["security_flag"]`, `state["security_reason"]`, `state["security_warnings"]`, `state["out_of_domain"]`, `state["request_type"]`, `state["query_complexity"]`, `state["decomposed_tasks"]`, and `state["retrieval_hints"]`.
- Extends `RequestUnderstandingContract` while remaining 100% backward compatible with existing contract validators and downstream consumers.
- Topologically invariant: 11 canonical worker nodes and 16 directed edges remain identical.

---

## 8. Benchmark Methodology & Results

Evaluation across 10 canonical scenarios:
1. `BENCH_1_SIMPLE` (Standard definition lookup)
2. `BENCH_2_MODERATE` (Clause requirement inquiry)
3. `BENCH_3_COMPLEX` (Multi-step vacuum flask assessment + missing documents)
4. `BENCH_4_EXPLICIT_IS` (Thermal retention limits under IS 17526:2021)
5. `BENCH_5_EXPLICIT_CLAUSE` (Test specifications for clause 19.102)
6. `BENCH_6_AMBIGUOUS` (Underspecified bottle inquiry)
7. `BENCH_7_OUT_OF_DOMAIN` (Python dice roll simulation)
8. `BENCH_8_PROMPT_INJECTION` (Direct compliance override attempt)
9. `BENCH_9_OVERSIZED` (Extremely long repeated query)
10. `BENCH_10_MALFORMED` (Random punctuation and symbols)

**Results**:
- Average deterministic preprocessing latency: **< 1.0 ms**
- LLM invocation count for deterministic fast-paths: **0**
- Task capping compliance: **100% (≤ 8 subtasks)**
- Out-of-domain and prompt injection catch rate: **100%**
- Compliance authority across all outputs: **0.0%**

*Note on Sample Size*: Because benchmark suite $N = 10 < 30$, these benchmarks are statistically classified as illustrative fixture benchmarks rather than high-$N$ production sample sets.

---

## 9. Known Limitations

1. **OCR Artifact Tolerance**: Highly distorted OCR texts containing fragmented standard numbers (e.g. `I S  1 7 5 2 6`) require upstream OCR cleaning in Layer 1 before standard regex extraction.
2. **Ambiguous Product Names**: Products with overlapping colloquial terminology (e.g., "thermos" vs "vacuum flask") rely on keyword synonym maps; unmapped regional terms will trigger ambiguity detection and request clarification.
3. **Bounded Tool Execution**: In accordance with least-privilege security, the Query Agent does not execute retrieval or search clauses directly; clause retrieval remains the strict responsibility of Node 4 (`retrieval_agent`).
