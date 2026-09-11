# M2 Compliance Reasoning & Evidence Graph Documentation

## 1. Core Architectural Principle

> **"The LLM generates explanations and extracts structured representations; deterministic logic, declarative rules, and verifiable evidence establish compliance claims."**

The LLM is **never** given compliance decision authority (`llm_decision_authority = 0`).

```
USER INPUT (Text / Document)
        ↓
PRODUCT DNA EXTRACTION (Rule / Regex / Structured Parser)
        ↓
NORMALIZATION & PROVENANCE ATTACHMENT
        ↓
MISSING ATTRIBUTE DETECTION & CLARIFICATION LOOP
        ↓
DETERMINISTIC RULE EVALUATOR (APP-DRINKWARE-001, etc.)
        ↓
APPLICABILITY DETERMINATION (Technical Relevance vs Mandatory Regulatory Status)
        ↓
REQUIREMENT EVIDENCE COMPARATOR (Predicate / Measurable Condition Matching)
        ↓
COMPLIANCE STATUS (8-State Verdict) & RECOMMENDED ACTION (4-State Pathway)
        ↓
DECISION RECORD (Immutable Audit Log)
        ↓
EVIDENCE GRAPH (Traceable React Flow DAG)
```

---

## 2. Subsystem Details

### 2.1 Product DNA Engine (`backend/app/services/product_dna/`)
- **Schema**: Extensible typed attributes with audit provenance (`source_document`, `page`, `source_text`, `confidence`, `extraction_method`).
- **Normalizer** (`normalizer.py`):
  - Volume/Capacity: Converts variations (`750 ml`, `750mL`, `0.75 litre`) to canonical `(750, 'ml')`.
  - Materials: Converts `SS 304`, `Stainless Steel Grade 304` to `stainless_steel_grade_304`.
  - Electrical: Extracts normalized voltage (`230 V`), current type (`AC`/`DC`), frequency (`50 Hz`), and wattage (`1500 W`).
- **Confidence Model**: Extraction confidence represents extraction certainty (0.0 to 1.0), never legal compliance certainty.

### 2.2 Clarification Engine (`backend/app/services/clarification/`)
- **Zero-Guessing Policy**: If an applicability-critical attribute is absent, the engine generates a structured `ClarificationRequirement(attribute, reason, options, criticality, blocking)`.
- **Non-Destructive Update**: User clarification answers update Product DNA attributes with `extraction_method="user_clarification"` without erasing prior provenance.

### 2.3 Deterministic Rule Engine (`backend/app/services/applicability/`)
- **Declarative Rule Format**: JSON definitions (`APP_DRINKWARE_001.json`, `APP_ELECTRICAL_001.json`) evaluating conditions recursively (`all`, `any`, `not`, `equals`, `contains`, `in`, `greater_than`, `less_than`).
- **Safety Gate**: Unverified rules cannot make authoritative compliance decisions (`verification_status == "VERIFIED"` required in Authoritative Mode).

### 2.4 Separation of Technical Relevance vs Regulatory Status
- **Standard Match $\neq$ Legal Mandate**:
  - `technical_relevance`: `LIKELY_APPLICABLE`, `POSSIBLY_APPLICABLE`, `MORE_INFORMATION_REQUIRED`, `NOT_APPLICABLE`.
  - `regulatory_status`: `VERIFIED_MANDATORY_QCO`, `MANDATORY_CRS`, `VOLUNTARY`, `MORE_INFORMATION_REQUIRED`.

### 2.5 Requirement Evidence Comparator & Gap Engine (`backend/app/services/gap_analysis/`)
- **8-State Verdict (`ComplianceStatus`)**:
  - `SATISFIED`
  - `POTENTIALLY_SATISFIED`
  - `MISSING_EVIDENCE`
  - `MORE_INFORMATION_REQUIRED`
  - `POTENTIAL_GAP`
  - `NOT_APPLICABLE`
  - `CONFLICTING_EVIDENCE`
  - `REQUIRES_EXPERT_REVIEW`
- **4-State Recommended Action (`RecommendedAction`)**:
  - `REQUIRES_TESTING`
  - `UPLOAD_EVIDENCE`
  - `PROVIDE_SPECIFICATION`
  - `EXPERT_REVIEW`

### 2.6 Decision Records & Evidence Graph
- **Audit Table**: `decision_records` capturing inputs snapshot, matched rule ID, clause number, status, recommended action, and `llm_decision=False`.
- **React Flow Evidence Graph**: Real backend IDs linking `PRODUCT` $\to$ `STANDARD` $\to$ `CLAUSE` $\to$ `REQUIREMENT` $\to$ `DECISION` $\to$ `ACTION`.
