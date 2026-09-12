# Milestone M25.1A — Official BIS Source Acquisition & Local Corpus Builder

## 1. Executive Overview

Milestone **M25.1A** establishes the controlled source-acquisition pipeline and versioned local corpus builder for the **Zyntrix BIS Compliance Compiler**. The system programmatically discovers, downloads, cryptographically hashes, validates, and indexes publicly accessible regulatory documents exclusively from official Bureau of Indian Standards (BIS) endpoints and official government gazette publications.

> [!IMPORTANT]
> **Cardinal Authority Rule**: This is **SOURCE DATA, NOT TRAINING DATA**. The acquired corpus is reserved exclusively for:
> - Layer 4 BIS Knowledge Retrieval
> - Layer 5 Applicability Engine
> - Layer 6 Clause-Level RAG
> - Layer 7 Compliance Gap Engine
> - Layer 8 Source Validation
> - Layer 9 Compliance Passport
>
> **"Downloaded" != "Verified"**: The system never treats downloaded content as authoritative merely because it was successfully downloaded. Every record undergoes strict state progression:
> `DISCOVERED` &rarr; `ACQUIRED` &rarr; `HASHED` &rarr; `SOURCE-IDENTIFIED` &rarr; `VERIFIED` &rarr; `INDEXED` (or `ACQUISITION_PENDING` / `REJECTED` / `INVALID_SOURCE`).

---

## 2. Official Source URLs & Whitelisted Domains

The pipeline restricts all network operations strictly to official Bureau of Indian Standards (BIS) domains and officially linked BIS portals. Third-party mirrors, scraper caches, and unofficial collections are strictly rejected.

### Whitelisted Domains
- `bis.gov.in` / `www.bis.gov.in`
- `standardsbis.bsbedge.com` (Official Standards Portal)
- `crsbis.in` / `www.crsbis.in` (Compulsory Registration Scheme)
- `lims.bis.gov.in` (Laboratory Information Management System)
- `services.bis.gov.in`
- `manakonline.in` / `huid.manakonline.in`

### Configured Official Seed Endpoints
1. **Primary Portal**: `https://www.bis.gov.in/`
2. **Product-Specific Guidelines**: `https://www.bis.gov.in/product-certification/product-specific-guideline/?lang=en`
3. **Know Your Standard**: `https://www.bis.gov.in/know-your-standard/`
4. **Standards Portal**: `https://standardsbis.bsbedge.com/`
5. **Product Certification**: `https://www.bis.gov.in/product-certification/?lang=en`
6. **Compulsory Certification**: `https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en`
7. **Scheme-I (Mark Scheme)**: `https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-i-mark-scheme/?lang=en`
8. **Product Certification Process**: `https://www.bis.gov.in/product-certification/product-certification-process/?lang=en`

---

## 3. Legal and Access Boundaries

The acquisition pipeline operates under strict legal and ethical compliance constraints:
- **Zero Bypass Policy**: No bypassing of BIS logins, authentication headers, CAPTCHAs, or commercial paywalls.
- **Paywalled Documents**: Standards requiring authorized commercial procurement via the BSBI / e-Sale portal are discovered, cataloged, and recorded in state `ACQUISITION_PENDING`. Missing full text is never fabricated or scraped from pirate sources.
- **Polite Crawling & Rate Limiting**: Requests enforce a conservative delay interval (`0.5s`), User-Agent transparency (`ZyntrixComplianceCompiler/1.0`), and non-aggressive retry caps (max 2 retries).
- **Soft-404 Defense**: The crawler explicitly detects and isolates HTML error pages returned in place of requested PDF resources, transitioning them to `ACQUISITION_PENDING`.

---

## 4. Local Corpus Directory Architecture

Local assets are stored under `data/bis/`, strictly partitioned into 12 separate collections to prevent monolothic data corruption:

```
data/bis/
    standards/                 # Indian Standards (IS) documents & packages
    product_manuals/           # Official BIS Product Manuals
    sit/                       # Scheme of Testing and Inspection (STI/SIT)
    product_guidelines/        # Product-Specific Guidelines
    qco/                       # Quality Control Orders & Gazette records
    gazette/                   # The Gazette of India notifications & schedules
    amendments/                # Official Amendment slips & orders
    revisions/                 # Revisions & standards formulation manuals
    normative_references/      # Normative dependency records
    schemes/                   # Certification scheme documentation (Scheme I, II, IV, X)
    laboratories/              # Recognized/empanelled test lab lists
    licences/                  # Officially published licence & refinery registries
    manifests/                 # Central index of all SourceManifest records
    snapshots/                 # Immutable timestamped snapshot archives
    acquisition_logs/          # Raw crawler discovery & acquisition audit logs
```

### File Immutability Rule
Original acquired files are stored untouched as `original.pdf` (or `.html` / `.txt`). Extracted clause text and metadata are written to separate derived files (`derived.txt`) and `manifest.json`. **Derived operations never mutate or overwrite original source files.**

Example:
```
data/bis/standards/IS_17526_2021/
    original.pdf               # Bit-exact preserved original binary
    derived.txt                # Derived page-aware text extraction
    manifest.json              # Provenance & cryptographic manifest
```

---

## 5. Source Manifest Schema

Every source in the corpus is accompanied by a typed `SourceManifest` model:

| Field | Type | Description |
| :--- | :--- | :--- |
| `source_id` | `str` | Unique canonical identifier (e.g., `STANDARDS_IS_17526_2021`) |
| `source_type` | `SourceType` | Enumeration across all 12 BIS source types |
| `authority` | `str` | Official body (`Bureau of Indian Standards`, `DPIIT`, etc.) |
| `source_url` | `str` | Original retrieval endpoint |
| `canonical_url` | `str` | Normalized official BIS URL |
| `retrieved_at` | `str` | ISO-8601 UTC timestamp of retrieval |
| `published_at` | `str` | Official publication date or `UNKNOWN` |
| `effective_date` | `str` | Legal implementation date or `UNKNOWN` |
| `standard_number` | `str` | Indian Standard designation (e.g., `IS 17526:2021`) |
| `title` | `str` | Official document or standard title |
| `revision` | `str` | Revision level (`First Revision`, `Third Revision`, etc.) |
| `document_status` | `str` | `ACTIVE`, `SUPERSEDED`, or `WITHDRAWN` |
| `acquisition_status` | `AcquisitionState`| `DISCOVERED`, `ACQUIRED`, `ACQUISITION_PENDING`, etc. |
| `verification_status` | `AcquisitionState`| `VERIFIED`, `INVALID_SOURCE`, `ACQUISITION_PENDING` |
| `file_path` | `str` | Relative path to local stored original binary |
| `mime_type` | `str` | Validated MIME type (`application/pdf`, etc.) |
| `file_size` | `int` | Exact byte count |
| `sha256` | `str` | SHA-256 cryptographic checksum |
| `related_standard_numbers` | `List[str]` | Normative and referenced standards |
| `provenance` | `Dict[str, Any]` | Audit trace of crawler, page title, and headers |
| `derived_text_path` | `str` | Relative path to `derived.txt` |
| `extraction_metadata` | `Dict[str, Any]` | Engine (`pymupdf`), version, timestamp, text hash |

---

## 6. Verification Workflow & Non-Automatic Transitions

The pipeline enforces an explicit verification boundary (`CorpusVerifier`). Downloaded files do not become verified automatically:

```
[DISCOVERED]
     ↓
[ACQUIRE & HASH]
     ↓
[ACQUIRED]  (File exists, SHA-256 calculated, exact bytes preserved)
     ↓
  (Explicit Verification Command)
     ↓
  Checks:
  - Is source URL in official BIS whitelist?
  - Is issuing authority legitimate?
  - Does file exist on disk and is non-empty?
  - Does file SHA-256 match manifest SHA-256?
  - Does magic bytes signature match declared MIME type?
  - Are required fields present without unauthorized fabrication?
     ↓
[VERIFIED]  (Eligible for Authoritative Indexing)
```

If any check fails:
- Failed hash or non-official domain: `INVALID_SOURCE`
- Access restriction or missing authorization: `ACQUISITION_PENDING`
- Unauthorized third-party source: `REJECTED`

---

## 7. Change Detection & Immutable Snapshots

### Change Detection
When re-acquiring or auditing an existing source:
1. Re-calculate SHA-256 of candidate bytes.
2. Compare against recorded manifest SHA-256:
   - Identical hash: `UNCHANGED`
   - Differing hash: `SOURCE_CHANGED`
3. A `SOURCE_CHANGED` event creates a new versioned entry without mutating historical provenance.

### Snapshot Creation
Corpus snapshots are generated as immutable, reproducible bundles under `data/bis/snapshots/snapshot_YYYYMMDD_HHMMSS/`. Each snapshot contains:
- `snapshot_manifest.json`: Snapshot ID, timestamp, counts across all 12 categories, acquisition states, and master manifest SHA-256.
- `sources.json`: Complete serialized dump of all manifests at snapshot time.
- **Immutability Invariant**: Re-creating or modifying an existing snapshot tag raises a `ValueError`.

---

## 8. CLI Commands Reference

The BIS CLI provides end-to-end dataset and corpus management:

```bash
# 1. Inspect dataset status across M22 & M25.1A collections
python -m app.cli.bis_dataset status

# 2. Discover official sources with dry-run inspection
python -m app.cli.bis_dataset discover --dry-run --limit 20

# 3. Acquire official sources into data/bis/
python -m app.cli.bis_dataset acquire --category QCO --limit 25

# 4. Verify cryptographic integrity & provenance across all local files
python -m app.cli.bis_dataset verify

# 5. Create an immutable corpus snapshot
python -m app.cli.bis_dataset snapshot

# 6. Diff two snapshots
python -m app.cli.bis_dataset diff snapshot_A snapshot_B
```

---

## 9. Machine-Readable Corpus Integrity Report

At completion of verification or acquisition, `CorpusManager` updates `data/bis/corpus_report.json`:

```json
{
  "catalog_records": 78,
  "sources_discovered": 78,
  "sources_acquired": 35,
  "sources_verified": 35,
  "standards_verified": 14,
  "qco_verified": 12,
  "amendments_verified": 3,
  "revisions_verified": 2,
  "normative_references_verified": 48,
  "clause_indexed": 5,
  "acquisition_pending": 43,
  "invalid_sources": 0,
  "generated_at": "2026-09-12T17:35:00Z",
  "integrity_status": "VALID"
}
```

---

## 10. Known Acquisition & Access Boundaries
1. **Commercial Standards**: Full texts of certain Indian Standards require payment via BSBI portal. These are indexed at the catalog level and marked `ACQUISITION_PENDING`.
2. **Server Rate Throttling**: Official servers occasionally close connections on very large historical PDF archives (>80MB). These failures are trapped gracefully and flagged `ACQUISITION_PENDING` without crashing the compiler.
3. **Soft-404 Pages**: WordPress endpoints that redirect deleted or missing documents to the homepage are identified via MIME signature inspection and prevented from contaminating the PDF standard repository.
