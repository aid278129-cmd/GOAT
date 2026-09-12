# M25.1 BIS Source Governance & Regulatory Dependency Engine

## Overview
This document outlines the architecture and implementation details for Milestone M25.1, focusing on establishing a traceable, versioned, provenance-first regulatory source model for the BIS (Bureau of Indian Standards) Applicability Engine.

## Phases Implemented

### PHASE A & B — Canonical Regulatory Source Model & Audit
- Validated the existing `StandardRevisionInfo` model in `version_registry.py`.
- Ensured deterministic source tracking directly from the Bureau of Indian Standards and official gazettes.
- Maintained a static, authoritative catalog.

### PHASE C — Standard Lifecycle
- Implemented states: `ACTIVE`, `SUPERSEDED`, `WITHDRAWN`, `ACQUISITION_PENDING`.
- Core invariant: Withdrawn/superseded standards can never be silently substituted as current applicable standards.

### PHASE D — Amendment Chain
- Formal tracking of amendments applied to a standard (e.g., "Amendment No. 1 (August 2023)").
- Represented in the standard's metadata and relationships.

### PHASE E — Revision / Supersession Graph
- Modeled inter-standard relationships via `NormativeRelationType` in `relationship_graph.py`.
- Enables tracking `SUPERSEDES` and `SUPERSEDED_BY` relationships, maintaining a directed graph.
- Tracks `PRIMARY_STANDARD`, `NORMATIVE_REFERENCE`, and `RELATED_STANDARD`.

### PHASE F — QCO / Gazette Governance
- Explicit flagging of `MANDATORY_QCO` vs `VOLUNTARY`.
- Links to official Gazette Order references, preserving legal provenance.

### PHASE G — Knowledge Snapshots
- Implemented `SnapshotManager` for immutable dataset snapshots.
- Cryptographic hashing (SHA-256) of standards, QCOs, and clauses.
- Tamper-evident verification and snapshot diffing to track changes between versions.

### PHASE H — Source Conflicts
- Detection of conflicting rules where product claims contradict the standard scope.
- Resolution via `EXPERT_REVIEW_REQUIRED`.

### PHASE I — Staleness
- Ensures that claims made against outdated standards correctly flag them as superseded.
- Replaces stale claims with the active counterpart or denies them based on strict catalog rules.

### PHASE J — User Claim Isolation
- Isolates user-provided standard numbers from the authoritative ground truth.
- Fabricated or hallucinated standards are outright rejected by the system.

### PHASE K — Audit Trail
- Utilizes `AuthorityAuditLogger` to record authoritative compliance decisions in a tamper-evident manner.
- Ensures all decisions are traced with unique correlation IDs and timestamps.

### PHASE L, M, N — Testing, Evaluation, Documentation
- Suite of 60 deterministic tests in `test_m25_1_source_governance.py`.
- Documentation created (this file).

## Conclusion
The regulatory dependency engine robustly integrates lifecycle governance with deterministic rule matching, preserving 0% LLM authority and 100% verifiability.
