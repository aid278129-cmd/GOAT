# M24.3 — Controlled Agent Tools & Retrieval Integration

**Project**: Zyntrix — BIS Compliance Compiler  
**SIH Problem Statement**: 26107 — AI-powered Intelligent Assistant for Indian Standards and BIS Services for Industries and Consumers  
**Theme**: Smart Automation  
**Milestone**: M24.3  
**Status**: **COMPLETE (HARDENED & AUDITED)**  

---

## 1. Purpose
Milestone M24.3 equips the LangGraph nodes introduced in M24.2 with **controlled, typed, read-only LangChain tools** while strictly prohibiting autonomous tool-calling loops, arbitrary code execution, or any delegation of compliance authority.

Under the cardinal architectural contract established in M24.0:
> **"The agents reason about the task. The deterministic engines reason about compliance."**  
> **"Tools read, look up, and normalize. Only deterministic engines evaluate and certify."**

---

## 2. Cardinal Governance & Invariants

1. **Exactly ONE LLM**:
   - The reasoning graph uses exactly one LLM instance (`single_structured_llm`), accessed exclusively through `langchain_chat_adapter`.
   - No sub-agents, tool-calling agents, or secondary models instantiate separate LLM instances.
2. **0.0% LLM Compliance Authority**:
   - `regulatory_conclusion = "NONE"`
   - `llm_compliance_authority = 0.0`
   - Tool outputs are strictly information artifacts (candidate clauses, verified lab records, normalized units, product facts).
   - Authoritative compliance verdicts remain exclusively with downstream deterministic engines (Layers 5, 7, 8, and 9).
3. **Explicitly Prohibited Tools**:
   The following tool operations are strictly blocked and raise `ToolSecurityError`:
   - `set_compliance_status`
   - `mark_satisfied`
   - `approve_product`
   - `certify_product`
   - `override_applicability`
   - `modify_gap_result`
   - `modify_evidence_trust`
   - `approve_source`
   - `write_passport`
   - `execute_sql`
   - `execute_python`
   - `read_file`
   - `write_file`
   - `fetch_url`

---

## 3. Controlled Tool Registry & Schemas

Located in `backend/app/services/orchestrator/tools/`:

### 3.1 Tool Definitions (`bis_tools.py`)

| Tool Name | Input Schema | Output Schema | Underlying Service / Engine | Authority |
|---|---|---|---|---|
| `search_bis_standards` | `SearchStandardsInput` | `SearchStandardsOutput` | `VERIFIED_STANDARDS_CATALOG` | 0.0% (Read-only catalog) |
| `search_bis_clauses` | `SearchClausesInput` | `SearchClausesOutput` | `VERIFIED_STANDARDS_CATALOG["clauses"]` | 0.0% (Read-only clauses) |
| `get_verified_evidence` | `GetVerifiedEvidenceInput` | `GetVerifiedEvidenceOutput` | Layer 8 Provenance / Trust Engine | 0.0% (Read-only evidence) |
| `normalize_unit` | `NormalizeUnitInput` | `NormalizeUnitOutput` | Layer 7 Deterministic Unit Engine (`units.py`) | 0.0% (Mathematical conversion) |
| `get_product_facts` | `GetProductFactsInput` | `GetProductFactsOutput` | Layer 2 Product DNA Engine | 0.0% (Read-only facts) |

### 3.2 Role-Based Least Privilege (`registry.py`)

Tools can only be executed by nodes possessing explicit role permissions:

```python
ROLE_TOOL_PERMISSIONS: Dict[str, Set[str]] = {
    "query_agent": {"search_bis_standards"},
    "retrieval_agent": {"search_bis_clauses", "search_bis_standards"},
    "analysis_agent": {"get_verified_evidence", "get_product_facts", "normalize_unit"},
    "planning_agent": {"get_verified_evidence", "normalize_unit"},
}
```

Any attempt to call a tool outside the assigned role raises a `ToolSecurityError`.

---

## 4. Security Guards & Boundaries (`guards.py`)

1. **Parameter Sanitization**:
   - Intercepts and rejects SQL injection attempts (`drop table`, `delete from`, etc.).
   - Intercepts directory traversal (`../`, `/etc/`, `c:\windows`).
   - Intercepts arbitrary dynamic execution attempts (`__import__`, `eval`, `exec`, `subprocess`, `os.system`).
2. **Standard Isolation**:
   - `enforce_standard_isolation(target_standard, queried_standard)` prevents cross-standard data leakage (e.g. querying clauses from `IS 302-2-201` while evaluating `IS 17526`).
3. **Execution Limits & Loop Prevention**:
   - `MAX_TOOL_CALLS_PER_RUN = 10` is enforced across the graph. If a graph run exceeds 10 tool calls, execution halts and returns a deterministic fallback.

---

## 5. LangGraph State Integration (`state.py` & `nodes.py`)

The graph state contract is extended with:
- `tool_call_count: int`
- `tool_execution_traces: List[ToolExecutionTrace]`

Each tool execution records:
- `tool_name: str`
- `node_name: str`
- `role: str`
- `input_summary: Dict[str, Any]`
- `status: str` (`"SUCCESS"` or `"ERROR"`)
- `error_message: Optional[str]`
- `duration_ms: float`
- `timestamp: str`

### Safe Degradation
If any tool invocation fails (network, syntax, or security guard violation), the node catches the error, appends it to `state["errors"]`, sets `regulatory_conclusion="NONE"` and `confidence_score=0.0`, and continues along deterministic graph edges.

---

## 6. Verification Results

- **M24.3 Focused Tests**: `backend/tests/test_m24_3_controlled_tools.py` — **20/20 PASSED**
  - Tool schema validation (Pydantic v2 typed inputs/outputs)
  - Catalog retrieval & clause search
  - Evidence gate filtering (suppression of unverified user claims)
  - Unit normalization
  - Role-based least privilege enforcement
  - Prohibited tool rejection
  - SQL injection, directory traversal, code execution rejection
  - Standard isolation violation rejection
  - Tool execution budget enforcement (maximum 10 calls)
  - Observability trace verification
  - Invariant verification (LLM authority = 0.0%, ONE LLM)
- **Full Backend Regression**: `backend/tests` — **472/472 PASSED (0 failures)**
- **Frontend Production Build**: `npm run build` — **SUCCESS (0 errors, 11.83s)**

---

## 7. Handoff to M24.4

With controlled tools, typed schemas, and strict security guards integrated into LangGraph, the project is ready for **M24.4 — Graph Observability, Evaluation & Hardening**.
