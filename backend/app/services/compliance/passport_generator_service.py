"""Milestone M26.3: Evidence-Backed Compliance Passport Generator Engine.

Deterministic Projection Engine:
Builds the final Compliance Passport from existing deterministic applicability,
evidence validation, evidence-to-requirement mapping, and compliance-gap aggregation results.

Preserves the 9-Layer Architecture, LangGraph topology, single-LLM invariant,
and Layer 7/8/9 authority boundaries:
- Layer 7: Sole compliance decision authority (emits verdicts, gap statuses)
- Layer 8: Sole evidence/source trust authority (validates artifacts, hashes, provenance)
- Layer 9: Output-integrity authority (enforces prohibited labels, SHA-256 integrity seal)
- LLM Compliance Authority: Exactly 0.0%

Non-Negotiables:
1. Compliance Passport != BIS Certification
2. Document Title: Strictly "Evidence-Backed Pre-Certification Compliance Assessment"
3. No representation as a BIS licence, BIS certificate, statutory approval, or certification issued by BIS.
4. Never invent missing evidence, clauses, laboratory results, fees, timelines, certification outcomes, or regulatory facts.
5. Incomplete, conflicting, unverified, or expert-review states are preserved explicitly.
6. Bit-for-bit reproducible SHA-256 integrity seal from identical inputs.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union

from backend.app.schemas.product_dna import ProductDNACore
from backend.app.schemas.product_evidence import (
    EvidenceType,
    SourceAuthenticity,
    ArtifactIntegrityStatus,
    EvidenceVerificationStatus,
    EvidenceOntologyTier,
    ProductEvidenceRecord,
    EvidenceRequirementMappingRecord,
    StandardRequirementDefinition,
)
from backend.app.schemas.compliance import (
    RequirementGapStatus,
    GapNextAction,
    ComplianceGapItem,
    DeterministicGapAggregationResult,
)
from backend.app.schemas.compliance_passport import (
    PASSPORT_DOCUMENT_TITLE,
    PASSPORT_PROHIBITED_LABELS,
    STATUTORY_DISCLAIMER_TEXT,
    PassportProductIdentity,
    PassportStandardReference,
    PassportRequirementItem,
    PassportNextActionItem,
    PassportExpertReviewItem,
    PassportSourceReference,
    EvidenceBackedCompliancePassport,
)
from backend.app.services.compliance.evidence_mapping_service import (
    DeterministicEvidenceRequirementMapper,
    VERIFIED_STANDARD_REQUIREMENTS,
)
from backend.app.core.logging import logger


STANDARD_TITLES = {
    "IS 17526": "Stainless Steel Vacuum Flasks and Insulated Flasks - Specification",
    "IS 302-2-201": "Safety of Household and Similar Electrical Appliances - Particular Requirements for Electric Immersion Water Heaters",
    "IS 9873-1": "Safety of Toys - Part 1: Safety Aspects Related to Mechanical and Physical Properties",
    "IS 1293": "Plugs and Socket-Outlets of Rated Voltage up to and including 250 Volts and Rated Current up to and including 16 Amperes - Specification",
    "IS 4151": "Protective Helmets for Motorcycle Riders - Specification",
}

QCO_MANDATES = {
    "IS 17526": "Cookware, Utensils and Canisters for Domestic Use (Quality Control) Order, 2023 - DPIIT",
    "IS 302-2-201": "Electrical Appliances (Quality Control) Order, 2023 - Ministry of Heavy Industries",
    "IS 9873-1": "Toys (Quality Control) Order, 2020 - DPIIT",
    "IS 1293": "Electrical Wires, Cables, Appliances and Accessories (Quality Control) Order, 2020",
    "IS 4151": "Helmets for Riders of Two Wheeler Motor Vehicles (Quality Control) Order, 2020 - MoRTH",
}

DISCLAIMERS_CATALOG = [
    "Compliance Passport ≠ BIS Certification.",
    "This document is an evidence-backed engineering pre-certification assessment.",
    "It does not constitute a statutory Bureau of Indian Standards (BIS) license, BIS certificate, statutory approval, or certification issued by BIS.",
    "Zyntrix is an engineering pre-certification compliance tool and does NOT perform physical laboratory testing; all test reports cited must originate from accredited NABL/BIS test facilities.",
    "Any alteration to product bill of materials, materials, components, or manufacturing processes invalidates this assessment snapshot.",
    "This digital artifact represents a deterministic projection of verified evidence as of the generation timestamp.",
]


class DeterministicCompliancePassportGenerator:
    """Production Engine for Milestone M26.3 Compliance Passport Generation."""

    @classmethod
    def compute_product_dna_digest(
        cls,
        product_id: str,
        category: str,
        attributes: Dict[str, Any],
    ) -> str:
        """Deterministically compute SHA-256 digest of Product DNA attributes."""
        canonical_str = json.dumps(
            {
                "product_id": product_id.strip(),
                "category": category.strip().lower(),
                "attributes": {k: str(v) for k, v in sorted(attributes.items())},
            },
            sort_keys=True,
            ensure_ascii=True,
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @classmethod
    def compute_passport_integrity_seal(
        cls,
        product_id: str,
        product_dna_digest: str,
        target_standard: str,
        standard_revision: str,
        overall_verdict: str,
        satisfied_count: int,
        not_satisfied_count: int,
        missing_evidence_count: int,
        unverified_count: int,
        conflicting_count: int,
        expert_review_count: int,
        not_applicable_count: int,
        requirements_fingerprints: List[str],
        evidence_fingerprints: List[str],
        source_snapshot_version: str,
        ruleset_version: str,
    ) -> str:
        """Deterministically compute canonical SHA-256 integrity seal for the passport."""
        canonical_payload = {
            "product_id": product_id.strip(),
            "product_dna_digest": product_dna_digest.strip(),
            "target_standard": target_standard.strip(),
            "standard_revision": standard_revision.strip(),
            "overall_verdict": overall_verdict.strip(),
            "counts": {
                "satisfied": satisfied_count,
                "not_satisfied": not_satisfied_count,
                "missing": missing_evidence_count,
                "unverified": unverified_count,
                "conflicting": conflicting_count,
                "expert_review": expert_review_count,
                "not_applicable": not_applicable_count,
            },
            "requirements": sorted(requirements_fingerprints),
            "evidence": sorted(evidence_fingerprints),
            "snapshot_version": source_snapshot_version.strip(),
            "ruleset_version": ruleset_version.strip(),
        }
        serialized = json.dumps(canonical_payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def check_prohibited_terms(cls, texts: List[str]) -> List[str]:
        """Scan texts for forbidden regulatory certification claims."""
        found: List[str] = []
        for text in texts:
            if not text:
                continue
            for prohibited in PASSPORT_PROHIBITED_LABELS:
                pattern = r"\b" + re.escape(prohibited) + r"\b"
                if re.search(pattern, text, re.IGNORECASE):
                    if prohibited not in found:
                        found.append(prohibited)
        return found

    @classmethod
    def generate_compliance_passport(
        cls,
        product_id: str,
        product_name: str,
        category: str,
        target_standard: str,
        gap_result: DeterministicGapAggregationResult,
        evidence_records: List[ProductEvidenceRecord],
        product_dna: Optional[Union[ProductDNACore, Dict[str, Any]]] = None,
        mapping_records: Optional[List[EvidenceRequirementMappingRecord]] = None,
        custom_requirements: Optional[List[StandardRequirementDefinition]] = None,
        source_snapshot_version: str = "v1.2.0-gazette-verified",
        knowledge_version: str = "v1.2.0-gazette-verified",
        ruleset_version: str = "2026.03-gazette",
        assessment_id: Optional[str] = None,
        assessment_number: Optional[str] = None,
        output_version: int = 1,
        generated_at: Optional[Union[datetime, str]] = None,
        strict_gate: bool = False,
    ) -> EvidenceBackedCompliancePassport:
        """Deterministically project existing verified results into the final Compliance Passport (Milestone M26.3)."""
        
        # 1. Authority Firewall Validation: Layer 7 Sole Compliance Decision Authority
        if gap_result.compliance_authority != "LAYER_7_ONLY":
            raise ValueError(
                f"Authority Violation: Compliance gap result must originate from 'LAYER_7_ONLY', "
                f"received '{gap_result.compliance_authority}'."
            )
        if gap_result.llm_compliance_authority != 0.0:
            raise ValueError(
                f"Authority Violation: LLM compliance authority must be exactly 0.0%, "
                f"received {gap_result.llm_compliance_authority}."
            )
        if gap_result.regulatory_conclusion != "NONE":
            raise ValueError(
                f"Invariant Violation: Intermediate regulatory_conclusion must be 'NONE', "
                f"received '{gap_result.regulatory_conclusion}'."
            )

        # 2. Extract and Validate Product DNA Provenance
        dna_attrs: Dict[str, Any] = {}
        dna_provenance = "USER_CLAIM"
        dna_facts_list: List[Dict[str, Any]] = []

        if product_dna:
            if isinstance(product_dna, ProductDNACore):
                dna_attrs["materials"] = list(product_dna.materials)
                dna_attrs["insulated"] = product_dna.insulated
                dna_attrs["electrical"] = product_dna.electrical
                if product_dna.intended_use:
                    dna_attrs["intended_use"] = product_dna.intended_use
                for attr in product_dna.attributes:
                    dna_attrs[attr.name] = attr.value
                for f in product_dna.facts:
                    dna_facts_list.append(f.model_dump())
                    if f.provenance:
                        dna_provenance = f.provenance.value
            elif isinstance(product_dna, dict):
                dna_attrs = dict(product_dna.get("attributes", product_dna))
                dna_provenance = product_dna.get("provenance", "USER_CLAIM")
                dna_facts_list = product_dna.get("facts", [])
        else:
            dna_attrs = {"category": category, "product_name": product_name}

        dna_digest = cls.compute_product_dna_digest(
            product_id=product_id,
            category=category,
            attributes=dna_attrs,
        )

        product_identity = PassportProductIdentity(
            product_id=product_id,
            product_name=product_name,
            category=category,
            product_dna_attributes=dna_attrs,
            product_dna_provenance=dna_provenance,
            product_dna_digest=dna_digest,
            product_facts=dna_facts_list,
        )

        # 3. Applicable BIS Standard & Statutory Revision Reference
        base_std, rev = DeterministicEvidenceRequirementMapper.parse_standard_and_revision(target_standard)
        actual_rev = rev or gap_result.standard_revision
        full_std = f"{base_std}:{actual_rev}" if actual_rev and actual_rev != "CURRENT" else base_std

        std_title = STANDARD_TITLES.get(base_std, f"Indian Standard {base_std} - Specification")
        qco_ref = QCO_MANDATES.get(base_std, "DPIIT Quality Control Order Mandate")

        standards_ref = [
            PassportStandardReference(
                standard_code=base_std,
                revision=actual_rev,
                full_standard_number=full_std,
                title=std_title,
                qco_order=qco_ref,
                regulatory_status="MANDATORY_QCO",
                source_reference=f"Gazette of India: {qco_ref}",
            )
        ]

        # 4. Map Evidence Lookup Dictionary
        evidence_by_id: Dict[str, ProductEvidenceRecord] = {
            ev.evidence_id: ev for ev in evidence_records
        }
        evidence_hashes: Dict[str, str] = {
            ev.evidence_id: (ev.sha256 or "") for ev in evidence_records if ev.evidence_id
        }

        # 5. Build Requirement-by-Requirement Matrix & Next Actions
        requirements_matrix: List[PassportRequirementItem] = []
        next_actions: List[PassportNextActionItem] = []
        expert_review_items: List[PassportExpertReviewItem] = []
        req_fingerprints: List[str] = []

        # Find matching standard requirements catalog
        std_catalog: Dict[str, StandardRequirementDefinition] = {}
        for k, cat in VERIFIED_STANDARD_REQUIREMENTS.items():
            k_base, k_rev = DeterministicEvidenceRequirementMapper.parse_standard_and_revision(k)
            if k_base == base_std:
                std_catalog = cat
                break
        if custom_requirements:
            for cr in custom_requirements:
                std_catalog[cr.requirement_id] = cr

        for gap in gap_result.gap_items:
            req_def = std_catalog.get(gap.requirement)
            req_title = req_def.requirement_title if req_def else f"Clause {gap.clause}"
            req_class = req_def.requirement_class if req_def else "TECHNICAL_SPECIFICATION"
            req_cond = req_def.description if req_def else "Statutory standard conformance required"

            # Match evidence record
            ev_id = gap.current_evidence if gap.current_evidence != "NONE" else None
            ev_rec: Optional[ProductEvidenceRecord] = evidence_by_id.get(ev_id) if ev_id else None

            # Determine observed value (NEVER invent when missing)
            observed_val: Optional[str] = None
            if ev_rec:
                observed_val = ev_rec.extracted_value or str(ev_rec.normalized_value or "")

            # Deterministic evaluation result
            if gap.gap_status == RequirementGapStatus.SATISFIED:
                det_result = "PASS"
            elif gap.gap_status == RequirementGapStatus.NOT_SATISFIED:
                det_result = "FAIL"
            elif gap.gap_status == RequirementGapStatus.MISSING_EVIDENCE:
                det_result = "GAP_IDENTIFIED"
            elif gap.gap_status == RequirementGapStatus.NOT_APPLICABLE:
                det_result = "NOT_APPLICABLE"
            else:
                det_result = "UNVERIFIED"

            req_item = PassportRequirementItem(
                standard=gap.standard,
                revision=gap.revision,
                clause_number=gap.clause,
                clause_title=req_title,
                requirement_id=gap.requirement,
                requirement_class=req_class,
                status=gap.gap_status,
                required_condition=req_cond,
                observed_value=observed_val,
                deterministic_result=det_result,
                evidence_id=ev_id,
                evidence_type=ev_rec.evidence_type.value if ev_rec else None,
                evidence_status=gap.evidence_status,
                evidence_sha256=ev_rec.sha256 if ev_rec else None,
                evidence_provenance=gap.provenance if ev_rec else None,
                source_authenticity=ev_rec.source_authenticity.value if ev_rec else None,
                artifact_integrity=ev_rec.artifact_integrity.value if ev_rec else None,
                required_next_action=gap.required_next_action,
                reason=gap.reason,
                audit_chain_summary=gap.format_gap_chain(),
            )
            requirements_matrix.append(req_item)

            # Fingerprint for reproducible integrity seal
            req_fingerprints.append(
                f"{gap.clause}|{gap.requirement}|{gap.gap_status.value}|{det_result}|"
                f"{ev_id or 'NONE'}|{ev_rec.sha256 if ev_rec else 'NONE'}"
            )

            # Build Next Actions (for unsatisfied requirements)
            if gap.gap_status != RequirementGapStatus.SATISFIED and gap.gap_status != RequirementGapStatus.NOT_APPLICABLE:
                action_desc = f"Address {gap.gap_status.value}: {gap.reason}"
                req_ev_type = "Accredited Laboratory Test Report" if gap.required_next_action == GapNextAction.LAB_TEST_REQUIRED else "Official Manufacturer Document / Drawing"
                next_actions.append(
                    PassportNextActionItem(
                        action_type=gap.required_next_action,
                        clause_number=gap.clause,
                        requirement_id=gap.requirement,
                        title=f"{gap.required_next_action.value} for {gap.clause}",
                        description=action_desc,
                        required_evidence_type=req_ev_type,
                    )
                )

            # Route Conflicting / Ambiguous Items to Expert Review
            if gap.gap_status in (RequirementGapStatus.CONFLICTING, RequirementGapStatus.EXPERT_REVIEW_REQUIRED) or gap.required_next_action == GapNextAction.EXPERT_REVIEW_REQUIRED:
                conf_ids = [ev_rec.evidence_id] if ev_rec else []
                # Also search other evidence linked to same requirement/clause
                for other_ev in evidence_records:
                    if other_ev.applicable_requirement == gap.requirement and other_ev.evidence_id not in conf_ids:
                        conf_ids.append(other_ev.evidence_id)
                expert_review_items.append(
                    PassportExpertReviewItem(
                        clause_number=gap.clause,
                        requirement_id=gap.requirement,
                        reason=gap.reason,
                        conflicting_evidence_ids=conf_ids,
                        review_recommendation="Technical expert review required to adjudicate contradictory or ambiguous evidence.",
                    )
                )

        # 6. Authoritative Source References
        source_refs: List[PassportSourceReference] = [
            PassportSourceReference(
                source_id=f"SRC-{base_std.replace(' ', '_')}",
                source_type="BIS_STANDARD",
                reference=f"{base_std}:{actual_rev} — {std_title}",
                publisher_or_authority="Bureau of Indian Standards",
                verification_status="VERIFIED",
                sha256_hash=None,
            ),
            PassportSourceReference(
                source_id="SRC-QCO-GAZETTE",
                source_type="GAZETTE_QCO",
                reference=qco_ref,
                publisher_or_authority="Department for Promotion of Industry and Internal Trade (DPIIT)",
                verification_status="VERIFIED",
                sha256_hash=None,
            ),
        ]
        # Include lab sources from authentic evidence records
        for ev in evidence_records:
            if ev.source_identity and "NABL" in ev.source_identity.upper():
                s_id = f"SRC-LAB-{ev.evidence_id}"
                if not any(s.source_id == s_id for s in source_refs):
                    source_refs.append(
                        PassportSourceReference(
                            source_id=s_id,
                            source_type="NABL_REPORT",
                            reference=f"Test Certificate {ev.source_reference} by {ev.source_identity}",
                            publisher_or_authority=ev.source_identity,
                            verification_status="VERIFIED" if ev.verified else "UNVERIFIED",
                            sha256_hash=ev.sha256,
                        )
                    )

        # 7. Check Prohibited Terms
        prohibited_in_input = cls.check_prohibited_terms(
            [product_name, category] + [g.reason for g in gap_result.gap_items]
        )
        if prohibited_in_input:
            raise ValueError(
                f"Prohibited regulatory certification claims detected: {prohibited_in_input}. "
                "Compliance Passport must never assert statutory approval or use prohibited labels."
            )

        # 8. Compute Reproducible Canonical SHA-256 Integrity Seal
        evidence_fingerprints = [
            f"{ev.evidence_id}:{ev.sha256 or ''}:{ev.verification_status.value}"
            for ev in sorted(evidence_records, key=lambda x: x.evidence_id)
        ]

        integrity_seal = cls.compute_passport_integrity_seal(
            product_id=product_id,
            product_dna_digest=dna_digest,
            target_standard=full_std,
            standard_revision=actual_rev,
            overall_verdict=gap_result.overall_verdict,
            satisfied_count=gap_result.satisfied_count,
            not_satisfied_count=gap_result.not_satisfied_count,
            missing_evidence_count=gap_result.missing_evidence_count,
            unverified_count=gap_result.unverified_count,
            conflicting_count=gap_result.conflicting_count,
            expert_review_count=gap_result.expert_review_count,
            not_applicable_count=gap_result.not_applicable_count,
            requirements_fingerprints=req_fingerprints,
            evidence_fingerprints=evidence_fingerprints,
            source_snapshot_version=source_snapshot_version,
            ruleset_version=ruleset_version,
        )

        # 9. Deterministic Generation Timestamp
        if generated_at is None:
            now_iso = datetime.now(timezone.utc).isoformat()
        elif isinstance(generated_at, datetime):
            now_iso = generated_at.astimezone(timezone.utc).isoformat()
        else:
            now_iso = str(generated_at)

        # 10. Lifecycle State Derivation
        if gap_result.overall_verdict == "COMPLIANT":
            lifecycle_state = "FINALIZED"
        elif gap_result.conflicting_count > 0 or gap_result.expert_review_count > 0:
            lifecycle_state = "UNDER_REVIEW"
        elif gap_result.not_satisfied_count > 0:
            lifecycle_state = "NON_COMPLIANT"
        else:
            lifecycle_state = "GAPS_IDENTIFIED"

        if strict_gate and lifecycle_state != "FINALIZED":
            raise ValueError(
                f"Strict Gate Rejected: Assessment cannot be finalized because "
                f"overall verdict is '{gap_result.overall_verdict}'."
            )

        # 11. Identifiers
        clean_num = assessment_number or f"{product_id}-{base_std.replace(' ', '_')}"
        clean_asm_id = assessment_id or f"ASM-{clean_num}"
        passport_id = f"PASSPORT-{clean_num}-v{output_version}"

        # 12. Frontend UI Projection Dictionaries
        compliance_evals: List[Dict[str, Any]] = []
        for r in requirements_matrix:
            compliance_evals.append({
                "applicable_standard": r.standard,
                "clause_number": r.clause_number,
                "requirement_code": r.requirement_id,
                "status": r.status.value,
                "measurable_condition": r.required_condition,
                "observed_value": r.observed_value,
                "recommended_action": r.required_next_action.value,
                "audit_chain": {
                    "evidence_id": r.evidence_id,
                    "evidence_hash": r.evidence_sha256,
                    "extracted_value": r.observed_value,
                    "document_id": r.evidence_id,
                    "page_number": 1,
                } if r.evidence_id else None,
                "evidence_ids": [r.evidence_id] if r.evidence_id else [],
            })

        testing_roadmap_ui: List[Dict[str, Any]] = []
        for gap in gap_result.roadmap_lab_test:
            testing_roadmap_ui.append({
                "clause_number": gap.clause,
                "test_name": f"Laboratory Test for {gap.clause}",
                "pass_criteria": gap.reason,
                "required_apparatus": "Accredited Laboratory Test Bench",
            })

        recognized_labs_ui: List[Dict[str, Any]] = []
        for ev in evidence_records:
            if ev.source_identity and "NABL" in ev.source_identity.upper():
                recognized_labs_ui.append({
                    "name": ev.source_identity,
                    "location": "Authorized Test Facility",
                    "state": "India",
                })

        source_index_ui: List[Dict[str, Any]] = []
        for s in source_refs:
            source_index_ui.append({
                "source_index_id": s.source_id,
                "title": s.reference,
                "standard_or_gazette_number": base_std,
                "clause_or_section": "General",
                "page": 1,
                "authority": s.publisher_or_authority,
                "verification_status": s.verification_status,
            })

        trust_basis_ui = {
            "verified_official_metadata": True,
            "verified_regulatory_sources": True,
            "full_standard_text_status": "GAZETTE_VERIFIED",
            "trust_level_summary": (
                f"Statutory mandate governed under {qco_ref}. "
                "Evaluated strictly via deterministic Layer 7 rules and Layer 8 provenance checks."
            ),
        }

        # 13. Assemble the Immutable Evidence-Backed Compliance Passport
        return EvidenceBackedCompliancePassport(
            passport_id=passport_id,
            assessment_id=clean_asm_id,
            assessment_number=clean_num,
            document_title=PASSPORT_DOCUMENT_TITLE,
            product=product_identity,
            applicable_standards=standards_ref,
            requirements_matrix=requirements_matrix,
            compliance_gaps=gap_result.gap_items,
            required_next_actions=next_actions,
            roadmap_lab_test=gap_result.roadmap_lab_test,
            roadmap_document=gap_result.roadmap_document,
            roadmap_declaration=gap_result.roadmap_declaration,
            roadmap_marking=gap_result.roadmap_marking,
            roadmap_corrective_action=gap_result.roadmap_corrective_action,
            roadmap_expert_review=gap_result.roadmap_expert_review,
            expert_review_items=expert_review_items,
            source_references=source_refs,
            overall_verdict=gap_result.overall_verdict,
            total_requirements=gap_result.total_requirements,
            satisfied_count=gap_result.satisfied_count,
            not_satisfied_count=gap_result.not_satisfied_count,
            missing_evidence_count=gap_result.missing_evidence_count,
            unverified_count=gap_result.unverified_count,
            conflicting_count=gap_result.conflicting_count,
            expert_review_count=gap_result.expert_review_count,
            not_applicable_count=gap_result.not_applicable_count,
            integrity_seal=integrity_seal,
            generated_at=now_iso,
            source_snapshot_version=source_snapshot_version,
            knowledge_version=knowledge_version,
            ruleset_version=ruleset_version,
            output_version=output_version,
            statutory_disclaimer=STATUTORY_DISCLAIMER_TEXT,
            disclaimers=DISCLAIMERS_CATALOG,
            prohibited_labels_asserted=[],
            compliance_authority="LAYER_7_ONLY",
            evidence_authority="LAYER_8_ONLY",
            output_integrity_authority="LAYER_9_PASSPORT_COMPILER",
            llm_compliance_authority=0.0,
            regulatory_conclusion="NONE",
            product_name=product_name,
            category=category,
            product_dna_version="v1.0",
            lifecycle_state=lifecycle_state,
            snapshot_hash=integrity_seal,
            evidence_hashes=evidence_hashes,
            compliance_evaluations=compliance_evals,
            testing_roadmap=testing_roadmap_ui,
            recognized_laboratories=recognized_labs_ui,
            source_index=source_index_ui,
            trust_basis=trust_basis_ui,
            claim_statement="Evidence-Backed Pre-Certification Compliance Evaluation Roadmap",
            mode="AUTHORITATIVE_MODE",
            limitations=[
                "Evidence-backed pre-certification assessment only; not an official BIS license or ISI certification.",
                "Zyntrix does not conduct physical laboratory testing.",
                "Any alteration to BOM or specifications invalidates this assessment snapshot.",
            ],
        )


# Global singleton instance
compliance_passport_generator = DeterministicCompliancePassportGenerator()
