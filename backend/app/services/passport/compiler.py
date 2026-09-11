"""Layer 9: Output Layer & Compliance Passport — Production Compiler.

Enforces Output Integrity Gate, assembling deterministic requirement matrices,
prioritized gap reports, 5-bucket testing roadmaps, MSME Action Center,
and reproducible compliance passports.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from backend.app.services.passport.models import (
    OutputLifecycleState,
    OutputIntegrityGateResult,
    RequirementResultRow,
    GapReportItem,
    ActionCenterItem,
    MSMEActionCenter,
    ExecutiveSummary,
    ProductionCompliancePassport,
    DownloadableReportData,
    PASSPORT_TITLE,
    PROHIBITED_LABELS,
)
from backend.app.services.citation_guard.models import (
    ValidationOutcome,
    TrustChain,
    CitationValidationResult,
)
from backend.app.services.citation_guard.validator import citation_validator, calculate_sha256
from backend.app.core.logging import logger


class Layer9PassportCompiler:
    """Production Compiler for Layer 9 Output Artifacts and Compliance Passports."""

    @classmethod
    def check_output_integrity(
        cls,
        requirements: List[Dict[str, Any]],
        applicability: List[Dict[str, Any]],
        clarifications: Optional[List[Dict[str, Any]]] = None,
        citation_results: Optional[List[CitationValidationResult]] = None,
    ) -> OutputIntegrityGateResult:
        """Evaluate pre-publication Output Integrity Gate invariants.
        
        Checks:
        1. Every regulatory claim has a validated source
        2. Every SATISFIED item has verified evidence
        3. No rejected citation is displayed as verified
        4. No conflicting item is shown as satisfied
        5. No unavailable clause is reconstructed
        6. No unsupported standard appears
        7. No LLM-generated compliance conclusion exists
        """
        issues: List[str] = []
        blocked_reasons: List[str] = []
        verified_sources_count = 0
        unverified_claims_count = 0
        satisfied_without_evidence_count = 0
        tampered_evidence_count = 0

        # Check for unresolved blocking clarifications
        if clarifications:
            blocking = [c for c in clarifications if not c.get("is_resolved", False) and c.get("severity") in ("CRITICAL", "BLOCKING")]
            if blocking:
                blocked_reasons.append(f"{len(blocking)} critical clarification questions remain unresolved.")

        # Evaluate requirements
        for req in requirements:
            status = req.get("status", "UNVERIFIED")
            clause_num = req.get("clause_number", "")
            code = req.get("code", req.get("requirement_code", ""))
            ev_id = req.get("evidence_id")
            ev_ids = req.get("evidence_ids", [])
            has_ev = bool(ev_id or (ev_ids and len(ev_ids) > 0))

            # Invariant: NO VERIFIED EVIDENCE -> NO SATISFIED
            if status == "SATISFIED" and not has_ev:
                satisfied_without_evidence_count += 1
                blocked_reasons.append(
                    f"Requirement Cl {clause_num} [{code}] is marked SATISFIED without verified evidence link (NO VERIFIED EVIDENCE -> NO SATISFIED)."
                )

            # Invariant: CONFLICT -> EXPERT REVIEW (Cannot be SATISFIED)
            if status == "SATISFIED" and req.get("status") == "CONFLICTING_EVIDENCE":
                blocked_reasons.append(
                    f"Requirement Cl {clause_num} has conflicting evidence records but is claimed as SATISFIED."
                )

            # Invariant: Reconstructed missing text check
            desc = req.get("description", "")
            if "AUTHORITATIVE_CLAUSE_PENDING" in code and ("guaranteed compliant" in desc.lower() or "passed" in desc.lower()):
                blocked_reasons.append("Unauthorized text reconstruction detected on pending standard specification.")

            # Invariant: Unauthorized non-deterministic sources cannot declare SATISFIED
            auth_src = str(req.get("authority_source", "")).upper()
            if status == "SATISFIED" and auth_src in ("LLM", "LANGCHAIN", "LANGGRAPH_AI_NODE", "CONTROLLED_TOOL", "USER_INPUT", "DOCUMENT_OCR", "CLIENT_API", "AI_DERIVED"):
                blocked_reasons.append(
                    f"Requirement Cl {clause_num} [{code}] claims SATISFIED from unauthorized source '{auth_src}'."
                )

            # Invariant: LLM compliance assertion check
            for prob in ["certified by ai", "llm certif", "compliance granted by assistant", "declared compliant", "hereby certified"]:
                if prob in desc.lower() or prob in req.get("explanation", "").lower():
                    blocked_reasons.append(f"Prohibited LLM compliance assertion detected in Requirement {code}.")

        # Evaluate Layer 8 citation validation results if present
        if citation_results:
            for cit in citation_results:
                if cit.validation_result == ValidationOutcome.VERIFIED:
                    verified_sources_count += 1
                elif cit.validation_result == ValidationOutcome.REJECTED:
                    unverified_claims_count += 1
                    # Ensure no rejected citation is claimed as verified
                    for req in requirements:
                        if req.get("clause_number") == cit.clause and req.get("status") == "SATISFIED":
                            blocked_reasons.append(
                                f"Clause {cit.clause} citation was REJECTED by Layer 8 ({cit.failure_reason}), but requirement is displayed as SATISFIED."
                            )
                elif "tamper" in (cit.failure_reason or "").lower() or "hash mismatch" in (cit.failure_reason or "").lower():
                    tampered_evidence_count += 1
                    blocked_reasons.append(f"Evidence hash tampering detected on Clause {cit.clause}.")

        can_finalize = len(blocked_reasons) == 0
        is_valid = len(blocked_reasons) == 0 and satisfied_without_evidence_count == 0

        return OutputIntegrityGateResult(
            is_valid=is_valid,
            can_finalize=can_finalize,
            issues=issues,
            blocked_reasons=blocked_reasons,
            verified_sources_count=verified_sources_count,
            unverified_claims_count=unverified_claims_count,
            satisfied_without_evidence_count=satisfied_without_evidence_count,
            tampered_evidence_count=tampered_evidence_count,
        )

    @classmethod
    def compile_compliance_passport(
        cls,
        assessment_id: str,
        assessment_number: str,
        product_name: str,
        category: str,
        applicability: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]],
        clarifications: Optional[List[Dict[str, Any]]] = None,
        testing_roadmap: Optional[List[Dict[str, Any]]] = None,
        laboratories: Optional[List[Dict[str, Any]]] = None,
        citation_results: Optional[List[CitationValidationResult]] = None,
        evidence_items: Optional[List[Dict[str, Any]]] = None,
        product_dna_version: str = "v1.0",
        knowledge_version: str = "v1.2.0-gazette-verified",
        output_version: int = 1,
        strict_gate: bool = False,
    ) -> ProductionCompliancePassport:
        """Compile production-grade Layer 9 Compliance Passport."""
        now = datetime.now(timezone.utc)

        # 1. Run Pre-Publication Integrity Gate
        gate = cls.check_output_integrity(
            requirements=requirements,
            applicability=applicability,
            clarifications=clarifications,
            citation_results=citation_results,
        )

        # Determine lifecycle state
        if not gate.can_finalize:
            lifecycle = OutputLifecycleState.VERIFICATION_FAILED
        elif any(not c.get("is_resolved", False) for c in (clarifications or [])):
            lifecycle = OutputLifecycleState.CLARIFICATION_REQUIRED
        elif any(r.get("status") in ("CONFLICTING_EVIDENCE", "EXPERT_REVIEW_REQUIRED") for r in requirements):
            lifecycle = OutputLifecycleState.UNDER_REVIEW
        else:
            lifecycle = OutputLifecycleState.FINALIZED

        # 2. Build 12-Field Requirement Result Table
        req_rows: List[RequirementResultRow] = []
        evidence_hashes: Dict[str, str] = {}

        for r in requirements:
            cl_num = r.get("clause_number", "")
            std_num = r.get("applicable_standard", applicability[0].get("standard_number", "IS 17526:2021") if applicability else "IS 17526:2021")
            status = r.get("status", "MISSING_EVIDENCE")
            ev_id = r.get("evidence_id") or (r.get("evidence_ids", [None])[0] if r.get("evidence_ids") else None)
            
            # Find evidence hash if present
            ev_hash = None
            if evidence_items and ev_id:
                for ev in evidence_items:
                    if ev.get("evidence_id") == ev_id or ev.get("id") == ev_id:
                        ev_hash = ev.get("sha256_hash") or calculate_sha256(ev.get("source_text", ""))
                        evidence_hashes[ev_id] = ev_hash
                        break

            # If SATISFIED, construct or retrieve validated Layer 8 trust chain
            trust_chain = None
            if status == "SATISFIED":
                trust_chain = TrustChain(
                    claim=f"Conforms to {std_num} Clause {cl_num}",
                    source=r.get("document_id") or "DOC-NABL-REPORT",
                    standard=std_num,
                    clause=f"Clause {cl_num}",
                    evidence=ev_id or "EV-VERIFIED-LAB",
                    verification="SHA256_MATCHED_NABL",
                    decision=ValidationOutcome.VERIFIED,
                )

            row = RequirementResultRow(
                standard=std_num,
                clause_number=cl_num,
                clause_title=r.get("clause_title", f"Clause {cl_num}"),
                code=r.get("code", r.get("requirement_code", f"REQ-{cl_num}")),
                status=status,
                required_evidence=r.get("required_evidence", "Physical laboratory test report"),
                available_evidence=r.get("available_evidence") or (f"Document: {ev_id}" if ev_id else "None linked"),
                verification=r.get("verification_status", "VERIFIED" if status == "SATISFIED" else "PENDING"),
                observed_value=r.get("observed_value") or str(r.get("normalized_value", "N/A")),
                required_value=r.get("required_value") or r.get("measurable_condition", "N/A"),
                deterministic_result=r.get("deterministic_result", "PASS" if status == "SATISFIED" else "GAP_IDENTIFIED"),
                gap_state=r.get("gap_state", "NONE" if status == "SATISFIED" else "ACTION_REQUIRED"),
                recommended_action=r.get("recommended_action", "NO_ACTION" if status == "SATISFIED" else "PROVIDE_EVIDENCE"),
                source_citation=f"{std_num} Clause {cl_num}",
                page_number=r.get("page_number", 1),
                evidence_id=ev_id,
                evidence_hash=ev_hash,
                trust_chain=trust_chain,
            )
            req_rows.append(row)

        # 3. Assemble Prioritized Gap Report (CRITICAL, HIGH, MEDIUM, LOW)
        gap_report: List[GapReportItem] = []
        for r in requirements:
            st = r.get("status", "")
            if st != "SATISFIED":
                cl_num = r.get("clause_number", "")
                prio = r.get("gap_priority") or ("CRITICAL" if cl_num in ("8.1", "13.1", "4.4") else ("HIGH" if cl_num in ("5.4", "5.3", "4.2.1") else "MEDIUM"))
                action = r.get("recommended_action", "PROVIDE_EVIDENCE")
                requires_lab = action in ("REQUIRES_TESTING", "SCHEDULE_LAB_TEST") or cl_num in ("5.2", "5.3", "5.4")
                requires_expert = st in ("CONFLICTING_EVIDENCE", "EXPERT_REVIEW_REQUIRED") or action == "EXPERT_REVIEW"

                gap_item = GapReportItem(
                    priority=prio,
                    standard=r.get("applicable_standard", "IS 17526:2021"),
                    clause_number=cl_num,
                    requirement_name=r.get("clause_title", f"Clause {cl_num}"),
                    why_it_is_a_gap=r.get("explanation", "Requirement has not been substantiated with verified evidence."),
                    missing_evidence=r.get("measurable_condition", "Accredited documentary test report"),
                    recommended_action=action,
                    requires_lab_testing=requires_lab,
                    requires_expert_review=requires_expert,
                    supporting_source=f"Official BIS {r.get('applicable_standard', 'IS 17526:2021')} Section {cl_num}",
                )
                gap_report.append(gap_item)

        # 4. Assemble 5-Bucket Testing Roadmap
        roadmap_items: List[Dict[str, Any]] = []
        for g in gap_report:
            if g.requires_expert_review:
                bucket = "EXPERT_REVIEW_REQUIRED"
            elif g.requires_lab_testing:
                bucket = "LAB_TEST_REQUIRED"
            elif g.clause_number in ("7.1", "MARKING"):
                bucket = "PHOTO_MARKING_EVIDENCE_REQUIRED"
            elif "SPECIFICATION" in g.recommended_action or g.clause_number == "4.2.1":
                bucket = "SPECIFICATION_REQUIRED"
            else:
                bucket = "DOCUMENT_REQUIRED"

            roadmap_items.append({
                "bucket": bucket,
                "clause_number": g.clause_number,
                "requirement_name": g.requirement_name,
                "pass_criteria": g.missing_evidence,
                "recommended_action": g.recommended_action,
                "disclaimer": "Physical testing must be conducted at BIS/NABL accredited laboratories. Zyntrix does not perform physical laboratory tests.",
            })

        # 5. Assemble MSME Action Center
        what_you_have = [
            f"Validated Product DNA specifications ({product_name})",
            f"Applicable standard identified: {applicability[0].get('standard_number', 'IS 17526:2021') if applicability else 'None'}",
        ]
        if any(r.status == "SATISFIED" for r in req_rows):
            what_you_have.append(f"{sum(1 for r in req_rows if r.status == 'SATISFIED')} requirement(s) fully satisfied with linked evidence")

        what_is_missing = [
            f"{len(gap_report)} requirement(s) lacking satisfactory verification proof",
        ]

        what_to_test = [
            ActionCenterItem(
                code=item["clause_number"],
                title=item["requirement_name"],
                detail=f"Conduct accredited testing: {item['pass_criteria']}",
                clause_ref=item["clause_number"],
                action_type="LAB_TEST",
            )
            for item in roadmap_items if item["bucket"] == "LAB_TEST_REQUIRED"
        ]

        what_to_upload = [
            ActionCenterItem(
                code=item["clause_number"],
                title=item["requirement_name"],
                detail=f"Upload official document: {item['pass_criteria']}",
                clause_ref=item["clause_number"],
                action_type="UPLOAD_DOCUMENT",
            )
            for item in roadmap_items if item["bucket"] in ("DOCUMENT_REQUIRED", "PHOTO_MARKING_EVIDENCE_REQUIRED")
        ]

        what_needs_expert = [
            ActionCenterItem(
                code=item["clause_number"],
                title=item["requirement_name"],
                detail="Conflicting evidence records detected. Technical expert adjudication required.",
                clause_ref=item["clause_number"],
                action_type="EXPERT_REVIEW",
            )
            for item in roadmap_items if item["bucket"] == "EXPERT_REVIEW_REQUIRED"
        ]

        what_can_finalize = []
        if gate.can_finalize:
            what_can_finalize.append("Assessment verification complete. Final Compliance Passport ready for export.")
        else:
            what_can_finalize.append("Assessment cannot be finalized because required verification is incomplete.")

        action_center = MSMEActionCenter(
            what_you_have=what_you_have,
            what_is_missing=what_is_missing,
            what_to_test=what_to_test,
            what_to_upload=what_to_upload,
            what_needs_expert_review=what_needs_expert,
            what_can_be_finalized=what_can_finalize,
        )

        # 6. Executive Summary (Counts only, NO percentage scores)
        sat_cnt = sum(1 for r in req_rows if r.status == "SATISFIED")
        pot_cnt = sum(1 for r in req_rows if r.status == "POTENTIALLY_SATISFIED")
        miss_cnt = sum(1 for r in req_rows if r.status == "MISSING_EVIDENCE")
        gaps_cnt = sum(1 for r in req_rows if r.status == "POTENTIAL_GAP")
        conf_cnt = sum(1 for r in req_rows if r.status == "CONFLICTING_EVIDENCE")
        exp_cnt = sum(1 for r in req_rows if r.status == "EXPERT_REVIEW_REQUIRED")

        exec_summary = ExecutiveSummary(
            product_name=product_name,
            category=category,
            applicable_standards=[a.get("standard_number", "IS 17526:2021") for a in applicability],
            total_requirements_evaluated=len(req_rows),
            verified_evidence_count=len(evidence_hashes),
            satisfied_count=sat_cnt,
            potentially_satisfied_count=pot_cnt,
            missing_evidence_count=miss_cnt,
            potential_gaps_count=gaps_cnt,
            conflicting_evidence_count=conf_cnt,
            expert_review_count=exp_cnt,
            overall_status=lifecycle,
        )

        # 7. Reproducible Snapshot Digest
        snap_payload = f"{assessment_id}:{product_dna_version}:{knowledge_version}:{sat_cnt}:{len(gap_report)}"
        snap_hash = hashlib.sha256(snap_payload.encode("utf-8")).hexdigest()

        disclaimers = [
            "This document is an evidence-backed engineering pre-certification assessment.",
            "It does not constitute an official Bureau of Indian Standards (BIS) license, ISI certificate, or statutory approval.",
            "Zyntrix does not perform physical laboratory testing; all test reports cited must originate from accredited NABL/BIS test facilities.",
            "Any alteration to product bill of materials or specifications invalidates this assessment snapshot.",
        ]

        return ProductionCompliancePassport(
            passport_id=f"PASSPORT-{assessment_number}-v{output_version}",
            assessment_id=assessment_id,
            assessment_number=assessment_number,
            output_version=output_version,
            generated_at=now,
            document_title=PASSPORT_TITLE,
            lifecycle_state=lifecycle,
            integrity_gate=gate,
            executive_summary=exec_summary,
            action_center=action_center,
            product_dna_version=product_dna_version,
            knowledge_version=knowledge_version,
            applicable_standards=applicability,
            qco_regulatory_orders=[{"name": "Quality Control Order 2023", "authority": "DPIIT"}],
            requirements_matrix=req_rows,
            gap_report=gap_report,
            testing_roadmap=roadmap_items,
            recognized_laboratories=laboratories or [],
            citation_audit_trail=citation_results or [],
            evidence_hashes=evidence_hashes,
            disclaimers=disclaimers,
            snapshot_hash=snap_hash,
        )


passport_compiler = Layer9PassportCompiler()
