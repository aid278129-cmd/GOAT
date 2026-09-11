# M24.6 — Reasoning Pipeline Evaluation & Benchmarking

**Project:** Zyntrix — BIS Compliance Compiler  
**Milestone:** M24.6  
**Status:** IMPLEMENTED & AUDITED  
**Baseline Test Count:** 564 passed  
**New Test Count:** 584 passed (+20 evaluation & benchmarking tests)  
**Evaluation Verdict:** 15 / 15 Dimensions Verified  

---

## 1. Executive Summary & Architectural Invariants

Milestone M24.6 provides a rigorous, reproducible, and mathematically grounded evaluation harness for the Zyntrix Layer 3 LangGraph reasoning pipeline. It audits the reasoning graph across 15 canonical operational dimensions using authentic Bureau of Indian Standards (BIS) ground-truth cases established in Milestone M22 and M23.1.

### Cardinal Invariants Strictly Preserved:
1. **Zero New Models or Agents**: No additional LLMs, sub-models, ML classifiers, or autonomous agents were added. The system remains bounded by `SingleStructuredLLM` and the 11 canonical LangGraph nodes.
2. **Untouched Graph Topology**: The 11-node, 16-edge strict DAG topology validated in M24.4.2 remains completely intact.
3. **0.0% Compliance Authority**: Neither the evaluator, observability tools, nor LLM possess any compliance decision authority. Compliance determination authority resides exclusively in Layer 7, evidence authority in Layer 8, and passport/output integrity in Layer 9.
4. **Authentic Provenance & Golden Locking**: Ground-truth cases from M22 are loaded directly. The `GOLDEN-SIH-2026-DEMO` case is cryptographically and logically locked (`golden_locked: true`).
5. **No Fabricated Metrics**: Small ground-truth sample sizes ($N < 30$) are explicitly classified as **`STATISTICALLY_INSUFFICIENT`** rather than claiming artificial statistical power. Wilson score 95% confidence intervals are computed for all binomial metrics.

---

## 2. Dataset & Sample Size Audit

| Dataset Property | Count / Status | Notes |
|---|---|---|
| Gazette-Verified Standards | 51 Standards | In-memory Layer 3 fast-catalog contains 5 core standards |
| Ground Truth Evaluation Cases | 10 Cases | 4 Positive, 1 Conflict, 1 Insufficient, 4 Negative / OOD |
| SIH Golden Demo Case | `GOLDEN-SIH-2026-DEMO` | IS 17526:2021 Stainless Steel Vacuum Flask (LOCKED) |
| Total Scorable Evaluator Queries | 25 Queries | Deterministic reasoning, short-circuit, and boundary queries |
| Out-of-Scope / Unsupported Cases | 5 Cases | US FDA 510(k), USPTO Patents, Fabricated IS 99999, Vague Products |

---

## 3. The 15 Canonical Evaluation Dimensions

The evaluation harness in `backend/app/services/evaluation/evaluator.py` dynamically tests and measures the 15 dimensions:

```
+---------------------------------------------------------------------------------------------------------+
|                                    15 Canonical Evaluation Dimensions                                   |
+----+------------------------------------+-----+---------+--------+----------------+---------------------+
| #  | Dimension Name                     | N   | Success | Rate   | 95% Wilson CI  | Statistical Status  |
+----+------------------------------------+-----+---------+--------+----------------+---------------------+
| 1  | Request Routing Accuracy           | 3   | 3       | 100.0% | [0.44, 1.00]   | INSUFFICIENT (N<30) |
| 2  | Product DNA Clarification Behavior | 2   | 2       | 100.0% | [0.34, 1.00]   | INSUFFICIENT (N<30) |
| 3  | BIS Standard Retrieval Accuracy    | 3   | 3       | 100.0% | [0.44, 1.00]   | INSUFFICIENT (N<30) |
| 4  | Clause Retrieval Accuracy          | 3   | 3       | 100.0% | [0.44, 1.00]   | INSUFFICIENT (N<30) |
| 5  | Evidence Grounding & Citation Val. | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 6  | Out-of-Domain Refusal Rate         | 3   | 3       | 100.0% | [0.44, 1.00]   | INSUFFICIENT (N<30) |
| 7  | Insufficient Information Handling  | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 8  | Conflict Handling                  | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 9  | Tool Failure & Boundary Handling   | 3   | 3       | 100.0% | [0.44, 1.00]   | INSUFFICIENT (N<30) |
| 10 | Authority Firewall Protection      | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 11 | Unsupported Claim Blocking         | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 12 | Cross-Standard Leakage Prevention  | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 13 | Deterministic Compliance Preserv.  | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 14 | End-to-End Graph Path Correctness  | 1   | 1       | 100.0% | [0.21, 1.00]   | INSUFFICIENT (N<30) |
| 15 | Latency & Execution Metrics        | 15  | 15      | 100.0% | [0.80, 1.00]   | INSUFFICIENT (N<30) |
+----+------------------------------------+-----+---------+--------+----------------+---------------------+
```

### Detailed Breakdown of Dimensions

1. **Request Routing Accuracy**: Evaluates `task_router` dispatch. Standard queries route to `retrieval_agent`; mathematical/unit queries route to `analysis_agent` (short-circuiting retrieval); adversarial jailbreaks route to `controlled_refusal`.
2. **Product DNA Clarification Behavior**: Validates that products lacking mandatory technical attributes (e.g. `product_name` and `category`) halt at `clarification_request` without guessing, while complete DNA continues to standard evaluation.
3. **BIS Standard Retrieval Accuracy**: Tests verified recall of authentic Indian Standards (`IS 17526:2021`, `IS 302-2-201:2008`, `IS 4151:2015`) using controlled tool `search_bis_standards`.
4. **Clause Retrieval Accuracy**: Tests retrieval of specific normative requirement clauses (e.g. Clauses 4.2.1, 5.2, 5.4 in IS 17526) with zero hallucinated clause numbers.
5. **Evidence Grounding & Citation Validity**: Enforces that all citations emitted by the graph reference verified standards with `verified=True` and contain full provenance metadata.
6. **Out-of-Domain Refusal Rate**: Tests queries referencing foreign regulatory frameworks (US FDA 510(k), USPTO patents) or non-existent standards (IS 99999), confirming graceful refusal (`NOT_IN_KNOWLEDGE_BASE`).
7. **Insufficient Information Handling**: Verifies detection of ambiguous or incomplete specifications, prompting for missing attributes deterministically.
8. **Conflict Handling**: Tests contradictory data (e.g., manufacturer spec claiming 68°C vs laboratory test measuring 53°C); validates that the evidence gate prevents automated compliance certification.
9. **Tool Failure & Boundary Handling**: Confirms that controlled tools (`search_bis_standards`, `search_bis_clauses`, `normalize_unit`) gracefully catch invalid limits, schema violations, and corrupt units without crashing the graph runtime.
10. **Authority Firewall Protection**: Enforces that direct prompts commanding the LLM to grant ISI marks or override gates are neutralized, maintaining `llm_compliance_authority = 0.0%`.
11. **Unsupported Claim Blocking**: Ensures user assertions lacking NABL laboratory test evidence are flagged as `UNVERIFIED` and cannot produce a `COMPLIANT` outcome.
12. **Cross-Standard Leakage Prevention**: Confirms standard isolation: querying pressure cooker standard IS 2347 strictly isolates clauses from helmet standard IS 4151.
13. **Deterministic Compliance Result Preservation**: Validates that running through LangGraph preserves the exact bitwise gap classification calculated by Layer 7 without alteration.
14. **End-to-End Graph Path Correctness**: Asserts that full executions strictly traverse the canonical 9-node DAG spine without skipped gates or dead ends.
15. **Latency & Execution Metrics**: Collects duration metrics across all node spans, ensuring sub-2-second response targets are consistently met.

---

## 4. Latency Performance Profile

```
+---------------------------------------------------------------------------------+
| Reasoning Pipeline Latency Statistics (N=15 Graph Invocations)                 |
+----------+----------+---------------+----------+----------+----------+----------+
| Samples  | Mean     | Median (P50)  | P90      | P95      | Min      | Max      |
+----------+----------+---------------+----------+----------+----------+----------+
| 15       | 19.9 ms  | 16.5 ms       | 33.7 ms  | 35.8 ms  | 5.3 ms   | 38.1 ms  |
+----------+----------+---------------+----------+----------+----------+----------+
```
All graph invocations execute well within the real-time threshold (< 2,000 ms), with a median execution latency of **16.5 ms** and a P95 of **35.8 ms**.

---

## 5. Statistical Caveats & Limitations

1. **Sample Size Constraint**: The current ground-truth suite consists of $N=10$ authentic cases and 25 scorable queries. While 100% of tested dimensions pass, small sample sizes mean Wilson confidence intervals are appropriately wide (e.g. $[0.44, 1.00]$ for $N=3$).
2. **Honest Labeling**: Per project principles, every dimension with $N < 30$ is cardinally marked `STATISTICALLY_INSUFFICIENT` to prevent mistaking test suite verification for production population accuracy.
3. **Reproducibility Guarantee**: All test queries and ground-truth records are locked under version `v1.2.0-gazette-verified` and do not rely on live external LLM API calls or fluctuating network latency.

---

## 6. How to Run the Evaluation CLI

To run the complete benchmark and export report artifacts:

```powershell
py -3.14 -m backend.app.services.evaluation.evaluator
```

### Generated Artifacts
- Machine-readable summary: `data/evaluation/results/m24_6/summary.json`
- Benchmark manifest: `data/evaluation/results/m24_6/manifest.json`
