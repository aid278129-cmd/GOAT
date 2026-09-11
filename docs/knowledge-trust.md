# Knowledge Trust, Source Provenance & Governance Model

**Milestone**: M1.6 (Official BIS Knowledge Path & Safe Synthetic Migration)  
**Author**: Team Zyntrix (SIH Problem Statement 26107)

---

## 1. Core Architectural Axioms

1. **INGESTION ≠ VERIFICATION**: A successfully extracted PDF does not become authoritative compliance knowledge.
2. **INDEXED ≠ VERIFIED**: `ingestion_status = "INDEXED"` means the document was parsed and vectorized into the database. `verification_status = "VERIFIED"` means its regulatory authenticity and text faithfulness were confirmed via controlled verification.
3. **ZERO FABRICATION & NO SNIPPET RECONSTRUCTION**: We never reconstruct copyrighted official standard text from snippets, summaries, or AI prompts.
4. **MACHINE VALIDATION vs HUMAN VERIFICATION**: Automated ingestion validates structural parseability and cryptographic checksums; human/expert review verifies legal applicability and textual authenticity.
5. **FAIL-SAFE RETRIEVAL**: Compliance claim retrieval enforces `verified_only = True` by default in the backend.

---

## 2. Source Hierarchy & Trust Classification

All knowledge ingested into the system is traced to an explicit record in the **Source Registry** (`sources` table):

| Priority | Source Type | Authority Level | Description | Permitted Role in System |
|---|---|---|---|---|
| **1 (Highest)** | `BIS_OFFICIAL` | `AUTHORITATIVE` | Official BIS gazette publication, Manakonline portal, BIS sales portal. | May establish verified compliance criteria. |
| **2** | `GOVERNMENT_OFFICIAL` | `AUTHORITATIVE` | Ministry of Consumer Affairs, DPIIT, MeitY gazette notifications. | May establish QCO enforcement dates and regulatory mandates. |
| **3** | `SUPPORTING` | `SUPPORTING` | Official BIS Product Manuals (`PM/IS...`), NABL test report formats. | May establish testing procedures and Scheme of Inspection (SIT). |
| **4** | `SECONDARY` | `SECONDARY` | Industry whitepapers, commentary, trade association summaries. | Discovery and educational guidance only; **CANNOT** establish compliance. |
| **5 (Lowest)** | `USER_PROVIDED` | `UNVERIFIED` | Locally generated sample fixtures, user-uploaded PDFs, external notes. | Initial pipeline validation only; **MUST BE FLAGGED REQUIRES_REVIEW**. |

---

## 3. M1.6 Official BIS Knowledge Package Status

For the demonstration standard **IS 17526:2021**:
- **Official Metadata**: `VERIFIED` (*Domestic Stainless Steel Vacuum Flask/Bottle*).
- **Quality Control Order (QCO)**: `VERIFIED` (*Insulated Flask, Bottles and Containers for Domestic Use (Quality Control) Order, 2023*, DPIIT).
- **Product Manual**: `VERIFIED` (*PM/IS 17526/1*, Central Marks Department-III, BIS).
- **Full Standard Specification PDF**: **`OFFICIAL_DOCUMENT_ACQUISITION_PENDING`** (Pending authorized procurement on Manakonline without bypassing digital rights controls).
- **Synthetic Demonstration Fixture**: Preserved under `data/bis/fixtures/synthetic/IS_17526_2021_representative.pdf` with explicit non-authoritative label (`SYNTHETIC_TEST_FIXTURE`).
