from fastapi import APIRouter
from backend.app.api.health import router as health_router
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
