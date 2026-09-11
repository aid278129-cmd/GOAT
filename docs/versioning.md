# Standard Versioning, Amendments & Regulatory Separation

**Milestone**: M1.5 (Knowledge Trust & Governance Hardening)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Version Architecture & Lineage

Standards evolve through revisions, new editions, and amendments. The system represents standard lineage through explicit relational attributes:

```
[Standard Catalog]
       ├── IS 17526:2018 (Edition 1) ──(Status: SUPERSEDED, superseded_by: "IS 17526:2021")
       └── IS 17526:2021 (Edition 2) ──(Status: ACTIVE, supersedes: "IS 17526:2018")
               │
               ├── Amendment No. 1 (2022) ──(Affected Clauses: "4.2.1, 5.4")
               └── Regulatory Instrument ──(QCO S.O. 4521(E))
```

### Key Principles:
1. **Never Silently Overwrite**: Ingesting a new standard edition never deletes or overwrites the previous version. Both exist in the database.
2. **Explicit Lineage**: `supersedes` points to the prior standard number; `superseded_by` points to the successor standard number.
3. **Historical Audit Access**: Historical records remain queryable for retro-active compliance checks on products manufactured under prior rules.
4. **Active Compliance Protection**: Superseded versions are automatically filtered out of active compliance retrieval (`status == 'ACTIVE'`).

---

## 2. Amendment Management

Amendments (`amendments` table) are tracked as child entities of a standard:
- `amendment_number`: e.g., "Amendment No. 1", "Corrigendum 1".
- `publication_date` & `effective_date`: Explicit dates; missing dates remain `null` without fabrication.
- `affected_clauses`: Specific clause identifiers modified by the amendment (e.g., `"4.2.1, 5.4"`). If affected clauses are unknown, status is marked `REQUIRES_REVIEW`.
- `description`: Textual summary of the revision.
- **No Destructive Merging**: Base standard clause text remains unchanged. Citations reference both the base clause and applicable amendments.

---

## 3. Regulatory Instrument Decoupling

A technical standard (`Standard`) is separate from a regulatory order (`RegulatoryInstrument`):
- Technical standards describe how a product must be constructed or tested.
- Quality Control Orders (QCOs) issued by central ministries mandate when and for whom compliance becomes legally compulsory.
- Mandate dates (`gazette_date`, `effective_date`) are stored in `regulatory_instruments` and require official gazette verification.
