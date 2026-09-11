# Document Ingestion Pipeline Specification

**Milestone**: M1 (Ingestion & Knowledge Base)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. End-to-End Pipeline Architecture

```
[Source Document (PDF / Scan)]
              │
              ▼
    [1. File Validation & SHA-256 Hashing] ──(Deduplication Check)
              │
              ▼
    [2. Document Registration] ──(Status: DISCOVERED)
              │
              ▼
    [3. PyMuPDF Layout Extraction] ──(Page Provenance + OCR Fallback)
              │
              ▼
    [4. Section & Metadata Detection] ──(IS Number, Edition, QCO Flag)
              │
              ▼
    [5. Hierarchical Clause Segmentation] ──(Dotted Decimal Hierarchy + Parent Links)
              │
              ▼
    [6. Structured Requirement Extraction] ──(Typing: Material/Performance/Safety)
              │
              ▼
    [7. Embedding Generation & Vector Storage] ──(pgvector Vector Columns)
              │
              ▼
    [8. Document Status Update] ──(Status: INDEXED & VERIFIED)
```

---

## 2. Ingestion Stages & Integrity Guarantees

| Stage | Module | Key Invariants |
|---|---|---|
| **Hashing & Registration** | `document_loader.py` | Calculates SHA-256 before processing; prevents duplicate ingestion. |
| **Page-Preserving PDF Parsing** | `pdf_extractor.py` | Extracts 1-indexed pages; tags pages as `TEXT` or `OCR`. |
| **OCR Fallback** | `ocr.py` | Automatically engages Tesseract OCR on scanned/image-only pages. |
| **Hierarchical Segmentation** | `clause_segmenter.py` | Preserves `page_start`, `page_end`, and parent-child hierarchy (`4.2.1` -> `4.2`). |
| **Requirement Typing** | `requirement_extractor.py` | Preserves exact text; flags uncertain interpretations as `REQUIRES_REVIEW`. |
| **Embedding Abstraction** | `embedder.py` | Dense 384-dimensional normalized vector representation. |

---

## 3. Developer CLI Usage

Ingest any BIS standard PDF directly from terminal:
```powershell
python -m backend.app.services.ingestion.cli ingest data/bis/standards/IS_17526_2021.pdf --standard "IS 17526:2021" --title "Commercial Beverage Coolers and Insulated Flasks - Specification"
```
