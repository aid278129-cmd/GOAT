# Citation Guard Trust Layer

**Milestone**: M0 (Engineering Foundation)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Principles

The Citation Guard is a first-class trust component that sits between the LLM and the final compliance output.

### Distinction:
- **Source Exists**: A document is present in the database.
- **Source Actually Supports Claim**: The specific text in the clause or test report mathematically or logically supports the claim.

If a claim cannot be verified against authoritative retrieved text, the Citation Guard suppresses or marks the claim as `UNVERIFIED` / `INSUFFICIENT_EVIDENCE`.

---

## 2. Implementation Status

### [IMPLEMENTED IN M0]
- `CitationGuardCheckRequest` and `CitationGuardCheckResponse` contracts.
- Pydantic models enforcing citation fields (`standard_number`, `clause_number`, `page_number`, `supporting_text`, `validation_status`).
- Unit tests verifying contract semantics.

### [PLANNED FOR M1 / M2]
- LLM natural language inference (NLI) entailment checker (M1).
- Contradiction and hallucination suppressor (M1).
- Outdated standard version warning generator (M1).
