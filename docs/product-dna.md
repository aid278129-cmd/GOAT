# Product DNA Engine Specification

**Milestone**: M0 (Engineering Foundation)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Principles

1. **Structured Representation**: Raw datasheets and descriptions are parsed into validated Pydantic models.
2. **Attribute Provenance**: Every technical property retains its source document, page, exact quoted text, extraction method, and confidence score.
3. **Zero-Guessing Policy**: If an applicability-critical attribute is missing, the system MUST NOT guess. It generates a `ClarificationRequirement`.

---

## 2. Implementation Status

### [IMPLEMENTED IN M0]
- Pydantic models: `ProductDNACore`, `DNAAttribute`, `AttributeProvenance`, `ClarificationRequirement`.
- SQLAlchemy models: `Product`, `ProductAttribute` with relational mapping and JSON metadata.
- Unit tests verifying serialization, validation, and clarification generation.

### [PLANNED FOR M1 / M2]
- Structured LLM extraction using Instructor/JSON Schema parsing (M1).
- BOM (Bill of Materials) tabular parser (M2).
- Dynamic industry taxonomy mapping (M1).
