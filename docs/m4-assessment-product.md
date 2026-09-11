# Milestone M4: MSME Assessment Workspace & Auditable Compliance Passport

## 1. Executive Summary & Objective

Milestone M4 transforms the underlying Zyntrix technical engine into a unified, manufacturer-facing compliance assessment product. 

Previously, users navigated between decoupled subsystems (Product DNA, Diagnostic health panels, Knowledge Base, Retrieval debugger). M4 establishes:
> **ONE PRODUCT $\to$ ONE ASSESSMENT $\to$ ONE CONTINUOUS WORKSPACE $\to$ ONE AUDITABLE COMPLIANCE PASSPORT**

The workflow allows an MSME manufacturer (e.g. producing domestic vacuum flasks) to start an assessment, inspect extracted Product DNA, answer required clarifications, evaluate applicable Indian Standards, review clause-by-clause requirements, submit supporting laboratory evidence, view identified gaps and recommended actions, inspect the testing roadmap, and generate a printable, tamper-evident **Compliance Assessment Passport**.

---

## 2. Assessment Architecture & Lifecycle

### Entity Relationships
```
Product
   │
   └── Assessment (1..N)
          │
          ├── Product DNA Snapshot
          ├── Applicability Snapshot
          ├── Compliance Summary Snapshot
          ├── AssessmentSnapshot (Audit Log 1..N)
          │      └── Points-in-time state (DNA, Knowledge Version, Rule Versions, Verdicts)
          ├── Linked Evidence (IDs)
          └── Decision Records (Audit table)
```

### Assessment Lifecycle States
1. `DRAFT`: Assessment created; initial text submitted.
2. `COLLECTING_INFORMATION`: Missing attributes detected by Clarification Engine; awaiting MSME specification.
3. `ANALYZING`: Running applicability rules and requirement gap comparison.
4. `REVIEW_REQUIRED`: Ambiguities or missing evidence flagged for manual audit.
5. `COMPLIANCE_REVIEW`: All clauses evaluated; gaps mapped to operational recommended actions (`UPLOAD_EVIDENCE`, `REQUIRES_TESTING`, `EXPERT_REVIEW`).
6. `COMPLETED`: All requirements assessed and certified against available evidence.
7. `ARCHIVED`: Historic snapshot retained for compliance record-keeping.

---

## 3. Stitch MCP Design System & Industrial UI

Using Stitch MCP (Project ID: `2612156763095075218`, Design Asset: `assets/2bcc59b6e3d745fd84c99890cf2f6a92`), we established the **Zyntrix Industrial Core** design system:
- **Character**: Technical, regulatory, clinical, and evidence-oriented.
- **Palette**: Deep slate background (`#0A0F1D` / `#091421`), crisp Geist headings, JetBrains Mono data tokens, and emerald/amber/rose semantic status chips.
- **No Decorative Gimmicks**: Strictly avoided purple gradients, floating AI bubbles, and artificial compliance percentages.
- **Unified Stepper**: One horizontal workflow stepper guiding the user through:
  1. *Assessment Overview*
  2. *Product DNA & Clarifications*
  3. *Compliance Requirements*
  4. *Evidence Workspace*
  5. *Testing Roadmap & Labs*
  6. *Evidence Graph*
  7. *Audit Snapshots*

---

## 4. Compliance Passport Specification

The **Compliance Assessment Passport** is the primary artifact generated at the conclusion of an assessment:
1. **Assessment Identity**: Product name, category, assessment ID, version, timestamp.
2. **Claim Statement**: *"Evidence-Backed Regulatory Compliance Assessment & Technical Gap Roadmap (Pre-Certification Assessment)"*. Strictly disclaims statutory BIS license claims.
3. **Knowledge Trust Basis**: Transparently discloses that official metadata and DPIIT QCO orders are verified, while full standard text acquisition remains pending.
4. **Structured Requirements Table**: 8-state verdict breakdown (`SATISFIED`, `POTENTIALLY_SATISFIED`, `MISSING_EVIDENCE`, etc.) with 4-state actions.
5. **Testing Roadmap & Laboratories**: Laboratory test apparatus schedule and NABL-accredited test centers.
6. **Provenance Source Index**: Direct citations to BIS Standards Catalog, Gazette QCO 2023, and BIS Product Manual PM/IS 17526/1.
7. **Export**: Print-optimized stylesheet (`@media print`) allowing instant PDF generation.

---

## 5. Context-Aware Assessment Chat

MSME users can query the assistant directly within the active assessment context:
- Answers reference specific clause evaluations (e.g., Clause 5.2 Leakage Test), reasons for gaps, and recommended actions.
- Operates in a strictly explanatory role; compliance decisions remain 100% computed by the deterministic rule engine (**LLM Decision Authority = 0**).

---

## 6. Verification & Test Metrics

- **Total Backend Tests Passing**: **74 / 74 tests** (including 5 dedicated M4 acceptance tests in `test_m4_assessment_product.py`).
- **Frontend Production Build**: Vite build passed in 47.84s (`dist/assets/index-CD0pMlzJ.js`).
