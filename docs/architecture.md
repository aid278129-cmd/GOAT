# BIS Compliance Compiler - System Architecture

**Milestone**: M0 (Engineering Foundation)  
**Author**: Team Zyntrix (SIH 26107)

---

## 1. Core Architectural Pipeline

The system is structured as a **Modular Monolith** designed for auditable provenance and zero ungrounded LLM compliance declarations:

```
[User Specification / Datasheet]
              │
              ▼
    [Input Processing / Sanitization]
              │
              ▼
    [Product DNA Engine] ──(Extensible Schema + Provenance)
              │
              ▼
    [Deterministic Rule Engine] ──(APP-xxx Rules + QCO Schedules)
              │
              ▼
    [Clause-Level Retrieval] ──(PostgreSQL + pgvector Knowledge Base)
              │
              ▼
    [Citation Guard Trust Layer] ──(Claim-to-Evidence Cross Verification)
              │
              ▼
    [Compliance Passport & Evidence Graph]
```

---

## 2. Milestone M0 Implementation Scope

### [IMPLEMENTED IN M0]
- **API Core**: FastAPI async application with RequestLoggingMiddleware, X-Request-ID propagation, CORS, and centralized exception handling.
- **Data Models**: SQLAlchemy 2.0 async ORM base and entity schemas for `User`, `Product`, `ProductAttribute`, `Document`, `Standard`, `Clause`, `Requirement`, `StandardTest`, `Evidence`, `ComplianceResult`, `Laboratory`, and `Conversation`.
- **Validation**: Strict Pydantic v2 schemas for Product DNA, Provenance Citations, and Multi-State Enums.
- **Diagnostics**: Endpoints `/health`, `/health/db`, `/health/vector`, `/api/v1/system/info`.
- **Frontend**: React 18 / Vite shell with interactive diagnostic pinging and modular UI components.
- **Docker**: `docker-compose.yml` supporting PostgreSQL 16 + pgvector, backend, and frontend.

### [PLANNED FOR M1 / M2]
- **Clause Ingestion & Chunking (M1)**: PyMuPDF PDF parser extracting clause numbers, tables, and test requirements.
- **pgvector HNSW Indexing (M1)**: Semantic search on IS clauses.
- **Deterministic Rule Evaluator (M1)**: Auditable rules for QCO applicability.
- **Evidence Graph Canvas (M1)**: React Flow visualization connecting claims to clauses.
- **Live BIS Portal Sync & OCR (M2)**: Synchronization with Manakonline/e-BIS and Tesseract OCR.
