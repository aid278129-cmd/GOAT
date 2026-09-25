"""Milestone M26.2: Deterministic Compliance Gap Aggregation Engine.

Enforces Cardinal Non-Negotiables & Regulatory Invariants:
1. 9-Layer Architecture Preservation:
   - Layer 1: Ingestion & Document Parsing
   - Layer 2: Product DNA & Candidate Fact Extraction (regulatory_conclusion = "NONE")
   - Layer 3: Standards Knowledge Graph
   - Layer 4: Quality Control Order (QCO) Mandates
   - Layer 5: Statutory Applicability Engine
   - Layer 6: Clause-Level RAG / Retrieval
   - Layer 7: Compliance Gap Analysis Engine (SOLE COMPLIANCE DECISION AUTHORITY)
   - Layer 8: Source Validation & Citation Guard (SOLE EVIDENCE / SOURCE TRUST AUTHORITY)
   - Layer 9: Regulatory Dossier & Passport Export
2. 4-Stage Transition Chain:
   VERIFIED EVIDENCE → REQUIREMENT SATISFACTION → GAP STATUS → COMPLIANCE RESULT.
3. 7-State Requirement Gap Taxonomy:
   SATISFIED, NOT_SATISFIED, MISSING_EVIDENCE, UNVERIFIED, CONFLICTING, EXPERT_REVIEW_REQUIRED, NOT_APPLICABLE.
4. Deterministic 10-Element Compliance Gap Chain:
   standard → revision → clause → requirement → current evidence → evidence status → gap status → reason → required next action → provenance.
5. Deterministic Next Actions:
   LAB_TEST_REQUIRED, DOCUMENT_REQUIRED, DECLARATION_REQUIRED, MARKING_EVIDENCE_REQUIRED, CORRECTIVE_ACTION_REQUIRED, EXPERT_REVIEW_REQUIRED, NO_ACTION_REQUIRED.
6. Single Satisfied Invariant:
   A single satisfied requirement must NEVER imply overall compliance.
7. Output Boundary Invariant:
   Do not generate unsupported laboratory names, fees, turnaround times, certification outcomes, or regulatory conclusions.
8. Authority Boundary:
   Layer 7 is sole compliance decision authority. Layer 8 is sole evidence/source trust authority. LLM authority = 0.0%.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from pydantic import BaseModel, Field

from backend.app.schemas.product_evidence import (
    EvidenceType,
    EvidenceHierarchyLevel,
    EvidenceVerificationStatus,
    SourceAuthenticity,
    ArtifactIntegrityStatus,
    EvidenceOntologyTier,
    EvidenceChainRecord,
    ProductEvidenceRecord,
    RequirementMappingStatus,
    RequirementSatisfactionStatus,
    EvidenceRequirementMappingChain,
    StandardRequirementDefinition,
    EvidenceRequirementMappingRecord,
)
from backend.app.schemas.compliance import (
    ComplianceStatus,
    RequirementGapStatus,
    GapNextAction,
    ComplianceGapItem,
    DeterministicGapAggregationResult,
    validate_transition_chain,
)
from backend.app.services.compliance.evidence_eligibility import (
    EvidenceEligibilityEngine,
    RequirementClass,
    EligibilityStatus,
)
from backend.app.services.compliance.evidence_mapping_service import (
    DeterministicEvidenceRequirementMapper,
    evidence_mapping_service,
    VERIFIED_STANDARD_REQUIREMENTS,
)
from backend.app.core.logging import logger


class DeterministicGapAggregationEngine:
    """Production Engine for Deterministic Compliance Gap Aggregation (Milestone M26.2)."""

    @classmethod
    def get_standard_requirements(
        cls,
        target_standard: str,
        custom_requirements: Optional[List[StandardRequirementDefinition]] = None,
    ) -> List[StandardRequirementDefinition]:
        """Fetch all mandatory statutory requirements for the target standard."""
        reqs: List[StandardRequirementDefinition] = []

        base_code, rev = DeterministicEvidenceRequirementMapper.parse_standard_and_revision(target_standard)

        # Lookup from authoritative catalog
        for std_key, cat in VERIFIED_STANDARD_REQUIREMENTS.items():
            k_base, k_rev = DeterministicEvidenceRequirementMapper.parse_standard_and_revision(std_key)
            if k_base == base_code and (rev is None or rev == k_rev):
                reqs.extend(cat.values())
                break

        # Append custom requirements if provided
        if custom_requirements:
            existing_ids = {r.requirement_id for r in reqs}
            for cr in custom_requirements:
                if cr.requirement_id not in existing_ids:
                    reqs.append(cr)

        return reqs

    @classmethod
    def derive_requirement_gap(
        cls,
        req: StandardRequirementDefinition,
        target_standard: str,
        evidence_records: List[ProductEvidenceRecord],
        target_product_category: Optional[str] = None,
        allow_synthetic: bool = True,
    ) -> ComplianceGapItem:
        """Deterministically derive the compliance gap item for a single requirement."""
        std_code, std_rev = DeterministicEvidenceRequirementMapper.parse_standard_and_revision(target_standard)
        actual_rev = std_rev or req.revision

        # 1. Find matching evidence records for this requirement
        matching_evs: List[ProductEvidenceRecord] = []
        for ev in evidence_records:
            # Check explicit requirement ID match
            if ev.applicable_requirement and ev.applicable_requirement.strip().lower() == req.requirement_id.strip().lower():
                matching_evs.append(ev)
                continue

            # Check explicit clause number match
            if ev.applicable_clause:
                ev_cl = ev.applicable_clause.lower().replace("clause", "").replace("cls", "").strip()
                req_cl = req.clause_number.lower().replace("clause", "").replace("cls", "").strip()
                if ev_cl == req_cl:
                    matching_evs.append(ev)
                    continue

            # Check attribute match if standard matches
            if ev.attribute and ev.applicable_standard:
                ev_std_base, _ = DeterministicEvidenceRequirementMapper.parse_standard_and_revision(ev.applicable_standard)
                if ev_std_base == std_code and ev.attribute.lower() in req.requirement_title.lower():
                    matching_evs.append(ev)

        # Case A: Missing Evidence
        if not matching_evs:
            # Determine appropriate required next action based on requirement class
            next_act = GapNextAction.DOCUMENT_REQUIRED
            if req.requirement_class == RequirementClass.LAB_TEST_REQUIREMENT.value:
                next_act = GapNextAction.LAB_TEST_REQUIRED
            elif req.requirement_class == RequirementClass.DECLARATION_REQUIREMENT.value:
                next_act = GapNextAction.DECLARATION_REQUIRED
            elif req.requirement_class == RequirementClass.PHYSICAL_MARKING.value:
                next_act = GapNextAction.MARKING_EVIDENCE_REQUIRED

            return ComplianceGapItem(
                standard=std_code,
                revision=actual_rev,
                clause=req.clause_number,
                requirement=req.requirement_id,
                current_evidence="NONE",
                evidence_status="MISSING",
                gap_status=RequirementGapStatus.MISSING_EVIDENCE,
                reason=f"No evidence artifact provided for mandatory requirement '{req.requirement_id}' ({req.requirement_title}).",
                required_next_action=next_act,
                provenance="No artifact supplied; required statutory verification pending.",
            )

        # Case B: Conflicting Evidence
        is_conflicting = (
            len(matching_evs) > 1
            or matching_evs[0].evidence_type == EvidenceType.CONFLICTING_EVIDENCE
            or matching_evs[0].verification_status == EvidenceVerificationStatus.CONFLICTING
        )
        if is_conflicting:
            primary_ev = matching_evs[0]
            return ComplianceGapItem(
                standard=std_code,
                revision=actual_rev,
                clause=req.clause_number,
                requirement=req.requirement_id,
                current_evidence=primary_ev.evidence_id,
                evidence_status="CONFLICTING",
                gap_status=RequirementGapStatus.CONFLICTING,
                reason=f"Multiple contradictory evidence artifacts detected for requirement '{req.requirement_id}'. Autonomous resolution prohibited.",
                required_next_action=GapNextAction.EXPERT_REVIEW_REQUIRED,
                provenance=f"Conflicting submissions across artifacts: {', '.join(e.evidence_id for e in matching_evs)}",
            )

        # Case C: Single Evidence Evaluation via M26.1 Mapping
        ev = matching_evs[0]
        mapping = evidence_mapping_service.map_evidence_to_requirement(
            evidence=ev,
            target_standard=target_standard,
            target_clause=req.clause_number,
            target_requirement_id=req.requirement_id,
            target_product_category=target_product_category,
            allow_synthetic=allow_synthetic,
        )

        # 1. Rejected Cases (Prompt injection, tampering, standard mismatch, revision mismatch)
        if mapping.mapping_status == RequirementMappingStatus.REJECTED:
            # Check prompt injection
            if "prompt injection" in mapping.mapping_reason.lower():
                return ComplianceGapItem(
                    standard=std_code,
                    revision=actual_rev,
                    clause=req.clause_number,
                    requirement=req.requirement_id,
                    current_evidence=ev.evidence_id,
                    evidence_status="REJECTED",
                    gap_status=RequirementGapStatus.UNVERIFIED,
                    reason=f"Security violation: {mapping.mapping_reason}",
                    required_next_action=GapNextAction.EXPERT_REVIEW_REQUIRED,
                    provenance=ev.provenance,
                )
            # Check standard / revision mismatch
            next_act = (
                GapNextAction.LAB_TEST_REQUIRED
                if req.requirement_class == RequirementClass.LAB_TEST_REQUIREMENT.value
                else GapNextAction.DOCUMENT_REQUIRED
            )
            return ComplianceGapItem(
                standard=std_code,
                revision=actual_rev,
                clause=req.clause_number,
                requirement=req.requirement_id,
                current_evidence=ev.evidence_id,
                evidence_status="REJECTED",
                gap_status=RequirementGapStatus.UNVERIFIED,
                reason=mapping.mapping_reason,
                required_next_action=next_act,
                provenance=ev.provenance,
            )

        # 2. Ineligible Evidence Type (e.g. datasheet for empirical lab test)
        if mapping.mapping_status == RequirementMappingStatus.INELIGIBLE:
            next_act = (
                GapNextAction.LAB_TEST_REQUIRED
                if req.requirement_class == RequirementClass.LAB_TEST_REQUIREMENT.value
                else GapNextAction.DOCUMENT_REQUIRED
            )
            return ComplianceGapItem(
                standard=std_code,
                revision=actual_rev,
                clause=req.clause_number,
                requirement=req.requirement_id,
                current_evidence=ev.evidence_id,
                evidence_status="INELIGIBLE",
                gap_status=RequirementGapStatus.UNVERIFIED,
                reason=mapping.mapping_reason,
                required_next_action=next_act,
                provenance=ev.provenance,
            )

        # 3. Unmapped Evidence (e.g. anti-keyword-only matching rejection)
        if mapping.mapping_status == RequirementMappingStatus.UNMAPPED:
            return ComplianceGapItem(
                standard=std_code,
                revision=actual_rev,
                clause=req.clause_number,
                requirement=req.requirement_id,
                current_evidence=ev.evidence_id,
                evidence_status="UNMAPPED",
                gap_status=RequirementGapStatus.UNVERIFIED,
                reason=mapping.mapping_reason,
                required_next_action=GapNextAction.DOCUMENT_REQUIRED,
                provenance=ev.provenance,
            )

        # 4. Expert Review Required (ambiguous, borderline, or conflicting)
        if mapping.mapping_status == RequirementMappingStatus.EXPERT_REVIEW_REQUIRED:
            return ComplianceGapItem(
                standard=std_code,
                revision=actual_rev,
                clause=req.clause_number,
                requirement=req.requirement_id,
                current_evidence=ev.evidence_id,
                evidence_status="EXPERT_REVIEW_REQUIRED",
                gap_status=RequirementGapStatus.EXPERT_REVIEW_REQUIRED,
                reason=mapping.mapping_reason,
                required_next_action=GapNextAction.EXPERT_REVIEW_REQUIRED,
                provenance=ev.provenance,
            )

        # 5. Successfully Mapped Evidence
        if mapping.mapping_status == RequirementMappingStatus.MAPPED:
            if mapping.satisfaction_status == RequirementSatisfactionStatus.SATISFIED:
                return ComplianceGapItem(
                    standard=std_code,
                    revision=actual_rev,
                    clause=req.clause_number,
                    requirement=req.requirement_id,
                    current_evidence=ev.evidence_id,
                    evidence_status="VERIFIED",
                    gap_status=RequirementGapStatus.SATISFIED,
                    reason=f"Verified authentic evidence artifact '{ev.evidence_id}' satisfies statutory conditions.",
                    required_next_action=GapNextAction.NO_ACTION_REQUIRED,
                    provenance=ev.provenance,
                )
            elif mapping.satisfaction_status == RequirementSatisfactionStatus.NOT_SATISFIED:
                return ComplianceGapItem(
                    standard=std_code,
                    revision=actual_rev,
                    clause=req.clause_number,
                    requirement=req.requirement_id,
                    current_evidence=ev.evidence_id,
                    evidence_status="VERIFIED",
                    gap_status=RequirementGapStatus.NOT_SATISFIED,
                    reason=mapping.gap or "Measured value or physical artifact failed mandatory statutory threshold.",
                    required_next_action=GapNextAction.CORRECTIVE_ACTION_REQUIRED,
                    provenance=ev.provenance,
                )
            elif mapping.satisfaction_status == RequirementSatisfactionStatus.PARTIALLY_SATISFIED:
                return ComplianceGapItem(
                    standard=std_code,
                    revision=actual_rev,
                    clause=req.clause_number,
                    requirement=req.requirement_id,
                    current_evidence=ev.evidence_id,
                    evidence_status="PARTIALLY_SUPPORTED",
                    gap_status=RequirementGapStatus.EXPERT_REVIEW_REQUIRED,
                    reason=mapping.gap or "Partial evidence provided; remaining criteria require expert evaluation.",
                    required_next_action=GapNextAction.EXPERT_REVIEW_REQUIRED,
                    provenance=ev.provenance,
                )

        # Fallback safe abstention
        return ComplianceGapItem(
            standard=std_code,
            revision=actual_rev,
            clause=req.clause_number,
            requirement=req.requirement_id,
            current_evidence=ev.evidence_id,
            evidence_status=ev.verification_status.value,
            gap_status=RequirementGapStatus.UNVERIFIED,
            reason="Evidence verification status could not be deterministically established.",
            required_next_action=GapNextAction.EXPERT_REVIEW_REQUIRED,
            provenance=ev.provenance,
        )

    @classmethod
    def aggregate_compliance_gaps(
        cls,
        product_id: str,
        target_standard: str,
        evidence_records: List[ProductEvidenceRecord],
        target_product_category: Optional[str] = None,
        custom_requirements: Optional[List[StandardRequirementDefinition]] = None,
        allow_synthetic: bool = True,
    ) -> DeterministicGapAggregationResult:
        """Execute full deterministic compliance gap aggregation for a product against an applicable standard (M26.2).
        
        Enforces Cardinal Transitions:
        VERIFIED EVIDENCE → REQUIREMENT SATISFACTION → GAP STATUS → COMPLIANCE RESULT.
        
        Strict Non-Negotiable:
        A single satisfied requirement must NEVER imply overall compliance.
        COMPLIANT is emitted ONLY when ALL mandatory requirements are SATISFIED.
        """
        std_code, std_rev = DeterministicEvidenceRequirementMapper.parse_standard_and_revision(target_standard)
        aggregation_id = f"GAP-AGG-{product_id}-{std_code.replace(' ', '_')}"

        # 1. Fetch all applicable requirements
        requirements = cls.get_standard_requirements(
            target_standard=target_standard,
            custom_requirements=custom_requirements,
        )

        total_reqs = len(requirements)
        gap_items: List[ComplianceGapItem] = []

        satisfied_count = 0
        not_satisfied_count = 0
        missing_count = 0
        unverified_count = 0
        conflicting_count = 0
        expert_review_count = 0
        not_applicable_count = 0

        # Roadmaps
        roadmap_lab: List[ComplianceGapItem] = []
        roadmap_doc: List[ComplianceGapItem] = []
        roadmap_dec: List[ComplianceGapItem] = []
        roadmap_mark: List[ComplianceGapItem] = []
        roadmap_corr: List[ComplianceGapItem] = []
        roadmap_exp: List[ComplianceGapItem] = []

        # 2. Derive gap for each requirement
        for req in requirements:
            item = cls.derive_requirement_gap(
                req=req,
                target_standard=target_standard,
                evidence_records=evidence_records,
                target_product_category=target_product_category,
                allow_synthetic=allow_synthetic,
            )
            gap_items.append(item)

            # Tally counts
            if item.gap_status == RequirementGapStatus.SATISFIED:
                satisfied_count += 1
            elif item.gap_status == RequirementGapStatus.NOT_SATISFIED:
                not_satisfied_count += 1
            elif item.gap_status == RequirementGapStatus.MISSING_EVIDENCE:
                missing_count += 1
            elif item.gap_status == RequirementGapStatus.UNVERIFIED:
                unverified_count += 1
            elif item.gap_status == RequirementGapStatus.CONFLICTING:
                conflicting_count += 1
            elif item.gap_status == RequirementGapStatus.EXPERT_REVIEW_REQUIRED:
                expert_review_count += 1
            elif item.gap_status == RequirementGapStatus.NOT_APPLICABLE:
                not_applicable_count += 1

            # Populate Roadmaps
            if item.required_next_action == GapNextAction.LAB_TEST_REQUIRED:
                roadmap_lab.append(item)
            elif item.required_next_action == GapNextAction.DOCUMENT_REQUIRED:
                roadmap_doc.append(item)
            elif item.required_next_action == GapNextAction.DECLARATION_REQUIRED:
                roadmap_dec.append(item)
            elif item.required_next_action == GapNextAction.MARKING_EVIDENCE_REQUIRED:
                roadmap_mark.append(item)
            elif item.required_next_action == GapNextAction.CORRECTIVE_ACTION_REQUIRED:
                roadmap_corr.append(item)
            elif item.required_next_action == GapNextAction.EXPERT_REVIEW_REQUIRED:
                roadmap_exp.append(item)

        # 3. Overall Compliance Verdict Derivation (Layer 7 Sole Authority)
        # Invariant: A single satisfied requirement must never imply overall compliance.
        effective_reqs = total_reqs - not_applicable_count
        if effective_reqs <= 0:
            overall_verdict = "UNVERIFIED"
        elif not_satisfied_count > 0:
            overall_verdict = "NON_COMPLIANT"
        elif satisfied_count == effective_reqs and missing_count == 0 and unverified_count == 0 and conflicting_count == 0 and expert_review_count == 0:
            overall_verdict = "COMPLIANT"
        else:
            # GAPS_IDENTIFIED: Some passed, but some missing/unverified/conflicting
            overall_verdict = "GAPS_IDENTIFIED"

        # 4. Transition Chain Assertion
        is_compliant = (overall_verdict == "COMPLIANT")
        for item in gap_items:
            has_ev = (item.current_evidence != "NONE" and item.evidence_status == "VERIFIED")
            is_sat = (item.gap_status == RequirementGapStatus.SATISFIED)
            ok, msg = validate_transition_chain(
                has_verified_evidence=has_ev,
                is_requirement_satisfied=is_sat,
                gap_status=item.gap_status,
                is_overall_compliant=is_compliant,
            )
            if not ok:
                logger.error("Transition chain violation on requirement %s: %s", item.requirement, msg)

        return DeterministicGapAggregationResult(
            aggregation_id=aggregation_id,
            product_id=product_id,
            target_standard=target_standard,
            standard_revision=std_rev or "CURRENT",
            overall_verdict=overall_verdict,
            total_requirements=total_reqs,
            satisfied_count=satisfied_count,
            not_satisfied_count=not_satisfied_count,
            missing_evidence_count=missing_count,
            unverified_count=unverified_count,
            conflicting_count=conflicting_count,
            expert_review_count=expert_review_count,
            not_applicable_count=not_applicable_count,
            gap_items=gap_items,
            roadmap_lab_test=roadmap_lab,
            roadmap_document=roadmap_doc,
            roadmap_declaration=roadmap_dec,
            roadmap_marking=roadmap_mark,
            roadmap_corrective_action=roadmap_corr,
            roadmap_expert_review=roadmap_exp,
            compliance_authority="LAYER_7_ONLY",
            llm_compliance_authority=0.0,
            regulatory_conclusion="NONE",
            notes=(
                f"Evaluated {total_reqs} mandatory requirements under {target_standard}. "
                f"Satisfied: {satisfied_count}, Gaps: {not_satisfied_count + missing_count + unverified_count + conflicting_count + expert_review_count}."
            ),
        )


# Global singleton instance
gap_aggregation_service = DeterministicGapAggregationEngine()
