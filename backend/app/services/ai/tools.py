"""Authoritative Tools for Zyntrix Phase 4A AI Engineering Copilot.

Tools are strictly job-scoped, multi-tenant isolated, and read-only.
Mutations generate formal AIActionProposals requiring human-in-the-loop authorization.
Direct statutory mutations (evidence acceptance, review approval, attestation issuance,
finding resolution) are blocked with AIAuthorityViolationError.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import json

from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_standards import JobStandard, JobRequirement
from backend.app.models.persistent_assessment import AssessmentRun, PersistentAssessmentResult, ComplianceFinding
from backend.app.models.persistent_review import ReviewItem, HumanAttestation
from backend.app.models.persistent_cad import CADModel, CADMeasurement, CADSnapshot
from backend.app.models.persistent_audit import AuditEvent
from backend.app.models.persistent_ai import AIActionProposal, AIToolCall
from backend.app.services.ai.firewall import AIAuthorityViolationError, ForbiddenAIAction


class AIToolRegistry:
    """Registry of job-scoped, tenant-isolated tools."""

    @classmethod
    async def get_job(cls, db: AsyncSession, org_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(ComplianceJob).where(ComplianceJob.id == job_id, ComplianceJob.organization_id == org_id)
        res = await db.execute(stmt)
        job = res.scalars().first()
        if not job:
            return None
        return {
            "id": job.id,
            "title": job.title,
            "job_number": job.job_number,
            "status": job.status,
            "target_standard": getattr(job, "target_standard", (job.metadata_json or {}).get("target_standard")),
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }

    @classmethod
    async def get_product_dna(cls, db: AsyncSession, org_id: str, job_id: str) -> List[Dict[str, Any]]:
        stmt = select(PersistentDNA).where(PersistentDNA.job_id == job_id, PersistentDNA.organization_id == org_id)
        res = await db.execute(stmt)
        items = res.scalars().all()
        return [
            {
                "id": d.id,
                "parameter": d.parameter,
                "value": d.value,
                "unit": d.unit,
                "status": d.status,
                "source_evidence_id": d.source_evidence_id,
                "source_file_name": d.source_file_name,
                "metadata": d.metadata_json or {},
            }
            for d in items
        ]

    @classmethod
    async def get_evidence(cls, db: AsyncSession, org_id: str, job_id: str, evidence_id: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = select(PersistentEvidence).where(PersistentEvidence.job_id == job_id, PersistentEvidence.organization_id == org_id)
        if evidence_id:
            stmt = stmt.where(PersistentEvidence.id == evidence_id)
        res = await db.execute(stmt)
        items = res.scalars().all()
        return [
            {
                "id": ev.id,
                "file_name": ev.file_name,
                "file_type": ev.file_type,
                "sha256": ev.sha256_hash,
                "acceptance_status": ev.acceptance_status,
                "processing_status": ev.processing_status,
                "extracted_parameters": (ev.extracted_data or {}).get("parameters", []) if isinstance(ev.extracted_data, dict) else (ev.extracted_data or []),
            }
            for ev in items
        ]

    @classmethod
    async def get_evidence_content(cls, db: AsyncSession, org_id: str, job_id: str, evidence_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(PersistentEvidence).where(
            PersistentEvidence.id == evidence_id,
            PersistentEvidence.job_id == job_id,
            PersistentEvidence.organization_id == org_id,
        )
        res = await db.execute(stmt)
        ev = res.scalars().first()
        if not ev:
            return None
        # Returns parsed metadata and summary (raw binary content is avoided)
        return {
            "id": ev.id,
            "file_name": ev.file_name,
            "acceptance_status": ev.acceptance_status,
            "sha256": ev.sha256_hash,
            "metadata": ev.metadata_json or {},
            "extracted_parameters": (ev.extracted_data or {}).get("parameters", []) if isinstance(ev.extracted_data, dict) else (ev.extracted_data or []),
        }

    @classmethod
    async def get_cad_model(cls, db: AsyncSession, org_id: str, job_id: str, cad_model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = select(CADModel).where(CADModel.job_id == job_id, CADModel.organization_id == org_id)
        if cad_model_id:
            stmt = stmt.where(CADModel.id == cad_model_id)
        res = await db.execute(stmt)
        models = res.scalars().all()
        return [
            {
                "id": m.id,
                "evidence_id": m.evidence_id,
                "file_name": m.file_name,
                "model_hash": m.model_hash,
                "processing_status": m.processing_status,
                "bounding_box": m.bounding_box or {},
                "volume_mm3": m.volume_mm3,
                "surface_area_mm2": m.surface_area_mm2,
            }
            for m in models
        ]

    @classmethod
    async def get_cad_measurements(cls, db: AsyncSession, org_id: str, job_id: str, cad_model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = (
            select(CADMeasurement)
            .join(CADModel, CADMeasurement.cad_model_id == CADModel.id)
            .where(CADModel.job_id == job_id, CADModel.organization_id == org_id)
        )
        if cad_model_id:
            stmt = stmt.where(CADMeasurement.cad_model_id == cad_model_id)
        res = await db.execute(stmt)
        measurements = res.scalars().all()
        return [
            {
                "id": m.id,
                "cad_model_id": m.cad_model_id,
                "measurement_type": m.measurement_type,
                "measured_value": m.measured_value,
                "unit": m.unit,
                "feature_reference": m.feature_reference,
                "metadata": m.metadata_json or {},
            }
            for m in measurements
        ]

    @classmethod
    async def get_standard(cls, db: AsyncSession, org_id: str, job_id: str) -> List[Dict[str, Any]]:
        stmt = select(JobStandard).where(JobStandard.job_id == job_id, JobStandard.organization_id == org_id)
        res = await db.execute(stmt)
        stds = res.scalars().all()
        return [
            {
                "id": s.id,
                "standard_identifier": s.standard_identifier,
                "revision_year": s.revision_year,
                "title": s.title,
                "is_active_assessment_basis": s.is_active_assessment_basis,
            }
            for s in stds
        ]

    @classmethod
    async def get_requirements(cls, db: AsyncSession, org_id: str, job_id: str, standard_id: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = select(JobRequirement).where(JobRequirement.job_id == job_id)
        if standard_id:
            stmt = stmt.where(JobRequirement.standard_id == standard_id)
        res = await db.execute(stmt)
        reqs = res.scalars().all()
        return [
            {
                "id": r.id,
                "requirement_id": r.requirement_id,
                "clause_number": r.clause_number or r.clause_reference,
                "clause_reference": r.clause_reference or r.clause_number,
                "section": r.section,
                "requirement_text": r.requirement_text or r.description,
                "requirement_type": r.requirement_type,
                "parameter_key": r.parameter_key,
                "expected_unit": r.expected_unit or r.unit,
                "comparison_operator": r.comparison_operator,
                "threshold_min": r.threshold_min or r.limit_min,
                "threshold_max": r.threshold_max or r.limit_max,
            }
            for r in reqs
        ]

    @classmethod
    async def get_assessment(cls, db: AsyncSession, org_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        stmt = (
            select(AssessmentRun)
            .where(AssessmentRun.job_id == job_id, AssessmentRun.organization_id == org_id)
            .order_by(desc(AssessmentRun.created_at))
        )
        res = await db.execute(stmt)
        run = res.scalars().first()
        if not run:
            return None

        # Fetch results
        r_stmt = select(PersistentAssessmentResult).where(PersistentAssessmentResult.assessment_run_id == run.id)
        r_res = await db.execute(r_stmt)
        results = r_res.scalars().all()

        return {
            "id": run.id,
            "engine_version": run.engine_version,
            "summary": run.summary or {},
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "results": [
                {
                    "id": res_item.id,
                    "requirement_id": res_item.requirement_id,
                    "clause_number": res_item.clause_number,
                    "parameter_key": res_item.parameter_key,
                    "assessment_state": res_item.assessment_state,
                    "observed_value": res_item.observed_value,
                    "observed_unit": res_item.observed_unit,
                    "threshold_min": res_item.threshold_min,
                    "threshold_max": res_item.threshold_max,
                    "comparison_operator": res_item.comparison_operator,
                    "evaluation_expression": res_item.evaluation_expression,
                    "explanation": res_item.explanation,
                    "trace_details": res_item.trace_details or {},
                }
                for res_item in results
            ],
        }

    @classmethod
    async def get_findings(cls, db: AsyncSession, org_id: str, job_id: str) -> List[Dict[str, Any]]:
        stmt = select(ComplianceFinding).where(ComplianceFinding.job_id == job_id, ComplianceFinding.organization_id == org_id)
        res = await db.execute(stmt)
        findings = res.scalars().all()
        return [
            {
                "id": f.id,
                "requirement_id": f.requirement_id,
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "observed_value": f.observed_value,
                "expected_value": f.expected_value,
                "status": f.status,
            }
            for f in findings
        ]

    @classmethod
    async def get_reviews(cls, db: AsyncSession, org_id: str, job_id: str) -> List[Dict[str, Any]]:
        stmt = select(ReviewItem).where(ReviewItem.job_id == job_id, ReviewItem.organization_id == org_id)
        res = await db.execute(stmt)
        items = res.scalars().all()
        return [
            {
                "id": r.id,
                "status": r.status,
                "review_decision": r.review_decision,
                "requirement_id": r.requirement_id,
                "finding_id": r.finding_id,
                "review_notes": r.review_notes,
            }
            for r in items
        ]

    @classmethod
    async def get_attestations(cls, db: AsyncSession, org_id: str, job_id: str) -> List[Dict[str, Any]]:
        stmt = select(HumanAttestation).where(HumanAttestation.job_id == job_id, HumanAttestation.organization_id == org_id)
        res = await db.execute(stmt)
        attestations = res.scalars().all()
        return [
            {
                "id": a.id,
                "attestation_type": a.attestation_type,
                "status": a.status,
                "declaration_text": a.declaration_text,
                "attestor_name": a.attestor_name,
                "attested_at": a.attested_at.isoformat() if a.attested_at else None,
            }
            for a in attestations
        ]

    @classmethod
    async def get_audit_events(cls, db: AsyncSession, org_id: str, job_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.job_id == job_id, AuditEvent.organization_id == org_id)
            .order_by(desc(AuditEvent.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        events = res.scalars().all()
        return [
            {
                "id": e.id,
                "action": e.action,
                "actor_email": e.actor_email,
                "actor_role": e.actor_role,
                "target_type": e.target_type,
                "target_id": e.target_id,
                "details": e.details or {},
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]

    # -------------------------------------------------------------------------
    # PROPOSAL TOOLS (HUMAN-GATED)
    # -------------------------------------------------------------------------

    @classmethod
    async def propose_review_request(
        cls,
        db: AsyncSession,
        org_id: str,
        job_id: str,
        requirement_id: str,
        reason: str,
    ) -> AIActionProposal:
        proposal = AIActionProposal(
            organization_id=org_id,
            job_id=job_id,
            action_type="CREATE_REVIEW_REQUEST",
            target_id=requirement_id,
            proposal_payload={"requirement_id": requirement_id, "action": "CREATE_REVIEW_ITEM"},
            reason=reason,
            status="PROPOSED",
            created_by_agent="AI_COMPLIANCE_ANALYST",
        )
        db.add(proposal)
        await db.flush()
        return proposal

    @classmethod
    async def propose_dna_candidate(
        cls,
        db: AsyncSession,
        org_id: str,
        job_id: str,
        parameter: str,
        value: str,
        unit: str,
        evidence_id: str,
        reason: str = "Extracted candidate parameter from evidence.",
    ) -> AIActionProposal:
        proposal = AIActionProposal(
            organization_id=org_id,
            job_id=job_id,
            action_type="CREATE_DNA_CANDIDATE",
            target_id=evidence_id,
            proposal_payload={
                "parameter": parameter,
                "value": str(value),
                "unit": unit,
                "source_evidence_id": evidence_id,
                "status": "AI_SUGGESTED",
            },
            reason=reason,
            status="PROPOSED",
            created_by_agent="AI_PRODUCT_DNA_ANALYST",
        )
        db.add(proposal)
        await db.flush()
        return proposal

    @classmethod
    async def propose_requirement_mapping(
        cls,
        db: AsyncSession,
        org_id: str,
        job_id: str,
        requirement_id: str,
        parameter_key: str,
        reason: str = "Suggested mapping between requirement and DNA parameter.",
    ) -> AIActionProposal:
        proposal = AIActionProposal(
            organization_id=org_id,
            job_id=job_id,
            action_type="MAP_REQUIREMENT",
            target_id=requirement_id,
            proposal_payload={
                "requirement_id": requirement_id,
                "parameter_key": parameter_key,
            },
            reason=reason,
            status="PROPOSED",
            created_by_agent="AI_STANDARDS_ANALYST",
        )
        db.add(proposal)
        await db.flush()
        return proposal

    # -------------------------------------------------------------------------
    # FORBIDDEN MUTATION TRAP
    # -------------------------------------------------------------------------

    @classmethod
    def execute_forbidden_action(cls, action_name: str) -> None:
        """Always blocks autonomous mutations."""
        raise AIAuthorityViolationError(
            action=action_name,
            details="AI cannot perform direct statutory mutations without authorized human confirmation.",
        )
