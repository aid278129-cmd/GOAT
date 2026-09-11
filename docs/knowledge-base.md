# BIS Knowledge Base Architecture & Standards Model

**Milestone**: M1.5 (Knowledge Trust & Governance Hardening)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Domain Separation & Trust Model

The BIS Compliance Compiler maintains strict trust boundaries across distinct knowledge domains:
1. **Source Registry (`sources`)**: Tracks publisher, authority level (`AUTHORITATIVE`, `SUPPORTING`, `SECONDARY`, `UNVERIFIED`), and acquisition method.
2. **Document Registry (`documents`)**: Ingested files with SHA-256 integrity checksums, decoupled ingestion status (`DISCOVERED` $\to$ `INDEXED`), and verification status (`UNVERIFIED` $\to$ `VERIFIED`).
3. **Indian Standards Catalog (`standards`)**: Official specifications with logical version chains (`supersedes`, `superseded_by`) and default `UNVERIFIED` trust state.
4. **Amendment Relationships (`amendments`)**: Tracked independently with explicit affected clauses without destructive text merging.
5. **Regulatory Instruments (`regulatory_instruments`)**: Quality Control Orders (QCO) and compulsory scheme mandates decoupled from standard technical definitions.
6. **Audit Verification Trail (`verification_records`)**: Detailed logs distinguishing machine extraction from human/source verification.

---

## 2. Ingested Demonstration Material & Provenance Audit

### Demonstration Category:
**Drinkware & Food Contact Containers** (Mandatory Quality Control Order)

### Current Demonstration Standard:
- **Standard Number**: `IS 17526:2021`
- **Title**: *Commercial Beverage Coolers and Insulated Flasks — Specification*
- **Source File**: `data/bis/standards/IS_17526_2021.pdf`
- **SHA-256 Hash**: Deterministically tracked in document registry.
- **Pages**: 4 pages, 20+ clauses.
- **Source Provenance**: Generated locally from representative public standard text (`generate_standard_fixture.py`).
- **M1.5 Verification Status**: **`REQUIRES_REVIEW`** (explicitly tagged to prevent claiming official certification without authentic gazette verification).

---

## 3. Implementation Status

### [IMPLEMENTED IN M0 / M1 / M1.5]
- Source Registry with authority hierarchy (`Source`).
- Independent `ingestion_status` and `verification_status` axes (`Document`).
- Amendment relationship tracking (`Amendment`).
- QCO / Regulatory Instrument decoupling (`RegulatoryInstrument`).
- Machine validation audit logging (`VerificationRecord`).
- Standard Knowledge Card API (`GET /api/v1/standards/{id}/knowledge-card`).
- Verified-only retrieval safety enforcement (`clause_retriever.py`).
- Deterministic SHA-256 hash deduplication.

### [PLANNED FOR M2 / M3]
- Ingestion of additional official BIS product categories with verified provenance (M2).
- Expert human review portal for compliance officers (M3).
- Automated sync with e-BIS / Manakonline API (M3).
