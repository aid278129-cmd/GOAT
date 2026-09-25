"""Layer 9: Output Layer & Compliance Passport REST API Router.

Exposes endpoints to compile, verify integrity, export, and download
the official Evidence-Backed Pre-Certification Compliance Assessment.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from backend.app.services.passport.models import (
    ProductionCompliancePassport,
    OutputIntegrityGateResult,
    MSMEActionCenter,
    PASSPORT_TITLE,
    PROHIBITED_LABELS,
)
from backend.app.services.passport.compiler import passport_compiler
from backend.app.services.passport.formatter import report_formatter
from backend.app.services.assessment.service import AssessmentService

passport_router = APIRouter(prefix="/passport", tags=["Layer 9 - Output & Compliance Passport"])


class CompilePassportPayload(BaseModel):
    assessment_id: str
    assessment_number: str
    product_name: str
    category: str
    applicability: List[Dict[str, Any]]
    requirements: List[Dict[str, Any]]
    clarifications: Optional[List[Dict[str, Any]]] = None
    testing_roadmap: Optional[List[Dict[str, Any]]] = None
    laboratories: Optional[List[Dict[str, Any]]] = None
    evidence_items: Optional[List[Dict[str, Any]]] = None
    product_dna_version: str = "v1.0"
    knowledge_version: str = "v1.2.0-gazette-verified"
    output_version: int = 1
    strict_gate: bool = False


@passport_router.post("/compile", response_model=ProductionCompliancePassport)
def compile_passport(payload: CompilePassportPayload) -> ProductionCompliancePassport:
    """Compile Layer 9 Production Compliance Passport with Output Integrity Gate verification."""
    passport = passport_compiler.compile_compliance_passport(
        assessment_id=payload.assessment_id,
        assessment_number=payload.assessment_number,
        product_name=payload.product_name,
        category=payload.category,
        applicability=payload.applicability,
        requirements=payload.requirements,
        clarifications=payload.clarifications,
        testing_roadmap=payload.testing_roadmap,
        laboratories=payload.laboratories,
        evidence_items=payload.evidence_items,
        product_dna_version=payload.product_dna_version,
        knowledge_version=payload.knowledge_version,
        output_version=payload.output_version,
        strict_gate=payload.strict_gate,
    )
    if payload.strict_gate and not passport.integrity_gate.can_finalize:
        raise HTTPException(
            status_code=400,
            detail=f"Assessment cannot be finalized because required verification is incomplete: {', '.join(passport.integrity_gate.blocked_reasons)}",
        )
    return passport


@passport_router.post("/integrity-check", response_model=OutputIntegrityGateResult)
def check_integrity(payload: CompilePassportPayload) -> OutputIntegrityGateResult:
    """Pre-flight check to verify if the assessment can be finalized."""
    return passport_compiler.check_output_integrity(
        requirements=payload.requirements,
        applicability=payload.applicability,
        clarifications=payload.clarifications,
    )


@passport_router.post("/download-html")
def download_html_report(payload: CompilePassportPayload) -> Response:
    """Generate self-contained print-ready HTML report for downloading."""
    passport = passport_compiler.compile_compliance_passport(
        assessment_id=payload.assessment_id,
        assessment_number=payload.assessment_number,
        product_name=payload.product_name,
        category=payload.category,
        applicability=payload.applicability,
        requirements=payload.requirements,
        clarifications=payload.clarifications,
        testing_roadmap=payload.testing_roadmap,
        laboratories=payload.laboratories,
        evidence_items=payload.evidence_items,
        product_dna_version=payload.product_dna_version,
        knowledge_version=payload.knowledge_version,
        output_version=payload.output_version,
    )
    html_content = report_formatter.format_html_report(passport)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=Compliance_Passport_{passport.assessment_number}.html"},
    )


@passport_router.get("/invariants")
def get_layer9_invariants() -> Dict[str, Any]:
    """Retrieve Layer 9 cardinal rules, prohibited terminology, and title requirements."""
    return {
        "layer": "LAYER_9_OUTPUT_AND_COMPLIANCE_PASSPORT",
        "document_title": PASSPORT_TITLE,
        "prohibited_labels": PROHIBITED_LABELS,
        "invariants": [
            "LAYER 9 NEVER CREATES A NEW REGULATORY FACT.",
            "LAYER 9 ONLY PRESENTS VERIFIED UPSTREAM RESULTS.",
            "NO VERIFIED SOURCE -> NO REGULATORY CLAIM",
            "NO VERIFIED EVIDENCE -> NO SATISFIED",
            "INVALID CITATION -> NO FINAL CLAIM",
            "CONFLICT -> EXPERT REVIEW",
            "UNKNOWN -> UNKNOWN",
            "LLM COMPLIANCE AUTHORITY = 0.0%",
            "COMPLIANCE PASSPORT != BIS CERTIFICATION",
        ],
        "compliance_score_gaming": "PROHIBITED (Honest Counts Only)",
    }


class GenerateEvidenceBackedPassportPayload(BaseModel):
    product_id: str
    product_name: str
    category: str
    target_standard: str
    gap_result: Any
    evidence_records: List[Any] = Field(default_factory=list)
    product_dna: Optional[Dict[str, Any]] = None
    source_snapshot_version: str = "v1.2.0-gazette-verified"
    knowledge_version: str = "v1.2.0-gazette-verified"
    ruleset_version: str = "2026.03-gazette"
    assessment_id: Optional[str] = None
    assessment_number: Optional[str] = None
    output_version: int = 1
    strict_gate: bool = False


@passport_router.post("/generate-evidence-backed")
def generate_evidence_backed_passport_endpoint(payload: GenerateEvidenceBackedPassportPayload) -> Dict[str, Any]:
    """Milestone M26.3: Generate Evidence-Backed Compliance Passport directly from verified results."""
    from backend.app.services.compliance.passport_generator_service import compliance_passport_generator
    from backend.app.schemas.compliance import DeterministicGapAggregationResult
    from backend.app.schemas.product_evidence import ProductEvidenceRecord

    gap_res = (
        DeterministicGapAggregationResult(**payload.gap_result)
        if isinstance(payload.gap_result, dict)
        else payload.gap_result
    )
    ev_records = [
        (ProductEvidenceRecord(**e) if isinstance(e, dict) else e)
        for e in payload.evidence_records
    ]

    passport = compliance_passport_generator.generate_compliance_passport(
        product_id=payload.product_id,
        product_name=payload.product_name,
        category=payload.category,
        target_standard=payload.target_standard,
        gap_result=gap_res,
        evidence_records=ev_records,
        product_dna=payload.product_dna,
        source_snapshot_version=payload.source_snapshot_version,
        knowledge_version=payload.knowledge_version,
        ruleset_version=payload.ruleset_version,
        assessment_id=payload.assessment_id,
        assessment_number=payload.assessment_number,
        output_version=payload.output_version,
        strict_gate=payload.strict_gate,
    )
    return passport.model_dump(mode="json")
