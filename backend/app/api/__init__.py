from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.compliance_jobs import router as jobs_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.product_dna import router as dna_router
from backend.app.api.standards_intelligence import router as standards_router
from backend.app.api.audit import router as audit_router
from backend.app.api.assessment_engine import router as assessment_engine_router
from backend.app.api.review_workflow import router as review_workflow_router
from backend.app.api.cad import router as cad_router
from backend.app.api.ai_copilot import router as ai_router

# Reference services
from backend.app.api.system import router as system_router
from backend.app.api.knowledge import router as knowledge_router
from backend.app.api.products import router as products_router
from backend.app.api.assessments import router as assessments_router
from backend.app.api.ingest import router as ingest_router
from backend.app.api.applicability import router as applicability_router
from backend.app.api.rag import router as rag_router
from backend.app.api.gap_analysis import router as gap_analysis_router
from backend.app.api.citation_guard import citation_guard_router
from backend.app.api.passport import passport_router
from backend.app.api.dataset import router as dataset_router

api_router = APIRouter()

# Phase 1 & 2A Authoritative Core Routers
api_router.include_router(auth_router)
api_router.include_router(jobs_router)
api_router.include_router(evidence_router)
api_router.include_router(dna_router)
api_router.include_router(standards_router)
api_router.include_router(audit_router)
api_router.include_router(assessment_engine_router)
api_router.include_router(review_workflow_router)
api_router.include_router(cad_router)
api_router.include_router(ai_router)

# Layer 2-5 Reference Subsystems
api_router.include_router(system_router)
api_router.include_router(knowledge_router)
api_router.include_router(products_router)
api_router.include_router(assessments_router)
api_router.include_router(ingest_router)
api_router.include_router(applicability_router)
api_router.include_router(rag_router)
api_router.include_router(gap_analysis_router)
api_router.include_router(citation_guard_router)
api_router.include_router(passport_router)
api_router.include_router(dataset_router)

__all__ = [
    "api_router",
    "health_router",
    "auth_router",
    "jobs_router",
    "evidence_router",
    "dna_router",
    "standards_router",
    "audit_router",
    "assessment_engine_router",
    "review_workflow_router",
    "cad_router",
    "knowledge_router",
    "products_router",
    "assessments_router",
    "ingest_router",
    "applicability_router",
    "rag_router",
    "gap_analysis_router",
    "citation_guard_router",
    "passport_router",
]
