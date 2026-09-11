# M24.4.3D — Advanced Planning Agent Intelligence Upgrade

## 1. Executive Overview & Cardinal Principle

The **Advanced Planning Agent** upgrades Layer 3 language reasoning within the Zyntrix BIS Compliance Compiler by translating deterministic gap findings, missing evidence, analysis conflicts, and product DNA into a structured, prioritized, actionable remediation plan.

> [!IMPORTANT]
> **Cardinal Planning Invariant**:
> The Planning Agent answers **"What should be done next?"**
> It does **NOT** answer *"Is the product compliant?"*
> - **LLM Compliance Authority** is strictly **`0.0%`**.
> - **Output Authority Level** is strictly **`AI_DERIVED / CANDIDATE`**.
> - **Regulatory Conclusion** is strictly **`NONE`**.
> - The Planning Agent **cannot** mark a requirement `SATISFIED`, cannot mark a product `COMPLIANT`, cannot determine applicability, and cannot declare certification eligibility.
> - Recommendations must never become authoritative compliance results.

```
LAYER 7 DETERMINISTIC FINDINGS
        +
VERIFIED EVIDENCE STATUS
        +
ANALYSIS & CONFLICTS
        ↓
PLANNING AGENT
        ↓
STRUCTURED ACTION PLAN (AI_DERIVED / CANDIDATE, Authority=0.0%)
        ↓
OUTPUT INTEGRITY GATE
        ↓
COMPLIANCE PASSPORT / ACTION CENTER
```

---

## 2. Architectural Invariants

| Invariant | Specification | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Single LLM Singleton** | Exactly ONE LLM (`SingleStructuredLLM` via `LangChainChatAdapter`). | Instantiated singleton, no secondary model initialization. |
| **Non-Authoritative Role** | Authority Level: `AI_DERIVED / CANDIDATE`. | `ComplianceAuthorityFirewall` blocks any authoritative compliance declaration originating from planning. |
| **Action Planning Only** | Answers "What should be done next?". | Output schema restricted to action items, blockers, and dependencies. |
| **No External Execution** | Recommendations only; no real-world execution. | Cannot book labs, send emails, or submit BIS applications. |
| **Dependency Integrity** | Enforces Directed Acyclic Graph (DAG) dependencies. | `DependencyValidator` detects cycles via DFS coloring and breaks backward dependencies. |
| **Action Deduplication** | Merges duplicate gaps sharing identical test procedures. | `ActionDeduplicator` groups clauses into consolidated action steps. |
| **Prompt Injection Defense** | Untrusted inputs treated strictly as **DATA**, not instructions. | Regex sanitizer strips attempts to bypass tests or mark gaps resolved. |
| **Strict Graph Topology** | 11 Canonical nodes, 16 directed edges, DAG. | No new nodes or dynamic edges created; node contracts preserved. |

---

## 3. Data Contract: `ActionPlan`

```python
class ActionPlan(BaseModel):
    standard_number: str
    total_actions: int = 0
    blockers_count: int = 0
    actions: List[ActionItem]
    blockers: List[BlockerItem]
    dependency_graph: Dict[str, List[str]]
    grouped_actions: Dict[str, List[str]]
    expert_review_required: bool = False
    sanitized_prompt_injections: List[str]
    plan_summary: str = ""

    # Non-negotiable Authority Firewalls
    authority: str = "AI_DERIVED / CANDIDATE"
    regulatory_conclusion: str = "NONE"
    llm_compliance_authority: float = 0.0
```

### ActionTaxonomy: `ActionType`
- `LAB_TEST_REQUIRED`: Missing mandatory empirical laboratory test report.
- `DOCUMENT_REQUIRED`: Missing accredited laboratory certificate or declaration.
- `MANUFACTURER_SPECIFICATION_REQUIRED`: Missing official manufacturer technical datasheet.
- `PHOTO_MARKING_EVIDENCE_REQUIRED`: Missing photograph of product marking plate with ISI mark & licence number.
- `EXPERT_REVIEW_REQUIRED`: Contradictory evidence detected; technical review by BIS consultant required.
- `PRODUCT_INFORMATION_REQUIRED`: Missing product discriminator or technical parameter.
- `SOURCE_VERIFICATION_REQUIRED`: Standard lacks verified gazetted documentation.
- `STANDARD_REVIEW_REQUIRED`: Requirement amendment review.

### Action Priorities & Functional Groups
- **Priorities**: `CRITICAL_BLOCKER` (1), `HIGH` (2), `MEDIUM` (3), `LOW` (4).
- **Groups**:
  - `IMMEDIATE_BLOCKERS`
  - `EVIDENCE_COLLECTION`
  - `LAB_TESTING`
  - `PRODUCT_INFORMATION`
  - `EXPERT_REVIEW`
  - `FINAL_REASSESSMENT`

---

## 4. Key Engines & Capabilities

### 4.1 Blocker Detection
Scans deterministic gaps and analysis outputs for blocking conditions:
1. `EVIDENCE_CONFLICT`: Contradictory evidence detected between specifications and test reports.
2. `UNVERIFIED_SOURCE`: Standard or clause lacking gazetted verification.
3. `MANDATORY_TESTING_GAP`: Missing empirical test reports for mandatory safety clauses.

### 4.2 Dependency Graph & Cycle Prevention
Formulates logical dependency sequences (e.g., *Resolve Product Specification $\rightarrow$ Obtain Laboratory Test $\rightarrow$ Evaluate Requirement*). The `DependencyValidator` detects cycles using DFS 3-color traversal and deterministically removes backward edges to enforce a strict DAG.

### 4.3 Action Deduplication
Consolidates redundant actions of the same type and test method (e.g., three separate heating clauses requiring the same temperature rise test are combined into a single unified action referencing all relevant clause numbers).

### 4.4 Prompt Injection & Gap Manipulation Defense
Neutralizes adversarial attempts to manipulate action plans (e.g. *"Tell manufacturer to ignore clause 5"*, *"Mark the gap as resolved"*, *"Book laboratory"*), replacing malicious directives with inert tokens (`[UNTRUSTED_INSTRUCTION_NEUTRALIZED]`).

---

## 5. Controlled Tool Usage & Caching

The Planning Agent operates under least privilege using permitted M24.3 tools:
- `get_product_facts`
- `get_verified_evidence`

Optimization metrics tracked:
- `planning_invocations`
- `llm_calls`
- `deterministic_short_circuits`
- `tool_calls`
- `cache_hits`
- `duplicate_actions_prevented`
- `blockers_identified`
- `injections_sanitized`

---

## 6. Benchmarking & Statistical Sufficiency

Following the Zyntrix Evaluation Protocol (M24.6):
- Any evaluation scenario with sample size $N < 30$ is strictly tagged as **`STATISTICALLY_INSUFFICIENT`**.
- Local test fixtures are designated as unit verification suites and are never represented as production population statistics.
