<div align="center">

# ⚡ GOAT
### Bureau of Indian Standards (BIS) Compliance Compiler

**Turn product information into traceable, source-backed BIS compliance intelligence.**

[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-905%20Passed%20(100%25)-10b981?style=for-the-badge&logo=pytest&logoColor=white)](backend/tests/)
[![Python Version](https://img.shields.io/badge/Python-3.14%20%7C%203.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Frontend Build](https://img.shields.io/badge/Frontend-Vite%206%20%2B%20React%2018-61dafb?style=for-the-badge&logo=react&logoColor=black)](frontend/)
[![AI Authority](https://img.shields.io/badge/LLM%20Compliance%20Authority-0.0%25%20(Deterministic)-ef4444?style=for-the-badge&logo=shield&logoColor=white)](docs/architecture/M24_4_COMPLIANCE_AUTHORITY_FIREWALL.md)
[![Reasoning Engine](https://img.shields.io/badge/Orchestrator-LangGraph%201.2%20DAG-8b5cf6?style=for-the-badge&logo=diagram-next&logoColor=white)](docs/architecture/M24_2_LANGGRAPH_CORE.md)
[![Observability](https://img.shields.io/badge/Observability-LangSmith%20%2B%20Studio-f97316?style=for-the-badge&logo=datadog&logoColor=white)](docs/architecture/M24_5_LANGSMITH_OBSERVABILITY.md)

<br/>

> **"This is NOT a generic chatbot.**  
> **LLMs generate natural language explanations; retrieved, NABL-verified evidence establishes compliance claims."**

<br/>

<img src="docs/assets/hero-pipeline.svg" alt="GOAT End-to-End Compliance Pipeline" width="100%"/>

</div>

---

## 📑 Table of Contents

- [1. Executive Overview](#1-executive-overview)
- [2. Why GOAT? (The Paradigm Shift)](#2-why-goat-the-paradigm-shift)
- [3. Verified Repository Metrics](#3-verified-repository-metrics)
- [4. 9-Layer Modular Architecture](#4-9-layer-modular-architecture)
- [5. LangGraph Reasoning Topology](#5-langgraph-reasoning-topology)
- [6. Trust, Provenance & Authority Firewall](#6-trust-provenance--authority-firewall)
- [7. Evidence-to-Passport Flow](#7-evidence-to-passport-flow)
- [8. The Compliance Passport](#8-the-compliance-passport)
- [9. Security, Privacy & Deterministic Redaction](#9-security-privacy--deterministic-redaction)
- [10. LangGraph Studio & Observability](#10-langgraph-studio--observability)
- [11. Technology Stack](#11-technology-stack)
- [12. Testing, Benchmarking & Quality Assurance](#12-testing-benchmarking--quality-assurance)
- [13. Golden Demo Case Walkthrough (SIH 2026)](#13-golden-demo-case-walkthrough-sih-2026)
- [14. Quick Start & Installation](#14-quick-start--installation)
- [15. Repository Structure](#15-repository-structure)
- [16. Project Roadmap](#16-project-roadmap)
- [17. Contribution Guide](#17-contribution-guide)
- [18. Regulatory Disclaimer](#18-regulatory-disclaimer)

---

## 1. Executive Overview

**GOAT** is an evidence-first, deterministic regulatory intelligence compiler engineered for Indian Standards (IS), Quality Control Orders (QCOs), and Scheme of Inspection and Testing (STI) conformity assessment.

Modern industrial compliance in India requires navigating hundreds of statutory Quality Control Orders (QCOs) issued by DPIIT, MeitY, and the Ministry of Steel. Traditional generic AI chatbots hallucinate compliance percentages, invent non-existent standard clauses, and conflate unverified manufacturer datasheets with empirical laboratory evidence.

GOAT enforces a **strict cryptographic and architectural separation**:
- **Generative Language (Layer 3)** is handled by **exactly ONE LLM** (`SingleStructuredLLM`) with **strictly 0.0% compliance authority**. It parses intents, extracts technical entities, and explains standards.
- **Compliance Determinations (Layers 5, 7, 8, 9)** are computed **100% deterministically** by mathematical constraint evaluators, gazette order matching engines, and empirical laboratory evidence verification firewalls.

```
+---------------------------------------------------------------------------------------------------------+
|                                    Core Compilation Lifecycle                                           |
|                                                                                                         |
|   [Input Data]  ──>  [Product DNA]  ──>  [QCO Applicability]  ──>  [Clause RAG]                         |
|   (PDF/Lab/BOM)      (Normalized)         (Statutory Scheme)       (Standard Isolated)                  |
|                                                                             │                           |
|                                                                             ▼                           |
|   [Passport Output]  <──  [Deterministic Gate]  <──  [Evidence Firewall] <─┘                           |
|   (Auditable Seal)        (Bitwise Math Gap)         (NABL Lab Verified)                                |
+---------------------------------------------------------------------------------------------------------+
```

<div align="center">
  <img src="docs/assets/pipeline-3d.svg" alt="GOAT Compilation Lifecycle" width="100%"/>
</div>

---

## 2. Why GOAT? (The Paradigm Shift)

| Architectural Dimension | Generic AI Chatbot | GOAT BIS Compliance Compiler |
|:---|:---|:---|
| **Compliance Decision Maker** | Probabilistic LLM guessing verdicts | **100% Deterministic Rule Engine** (Layer 7) |
| **LLM Compliance Authority** | Unbounded (~100%) | **Strictly 0.0%** (Hard-enforced by firewall) |
| **Evidence Standards** | Treats unverified text as proof | **User claim alone NEVER satisfies a requirement** |
| **Compliance Metrics** | Arbitrary percentages (e.g., "85% compliant") | **Honest Counts**: `Satisfied`, `Missing Evidence`, `Gap` |
| **Cross-Standard Isolation** | Bleeds requirements across distinct standards | **Cryptographic Standard Isolation Lock** |
| **Missing Information** | Fabricates plausible assumptions | **Zero-Guessing Clarification Queue** (Halts & Prompts) |
| **Adversarial Resilience** | Susceptible to "Approve this product" prompt injection | **Zero-Authority Refusal Gate** (Instant Neutralization) |
| **Output Artifact** | Fleeting conversational text | **Auditable Pre-Certification Compliance Passport** |

---

## 3. Verified Repository Metrics

Every statistic below is audited directly from the live codebase, Git commit history, and test runner:

<div align="center">

| Metric Category | Verified Repository Value | Audit Proof |
|:---|:---|:---|
| **Automated Test Suite** | **905 / 905 Passed** (100% Pass Rate) | `py -3.14 -m pytest backend/tests -q` (15.09s) |
| **Frontend Production Build** | **Built Cleanly** (1,758 modules, 0 errors) | `npm run build` in `frontend/` (Vite v6.4.3) |
| **Architecture Stack** | **9 Modular Layers** (L1 through L9) | `backend/app/services/` |
| **Reasoning Graph Topology** | **11 Canonical Nodes, 16 Directed Edges** | `backend/app/services/orchestrator/graph/` |
| **Graph Mathematical Form** | **Strict Directed Acyclic Graph (0 Cycles)** | Static topology audit (M24.4.2) |
| **LLM Model Cardinality** | **Exactly ONE Model** (`SingleStructuredLLM`) | Zero competing sub-models or dual LLMs |
| **LLM Compliance Authority** | **0.0% Authority** | Enforced across Layers 3, 5, 7, 8, 9 |
| **BIS Dataset Scope** | **51 Authentic Gazette-Verified Standards** | `data/bis_dataset/real_bis_standards.json` |
| **Formal Ground Truth** | **10 Multi-Scenario Test Cases** | `data/evaluation/ground_truth/*.json` |
| **SIH Golden Demo Case** | `GOLDEN-SIH-2026-DEMO` (**Locked**) | IS 17526:2021 Stainless Steel Vacuum Flask |
| **Execution Latency** | **P50: 16.5 ms \| P95: 35.8 ms** (Sub-2s Target) | M24.6 Benchmark Latency Profile |
| **Git Repository History** | **50 Commits \| 3 Active Authors** | `git rev-list --count HEAD` |

</div>

---

## 4. 9-Layer Modular Architecture

GOAT is structured into 9 isolated, independently auditable layers:

<div align="center">
  <img src="docs/assets/architecture.svg" alt="GOAT 9-Layer Architecture" width="100%"/>
</div>

### Layer Breakdown

1. **Layer 1 — Guided Multi-Modal Input & Preparation**:
   Ingests manufacturer test documentation across PDF datasheets, high-resolution rating plate images (structured layout & OCR via OpenDataLoader PDF), voice memos (STT), Excel/CSV Bills of Materials (BOM), and manual inputs. Generates dynamic document readiness checklists.
2. **Layer 2 — Product DNA Engine & Normalization**:
   Extracts structured technical parameters (`rated_wattage`, `capacity_ml`, `sheath_material`). Executes deterministic unit conversion (°F &rarr; °C, inches &rarr; mm) without loss of precision. Features an automated clarification queue when mandatory attributes are absent.
3. **Layer 3 — AI Orchestrator & Reasoning Graph**:
   Wraps the single underlying LLM via `GOATLangChainChatAdapter`. Operates a 11-node compiled LangGraph state graph. Governs intent classification, conversational explanations, and controlled tool dispatches. **LLM Compliance Authority = 0.0%**.
4. **Layer 4 — Segmented BIS Knowledge Base**:
   Dual lexical BM25 and vector embeddings index verified Indian Standards, Quality Control Orders (QCOs), and Schemes of Inspection and Testing (STI). Enforces cryptographic SHA-256 clause fingerprinting.
5. **Layer 5 — Deterministic BIS Applicability Engine**:
   Evaluates statutory product applicability across 6 orthogonal dimensions (Standard Scope, QCO Mandate, Product Conditions, Standard Status, Normative Dependencies, Evidence Availability). Implements a strict 10-step decision pipeline powered by an authoritative version/supersession registry (`version_registry.py`), a directed normative/allied standards graph (`relationship_graph.py`), and a typed condition evaluator (`conditional.py`). Invariants: Missing discriminators produce `MORE_INFORMATION_REQUIRED`, contradictions trigger `CONFLICTING_RULES`, and `COVERAGE_GAP ≠ NOT_APPLICABLE`. **LLM Authority = 0.0%**.
6. **Layer 6 — Clause-Level RAG (Standard-Isolated)**:
   Applies a strict namespace lock preventing cross-standard contamination (e.g., pressure cooker queries can never retrieve helmet clauses). Reranks normative clauses and tracks parent-child requirement hierarchies.
7. **Layer 7 — Compliance Gap Analysis Engine**:
   Computes 100% deterministic mathematical evaluations: parameter tolerance boundaries, numerical limit comparisons, and formula checks. Classifies requirements into 8 canonical statuses and outputs a prioritized gap register (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
8. **Layer 8 — Source Validation & Evidence Firewall**:
   Validates laboratory accreditation (NABL), test report authenticity, and document provenance. Enforces the cardinal rule: *User claim alone NEVER satisfies a requirement*. Flags conflicting test values for mandatory human expert review.
9. **Layer 9 — Compliance Passport & Output Integrity**:
   Compiles the final, legally defensible pre-certification Compliance Passport. An output integrity gate intercepts and suppresses hallucinated verdicts, enforcing honest counts and citation verification.

---

## 5. LangGraph Reasoning Topology

Layer 3 executes a compiled LangGraph `StateGraph` adhering strictly to an 11-node, 16-edge Directed Acyclic Graph:

<div align="center">
  <img src="docs/assets/reasoning-graph.svg" alt="LangGraph Reasoning Topology" width="100%"/>
</div>

### Canonical Node Inventory

| Node Identifier | Type | Role & Operational Invariant | Authority |
|:---|:---|:---|:---|
| `__start__` | Entrypoint | Graph execution initializer | None |
| `request_understanding` | Security Gate | Input sanitization, intent classification, prompt injection defense | `UNTRUSTED` |
| `controlled_refusal` | Terminal Gate | Instant zero-authority refusal upon detecting malicious compliance override commands | `0.0% Authority` |
| `product_dna_check` | Parameter Gate | Validates presence of mandatory Product DNA parameters | `UNTRUSTED` |
| `clarification_request`| Terminal Gate | Halts automated assumptions; asks user for missing technical attributes | `0.0% Authority` |
| `task_router` | Router Node | Resolves standard; identifies short-circuit paths (e.g., unit conversion) | `DETERMINISTIC` |
| `retrieval_agent` | Knowledge Agent | Queries verified BIS catalog via controlled tools (`search_bis_standards`) | `VERIFIED_SOURCE` |
| `evidence_validation_gate`| Provenance Gate | Enforces Layer 8 evidence trust rules on submitted lab reports | `DETERMINISTIC` |
| `analysis_agent` | Reasoning Agent | Generates natural language analysis via single LLM or executes unit math | `AI_DERIVED (0.0%)` |
| `deterministic_compliance_gate` | Compliance Engine | Authoritative clause gap calculation via Layer 7 mathematical engine | `100.0% AUTHORITY` |
| `planning_agent` | Remediation Agent | Synthesizes an actionable 5-bucket testing roadmap | `AI_DERIVED (0.0%)` |
| `output_integrity_gate` | Integrity Gate | Layer 9 validation: citation verification & suppression of false claims | `PASSPORT_GATE` |
| `__end__` | Exitpoint | Terminal graph boundary | None |

### Directed Edge Dispatch Rules (16 Edges)

```
__start__                      ──>  request_understanding
request_understanding          ──>  controlled_refusal         [if security_flag == True]
request_understanding          ──>  product_dna_check          [if security_flag == False]
controlled_refusal             ──>  __end__                    [terminal exit]
product_dna_check              ──>  clarification_request      [if dna_sufficient == False]
product_dna_check              ──>  task_router                [if dna_sufficient == True]
clarification_request          ──>  __end__                    [terminal exit]
task_router                    ──>  retrieval_agent            [if retrieval_required == True]
task_router                    ──>  analysis_agent             [if retrieval_required == False (short-circuit)]
retrieval_agent                ──>  evidence_validation_gate   [sequential dispatch]
evidence_validation_gate       ──>  analysis_agent             [verified evidence]
evidence_validation_gate       ──>  output_integrity_gate      [unverified standard / severe conflict]
analysis_agent                 ──>  deterministic_compliance_gate [deterministic evaluation]
deterministic_compliance_gate  ──>  planning_agent             [passes mathematical gap records]
planning_agent                 ──>  output_integrity_gate      [sequential dispatch]
output_integrity_gate          ──>  __end__                    [terminal exit]
```

---

## 6. Trust, Provenance & Authority Firewall

GOAT establishes an unbreachable firewall between conversational language generation and compliance determination:

<div align="center">
  <img src="docs/assets/authority-model.svg" alt="Authority Firewall & Trust Boundaries" width="100%"/>
</div>

### The Cardinal Compliance Equation

$$\mathbf{SATISFIED} \iff 	ext{Req}_{	ext{Verified}} \wedge 	ext{Evidence}_{	ext{Lab}} \wedge 	ext{Link}_{	ext{Verified}} \wedge 	ext{Eval}_{	ext{Deterministic}} \wedge 
eg	ext{Conflict}$$

1. **User Claim $
e$ Compliance Evidence**: Manufacturer statements or datasheets alone can never result in a `SATISFIED` determination.
2. **Clause Retrieved $
e$ Requirement Satisfied**: Successfully retrieving a BIS clause only establishes the *benchmark*; it does not verify conformity.
3. **Conflict $\implies$ Expert Review**: If laboratory measurements contradict manufacturer specifications, the system blocks automated certification and escalates to human expert review.

---

## 7. Evidence-to-Passport Flow

Raw product facts are transformed into auditable pre-certification compliance items through a five-stage verification pipeline:

<div align="center">
  <img src="docs/assets/evidence-flow.svg" alt="Evidence Flow Pipeline" width="100%"/>
</div>

1. **Product Fact**: Extracted from manufacturer documents and unit-normalized (e.g., 750 ml Stainless Steel 304).
2. **Statutory QCO**: Matched against Ministry Quality Control Orders to determine applicable standards (e.g., DPIIT QCO 2023 $\implies$ IS 17526:2021).
3. **BIS Clause**: Relevant normative clauses retrieved under standard isolation (e.g., Clause 5.4 Heat Retention $\ge 60^\circ	ext{C}$ after 6 hours).
4. **Lab Evidence**: Ingests NABL-accredited test reports with cryptographic SHA-256 hash checks.
5. **Deterministic Gap Gate**: Evaluates empirical measurement ($68.2^\circ	ext{C}$) against normative threshold ($60.0^\circ	ext{C}$). Renders `SATISFIED`.

---

## 8. The Compliance Passport

The primary output of GOAT is the **Evidence-Backed Pre-Certification Compliance Passport** (Layer 9), structured for MSMEs, testing laboratories, and regulatory auditors:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  GOAT EVIDENCE-BACKED COMPLIANCE PASSPORT                                                │
│  Standard: IS 17526:2021 • Product: Domestic Vacuum Flask 750ml • Status: PRE-CERT AUDITED   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│  1. EXECUTIVE SUMMARY                                                                       │
│     - Scope: Domestic Insulated Drinkware Containers                                        │
│     - Governing Order: DPIIT QCO Order 2023 (Mandatory Scheme I - ISI Mark)                 │
│     - Honest Counts: 5 Satisfied | 0 Critical Gaps | 1 Info Required | 0 Conflicts          │
│                                                                                             │
│  2. CLAUSE VERIFICATION MATRIX                                                              │
│     - Cl 4.2.1 (Material SS304): SATISFIED [Evidence: Mill Cert #MC-9941, Verified]        │
│     - Cl 5.2 (Inversion Leakage): SATISFIED [Evidence: NABL Lab Report TC-5291, Verified]   │
│     - Cl 5.4 (Heat Retention >=60C): SATISFIED [Measured: 68.2C, NABL Lab Report TC-5291] │
│                                                                                             │
│  3. PRIORITIZED GAP REGISTER                                                                │
│     - Critical Gaps: None                                                                   │
│     - Action Required: Submit NABL Overall Migration Report for silicone seal (IS 9845)     │
│                                                                                             │
│  4. 5-BUCKET TESTING ROADMAP                                                                │
│     [Lab Tests] -> IS 9845 Overall Migration Limit (Polypropylene / Silicone)               │
│     [Factory STI] -> Routine Inversion Leakage Batch Testing Procedure                      │
│                                                                                             │
│  5. MSME ACTION CENTER                                                                      │
│     - Recommended Testing Laboratory: NABL Lab TC-5291 (Accredited for IS 17526)            │
│     - Downloadable Dossier: Complete compliance package ready for BIS Manakonline portal    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> **Legal Notice**: GOAT provides an evidence-backed pre-certification compliance assessment. It does **not** issue official BIS licenses or ISI marks. Official licenses are granted exclusively by the Bureau of Indian Standards following statutory inspection.

---

## 9. Security, Privacy & Deterministic Redaction

GOAT enforces strict security and data protection invariants:

1. **Deterministic Secret Redaction**: All trace logs and observability payloads pass through recursive regex sanitization:
   - OpenAI, Composio, Groq, and LangSmith API keys (`sk-...`, `ak_...`, `gsk_...`, `lsv2_pt_...`)
   - Bearer authentication tokens
   - Database connection URIs with embedded passwords (`postgresql://user:pass@host/db`)
   - Personally Identifiable Information (PII: emails, Indian phone numbers, 12-digit Aadhaar numbers)
2. **Proprietary BOM Protection**: Raw Bill of Materials data and chemical formulas are hashed into SHA-256 fingerprints (`[PROTECTED_PAYLOAD: hash=...]`) before reaching traces.
3. **Adversarial Prompt Injection Defense**: The `request_understanding` node detects jailbreaks, prompt injection, and override attempts, routing immediately to `controlled_refusal`.
4. **Failure Isolation**: If LangSmith, external APIs, or networks experience downtime, the orchestrator catches errors gracefully, continuing local graph execution with zero disruption.

---

## 10. LangGraph Studio & Observability

GOAT includes native configuration for **LangGraph Studio**, providing real-time visual inspection of the reasoning graph canvas:

```powershell
# Launch the interactive LangGraph Studio development server
.\start_studio.bat
```

The script automatically sets `PYTHONIOENCODING=utf-8` (preventing Windows console Unicode crashes) and starts the server at `http://127.0.0.1:2024`.

To visualize:
1. Open [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024) in your browser.
2. The UI renders the live compiled `compliance_graph` with all 11 nodes, conditional edges, and execution state trees.

To toggle LangSmith cloud tracing:
```bash
# In your .env file
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_your_key_here
LANGSMITH_PROJECT=goat-bis-compliance
```

---

## 11. Technology Stack

```
+─────────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                         GOAT Technology Stack                                        |
+──────────────────────────┬────────────────────────────────────────┬─────────────────────────────────────+
| Layer Area               | Technology / Framework                 | Purpose                             |
+──────────────────────────┼────────────────────────────────────────┼─────────────────────────────────────+
| Frontend Web UI          | React 18 • TypeScript • Tailwind CSS   | Interactive regulatory dashboard    |
| Frontend Build & Flow    | Vite v6.4 • @xyflow/react • Lucide     | Visual graph canvas & PDF viewer    |
| Backend API Server       | Python 3.14 • FastAPI • Uvicorn        | High-performance async REST API     |
| AI Reasoning & Graphs    | LangGraph 1.2 • LangChain Core 1.5.3   | 11-node state graph orchestrator    |
| Observability & Tracing  | LangSmith 0.10 • LangGraph Studio      | Failure-isolated privacy tracing    |
| Relational & Vector DB   | PostgreSQL • pgvector • SQLAlchemy 2.0 | Standard knowledge & clause storage |
| Local Dev Fallback DB    | SQLite • aiosqlite                     | Zero-configuration offline mode     |
| Document Intelligence    | PyMuPDF (fitz) • PyPDF • ReportLab     | PDF parsing, OCR & passport export  |
| Image & Speech OCR       | OpenDataLoader PDF • Pillow                   | Multi-modal spec sheet intake       |
| Statistical Testing      | Pytest 9.1 • pytest-asyncio            | 584 automated verification tests    |
+──────────────────────────┴────────────────────────────────────────┴─────────────────────────────────────+
```

---

## 12. Testing, Benchmarking & Quality Assurance

The GOAT codebase is verified by **584 automated tests** covering every layer, node, tool, and compliance firewall:

```
============================= 584 passed in 12.32s =============================
```

### Test Suite Distribution

- **Layer 1 Multi-Modal Tests**: OCR extraction, file validation, BOM format parsing.
- **Layer 2 Product DNA Tests**: Fact normalization, unit standardizations, clarification workflows.
- **Layer 3 AI Orchestrator Tests**: Single LLM invariant, grounding guard, citation verification.
- **Layer 5 Applicability Tests**: QCO regulatory order matching, scheme classification.
- **Layer 6 Clause RAG Tests**: Standard isolation lock, hybrid dense/sparse retrieval.
- **Layer 7 Gap Analysis Tests**: Range/limit checks, formula evaluations, roadmap generation.
- **Layer 8 Evidence Firewall Tests**: NABL certificate validation, contradictory evidence alerts.
- **Layer 9 Output Passport Tests**: Citation checks, honest count validation, tamper prevention.
- **M24.2–M24.4.2 LangGraph Suite**: 11 nodes, 16 edges, DAG topology, agent intelligence optimization.
- **M24.5 Observability Suite**: 14 tests verifying redaction, PII protection, failure isolation.
- **M24.6 Benchmark Suite**: 20 tests verifying the 15-dimension reasoning evaluation matrix.
- **M25.0 Applicability Engine Suite**: 58 focused tests verifying scope inclusion/exclusion, blocking discriminators, typed condition thresholds, QCO gazette orders, supersessions, amendments, normative graphs, contradiction isolation, and the 14 golden benchmark cases.

### Reproducible Quality Commands

```powershell
# Run the complete backend regression test suite
py -3.14 -m pytest backend/tests -q

# Run the 15-dimension reasoning evaluation harness
py -3.14 -m backend.app.services.evaluation.evaluator

# Run the frontend production build
cd frontend && npm run build
```

---

## 13. Golden Demo Case Walkthrough (SIH 2026)

The repository includes a cryptographically locked golden demonstration case (`GOLDEN-SIH-2026-DEMO`):

- **Product**: 750ml Double-Walled Vacuum Insulated Flask (SS304 Liner)
- **Applicable Standard**: `IS 17526:2021` (Mandatory via DPIIT QCO 2023)
- **Key Clauses Evaluated**:
  - `Clause 4.2.1`: Material Specification (SS304 Chemical Analysis) $\implies$ **SATISFIED**
  - `Clause 5.2`: Inversion Leakage (10 min inversion test) $\implies$ **SATISFIED**
  - `Clause 5.4`: Thermal Heat Retention ($\ge 60^\circ	ext{C}$ at 6 hours) $\implies$ **SATISFIED**
  - `Clause 7.1`: Mandatory BIS ISI Rating Plate Marking $\implies$ **SATISFIED**
- **Gap Classification**: `SATISFIED`
- **Testing Roadmap**: Action plan generated for routine batch inspection and STI conformity.

---

## 14. Quick Start & Installation

### Prerequisites
- **Python**: Version `3.11`, `3.12`, `3.13`, or `3.14` (Verified on Python 3.14.3)
- **Node.js**: Version `18.0.0` or higher
- **Git**: Installed and configured

### 1. Clone & Configure Workspace

```bash
git clone https://github.com/Jeffin2007/GOAT.git
cd GOAT
```

### 2. Backend Setup

```powershell
# Create and activate Python virtual environment
py -3.14 -m venv .venv
.\.venv\Scriptsctivate

# Install production dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env   # Or create .env with your optional keys
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run build    # Verify production assets
npm run dev      # Start development server
```

### 4. Run the Full Test Suite

```powershell
# In the workspace root
py -3.14 -m pytest backend/tests -q
```

---

## 15. Repository Structure

```
GOAT/
├── backend/
│   ├── app/
│   │   ├── api/                     # FastAPI REST API endpoints
│   │   ├── core/                    # Configuration, settings, logging
│   │   ├── schemas/                 # Pydantic v2 data models & contracts
│   │   └── services/
│   │       ├── product_dna/         # Layer 2: Technical fact extraction
│   │       ├── orchestrator/        # Layer 3: LangGraph reasoning graph
│   │       │   ├── graph/           # 11 nodes, 16 edges, builder, tracing
│   │       │   └── tools/           # Controlled LangChain tools & guards
│   │       ├── knowledge/           # Layer 4: Segmented BIS knowledge base
│   │       ├── applicability/       # Layer 5: 10-step applicability engine
│   │       │   ├── version_registry.py  # Standard versions, supersessions & amendments
│   │       │   ├── relationship_graph.py# Normative & allied standard directed graph
│   │       │   └── conditional.py       # Typed condition evaluator (no guessing)
│   │       ├── rag/                 # Layer 6: Clause RAG & standard isolation
│   │       ├── gap_analysis/        # Layer 7: Mathematical gap engine
│   │       ├── laboratory/          # Layer 8: Evidence firewall & NABL trust
│   │       ├── passport/            # Layer 9: Compliance passport generator
│   │       └── evaluation/          # M24.6: 15-dimension benchmark harness
│   └── tests/                       # 905 unit, integration, and graph tests
├── frontend/
│   ├── src/                         # React 18 + TypeScript + Tailwind UI
│   ├── package.json                 # Frontend dependencies (Vite v6)
│   └── vite.config.ts               # Vite configuration
├── data/
│   ├── bis_dataset/                 # Authentic BIS standards & QCO records
│   └── evaluation/
│       ├── ground_truth/            # 10 verified evaluation cases (Golden locked)
│       └── results/                 # M23.1 & M24.6 benchmark results
├── docs/
│   ├── architecture/                # Milestone architecture documents (M24.0-M24.6)
│   └── assets/                      # High-resolution SVG diagrams and visuals
├── langgraph.json                   # LangGraph Studio configuration
├── start_studio.bat                 # LangGraph Studio launcher (UTF-8 enabled)
└── README.md                        # Primary project documentation
```

---

## 16. Project Roadmap

| Phase | Milestone | Scope / Objective | Status |
|:---|:---|:---|:---|
| **Phase 1** | **M1–M9** | Core 9-Layer Architecture (Input &rarr; Passport) | ✅ **APPROVED** |
| **Phase 2** | **M20–M22** | Gazette Data Ingestion & Real BIS Catalog | ✅ **APPROVED** |
| **Phase 3** | **M23–M23.1** | ML/DL Intelligence & Model Provenance Audit | ✅ **APPROVED** |
| **Phase 4** | **M24.1** | LangChain Model Adapter (Single LLM Invariant) | ✅ **APPROVED** |
| **Phase 5** | **M24.2** | LangGraph StateGraph Core Engine | ✅ **APPROVED** |
| **Phase 6** | **M24.3** | Controlled Agent Tools & Security Guards | ✅ **APPROVED** |
| **Phase 7** | **M24.4** | Compliance Authority Firewall (0.0% LLM Authority)| ✅ **APPROVED** |
| **Phase 8** | **M24.4.1** | Agent Specialization & Runtime Optimization | ✅ **APPROVED** |
| **Phase 9** | **M24.4.2** | Graph Topology & Runtime Path Verification | ✅ **APPROVED** |
| **Phase 10** | **M24.5** | LangSmith Observability & LangStudio Visualizer | ✅ **APPROVED** |
| **Phase 11** | **M24.6** | 15-Dimension Evaluation & Benchmarking Suite | ✅ **APPROVED** |
| **Phase 12** | **M25.0** | Deterministic BIS Applicability Intelligence & Validation | ✅ **APPROVED** |
| **Phase 13** | **M25.1** | Production Deployment & Multi-Standard Assembly Pipeline | 🔄 **READY TO BEGIN** |

---

## 17. Contribution Guide

We welcome contributions adhering to the project's strict engineering and compliance invariants:

### Cardinal Rules for Contributors
1. **Never Grant Compliance Authority to LLMs**: AI generates natural language explanations and summaries only. All compliance determinations must remain 100% computed by deterministic rule engines.
2. **Never Add Dual LLMs**: Exactly one structured LLM model is permitted across the entire platform.
3. **Preserve Graph Invariants**: The 11-node, 16-edge LangGraph topology must remain a strict Directed Acyclic Graph (DAG) with zero cycles.
4. **100% Test Pass Rate**: All 905 backend tests and frontend production builds must pass before submitting a Pull Request.

### Development Workflow
```bash
# 1. Create a feature branch
git checkout -b feat/your-feature-name

# 2. Make changes and verify test suite
py -3.14 -m pytest backend/tests -q

# 3. Commit adhering to Conventional Commits
git commit -m "feat(module): description of changes"

# 4. Open Pull Request with architecture rationale
```

---

## 18. Regulatory Disclaimer

> [!IMPORTANT]
> **Regulatory Disclaimer**:  
> GOAT is an evidence-first software intelligence platform designed to assist manufacturers, laboratories, and regulatory consultants with **pre-certification compliance analysis**.
> 
> - GOAT **does NOT grant official BIS certification** or issue ISI mark licenses.
> - Official licenses are issued exclusively by the **Bureau of Indian Standards (BIS)** in accordance with the Bureau of Indian Standards Act, 2016, and statutory verification by designated BIS officers.
> - LLM-generated explanations are analytical aids and do **not** constitute legal or regulatory opinions.
> - Binding compliance determinations strictly require authentic NABL-accredited test reports and statutory conformity inspection.

---

<div align="center">

**GOAT — BIS Compliance Compiler**  
Built for the Smart India Hackathon (Problem ID: 26107)  
*Crafted with precision by the GOAT Engineering Team*

</div>
