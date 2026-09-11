# Deterministic Applicability Engine

**Milestone**: M0 (Engineering Foundation)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Principles

Applicability of Indian Standards must not rely purely on unconstrained LLM reasoning. Instead, it utilizes deterministic rules based on Product DNA combined with QCO gazette orders.

### Applicability Multi-State Model
- `LIKELY_APPLICABLE`: Product DNA matches standard scope and criteria.
- `POSSIBLY_APPLICABLE`: Probable match requiring minor clarification.
- `MORE_INFORMATION_REQUIRED`: Critical parameters missing; cannot determine without input.
- `NOT_APPLICABLE`: Definitively out of scope.

---

## 2. Implementation Status

### [IMPLEMENTED IN M0]
- `ApplicabilityStatus` enum in Pydantic schemas and database models.
- Product DNA parameter validation and clarification trigger structure.

### [PLANNED FOR M1 / M2]
- Rule catalog (`APP-001`, `APP-002`, etc.) with auditable conditions and source clause mapping (M1).
- Execution engine combining deterministic rules with vector retrieval (M1).
