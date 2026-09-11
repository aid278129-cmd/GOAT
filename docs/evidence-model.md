# Evidence Model & Provenance Chain

**Milestone**: M0 (Engineering Foundation)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Provenance Chain Structure

Every compliance result consists of a verifiable chain:
```
[Product DNA Attribute / Lab Value]
               │
               ▼
   [Extracted Evidence Chunk] (Source document, page, exact quote)
               │
               ▼
   [Authoritative Standard Clause] (IS Number, Clause Number, Limit)
               │
               ▼
   [Citation Guard Validation Status] (SUPPORTED / UNVERIFIED / CONTRADICTED)
               │
               ▼
   [Compliance Assessment State] (SATISFIED / POTENTIAL_GAP / etc.)
```

---

## 2. Multi-State Compliance Model

Rather than a simple binary PASS/FAIL, the model represents real-world regulatory nuances:
- `SATISFIED`: Verified evidence directly meets standard requirements.
- `POTENTIALLY_SATISFIED`: Likely compliant but requires formal lab test verification.
- `MISSING_EVIDENCE`: Standard requirement exists, but no manufacturer test data provided.
- `MORE_INFORMATION_REQUIRED`: Ambiguous product specifications.
- `POTENTIAL_GAP`: Manufacturer specification violates clause limits.
- `NOT_APPLICABLE`: Requirement excluded by product classification.
- `CONFLICTING_EVIDENCE`: Inconsistent test values across submitted documents.
- `REQUIRES_EXPERT_REVIEW`: Complex edge case requiring BIS technical committee interpretation.

---

## 3. Implementation Status

### [IMPLEMENTED IN M0]
- Database `Evidence` and `ComplianceResult` models with relational linkages.
- Pydantic `ComplianceStatus`, `ValidationStatus`, `ProvenanceCitation` schemas.
- UI components visualizing the provenance citation structure.

### [PLANNED FOR M1 / M2]
- Dynamic provenance graph generator (M1).
- Cryptographic hash chaining for tamper-evident compliance passports (M1).
