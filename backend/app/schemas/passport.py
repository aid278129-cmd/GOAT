from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.compliance import ComplianceStatus


class CompliancePassportCard(BaseModel):
    """Auditable, tamper-evident digital Compliance Passport."""

    passport_id: str
    product_id: str
    product_name: str
    category: str
    standard_number: str
    overall_status: ComplianceStatus
    qco_applicable: bool
    scheme: str
    issuance_date: datetime
    evidence_items_count: int
    provenance_hash: Optional[str] = None
    readiness_score_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    certification_stage: str = "PRE_EVALUATION"  # PRE_EVALUATION | LAB_TESTING | AUDIT_READY | CERTIFIED
