# Clause Retrieval Engine & Provenance Citations

**Milestone**: M1.5 (Knowledge Trust & Governance Hardening)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Retrieval Strategy & Trust Policy

The retrieval engine provides **Trust-Gated Semantic Search**:
```
User / System Query (e.g. "food contact stainless steel grade 304")
              │
              ▼
    [Query Embedding (384-d normalized vector)]
              │
              ▼
    [Trust Gate Enforcement]
        ├── Active Compliance: WHERE verification_status = 'VERIFIED' AND status = 'ACTIVE'
        └── Developer Mode: include_unverified = True
              │
              ▼
    [Vector Similarity Scoring] (Cosine Similarity)
              │
              ▼
    [Provenance Citation Packaging] (Includes source_authority & verification_status)
```

---

## 2. Default Backend Safety

- `verified_only = True` is enforced by the backend endpoint `POST /api/v1/knowledge/search`.
- Even if a frontend client omits the flag, the backend default rejects unverified knowledge for compliance claims.
- `include_unverified = True` is only available for internal administrative and audit inspection.

---

## 3. Retrieval Result Structure with Trust Signals

```json
{
  "clause_id": "cls-uuid-421",
  "standard_id": "std-uuid-17526",
  "standard_number": "IS 17526:2021",
  "standard_title": "Commercial Beverage Coolers and Insulated Flasks — Specification",
  "clause_number": "4.2.1",
  "clause_title": "Stainless Steel Parts",
  "section": "Section 4",
  "page_number": 2,
  "text_content": "All metallic parts in direct contact with liquid or food shall be manufactured from stainless steel conforming to Grade 304 of IS 6911 or superior grade.",
  "similarity_score": 0.942,
  "verification_status": "VERIFIED",
  "source_authority": "BIS_OFFICIAL",
  "citation": {
    "document_id": "doc-uuid-12345",
    "standard_number": "IS 17526:2021",
    "clause_number": "4.2.1",
    "page_number": 2,
    "verification_status": "VERIFIED",
    "source_authority": "BIS_OFFICIAL",
    "supporting_text": "All metallic parts in direct contact with liquid or food..."
  }
}
```
