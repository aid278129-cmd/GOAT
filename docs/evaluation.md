# Evaluation, Benchmark Rigor & Accuracy Staging

**Milestone**: M1.5 (Knowledge Trust & Governance Hardening)  
**Author**: Team Zyntrix (SIH Problem Statement 26107)

---

## 1. Context & Evaluator Directives

In response to SIH evaluator feedback (*"validating the claimed accuracy, reducing dependence on LLM reasoning, and demonstrating the system with real BIS compliance cases"*), accuracy validation is maintained with strict scientific honesty.

### Policy on Claims:
- **Zero Fabricated Accuracy Claims**: We never claim generalized "100% accuracy" or "compliance certified" based on narrow test fixtures.
- **Explicit Sample Size**: All metrics explicitly report the sample size ($N$).
- **Distinction Between Unit Pipeline Proof and Multi-Category Accuracy**: An initial pipeline verification on a single representative case demonstrates technical feasibility, not production-wide accuracy.

---

## 2. Current Benchmark Staging Status (M1.5)

> [!IMPORTANT]
> **Initial Benchmark Scope**: $N = 1$ verified reference case (`CASE-DRINKWARE-001` for **IS 17526:2021**).
> 
> The initial benchmark verified that the pipeline successfully extracted and retrieved the tested target clauses (Clauses 4.2.1 and 5.4) from the fixture. Broader evaluation across multiple diverse BIS product categories is ongoing.

| Evaluation Dimension | Target Metric | Measured Result ($N=1$ Reference Case) | Benchmark Scope & Staging | Target Milestone |
|---|---|---|---|---|
| **Product DNA Extraction** | Attribute Extraction Accuracy (%) | *Not measured* | Pydantic schema validated; extraction engine pending | M2 (Extraction Engine) |
| **Standard Identification** | IS Number Matching Precision | **100% ($1/1$ case)** | Single case unit validation on IS 17526:2021 fixture | M1.5 |
| **Clause-Level Retrieval** | Recall@3 on Target Clauses | **100% on tested clauses ($2/2$)** | Clause 4.2.1 (Material) & Clause 5.4 (Thermal) retrieved in top-3 | M1.5 |
| **Applicability Decision** | Accuracy vs QCO Gazette Schedule | *Not measured* | Deterministic rule engine pending | M2 (Rule Engine) |
| **Citation Validity** | Unsupported Claim Rate (%) | **0% ($1/1$ case)** | All retrieved items mapped to page provenance | M1.5 (Citation Guard) |
| **Ingestion Throughput** | Pages Processed per Second | **~12 pages/sec** | Measured locally with PyMuPDF layout parser | M1.5 |

---

## 3. Benchmark Dataset Structure

```
data/
 ├── bis/standards/
 │    └── IS_17526_2021.pdf       # Structurally representative fixture (REQUIRES_REVIEW)
 ├── test_cases/
 │    └── drinkware_case_001.json # Initial reference benchmark (N=1)
 └── evaluation/
```

---

## 4. Path to Statistically Significant Evaluation (M2 / M3)

1. **Category Expansion (M2)**: Expand benchmark cases from 1 to 10+ real BIS categories:
   - Domestic Electrical Appliances (`IS 302-2-15` Electric Kettles)
   - Footwear (`IS 15844` Sports Footwear)
   - Toys Safety (`IS 9873`)
   - Packaged Drinking Water (`IS 14543`)
   - Cement (`IS 1489`)
2. **Retrieval Metrics (M3)**: Implement Mean Reciprocal Rank (MRR@10) and Normalized Discounted Cumulative Gain (nDCG@5) across 1,000+ segmented clauses.
3. **Double-Blind Evaluation (M3)**: Independent verification of system compliance outputs against certified BIS laboratory test reports.
