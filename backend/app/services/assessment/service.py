"""Assessment Service orchestrating the unified MSME assessment lifecycle.

Unifies:
Product Input -> Product DNA -> Clarification -> Applicability -> Hybrid Retrieval
-> Requirements -> Evidence -> Gap Analysis -> Testing Roadmap -> Labs
-> Evidence Graph -> Compliance Passport -> Point-in-time Snapshots.
"""
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.assessment import Assessment, AssessmentSnapshot, AssessmentStatus
from backend.app.models.product import Product
from backend.app.models.decision_record import DecisionRecord
from backend.app.models.requirement_evidence_link import RequirementEvidenceLink
from backend.app.core.logging import logger
from backend.app.services.assessment.memory_store import (
    save_assessment_mem,
    get_assessment_mem,
    save_snapshot_mem,
    PRODUCTS_STORE,
    save_evidence_mem,
    get_evidence_mem,
    save_link_mem,
    get_links_mem,
)
from backend.app.schemas.product_dna import ProductDNACore, ClarificationRequirement
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.schemas.assessment import (
    AssessmentCreateRequest,
    AssessmentSummaryResponse,
    CompliancePassport,
    PassportTrustSection,
    PassportSourceIndexItem,
    AssessmentDetailResponse,
)
from backend.app.services.product_dna.extractor import extract_product_dna_from_text
from backend.app.services.clarification.engine import (
    detect_missing_attributes,
    apply_clarification_response,
)
from backend.app.services.applicability.engine import (
    determine_applicability,
    ApplicabilityDecision,
)
from backend.app.services.gap_analysis.engine import (
    evaluate_compliance_gaps,
    StandardComplianceEvaluation,
)
from backend.app.services.gap_analysis.graph_builder import (
    build_evidence_graph,
    EvidenceGraphData,
)
from backend.app.services.gap_analysis.evidence_extractor import (
    extract_evidence_from_snippet,
    detect_evidence_conflicts,
    StructuredEvidence,
)
from backend.app.services.gap_analysis.evidence_matcher import match_evidence_to_requirements
from backend.app.services.gap_analysis.evidence_gate import get_evidence_spec_for_requirement
from backend.app.services.laboratory.test_roadmap import (
    compile_testing_roadmap,
    get_verified_laboratories,
    TestRoadmapItem,
    RecognizedLaboratory,
)


class AssessmentService:
    """Core service managing assessment execution, state aggregation, snapshotting, and passport generation."""

    @staticmethod
    def _build_requirements_catalog(authoritative_mode: bool) -> List[Dict[str, Any]]:
        if authoritative_mode:
            return [
                {
                    "id": "req-auth-pending",
                    "clause_number": "PENDING",
                    "clause_title": "Official Standard Specification Acquisition Pending",
                    "code": "AUTHORITATIVE_CLAUSE_PENDING",
                    "requirement_type": "REGULATORY_GOVERNANCE",
                    "description": "Full official technical standard specification document for IS 17526:2021 is pending acquisition from authorized Bureau of Indian Standards procurement channel. Official Gazette QCO Order 2023 and BIS Product Manual PM/IS 17526/1 are verified.",
                    "measurable_condition": "Verified official publication from Bureau of Indian Standards",
                }
            ]
        return [
            {
                "id": "req-4-2-1",
                "clause_number": "4.2.1",
                "clause_title": "Stainless Steel Parts (Development Test Fixture)",
                "code": "REQ-MAT-304",
                "requirement_type": "MATERIAL",
                "description": "All metallic parts in direct contact with food shall be manufactured from Stainless Steel Grade 304 or superior.",
                "measurable_condition": "Grade 304 of IS 6911",
            },
            {
                "id": "req-5-2",
                "clause_number": "5.2",
                "clause_title": "Leakage Test (Development Test Fixture)",
                "code": "REQ-PERF-LEAK",
                "requirement_type": "PERFORMANCE",
                "description": "Container filled to capacity and inverted for 10 minutes shall show zero leakage or moisture seepage.",
                "measurable_condition": "Inverted 10 minutes, zero leakage",
            },
            {
                "id": "req-5-4",
                "clause_number": "5.4",
                "clause_title": "Thermal Performance Test (Development Test Fixture)",
                "code": "REQ-PERF-THERM",
                "requirement_type": "PERFORMANCE",
                "description": "Initial hot water at 95 deg C sealed at room ambient; after 6 hours temperature shall not be less than 60 deg C.",
                "measurable_condition": ">= 60 deg C after 6 hours",
            },
            {
                "id": "req-7-1",
                "clause_number": "7.1",
                "clause_title": "Marking Requirements (Development Test Fixture)",
                "code": "REQ-MARK-ISI",
                "requirement_type": "MARKING",
                "description": "Legibly marked with manufacturer trademark, nominal capacity, and the BIS Standard Mark (ISI Mark).",
                "measurable_condition": "Standard Mark (ISI Mark) + capacity",
            },
        ]

    @classmethod
    async def create_assessment(
        cls,
        db: AsyncSession,
        req: AssessmentCreateRequest,
    ) -> Assessment:
        """Create a new assessment with initial product DNA extraction and applicability calculation."""
        product_id = f"PROD-{uuid.uuid4().hex[:8].upper()}"
        assessment_id = f"ASM-{uuid.uuid4().hex[:8].upper()}"
        assessment_num = f"ASM-2026-{uuid.uuid4().hex[:6].upper()}"

        # 1. Extract Product DNA
        dna = extract_product_dna_from_text(req.description)
        dna.product_name = req.product_name
        if req.category:
            dna.category = req.category
        clarifications = detect_missing_attributes(dna)
        dna.pending_clarifications = clarifications

        # 2. Determine Applicability
        applicability = determine_applicability(dna, authoritative_only=req.authoritative_mode)

        # 3. Evaluate initial compliance gaps
        compliance_eval: Optional[StandardComplianceEvaluation] = None
        standard_number = "IS 17526:2021"
        standard_title = "Domestic Stainless Steel Vacuum Flask/Bottle"
        if applicability:
            standard_number = applicability[0].standard_number
            standard_title = applicability[0].standard_title

        catalog = cls._build_requirements_catalog(req.authoritative_mode)
        compliance_eval = evaluate_compliance_gaps(
            standard_number=standard_number,
            standard_title=standard_title,
            requirements_catalog=catalog,
            dna=dna,
        )

        # 4. Create Product & Assessment in DB or Memory
        prod = Product(
            id=product_id,
            name=req.product_name,
            category=req.category,
            description=req.description,
            dna_metadata=dna.model_dump(),
        )
        if db is not None:
            try:
                res_add = db.add(prod)
                if asyncio.iscoroutine(res_add):
                    await res_add
            except Exception as exc:
                logger.warning(f"DB prod add skipped: {exc}")

        mode_str = "AUTHORITATIVE_MODE" if req.authoritative_mode else "DEVELOPMENT_MODE"
        init_status = AssessmentStatus.COLLECTING_INFORMATION if clarifications else AssessmentStatus.COMPLIANCE_REVIEW

        assessment = Assessment(
            id=assessment_id,
            product_id=product_id,
            assessment_number=assessment_num,
            title=f"Compliance Assessment - {req.product_name}",
            status=init_status.value,
            mode=mode_str,
            current_version=1,
            product_dna_snapshot=dna.model_dump(),
            applicability_snapshot=[a.model_dump() for a in applicability],
            compliance_summary_snapshot=compliance_eval.model_dump() if compliance_eval else {},
            evidence_ids=[],
            source_ids=["SRC-BIS-OFFICIAL", "SRC-DPIIT-QCO-2023"],
        )
        if db is not None:
            try:
                res_add = db.add(assessment)
                if asyncio.iscoroutine(res_add):
                    await res_add
                await db.commit()
                await db.refresh(assessment)
            except Exception as exc:
                logger.warning(f"DB assessment add skipped, continuing in memory: {exc}")

        # Always persist to in-memory store
        save_assessment_mem(assessment, prod)

        # 5. Create Genesis Snapshot for Reproducibility
        await cls.create_snapshot(
            db=db,
            assessment=assessment,
            trigger_event="ASSESSMENT_INITIALIZED",
        )

        return assessment

    @classmethod
    async def create_snapshot(
        cls,
        db: Optional[AsyncSession],
        assessment: Assessment,
        trigger_event: str,
    ) -> AssessmentSnapshot:
        """Create an immutable point-in-time assessment snapshot recording exact inputs, rules, and outcomes."""
        summary = cls.compute_summary(assessment)
        snapshot = AssessmentSnapshot(
            id=f"SNAP-{uuid.uuid4().hex[:8].upper()}",
            assessment_id=assessment.id,
            version=assessment.current_version,
            trigger_event=trigger_event,
            product_dna_state=assessment.product_dna_snapshot,
            knowledge_version="M4.0-OFFICIAL-2023",
            rule_versions={
                "APP_DRINKWARE_001": "1.0.0",
                "IS_17526_2021": "First Edition 2021 + Amend 1-2",
            },
            decision_records_snapshot=assessment.compliance_summary_snapshot.get("evaluations", []),
            evidence_ids=assessment.evidence_ids,
            summary_counts=summary.model_dump(),
        )
        if db is not None:
            try:
                res_add = db.add(snapshot)
                if asyncio.iscoroutine(res_add):
                    await res_add
                await db.commit()
                await db.refresh(snapshot)
            except Exception as exc:
                logger.warning(f"DB snapshot persist skipped, continuing in memory: {exc}")
        save_snapshot_mem(snapshot)
        return snapshot

    @classmethod
    def compute_summary(cls, assessment: Assessment) -> AssessmentSummaryResponse:
        """Compute structured count-based summary without fake percentages."""
        comp = assessment.compliance_summary_snapshot or {}
        evals = comp.get("evaluations", [])

        sat = sum(1 for e in evals if e.get("status") == ComplianceStatus.SATISFIED.value)
        pot_sat = sum(1 for e in evals if e.get("status") == ComplianceStatus.POTENTIALLY_SATISFIED.value)
        miss = sum(1 for e in evals if e.get("status") == ComplianceStatus.MISSING_EVIDENCE.value)
        more_info = sum(1 for e in evals if e.get("status") == ComplianceStatus.MORE_INFORMATION_REQUIRED.value)
        gaps = sum(1 for e in evals if e.get("status") == ComplianceStatus.POTENTIAL_GAP.value)
        not_app = sum(1 for e in evals if e.get("status") == ComplianceStatus.NOT_APPLICABLE.value)
        conflicts = sum(1 for e in evals if e.get("status") == ComplianceStatus.CONFLICTING_EVIDENCE.value)
        expert = sum(1 for e in evals if e.get("status") == ComplianceStatus.REQUIRES_EXPERT_REVIEW.value)

        actions: Dict[str, int] = {}
        for e in evals:
            act = e.get("recommended_action")
            if act:
                actions[act] = actions.get(act, 0) + 1

        overall = comp.get("overall_status", ComplianceStatus.MORE_INFORMATION_REQUIRED.value)
        is_auth = assessment.mode == "AUTHORITATIVE_MODE"

        return AssessmentSummaryResponse(
            assessment_id=assessment.id,
            product_id=assessment.product_id,
            assessment_number=assessment.assessment_number,
            status=assessment.status,
            mode=assessment.mode,
            total_requirements=len(evals),
            satisfied_count=sat,
            potentially_satisfied_count=pot_sat,
            missing_evidence_count=miss,
            more_information_required_count=more_info,
            potential_gaps_count=gaps,
            not_applicable_count=not_app,
            conflicting_evidence_count=conflicts,
            expert_review_count=expert,
            recommended_actions=actions,
            summary_verdict=overall,
            trust_basis={
                "is_authoritative": is_auth,
                "verified_metadata": True,
                "verified_qco": True,
                "full_text_acquisition": "OFFICIAL_DOCUMENT_ACQUISITION_PENDING",
            },
        )

    @classmethod
    async def get_assessment_detail(
        cls,
        db: Optional[AsyncSession],
        assessment: Assessment,
    ) -> AssessmentDetailResponse:
        """Compose comprehensive assessment workspace detail."""
        prod = None
        if db is not None:
            try:
                prod_stmt = select(Product).where(Product.id == assessment.product_id)
                prod_res = await db.execute(prod_stmt)
                prod = prod_res.scalar_one_or_none()
            except Exception as exc:
                logger.warning(f"DB product query notice: {exc}")
        if not prod:
            prod = PRODUCTS_STORE.get(assessment.product_id)

        dna = ProductDNACore.model_validate(assessment.product_dna_snapshot or {})
        clarifications = detect_missing_attributes(dna)
        dna.pending_clarifications = clarifications

        applicability = [
            ApplicabilityDecision.model_validate(a)
            for a in (assessment.applicability_snapshot or [])
        ]
        
        comp_eval = None
        if assessment.compliance_summary_snapshot:
            comp_eval = StandardComplianceEvaluation.model_validate(assessment.compliance_summary_snapshot)

        # Roadmap and laboratories
        std_num = applicability[0].standard_number if applicability else "IS 17526:2021"
        roadmap = compile_testing_roadmap(std_num)
        labs = get_verified_laboratories(std_num)

        # Graph
        graph = build_evidence_graph(
            product_id=assessment.product_id,
            dna=dna,
            applicability=applicability,
            compliance=comp_eval,
        )

        summary = cls.compute_summary(assessment)

        raw_evs = get_evidence_mem(assessment.id)
        evidence_items = [
            StructuredEvidence.model_validate(ev) if not isinstance(ev, StructuredEvidence) else ev
            for ev in raw_evs
        ]
        conflicts = detect_evidence_conflicts(evidence_items)

        return AssessmentDetailResponse(
            assessment_id=assessment.id,
            product_id=assessment.product_id,
            assessment_number=assessment.assessment_number,
            title=assessment.title,
            status=assessment.status,
            mode=assessment.mode,
            current_version=assessment.current_version,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            completed_at=assessment.completed_at,
            product_dna=dna,
            clarifications=clarifications,
            applicability=applicability,
            compliance=comp_eval,
            evidence_items=evidence_items,
            evidence_conflicts=conflicts,
            testing_roadmap=roadmap,
            laboratories=labs,
            evidence_graph=graph,
            summary=summary,
        )

    @classmethod
    async def add_evidence_and_recalculate(
        cls,
        db: Optional[AsyncSession],
        assessment: Assessment,
        snippet: str,
        evidence_type: str = "TEST_REPORT",
        authority: str = "LAB_REPORT",
        page: Optional[int] = None,
    ) -> Assessment:
        """Extract evidence from snippet, detect conflicts, match to requirements, recalculate compliance, bump version, and save snapshot."""
        evs = extract_evidence_from_snippet(
            snippet=snippet,
            evidence_type=evidence_type,
            authority=authority,
            page=page,
            assessment_id=assessment.id,
        )
        for ev in evs:
            save_evidence_mem(assessment.id, ev)

        raw_evs = get_evidence_mem(assessment.id)
        all_evs = [
            StructuredEvidence.model_validate(ev) if not isinstance(ev, StructuredEvidence) else ev
            for ev in raw_evs
        ]
        conflicts = detect_evidence_conflicts(all_evs)

        # Build evidence payload dictionary for backwards compatibility
        evidence_payload: Dict[str, Any] = {}
        for ev in all_evs:
            if ev.attribute == "tested_heat_retention_temp":
                evidence_payload["tested_temp_after_6hrs"] = ev.normalized_value
            elif ev.attribute == "leakage_test_result":
                evidence_payload["leakage_test_passed"] = (ev.normalized_value == 1.0)
            elif ev.attribute == "material_grade_verified":
                evidence_payload["mill_test_certificate"] = True

        catalog = cls._build_requirements_catalog(assessment.mode == "AUTHORITATIVE_MODE")
        req_evidence_map, links, rule_results = match_evidence_to_requirements(catalog, all_evs, assessment.id)
        for l in links:
            save_link_mem(assessment.id, l)

        # Map conflicts by requirement
        conflicts_map: Dict[str, bool] = {}
        conflicted_attrs = {c["attribute"] for c in conflicts}
        for req in catalog:
            rid = req.get("id") or req.get("code")
            code = req.get("code", "")
            if "MAT" in code and "material_grade_verified" in conflicted_attrs:
                conflicts_map[rid] = True
            elif "LEAK" in code and "leakage_test_result" in conflicted_attrs:
                conflicts_map[rid] = True
            elif "THERM" in code and "tested_heat_retention_temp" in conflicted_attrs:
                conflicts_map[rid] = True
            elif "capacity_ml" in conflicted_attrs:
                conflicts_map[rid] = True

        dna = ProductDNACore.model_validate(assessment.product_dna_snapshot or {})

        comp_eval = evaluate_compliance_gaps(
            standard_number=assessment.applicability_snapshot[0]["standard_number"] if assessment.applicability_snapshot else "IS 17526:2021",
            standard_title=assessment.applicability_snapshot[0]["standard_title"] if assessment.applicability_snapshot else "Domestic Stainless Steel Vacuum Flask/Bottle",
            requirements_catalog=catalog,
            dna=dna,
            evidence_payload=evidence_payload,
            linked_evidences_map=req_evidence_map,
            conflicts_map=conflicts_map,
        )

        assessment.current_version += 1
        assessment.compliance_summary_snapshot = comp_eval.model_dump()
        new_ev_ids = [ev.evidence_id for ev in all_evs]
        assessment.evidence_ids = list(set((assessment.evidence_ids or []) + new_ev_ids))
        assessment.status = AssessmentStatus.COMPLIANCE_REVIEW.value

        if db is not None:
            try:
                await db.commit()
                await db.refresh(assessment)
            except Exception as exc:
                logger.warning(f"DB evidence commit skipped: {exc}")
        save_assessment_mem(assessment)

        # Snapshot the new decision state
        await cls.create_snapshot(
            db=db,
            assessment=assessment,
            trigger_event=f"EVIDENCE_ADDED_{evidence_type}",
        )
        return assessment

    @classmethod
    async def answer_clarification_and_recalculate(
        cls,
        db: Optional[AsyncSession],
        assessment: Assessment,
        attribute_name: str,
        raw_value: str,
    ) -> Assessment:
        """Apply clarification answer to Product DNA, update database, re-evaluate reasoning, and create snapshot."""
        dna = ProductDNACore.model_validate(assessment.product_dna_snapshot or {})
        updated_dna = apply_clarification_response(
            dna=dna,
            attribute_name=attribute_name,
            raw_value=raw_value,
            source_type="USER_CORRECTION",
        )

        clarifications = detect_missing_attributes(updated_dna)
        updated_dna.pending_clarifications = clarifications

        is_auth = assessment.mode == "AUTHORITATIVE_MODE"
        applicability = determine_applicability(updated_dna, authoritative_only=is_auth)
        catalog = cls._build_requirements_catalog(is_auth)

        comp_eval = evaluate_compliance_gaps(
            standard_number=applicability[0].standard_number if applicability else "IS 17526:2021",
            standard_title=applicability[0].standard_title if applicability else "Domestic Stainless Steel Vacuum Flask/Bottle",
            requirements_catalog=catalog,
            dna=updated_dna,
        )

        assessment.current_version += 1
        assessment.product_dna_snapshot = updated_dna.model_dump()
        assessment.applicability_snapshot = [a.model_dump() for a in applicability]
        assessment.compliance_summary_snapshot = comp_eval.model_dump()
        if not clarifications:
            assessment.status = AssessmentStatus.COMPLIANCE_REVIEW.value

        if db is not None:
            try:
                await db.commit()
                await db.refresh(assessment)
            except Exception as exc:
                logger.warning(f"DB clarification commit skipped: {exc}")
        save_assessment_mem(assessment)

        await cls.create_snapshot(
            db=db,
            assessment=assessment,
            trigger_event=f"CLARIFICATION_ANSWERED_{attribute_name}",
        )
        return assessment

    @classmethod
    def generate_compliance_passport(
        cls,
        assessment: Assessment,
        prod_name: str,
        category: str,
    ) -> CompliancePassport:
        """Compile first-class structured Compliance Passport with source index and honest trust disclaimers."""
        is_auth = assessment.mode == "AUTHORITATIVE_MODE"
        dna = ProductDNACore.model_validate(assessment.product_dna_snapshot or {})
        applicability = [
            ApplicabilityDecision.model_validate(a)
            for a in (assessment.applicability_snapshot or [])
        ]
        comp = assessment.compliance_summary_snapshot or {}
        evals = comp.get("evaluations", [])

        gaps = [
            e for e in evals
            if e.get("status") in (
                ComplianceStatus.POTENTIAL_GAP.value,
                ComplianceStatus.MISSING_EVIDENCE.value,
                ComplianceStatus.MORE_INFORMATION_REQUIRED.value,
                ComplianceStatus.CONFLICTING_EVIDENCE.value,
                ComplianceStatus.REQUIRES_EXPERT_REVIEW.value,
            )
        ]

        roadmap = compile_testing_roadmap("IS 17526:2021")
        labs = get_verified_laboratories("IS 17526:2021")

        actions = []
        for e in evals:
            if e.get("recommended_action"):
                actions.append({
                    "clause_number": e.get("clause_number"),
                    "action": e.get("recommended_action"),
                    "explanation": e.get("explanation"),
                })

        # Structured Source Index
        source_index = [
            PassportSourceIndexItem(
                source_index_id="SRC-001",
                citation_type="STANDARD",
                title="IS 17526:2021 - Domestic Stainless Steel Vacuum Flask/Bottle",
                standard_or_gazette_number="IS 17526:2021",
                clause_or_section="Scope & Technical Specifications",
                page=1,
                url="https://www.manakonline.in",
                authority="BIS_OFFICIAL",
                verification_status="VERIFIED_METADATA",
            ),
            PassportSourceIndexItem(
                source_index_id="SRC-002",
                citation_type="REGULATION",
                title="Insulated Flask, Bottles and Containers for Domestic Use (Quality Control) Order, 2023",
                standard_or_gazette_number="DPIIT Gazette Order 2023",
                clause_or_section="Section 16, 17, 25(3)",
                page=2,
                url="https://egazette.gov.in",
                authority="GOVERNMENT_OFFICIAL",
                verification_status="VERIFIED",
            ),
            PassportSourceIndexItem(
                source_index_id="SRC-003",
                citation_type="PRODUCT_MANUAL",
                title="BIS Product Manual for Domestic Stainless Steel Vacuum Flasks (PM/IS 17526/1)",
                standard_or_gazette_number="PM/IS 17526/1",
                clause_or_section="Scheme of Inspection & Testing (8-sample protocol)",
                page=4,
                url="https://www.bis.gov.in",
                authority="BIS_OFFICIAL",
                verification_status="VERIFIED",
            ),
        ]

        trust_section = PassportTrustSection(
            verified_official_metadata=True,
            verified_regulatory_sources=True,
            full_standard_text_status="OFFICIAL_DOCUMENT_ACQUISITION_PENDING",
            synthetic_development_data_used=not is_auth,
            trust_level_summary=(
                "AUTHORITATIVE_VERIFIED: Evaluated exclusively against verified BIS metadata, DPIIT QCO 2023, and BIS Product Manual PM/IS 17526/1. Unsupported clause claims strictly refused."
                if is_auth else
                "DEVELOPMENT_MODE: Evaluated using synthetic test fixtures for development and testing. Strictly non-authoritative."
            ),
        )

        limitations = [
            "This Compliance Assessment Passport is an evidence-backed technical roadmap, NOT an official Bureau of Indian Standards License or ISI Mark Certificate.",
            "Full official technical standard specification document for IS 17526:2021 is pending authorized acquisition.",
            "This platform produces testing parameters and schedules; it does not physically execute laboratory experiments.",
            "Accredited testing must be conducted at a verified BIS/NABL recognized laboratory facility.",
        ]

        # Invariant check: SATISFIED is strictly prohibited without verified evidence
        for e in evals:
            if e.get("status") == ComplianceStatus.SATISFIED.value:
                has_ev = bool(e.get("evidence_ids") or e.get("audit_chain") or e.get("available_evidence"))
                if not has_ev:
                    raise ValueError(
                        f"Compliance Passport Invariant Violation: Requirement '{e.get('requirement_code')}' "
                        "cannot be marked SATISFIED without verified supporting evidence."
                    )

        return CompliancePassport(
            passport_id=f"PSP-{uuid.uuid4().hex[:8].upper()}",
            assessment_id=assessment.id,
            assessment_number=assessment.assessment_number,
            product_name=prod_name,
            category=category,
            mode=assessment.mode,
            generated_at=datetime.now(timezone.utc),
            claim_statement="Evidence-Backed Regulatory Compliance Assessment & Technical Gap Roadmap",
            trust_basis=trust_section,
            product_dna=dna,
            applicable_standards=applicability,
            compliance_evaluations=evals,
            gaps=gaps,
            testing_roadmap=roadmap,
            recognized_laboratories=labs,
            recommended_actions=actions,
            source_index=source_index,
            limitations=limitations,
        )

    @classmethod
    def answer_assessment_question(
        cls,
        assessment: Assessment,
        question: str,
    ) -> Dict[str, Any]:
        """Context-aware assistant operating strictly within the assessment, DNA, evidence, and rule boundaries.
        
        Strict safety: Assistant explains requirements and missing evidence; has ZERO authority to assert compliance.
        """
        q_lower = question.lower()
        comp = assessment.compliance_summary_snapshot or {}
        evals = comp.get("evaluations", [])
        dna = assessment.product_dna_snapshot or {}

        # Security & Zero-Hallucination Guard: Reject prompt injections and compliance override attempts
        if any(w in q_lower for w in ["ignore previous", "override", "certify compliant", "mark compliant", "declare compliant", "bypass gate"]):
            return {
                "answer": "The AI assistant has ZERO authority to declare, override, or certify compliance. All compliance determinations are strictly computed by the deterministic compliance gate (can_be_satisfied) based on verified laboratory evidence.",
                "assessment_id": assessment.id,
                "context_used": {"authority": "DETERMINISTIC_GATE_ONLY"},
                "citations": [{"source": "Zero-Hallucination Regulatory Integrity Policy"}],
            }

        # Check for ungrounded / fake standards
        import re
        fake_std_match = re.search(r"\bis\s*(\d{4,6})\b", q_lower)
        if fake_std_match:
            asked_std = f"IS {fake_std_match.group(1)}"
            app_stds = [str(a.get("standard_number", "")) for a in (assessment.applicability_snapshot or [])]
            cur_std = comp.get("standard_number", "IS 17526:2021")
            if not any(asked_std in s for s in app_stds + [cur_std]):
                return {
                    "answer": f"Standard '{asked_std}' is not an applicable standard for this product assessment. The system strictly refuses to invent ungrounded requirements or speculate on unverified standards.",
                    "assessment_id": assessment.id,
                    "context_used": {"verified_standards": [cur_std] + app_stds},
                    "citations": [{"source": "BIS Official Knowledge Catalog"}],
                }

        # Check for ungrounded / fake clauses
        fake_clause_match = re.search(r"\bclause\s*(\d+(\.\d+)+)\b", q_lower)
        if fake_clause_match:
            asked_clause = fake_clause_match.group(1)
            known_clauses = [str(e.get("clause_number")) for e in evals if e.get("clause_number")]
            if known_clauses and asked_clause not in known_clauses:
                return {
                    "answer": f"Clause {asked_clause} does not exist in the codified requirements for {comp.get('standard_number', 'IS 17526:2021')}. The system will not invent ungrounded clauses.",
                    "assessment_id": assessment.id,
                    "context_used": {"known_clauses": known_clauses},
                    "citations": [{"source": "BIS Official Knowledge Catalog"}],
                }

        # Search matching clause or requirement
        matched_eval = None
        for ev in evals:
            c_num = str(ev.get("clause_number", "")).lower()
            c_code = str(ev.get("requirement_code", "")).lower()
            c_title = str(ev.get("clause_title", "")).lower()
            if (c_num and (f"clause {c_num}" in q_lower or f"{c_num}" in q_lower)) or (c_code and c_code in q_lower) or (c_title and any(w in q_lower for w in c_title.split() if len(w) > 4)):
                matched_eval = ev
                break

        if matched_eval:
            req_evs = matched_eval.get("required_evidence_types", ["LAB_REPORT"])
            avail_evs = matched_eval.get("available_evidence", [])
            act = matched_eval.get("recommended_action") or "UPLOAD_EVIDENCE"
            cur_ev_str = ", ".join(e.get("evidence_id", "EV") for e in avail_evs) if avail_evs else "None"

            if matched_eval.get("status") == ComplianceStatus.SATISFIED.value:
                chain = matched_eval.get("audit_chain", {})
                ans = (
                    f"Requirement '{matched_eval.get('requirement_code')}' (Clause {matched_eval.get('clause_number')}: {matched_eval.get('clause_title')}) "
                    f"is SATISFIED based on verified evidence [{chain.get('evidence_id')}] (Page {chain.get('page_number', 1)}) from {chain.get('source_authority')}. "
                    f"Evaluation rule: '{chain.get('evaluation_rule')}' -> Result: PASS."
                )
            else:
                ans = (
                    f"The system cannot establish SATISFIED for Clause {matched_eval.get('clause_number')} ({matched_eval.get('clause_title')}) "
                    f"because no verified laboratory test report or certificate has been linked to this requirement. "
                    f"Requirement: {matched_eval.get('requirement_code')}. "
                    f"Current Status: {matched_eval.get('status')}. "
                    f"Required Evidence: {', '.join(req_evs)}. "
                    f"Current Evidence: {cur_ev_str}. "
                    f"Recommended Action: {act}. "
                    f"Invariant: User-entered product text describes claims, but never compliance."
                )
            citations = [
                {
                    "standard": comp.get("standard_number", "IS 17526:2021"),
                    "clause": matched_eval.get("clause_number"),
                    "source": "BIS Standards Catalog & Product Manual PM/IS 17526/1",
                }
            ]
        elif "gap" in q_lower or "missing" in q_lower:
            gaps = [e for e in evals if e.get("status") in (ComplianceStatus.MISSING_EVIDENCE.value, ComplianceStatus.POTENTIAL_GAP.value, ComplianceStatus.MORE_INFORMATION_REQUIRED.value)]
            ans = f"This assessment has identified {len(gaps)} compliance gap(s) or missing evidence items: " + "; ".join(f"Clause {g.get('clause_number')}: {g.get('explanation')}" for g in gaps)
            citations = [{"standard": "IS 17526:2021", "source": "Product Manual PM/IS 17526/1"}]
        elif "dna" in q_lower or "material" in q_lower or "capacity" in q_lower:
            ans = f"Current Product DNA record: Name: '{dna.get('product_name')}', Category: '{dna.get('category')}', Materials: {dna.get('materials')}, Capacity: {dna.get('capacity_ml')}ml, Insulated: {dna.get('insulated')}."
            citations = [{"source": "Product DNA Extractor & Normalizer"}]
        elif "passport" in q_lower or "certificate" in q_lower:
            ans = "The Compliance Passport provides an auditable technical roadmap and evidence breakdown. It is not an official BIS ISI license, which requires official laboratory testing and factory audit."
            citations = [{"source": "DPIIT QCO Order 2023", "clause": "Scheme-I Conformity Assessment Regulations"}]
        else:
            ans = (
                f"Assessment '{assessment.assessment_number}' is in mode '{assessment.mode}' with verdict '{comp.get('overall_status', 'UNDER_EVALUATION')}'. "
                "You can inspect Product DNA attributes, upload test reports, view the testing roadmap, or generate the auditable Compliance Passport."
            )
            citations = [{"source": "Zyntrix Assessment Context Engine"}]

        return {
            "answer": ans,
            "assessment_id": assessment.id,
            "context_used": {
                "assessment_number": assessment.assessment_number,
                "mode": assessment.mode,
                "overall_status": comp.get("overall_status"),
                "total_requirements": len(evals),
            },
            "citations": citations,
            "disclaimer": "AI assistant operates strictly in an explanatory capacity. All compliance decisions are deterministically computed by the rule engine.",
        }

    @classmethod
    def get_requirements(cls, assessment: Assessment) -> List[Dict[str, Any]]:
        """Retrieve all requirements with required evidence, available evidence, and deterministic audit chain."""
        comp = assessment.compliance_summary_snapshot or {}
        return comp.get("evaluations", [])

    @classmethod
    def get_requirement_detail(cls, assessment: Assessment, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single requirement detail with its evidence chain."""
        reqs = cls.get_requirements(assessment)
        for r in reqs:
            if r.get("requirement_id") == requirement_id or r.get("requirement_code") == requirement_id:
                return r
        return None

    @classmethod
    def get_requirement_evidence(cls, assessment: Assessment, requirement_id: str) -> List[Any]:
        """Retrieve evidence items linked to a specific requirement."""
        req = cls.get_requirement_detail(assessment, requirement_id)
        if not req:
            return []
        return req.get("available_evidence", [])

    @classmethod
    async def link_evidence_to_requirement(
        cls,
        assessment: Assessment,
        requirement_id: str,
        evidence_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Link an evidence item to a requirement and trigger deterministic re-evaluation."""
        all_evs = get_evidence_mem(assessment.id)
        matched_ev = next((ev for ev in all_evs if getattr(ev, "evidence_id", None) == evidence_id or getattr(ev, "id", None) == evidence_id), None)
        if not matched_ev:
            raise ValueError(f"Evidence '{evidence_id}' not found in assessment '{assessment.id}'.")

        catalog = cls._build_requirements_catalog(assessment.mode == "AUTHORITATIVE_MODE")
        target_req = next((r for r in catalog if r.get("id") == requirement_id or r.get("code") == requirement_id), None)
        if not target_req:
            raise ValueError(f"Requirement '{requirement_id}' not found in catalog.")

        link = RequirementEvidenceLink(
            id=f"LNK-{uuid.uuid4().hex[:8].upper()}",
            assessment_id=assessment.id,
            requirement_id=target_req.get("id") or target_req.get("code"),
            evidence_id=evidence_id,
            linkage_type="DIRECT_SUPPORT",
            relevance="PRIMARY",
            linkage_confidence=1.0,
            supporting_excerpt=getattr(matched_ev, "source_excerpt", "") or getattr(matched_ev, "source_text", ""),
            evaluation_rule=target_req.get("measurable_condition") or target_req.get("description"),
            rule_result="PASS",
        )
        save_link_mem(assessment.id, link)

        # Trigger re-evaluation with all evidences
        updated_asm = await cls.add_evidence_and_recalculate(
            db=db,
            assessment=assessment,
            snippet=getattr(matched_ev, "source_excerpt", "") or getattr(matched_ev, "source_text", "Linked evidence update"),
            evidence_type=getattr(matched_ev, "evidence_type", "TEST_REPORT"),
            authority=getattr(matched_ev, "source_authority", "LAB_REPORT"),
            page=getattr(matched_ev, "page_number", 1),
        )
        return {
            "link_id": link.id,
            "assessment_id": assessment.id,
            "requirement_id": requirement_id,
            "evidence_id": evidence_id,
            "linkage_type": link.linkage_type,
            "status": "LINKED",
        }

