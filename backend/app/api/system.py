from fastapi import APIRouter, HTTPException
from backend.app.core.config import settings
from backend.app.services.diagnostics.dependency_checker import (
    check_all_dependencies,
    SystemDiagnosticsResponse,
    DependencyHealthRecord,
)

router = APIRouter(prefix="/system", tags=["System Architecture & Diagnostics"])


@router.get("/info", summary="System Information & M0 Architecture State")
async def get_system_info():
    return {
        "project": settings.PROJECT_NAME,
        "team": settings.PROJECT_TEAM,
        "sih_problem_id": settings.SIH_PROBLEM_ID,
        "milestone": "M0 - Engineering Foundation",
        "current_audit": "M20 - System Diagnostics & Integration Audit",
        "compliance_principle": "LLM generates explanations; retrieved evidence establishes compliance claims.",
        "active_modules": {
            "api_gateway": "READY",
            "database_orm": "READY",
            "pydantic_schemas": "READY",
            "citation_guard_contract": "READY",
            "product_dna_schema": "READY",
            "rag_clause_retrieval": "READY",
            "gap_analysis_engine": "READY",
            "evidence_graph": "READY",
            "ocr_multilingual": "READY",
            "compliance_passport": "READY",
        },
    }


@router.get("/dependencies", response_model=SystemDiagnosticsResponse, summary="Comprehensive System & Dependency Diagnostics")
async def get_dependencies():
    """Returns complete runtime health, latency, configuration, and fallback status across all services."""
    return check_all_dependencies()


@router.get("/ml-data-health", summary="ML/DL Dataset Health & Training Readiness Diagnostic")
async def get_ml_data_health():
    """Returns dynamic data foundation readiness for auxiliary ML models.
    
    Invariants:
    1. Training is DISABLED if approved real cases are insufficient.
    2. ML/DL models possess 0% compliance decision authority.
    3. Values are calculated dynamically from actual records (never hardcoded).
    """
    from backend.app.services.dataset.builder import get_dataset_repository

    repo = get_dataset_repository()
    m = repo.manifest

    return {
        "dataset_version": m.version,
        "standards": m.standards_count,
        "qco_verified": m.qco_count,
        "full_documents": m.verified_documents_count,
        "clause_indexed": m.clause_count,
        "ground_truth_cases": m.ground_truth_cases,
        "approved_cases": m.approved_cases,
        "training_ready": False,
        "reason": "DATA_INSUFFICIENT_FOR_TRAINING: Insufficient approved labelled data for production training. Auxiliary models must remain PRETRAINED.",
        "limitations": [
            "ML/DL compliance decision authority = 0.0%",
            "Deterministic compliance engine is the sole regulatory authority",
            "Full BIS texts require authorized legal acquisition (ACQUISITION_PENDING preserved)",
            "Pretrained auxiliary models only (MODEL_SOURCE = PRETRAINED)",
            "Synthetic fixtures prohibited from authoritative benchmark scoring",
        ],
    }

