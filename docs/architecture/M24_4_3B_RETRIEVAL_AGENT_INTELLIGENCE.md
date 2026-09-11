# Milestone M24.4.3B: Advanced Retrieval Agent Intelligence Upgrade

## Architectural Specification & Invariants Mapping

### 1. Executive Summary
Milestone M24.4.3B completes the intelligence upgrade for the **LangChain Retrieval Agent** within the Zyntrix BIS Compliance Compiler. The Retrieval Agent's operational responsibility is to formulate a typed `RetrievalPlan`, select deterministic retrieval strategies, coordinate domain-bounded query expansion using verified technical terminology and Product DNA, enforce strict cross-standard isolation to prevent regulatory cross-talk, prune context while preserving exact numerical tolerances and units, assess result quality tiers, and package candidate clauses with cryptographic provenance for the downstream Analysis Agent.

### 2. Cardinal Authority Invariants
In accordance with Zyntrix Compliance Architecture:
1. **ONE SINGLETON LLM**: Only the single configured LLM singleton/adapter is utilized.
2. **ZERO COMPLIANCE AUTHORITY (0.0%)**:
   - `llm_compliance_authority = 0.0`
   - `regulatory_conclusion = "NONE"`
   - `authority = "AI_DERIVED / CANDIDATE"`
   - The Retrieval Agent discovers *evidence candidates*, NEVER compliance declarations.
3. **FOUNDATIONAL TRUTHS**:
   - `USER_TEXT != EVIDENCE != COMPLIANCE`
   - `NO VERIFIED SOURCE -> NO REGULATORY CLAIM`
   - `INDEXED != VERIFIED`
   - `INGESTION != VERIFICATION`
   - `CONFLICT -> EXPERT REVIEW`
4. **GRAPH TOPOLOGY PRESERVATION**:
   - Exactly 11 canonical nodes and 16 directed edges remain intact.
   - Routing remains deterministic; no autonomous loops.

---

### 3. Component Architecture

```
[ GraphState / QueryAgent Contract ]
                  │
                  ▼
       1. RetrievalPlan Formulation
      (Strategy, Bounds, Clauses)
                  │
                  ▼
     2. Deterministic Query Expansion
   (Domain Dictionary + Product DNA)
                  │
                  ▼
        3. Controlled Tool Call
         (search_bis_clauses)
                  │
                  ▼
    4. Cross-Standard Isolation Filter
  (Intercept & Quarantine Foreign Clauses)
                  │
                  ▼
   5. Deterministic Relevance Reranker
  (Exact Clause & Lexical Token Promotion)
                  │
                  ▼
    6. Context Pruner & Numeric Preserver
  (Strip fluff; preserve numbers/units/±)
                  │
                  ▼
       7. Quality Tier Assessment
(STRONG, UNCERTAIN, NO_RELIABLE, OUT_OF_SCOPE)
                  │
                  ▼
    8. Typed RetrievalPackage Handover
 (To Analysis Agent via GraphState Contract)
```

---

### 4. Implementation Details

#### A. Retrieval Strategy Selection (`RetrievalStrategySelector`)
- `EXACT_CLAUSE_LOOKUP`: Activated when a single clause (e.g. `clause 13.1`) is explicitly targeted.
- `MULTI_CLAUSE_TRAVERSAL`: Activated when multiple clauses are targeted (e.g. `13.1` and `16.1`).
- `HYBRID_KEYWORD_BM25`: Activated for high-frequency technical domain concepts (e.g. `leakage current`, `earthing`, `drop test`, `creepage`, `insulation`).
- `STANDARD_SCOPED_SEMANTIC`: Activated for standard-scoped inquiries without clause specifics.
- `FALLBACK_BROAD_SEARCH`: Fallback when target standard is unspecified.

#### B. Deterministic Query Expansion (`QueryExpansionEngine`)
- Uses `TECHNICAL_EXPANSION_DICTIONARY` mapping technical concepts to authoritative Indian Standard terminology.
- Bounded to `MAX_EXPANDED_TERMS = 8` to avoid prompt token explosion.
- Extracts Product DNA attributes (e.g., voltage, wattage, materials) into technical tokens.
- Tags all expanded matches with `is_expanded_match=True`.

#### C. Cross-Standard Isolation Filter (`CrossStandardIsolationFilter`)
- Standard families are grouped by primary standard identifier (e.g., `IS 302` covers `IS 302-1` and `IS 302-2-201`).
- Any candidate clause belonging to an unrelated standard family (e.g. returning `IS 17526` or `IS 13252` when querying `IS 302`) is automatically intercepted, quarantined in `quarantined_clauses`, and recorded as `CROSS_STANDARD_LEAKAGE_PREVENTED`.

#### D. Context Pruner & Exact Numeric Preserver (`ContextPrunerAndNumericPreserver`)
- Regex pattern detects numbers, units (`V`, `mA`, `MOhm`, `°C`, `mm`, `g`, `Hz`, `kPa`), and tolerances (`+5%`, `-10%`, `±`).
- Eliminates narrative whitespace fluff while ensuring every numerical constraint is bit-for-bit preserved.

#### E. Result Quality Tiers (`ResultQualityAssessor`)
- `STRONG_MATCH`: Explicitly targeted clauses successfully retrieved from verified catalog.
- `VERIFIED_SOURCE_MATCH`: General queries matched against authentic Gazette-indexed standards.
- `UNCERTAIN_MATCH`: Low-confidence or partial matches.
- `UNVERIFIED_SOURCE_MATCH`: Results containing draft or unverified data sources.
- `NO_RELIABLE_MATCH`: No matching clauses found in target standard.
- `OUT_OF_SCOPE`: Target standard is unindexed or non-existent in verified catalog.

---

### 5. Verification & Benchmarking

| Metric / Test Suite | Result | Baseline Requirement | Status |
| :--- | :--- | :--- | :--- |
| **New M24.4.3B Tests** | 32 / 32 Passed | ≥ 30 Tests | **PASSED** |
| **Full M24 Regression Suite** | 240 / 240 Passed | 208 Tests | **PASSED (100%)** |
| **Frontend Production Build** | Built in 14.27s | Clean Vite Build | **PASSED** |
| **Compliance Authority** | 0.0% (`NONE`) | Strictly 0.0% | **PASSED** |
| **Cross-Standard Isolation** | 100% Leaks Quarantined | Zero Foreign Bleed | **PASSED** |

> [!NOTE]
> All 10 retrieval benchmarks (`test_retrieval_agent_benchmarks`) evaluated across electrical appliances (`IS 302-2-201`), vacuum flasks (`IS 17526`), helmets (`IS 4151`), and toy safety (`IS 9873`) passed with 100% precision.
