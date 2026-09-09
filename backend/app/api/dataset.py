"""M22 Read-Only Dataset & Evaluation APIs.

Provides transparent, audit-ready data trust endpoints:
- GET /api/v1/dataset/status
- GET /api/v1/dataset/manifest
- GET /api/v1/dataset/standards
- GET /api/v1/dataset/standards/{standard_number}
- GET /api/v1/dataset/standards/{standard_number}/provenance
- GET /api/v1/dataset/standards/{standard_number}/clauses
- GET /api/v1/dataset/evaluation/status
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.services.dataset.builder import get_dataset_repository
from backend.app.services.dataset.evaluator import DatasetEvaluator
from backend.app.services.dataset.models import StandardRecord, ClauseRecord, DatasetManifest

router = APIRouter(prefix="/dataset", tags=["BIS Dataset Governance & Evaluation"])


@router.get("/status", summary="Dataset Trust & Acquisition Status")
async def get_dataset_status():
    """Returns dataset health, acquisition status summary, and provenance integrity."""
    repo = get_dataset_repository()
    m = repo.manifest
    return {
        "dataset_name": m.dataset_name,
        "dataset_version": m.version,
        "sha256": m.sha256,
        "standards_count": m.standards_count,
        "qco_count": m.qco_count,
        "documents_count": m.documents_count,
        "verified_documents_count": m.verified_documents_count,
        "clause_count": m.clause_count,
        "requirement_count": m.requirement_count,
        "ground_truth_cases": m.ground_truth_cases,
        "approved_cases": m.approved_cases,
        "acquisition_pending_count": m.acquisition_pending_count,
        "governance_policy": {
            "authoritative_compliance_authority": "DETERMINISTIC_COMPLIANCE_ENGINE_ONLY",
            "llm_compliance_authority": 0.0,
            "ml_compliance_authority": 0.0,
            "scraping_policy": "STRICTLY_PROHIBITED",
            "full_document_procurement": "OFFICIAL_MANUAL_AUTHORIZED_PROCUREMENT_ONLY",
        },
        "limitations": m.limitations,
    }


@router.get("/manifest", response_model=DatasetManifest, summary="Dataset Cryptographic Manifest")
async def get_dataset_manifest():
    """Returns the official cryptographic dataset manifest with calculated counts."""
    repo = get_dataset_repository()
    return repo.manifest


@router.get("/standards", response_model=List[StandardRecord], summary="List Authentic BIS Standards")
async def list_dataset_standards(
    category: Optional[str] = Query(None, description="Filter by product category"),
    mandatory_only: bool = Query(False, description="Filter to mandatory QCO standards only"),
):
    """Retrieves all registered standards with explicit verification and acquisition states."""
    repo = get_dataset_repository()
    results = list(repo.standards.values())
    if category:
        results = [s for s in results if category.lower() in s.category.lower()]
    if mandatory_only:
        results = [s for s in results if s.qco_reference is not None]
    return results


@router.get("/standards/{standard_number}", response_model=StandardRecord, summary="Get Standard by Number or ID")
async def get_dataset_standard(standard_number: str):
    """Fetch single standard record by code or ID."""
    repo = get_dataset_repository()
    clean_query = standard_number.strip().lower()

    # Search by standard_id or standard_number
    for s in repo.standards.values():
        if s.standard_id.lower() == clean_query or clean_query in s.standard_number.lower():
            return s

    raise HTTPException(status_code=404, detail=f"Standard '{standard_number}' not found in official dataset.")


@router.get("/standards/{standard_number}/provenance", summary="Get Standard Legal Provenance & QCO")
async def get_standard_provenance(standard_number: str):
    """Fetch legal source, QCO notification, and document acquisition status for a standard."""
    repo = get_dataset_repository()
    clean_query = standard_number.strip().lower()

    target_std = None
    for s in repo.standards.values():
        if s.standard_id.lower() == clean_query or clean_query in s.standard_number.lower():
            target_std = s
            break

    if not target_std:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_number}' not found.")

    # Find associated QCO if mandatory
    associated_qco = None
    if target_std.qco_reference and target_std.qco_reference in repo.qcos:
        associated_qco = repo.qcos[target_std.qco_reference].model_dump()

    return {
        "standard_number": target_std.standard_number,
        "standard_id": target_std.standard_id,
        "verification_status": target_std.verification_status,
        "acquisition_status": target_std.acquisition_status,
        "source_authority": target_std.source_authority,
        "source_url": target_std.source_url,
        "document_hash": target_std.document_hash,
        "dataset_version": target_std.dataset_version,
        "license_access_notes": target_std.license_access_notes,
        "qco_order": associated_qco,
        "amendments": target_std.amendments,
        "provenance_chain": {
            "source_type": target_std.source_type,
            "retrieval_date": target_std.retrieval_date,
            "legal_source": target_std.metadata.get("legal_source"),
        },
    }


@router.get("/standards/{standard_number}/clauses", response_model=List[ClauseRecord], summary="Get Traceable Clauses")
async def get_standard_clauses(standard_number: str):
    """Retrieves verified, traceable clauses for a standard.
    
    If the standard is in ACQUISITION_PENDING state, returns empty list with explicit status.
    """
    repo = get_dataset_repository()
    clean_query = standard_number.strip().lower()

    target_clauses = [
        c for c in repo.clauses.values()
        if clean_query in c.standard_number.lower()
    ]
    return target_clauses


@router.get("/evaluation/status", summary="Ground-Truth Evaluation Benchmark Status")
async def get_evaluation_status():
    """Runs evaluation on APPROVED cases only and returns baseline metrics."""
    report = DatasetEvaluator.evaluate_baseline()
    return report
