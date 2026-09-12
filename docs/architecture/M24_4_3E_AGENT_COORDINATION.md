# M24.4.3E — Controlled Agent Coordination & Runtime Optimization

## 1. Executive Overview & Cardinal Principles

Milestone **M24.4.3E** upgrades the coordination layer between the four specialized agents of the Zyntrix BIS Compliance Reasoning Architecture:
1. **Query Agent** (Intent classification, query sanitization, task decomposition, ambiguity detection)
2. **Retrieval Agent** (Standard matching, clause retrieval, query expansion, cross-standard isolation)
3. **Analysis Agent** (Requirement-to-evidence matching, contradiction detection, technical comparison)
4. **Planning Agent** (Remediation action planning, blocker identification, dependency ordering)

> [!IMPORTANT]
> **Cardinal Coordination Invariants**:
> - **ONE LLM SINGLETON**: Exactly ONE LLM singleton (`SingleStructuredLLM` via `LangChainChatAdapter`) is shared across all four agents. No secondary LLM or autonomous subagent runtime exists.
> - **ZERO COMPLIANCE AUTHORITY**: All four agents have strictly **`0.0%`** compliance authority. Authority level is **`AI_DERIVED / CANDIDATE`**. Regulatory conclusion is **`NONE`**.
> - **DETERMINISTIC GRAPH CONTROLLER**: LangGraph is the single authoritative controller (11 nodes, 16 edges, strict DAG). Agents reason; the graph controls; deterministic engines decide compliance.
> - **PRESERVATION OF FOUNDATIONAL TRUTHS**:
>   - `USER_TEXT != EVIDENCE != COMPLIANCE`
>   - `NO VERIFIED SOURCE -> NO REGULATORY CLAIM`
>   - `NO VERIFIED EVIDENCE -> NO SATISFIED`
>   - `NO SUFFICIENT INFORMATION -> ASK / UNKNOWN`
>   - `CONFLICT -> EXPERT REVIEW`
>   - `RECOMMENDATIONS != COMPLIANCE EVALUATION`

```
                                  ONE LLM SINGLETON
                         (SingleStructuredLLM / LangChain Adapter)
                                     │
         ┌───────────────────┬───────┴───────────┬───────────────────┐
         ▼                   ▼                   ▼                   ▼
    Query Agent       Retrieval Agent     Analysis Agent      Planning Agent
 (Understand/Decomp)  (Fetch Clauses)    (Compare/Evaluate)  (Remediate Actions)
         │                   │                   │                   │
         └───────────────────┴───────┬───────────┴───────────────────┘
                                     ▼
                      LANGGRAPH DETERMINISTIC CONTROLLER
                  (11 Nodes, 16 Edges, Strict DAG, Zero Loops)
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
   DOWNSTREAM AUTHORITIES                               COORDINATION ENGINES
   - Layer 5: Applicability Matrix                      - SnapshotManager (SHA-256)
   - Layer 7: Compliance Gap Engine                     - HandoffValidator (Typed Contracts)
   - Layer 8: Evidence Verification Gate                - AgentReadinessGate (Prerequisites)
   - Layer 9: Output Integrity Gate                     - BudgetEnforcer (Hard Bounds)
```

---

## 2. Architectural Invariants

| Invariant | Specification | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Single LLM Singleton** | Exactly ONE LLM (`SingleStructuredLLM` via `LangChainChatAdapter`). | Instantiated singleton; all agents delegate to this single interface. |
| **Zero Compliance Authority** | Authority Level: `AI_DERIVED / CANDIDATE`. Regulatory conclusion: `NONE`. Authority: `0.0%`. | `ComplianceAuthorityFirewall` + `HandoffValidator` reject any non-NONE conclusion. |
| **LangGraph Controller** | 11 Canonical nodes, 16 directed edges, DAG. No autonomous agent loops. | LangGraph runtime controls all transitions; agents cannot invoke each other directly. |
| **Deterministic Authorities** | Downstream layers (5, 7, 8, 9) retain exclusive compliance authority. | Layer 7 gap engine computes SATISFIED / UNSATISFIED; firewall audits decisions. |
| **State Immutability** | Deterministic fields cannot be altered or falsified by agent reasoning. | Node wrapper snapshots and restores `applicability_decision`, `gap_analysis_summary`, etc. |
| **Cryptographic Snapshots** | SHA-256 fingerprints recorded at each agent entry point. | `SnapshotManager` captures snapshots into `state["state_snapshots"]`. |
| **Typed Handoff Contracts** | Explicit data validation before downstream consumption. | `HandoffValidator` checks schema, preconditions, and flags blocks. |
| **Execution Budgets** | Hard bounds on LLM (max 3), tools (max 10), and retrievals (max 3). | `BudgetEnforcer` halts runaway processes and triggers deterministic fallbacks. |
| **Failure Isolation** | Upstream failure causes controlled uncertainty, not hallucinations. | `AgentReadinessGate` flags blocked state; Layer 7 marks `CANNOT_EVALUATE`. |

---

## 3. Coordination Architecture & Pipeline Stages

The reasoning pipeline enforces explicit handoff validation and state snapshotting at every inter-agent transition:

```
[START]
   │
   ▼
[1. Request Understanding] (Query Agent)
   │ (Snapshot captured: SNAP-REQU-...)
   │ [Handoff: QUERY_TO_RETRIEVAL validated]
   ▼
[2. Product DNA Check]
   │
   ▼
[3. Task Router]
   │
   ▼
[4. Retrieval Agent] (Retrieval Agent)
   │ (Readiness Gate checked)
   │ (Snapshot captured: SNAP-RETR-...)
   │ [Handoff: RETRIEVAL_TO_ANALYSIS validated]
   ▼
[5. Evidence Validation Gate] (Layer 8)
   │
   ▼
[6. Analysis Agent] (Analysis Agent)
   │ (Readiness Gate checked)
   │ (Snapshot captured: SNAP-ANAL-...)
   │ (Budget checked: LLM calls <= 3)
   │ [Handoff: ANALYSIS_TO_LAYER7 validated]
   ▼
[7. Deterministic Compliance Gate] (Layer 7 Authoritative Gap Engine)
   │ (Deterministic evaluation: SATISFIED / UNSATISFIED)
   ▼
[8. Planning Agent] (Planning Agent)
   │ (Readiness Gate checked)
   │ (Snapshot captured: SNAP-PLAN-...)
   │ [Handoff: PLANNING_TO_OUTPUT validated]
   ▼
[9. Output Integrity Gate] (Layer 9 Grounding Guard & Firewall)
   │
   ▼
[END]
```

---

## 4. Explicit Data Contracts & Handoff Stages

Inter-agent handoffs are governed by `AgentHandoffContract` via `HandoffValidator`:

| Handoff Stage | Producer Agent | Consumer Agent | Validation Rules & Preconditions | Failure Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `QUERY_TO_RETRIEVAL` | `QUERY` | `RETRIEVAL` | - Query understanding present.<br>- Target standard number identified or query sanitized.<br>- Query NOT out-of-domain. | Blocked: Router routes to `controlled_refusal`. |
| `RETRIEVAL_TO_ANALYSIS` | `RETRIEVAL` | `ANALYSIS` | - Retrieval package and clauses present.<br>- Zero cross-standard violations.<br>- Retrieval status != `FAILED`. | Blocked: Analysis handles uncertainty; Layer 7 flags `CANNOT_EVALUATE`. |
| `ANALYSIS_TO_LAYER7` | `ANALYSIS` | `LAYER7` | - Structured analysis present.<br>- No authoritative `SATISFIED` candidate.<br>- `regulatory_conclusion == "NONE"`.<br>- `llm_compliance_authority == 0.0`. | Blocked: Authority firewall strips untrusted claims. |
| `LAYER7_TO_PLANNING` | `LAYER7` | `PLANNING` | - Layer 7 gap summary present.<br>- Unsatisfied clauses attached. | Blocked: Planning defaults to safe fallback. |
| `PLANNING_TO_OUTPUT` | `PLANNING` | `OUTPUT` | - Structured action plan present.<br>- No actions marked `SATISFIED` or `COMPLETED`.<br>- `regulatory_conclusion == "NONE"`.<br>- `llm_compliance_authority == 0.0`. | Blocked: Output gate strips illegal action claims. |

---

## 5. Cryptographic State Snapshots & Auditing

`SnapshotManager` creates immutable cryptographic checkpoints of agent inputs:

```python
snap = SnapshotManager.capture_snapshot("analysis_agent", {
    "target_standard_number": "IS 302-2-201:2008",
    "clauses_count": 3,
    "evidence_records_count": 1,
})
# StateSnapshot(snapshot_id="SNAP-ANAL-6A8F12", state_hash="6a8f12...", ...)
```

- Every snapshot generates a deterministic SHA-256 fingerprint of the serialized state subset.
- Snapshots are recorded in `state["state_snapshots"]` for complete auditability.
- Downstream tampering or silent state corruption is immediately detectable by comparing fingerprints.

---

## 6. Execution Budget & Resource Governance

To prevent runaway loops, infinite retries, and unbounded LLM costs:

| Resource Metric | Hard Cap | Enforcement Component | Exceeded Action |
| :--- | :--- | :--- | :--- |
| **Max LLM Calls** | 3 per execution | `BudgetEnforcer.check_and_increment_llm` | Short-circuit to deterministic Layer 7 summary; `state["budget_exceeded"] = True`. |
| **Max Tool Calls** | 10 per execution | `BudgetEnforcer.check_and_increment_tool` | Reject tool invocation; raise `ToolSecurityError`. |
| **Max Retrieval Calls** | 3 per execution | `ExecutionBudget.max_retrieval_calls` | Abort additional queries; fallback to catalog cache. |
| **Tool Deduplication** | Unlimited cache | `_execute_controlled_tool` Cache | Return cached result; increment `duplicate_work_prevented`. |

---

## 7. Failure Isolation & Uncertainty Propagation

Agent failures are strictly isolated to prevent cascading hallucinations:

```
RETRIEVAL AGENT ERROR / TIMEOUT
              │
              ▼
   Retrieval Status = FAILED
   Errors attached to state
              │
              ▼
    Readiness Gate Check
              │
    ┌─────────┴────────────────────────┐
    ▼                                  ▼
Analysis Agent                  Layer 7 Deterministic Gate
(Recognizes missing evidence;   (Cannot evaluate; emits
 emits uncertain candidate;     REQUIRES_EXPERT_REVIEW;
 no hallucinated clauses)       zero compliance claims)
```

1. **Failure Containment**: A failure in the Retrieval Agent does NOT cause the Analysis Agent to fabricate standards or clauses.
2. **Deterministic Fallback**: If LLM budget is exceeded, the pipeline falls back to precomputed deterministic gap summaries.
3. **Audit Trail**: Every error is recorded in `state["errors"]` and `AgentExecutionTrace.errors`.

---

## 8. Verification & Benchmarking Standards

All coordination benchmarks adhere to the strict statistical sufficiency rule:
- **Sample Size Rule**: Any benchmark where sample count $N < 30$ must explicitly report `STATISTICALLY_INSUFFICIENT`.
- **Wilson Score Intervals**: Confidence intervals must be computed with continuity correction when applicable.
- **Latency Tracking**: End-to-end graph latency, individual agent node durations, and cache hit acceleration are systematically benchmarked.
