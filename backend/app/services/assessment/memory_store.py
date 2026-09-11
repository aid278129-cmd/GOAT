"""In-Memory and Standalone Store for Continuous Assessments.

Enables the Zyntrix BIS Compliance Compiler to run fully without external PostgreSQL dependency,
while maintaining full assessment creation, live evidence upload, snapshotting, and passport generation.
"""
from typing import Dict, List, Optional, Any
from backend.app.models.assessment import Assessment, AssessmentSnapshot
from backend.app.models.product import Product

# Global In-Memory Stores
ASSESSMENTS_STORE: Dict[str, Assessment] = {}
SNAPSHOTS_STORE: Dict[str, List[AssessmentSnapshot]] = {}
PRODUCTS_STORE: Dict[str, Product] = {}
EVIDENCE_STORE: Dict[str, List[Any]] = {}
LINKS_STORE: Dict[str, List[Any]] = {}


def save_assessment_mem(assessment: Assessment, product: Optional[Product] = None) -> None:
    ASSESSMENTS_STORE[assessment.id] = assessment
    if product:
        PRODUCTS_STORE[product.id] = product


def get_assessment_mem(assessment_id: str) -> Optional[Assessment]:
    return ASSESSMENTS_STORE.get(assessment_id)


def list_assessments_mem() -> List[Assessment]:
    return sorted(ASSESSMENTS_STORE.values(), key=lambda a: a.created_at, reverse=True)


def save_snapshot_mem(snapshot: AssessmentSnapshot) -> None:
    SNAPSHOTS_STORE.setdefault(snapshot.assessment_id, []).append(snapshot)


def get_snapshots_mem(assessment_id: str) -> List[AssessmentSnapshot]:
    return sorted(SNAPSHOTS_STORE.get(assessment_id, []), key=lambda s: s.version, reverse=True)


def save_evidence_mem(assessment_id: str, evidence_item: Any) -> None:
    EVIDENCE_STORE.setdefault(assessment_id, []).append(evidence_item)


def get_evidence_mem(assessment_id: str) -> List[Any]:
    return EVIDENCE_STORE.get(assessment_id, [])


def save_link_mem(assessment_id: str, link: Any) -> None:
    LINKS_STORE.setdefault(assessment_id, []).append(link)


def get_links_mem(assessment_id: str) -> List[Any]:
    return LINKS_STORE.get(assessment_id, [])


async def ensure_golden_demo_seeded() -> Assessment:
    """Pre-seeds the Golden SIH Demo Assessment if store is empty."""
    if ASSESSMENTS_STORE:
        return next(iter(ASSESSMENTS_STORE.values()))
    from backend.app.services.assessment.golden_demo import GOLDEN_DEMO_PRODUCT
    from backend.app.schemas.assessment import AssessmentCreateRequest
    from backend.app.services.assessment.service import AssessmentService
    req = AssessmentCreateRequest(**GOLDEN_DEMO_PRODUCT)
    asm = await AssessmentService.create_assessment(None, req)
    return asm


async def reset_golden_demo_mem() -> Assessment:
    """Explicitly resets or recreates the Golden SIH Demo Assessment."""
    from backend.app.services.assessment.golden_demo import GOLDEN_DEMO_PRODUCT
    from backend.app.schemas.assessment import AssessmentCreateRequest
    from backend.app.services.assessment.service import AssessmentService
    EVIDENCE_STORE.clear()
    LINKS_STORE.clear()
    req = AssessmentCreateRequest(**GOLDEN_DEMO_PRODUCT)
    asm = await AssessmentService.create_assessment(None, req)
    return asm


def clear_assessments_mem() -> None:
    """Clear all in-memory assessments and associated stores."""
    ASSESSMENTS_STORE.clear()
    SNAPSHOTS_STORE.clear()
    PRODUCTS_STORE.clear()
    EVIDENCE_STORE.clear()
    LINKS_STORE.clear()

