# Evidence-First Compliance Engine Architecture

**Project:** Zyntrix BIS Compliance Compiler  
**Milestone:** M7 — Evidence-First Compliance Engine Hardening  
**SIH Problem Statement:** 26107  

---

## 1. Executive Summary & Foundational Invariant

The fundamental principle governing this compliance compiler is:

$$\text{PRODUCT FACT} \neq \text{COMPLIANCE EVIDENCE}$$

A product description, catalog excerpt, or user claim describes product attributes or intentions, but **NEVER** by itself establishes regulatory compliance.

Under Indian Standards (BIS) and mandatory Quality Control Orders (QCOs), compliance can only be established through verified documentary and laboratory evidence evaluated against official standards via deterministic rules.

```
+------------------+         +---------------------+         +----------------------+
|   Product Fact   |  =/=>   | Compliance Evidence |  --->   |  Compliance Verdict  |
|  ("Grade 304")   |         | (Mill Test Report)  |         |     (SATISFIED)      |
+------------------+         +---------------------+         +----------------------+
```

---

## 2. Evidence Lifecycle & Supported Evidence Types

Evidence is a first-class entity with strict schema definition, authority tracking, document coordinates, and cryptographic hashing.

### Supported Evidence Types
1. `TEST_REPORT`: Physical testing results (e.g. Inversion leakage test, thermal retention).
2. `LAB_REPORT`: Accredited laboratory formal certificate of analysis.
3. `MATERIAL_CERTIFICATE`: Raw material composition mill test certificate (e.g. IS 6911).
4. `CALIBRATION_CERTIFICATE`: Calibration log for testing apparatus.
5. `PRODUCT_SPECIFICATION`: Manufacturer technical datasheet.
6. `TECHNICAL_DRAWING`: Dimensional or engineering CAD drawing.
7. `LABEL_PHOTO`: High-resolution photo of product label and BIS Standard Mark (ISI mark).
8. `PACKAGING_PHOTO`: Outer packaging marking and warnings.
9. `MANUFACTURER_DECLARATION`: Formal conformity statement by manufacturer.
10. `BIS_DOCUMENT`: Official BIS Product Manual, STI, or Gazette publication.
11. `QCO_DOCUMENT`: Ministry/DPIIT Quality Control Order.
12. `PRODUCT_MANUAL`: BIS Scheme of Inspection and Testing (PM/IS 17526/1).
13. `USER_PROVIDED_DOCUMENT`: General uploaded documentation pending classification.

---

## 3. Product Fact vs Evidence Provenance Separation

Attributes within the system carry explicit provenance tags to isolate claims from evidence:

| Provenance Classification | Meaning | Eligible as Compliance Evidence? |
|---|---|---|
| `USER_CLAIM` | Free-text product description entered by the user | **NO** (Strictly prohibited) |
| `USER_CLARIFICATION` | User responses to clarification questionnaires | **NO** (Product attribute only) |
| `DOCUMENT_EVIDENCE` | Extracted from engineering drawings or specs | **YES** (For dimensional/spec clauses) |
| `LAB_EVIDENCE` | Extracted from NABL/BIS accredited laboratory reports | **YES** (For performance/physical test clauses) |
| `OFFICIAL_SOURCE` | Extracted from BIS Gazettes or official standards | **YES** (Authoritative rule baseline) |
| `DERIVED_VALUE` | Computed via deterministic formulas | **YES** (Derived test calculations) |

---

## 4. Hard Deterministic SATISFIED Gate (`can_be_satisfied`)

A centralized function enforces the invariant that **no requirement can be marked SATISFIED without verifiable supporting evidence**.

A requirement receives a `SATISFIED` verdict **if and only if** all following conditions hold:
1. An applicable requirement exists and has an authoritative rule specification.
2. At least one linked evidence item exists in the assessment.
3. The linked evidence has verified provenance (`LAB_EVIDENCE`, `DOCUMENT_EVIDENCE`, `OFFICIAL_SOURCE`) and is **NOT** a `USER_CLAIM`.
4. The evidence authority matches the requirement type (e.g. Performance requires `LAB_REPORT` or `TEST_REPORT`).
5. Extracted evidence values pass the deterministic mathematical/textual condition (`rule_result == PASS`).
6. No unresolved contradictory evidence exists across documents.
7. No pending expert review condition exists.

If any condition fails, the gate rejects `SATISFIED` and assigns an honest status:
- `MISSING_EVIDENCE` (Action: `UPLOAD_EVIDENCE`)
- `POTENTIALLY_SATISFIED` (Action: `REQUIRES_TESTING` for physical laboratory procedures)
- `CONFLICTING_EVIDENCE` (Action: `EXPERT_REVIEW`)
- `MORE_INFORMATION_REQUIRED` (Action: `PROVIDE_SPECIFICATION`)
- `POTENTIAL_GAP` (Action: `PROVIDE_SPECIFICATION`)

---

## 5. Evidence Requirement Matrix

The system specifies allowed evidence types and mandatory operational actions for each standard requirement:

```python
EVIDENCE_REQUIREMENT_MATRIX = {
    "REQ-MAT-304": EvidenceRequirementSpec(
        expected_evidence_types=["MATERIAL_CERTIFICATE", "LAB_REPORT"],
        requires_physical_testing=False,
        default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
    ),
    "REQ-PERF-LEAK": EvidenceRequirementSpec(
        expected_evidence_types=["LAB_REPORT", "TEST_REPORT"],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
    ),
    "REQ-PERF-THERM": EvidenceRequirementSpec(
        expected_evidence_types=["LAB_REPORT", "TEST_REPORT"],
        requires_physical_testing=True,
        default_missing_action=RecommendedAction.REQUIRES_TESTING,
    ),
    "REQ-MARK-ISI": EvidenceRequirementSpec(
        expected_evidence_types=["LABEL_PHOTO", "PACKAGING_PHOTO"],
        requires_physical_testing=False,
        default_missing_action=RecommendedAction.UPLOAD_EVIDENCE,
    ),
}
```

---

## 6. Conflict Detection Engine

When multiple documents or test reports provide competing values for an attribute:
- **Numeric Conflict:** Report 1 declares 1000 ml; Report 2 declares 750 ml.
- **Unit-Normalized Conflict:** Report 1 declares 1.0 L; Spec Sheet declares 750 ml.
- **Textual Conflict:** Mill Certificate declares Grade 304; Supplier sheet declares Grade 201.

### Policy
- The engine strictly prohibits silent automated resolution or LLM guessing.
- Verdict is immediately set to `CONFLICTING_EVIDENCE`.
- Recommended Action is set to `EXPERT_REVIEW`.

---

## 7. Zero LLM Compliance Authority

Large Language Models (LLMs) may assist in:
- Optical layout parsing and OCR assistance.
- Text sanitization against adversarial prompt injections.
- Explanation generation for non-technical MSME users.

**LLMs have ZERO authority to decide compliance.**  
Every compliance decision is computed deterministically in code by `compare_requirement_with_evidence()` and `can_be_satisfied()`. The flag `llm_decision` is hardcoded to `False` across all evaluations.

---

## 8. Point-in-Time Snapshot Reproducibility & Compliance Passport

### AssessmentSnapshot
Every evidence addition, clarification answer, or re-evaluation creates an immutable snapshot containing:
- Complete Product DNA state and attribute provenances.
- Knowledge and rule engine version identifiers.
- Hash-indexed list of linked evidence IDs.
- Deterministic decision records and count summaries.

### Compliance Passport
The Compliance Passport produces an auditable pre-certification roadmap:
- **Hard Invariant:** Any requirement marked `SATISFIED` without an auditable evidence citation (Evidence ID, Source Authority, Page Number, Rule Basis) causes passport compilation to fail with an invariant violation error.
- Full Source Index mapping BIS standards, DPIIT Gazette QCOs, and laboratory certificates.
- Disclaimers stating that the Passport is a compliance roadmap, not an official BIS ISI license.
