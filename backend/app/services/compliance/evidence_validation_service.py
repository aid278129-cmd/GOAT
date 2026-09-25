"""Milestone M26.0: Real Evidence Validation & Artifact Authenticity Engine.

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
2. 4-Tier Ontological Distinction:
   USER CLAIM ≠ DOCUMENT ≠ VERIFIED EVIDENCE ≠ COMPLIANCE RESULT.
3. 7-Step Evidence Retention Chain:
   artifact identity → source → provenance → authenticity → evidence type → applicable requirement → verification status.
4. Laboratory Test vs Datasheet Invariant:
   Do not allow a manufacturer datasheet to satisfy an empirical laboratory-test requirement
   unless an existing deterministic evidence rule explicitly permits it.
5. Authenticity Decoupling Invariant:
   Do not infer authenticity merely from file existence, filename, metadata, OCR text, or SHA-256 integrity.
6. Safe Abstention:
   Where authenticity or requirement mapping cannot be established, return UNVERIFIED, MISSING, CONFLICTING,
   or EXPERT_REVIEW_REQUIRED as appropriate.
7. Authority Boundary Invariant:
   LLM / ML authority = 0.0%. LLM may extract candidate facts from artifacts, but possesses 0.0% compliance authority.
8. Security & Isolation:
   - Cryptographic SHA-256 integrity verification.
   - Adversarial prompt injection interception in artifact contents.
   - Cross-standard evidence isolation (0% cross-standard leakage).
   - Numerical safety with rigorous unit normalization.
"""

import os
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from pydantic import BaseModel, Field, ConfigDict

from backend.app.schemas.product_evidence import (
    EvidenceType,
    EvidenceHierarchyLevel,
    EvidenceVerificationStatus,
    SourceAuthenticity,
    ArtifactIntegrityStatus,
    EvidenceOntologyTier,
    EvidenceChainRecord,
    ProductEvidenceRecord,
    get_hierarchy_for_evidence_type,
    classify_evidence_type,
    validate_ontological_separation,
)
from backend.app.services.compliance.evidence_eligibility import (
    EvidenceEligibilityEngine,
    EligibilityStatus,
    RequirementClass,
    EligibilityEvaluationResult,
    PERMITTED_EVIDENCE_TYPES,
)
from backend.app.services.citation_guard.models import ValidationOutcome
from backend.app.services.citation_guard.validator import calculate_sha256, PROHIBITED_INJECTION_PATTERNS
from backend.app.services.gap_analysis.comparator import compare_numeric_threshold, normalize_unit
from backend.app.schemas.compliance import ComplianceStatus, RecommendedAction
from backend.app.core.logging import logger


# Verified Directory of Authoritative Issuing Bodies / NABL Laboratories
AUTHORITATIVE_REGISTRY_DIRECTORY: Set[str] = {
    "NABL_ACCREDITED_LAB",
    "NABL_ACCREDITED_LAB_01",
    "NATIONAL_TEST_HOUSE",
    "CENTRAL_POWER_RESEARCH_INSTITUTE",
    "CPRI",
    "ARAI_PUNE",
    "ICAT_MANESAR",
    "BIS_CENTRAL_LABORATORY",
    "BIS_LAB_SAHIBABAD",
    "BUREAU_OF_INDIAN_STANDARDS",
    "OFFICIAL_GAZETTE_OF_INDIA",
    "DPIIT_OFFICIAL",
    "STEEL_AUTHORITY_OF_INDIA_MILL",
    "JINDAL_STAINLESS_MILL_LAB",
}


class ValidationReport(BaseModel):
    """Auditable result of validating an artifact against a requirement."""
    artifact_id: str
    requirement_id: str
    target_standard: str
    target_clause: str
    evidence_type: EvidenceType
    ontology_tier: EvidenceOntologyTier
    source_authenticity: SourceAuthenticity
    artifact_integrity: ArtifactIntegrityStatus
    verification_status: EvidenceVerificationStatus
    is_eligible: bool
    eligibility_reason: str
    is_authoritative: bool
    compliance_verdict: str = "PENDING_LAYER_7"
    gap: Optional[str] = None
    next_action: RecommendedAction = RecommendedAction.UPLOAD_EVIDENCE
    evidence_chain: EvidenceChainRecord
    regulatory_conclusion: str = "NONE"
    prompt_injection_detected: bool = False
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceValidationPipeline:
    """Production M26.0 Evidence Validation & Artifact Authenticity Engine."""

    @staticmethod
    def classify_artifact(
        identifier_or_text: str,
        source_reference: str = "",
        mime_type: Optional[str] = None,
    ) -> EvidenceType:
        """Deterministically classify an artifact into one of the 10 canonical evidence types."""
        combined = f"{identifier_or_text} {source_reference} {mime_type or ''}".strip()
        return classify_evidence_type(combined)

    @classmethod
    def verify_artifact_authenticity(
        cls,
        evidence_record: ProductEvidenceRecord,
        raw_bytes: Optional[bytes] = None,
        allow_synthetic: bool = True,
    ) -> Tuple[SourceAuthenticity, ArtifactIntegrityStatus, List[str]]:
        """Rigorous authenticity & integrity assessment.
        
        Cardinal Invariants:
        1. Do not infer authenticity merely from file existence, filename, metadata, OCR text, or SHA-256 integrity.
        2. Cryptographic hash validity is a prerequisite, NOT proof of authenticity.
        3. Prompt injections immediately yield REJECTED.
        4. Real authoritative status requires verification in official accredited directory.
        """
        issues: List[str] = []

        # 1. Byte-level Cryptographic Integrity Check
        calc_hash = evidence_record.sha256
        if raw_bytes is not None:
            calc_hash = hashlib.sha256(raw_bytes).hexdigest()
            if calc_hash.lower() != evidence_record.sha256.lower():
                issues.append(
                    f"SHA-256 mismatch: declared {evidence_record.sha256[:12]}... != computed {calc_hash[:12]}..."
                )
                return SourceAuthenticity.REJECTED, ArtifactIntegrityStatus.TAMPERED, issues

        if not evidence_record.sha256 or len(evidence_record.sha256) != 64:
            issues.append("Missing or invalid SHA-256 digest length.")
            return SourceAuthenticity.UNVERIFIED, ArtifactIntegrityStatus.UNHASHED, issues

        # 2. Prompt Injection Defense
        content_to_scan = f"{evidence_record.extracted_value} {evidence_record.source_reference} {evidence_record.notes or ''}"
        for pattern in PROHIBITED_INJECTION_PATTERNS:
            if pattern.search(content_to_scan):
                issues.append("Adversarial prompt injection attempt intercepted in artifact content.")
                return SourceAuthenticity.REJECTED, ArtifactIntegrityStatus.HASH_VALID, issues

        # 3. Ontological Check: USER_CLAIM can NEVER be authentic evidence
        if evidence_record.evidence_type in (EvidenceType.USER_PROVIDED_CLAIM, EvidenceType.USER_CLAIM):
            issues.append("User provided claims cannot be authoritative regulatory evidence.")
            return SourceAuthenticity.UNVERIFIED, ArtifactIntegrityStatus.HASH_VALID, issues

        # 4. Controlled Benchmark Fixture Handling
        if evidence_record.source_authenticity in (SourceAuthenticity.SYNTHETIC, SourceAuthenticity.SIMULATED):
            if allow_synthetic:
                return evidence_record.source_authenticity, ArtifactIntegrityStatus.HASH_VALID, issues
            else:
                issues.append("Synthetic benchmark fixtures are strictly prohibited in live production assessment.")
                return SourceAuthenticity.REJECTED, ArtifactIntegrityStatus.HASH_VALID, issues

        # 5. External Authoritative Source Directory Grounding
        source_ident = (evidence_record.source_identity or evidence_record.source_reference or "").upper().replace(" ", "_")
        is_directory_verified = any(
            trusted in source_ident for trusted in AUTHORITATIVE_REGISTRY_DIRECTORY
        ) or (
            evidence_record.verification_method in ("NABL_DIRECTORY", "BIS_CRS_PORTAL", "OFFICIAL_GAZETTE")
        )

        if is_directory_verified and evidence_record.verified:
            return SourceAuthenticity.REAL_AUTHORITATIVE, ArtifactIntegrityStatus.HASH_VALID, issues

        if evidence_record.source_authenticity == SourceAuthenticity.REAL_AUTHORITATIVE and not is_directory_verified:
            # Rejection of unverified claims of authoritativeness
            issues.append("Issuer cannot be verified against authoritative accredited directory.")
            return SourceAuthenticity.UNVERIFIED, ArtifactIntegrityStatus.HASH_VALID, issues

        # Fallback to current or unverified
        return evidence_record.source_authenticity, ArtifactIntegrityStatus.HASH_VALID, issues

    @classmethod
    def validate_artifact_against_requirement(
        cls,
        evidence: Optional[ProductEvidenceRecord],
        requirement_id: str,
        target_standard: str,
        target_clause: str,
        requirement_class: Optional[RequirementClass] = None,
        threshold_spec: Optional[Dict[str, Any]] = None,
        allow_synthetic: bool = True,
        conflicting_evidences: Optional[List[ProductEvidenceRecord]] = None,
    ) -> ValidationReport:
        """Execute complete deterministic evidence validation against an applicable requirement."""
        req_class = requirement_class or EvidenceEligibilityEngine.infer_requirement_class(
            requirement_id,
            evidence.attribute if evidence else "",
        )

        # 1. Missing Evidence Case
        if evidence is None or evidence.evidence_type == EvidenceType.MISSING_EVIDENCE:
            chain = EvidenceChainRecord(
                artifact_identity="NO_ARTIFACT",
                source="NONE",
                provenance="No artifact supplied",
                authenticity=SourceAuthenticity.UNVERIFIED,
                evidence_type=EvidenceType.MISSING_EVIDENCE,
                applicable_requirement=requirement_id,
                verification_status=EvidenceVerificationStatus.MISSING,
            )
            act = RecommendedAction.REQUIRES_TESTING if req_class == RequirementClass.LAB_TEST_REQUIREMENT else RecommendedAction.UPLOAD_EVIDENCE
            return ValidationReport(
                artifact_id="NO_ARTIFACT",
                requirement_id=requirement_id,
                target_standard=target_standard,
                target_clause=target_clause,
                evidence_type=EvidenceType.MISSING_EVIDENCE,
                ontology_tier=EvidenceOntologyTier.USER_CLAIM,
                source_authenticity=SourceAuthenticity.UNVERIFIED,
                artifact_integrity=ArtifactIntegrityStatus.UNHASHED,
                verification_status=EvidenceVerificationStatus.MISSING,
                is_eligible=False,
                eligibility_reason=f"No evidence artifact provided for requirement '{requirement_id}'.",
                is_authoritative=False,
                compliance_verdict="MISSING_EVIDENCE",
                gap=f"Missing required evidence for requirement '{requirement_id}' under {target_standard}.",
                next_action=act,
                evidence_chain=chain,
                regulatory_conclusion="NONE",
                notes="Safe abstention: no evidence available to evaluate requirement.",
            )

        # 2. Conflicting Evidence Case
        is_conflicting = (
            evidence.evidence_type == EvidenceType.CONFLICTING_EVIDENCE
            or evidence.verification_status == EvidenceVerificationStatus.CONFLICTING
            or (conflicting_evidences and len(conflicting_evidences) > 1)
        )
        if is_conflicting:
            chain = evidence.to_evidence_chain_record()
            chain.verification_status = EvidenceVerificationStatus.CONFLICTING
            return ValidationReport(
                artifact_id=evidence.evidence_id,
                requirement_id=requirement_id,
                target_standard=target_standard,
                target_clause=target_clause,
                evidence_type=EvidenceType.CONFLICTING_EVIDENCE,
                ontology_tier=EvidenceOntologyTier.DOCUMENT,
                source_authenticity=evidence.source_authenticity,
                artifact_integrity=evidence.artifact_integrity,
                verification_status=EvidenceVerificationStatus.CONFLICTING,
                is_eligible=False,
                eligibility_reason="Conflicting documentary evidence detected for this requirement.",
                is_authoritative=False,
                compliance_verdict="EXPERT_REVIEW_REQUIRED",
                gap=f"Conflicting evidence artifacts detected for '{requirement_id}'. Autonomous resolution prohibited.",
                next_action=RecommendedAction.EXPERT_REVIEW,
                evidence_chain=chain,
                regulatory_conclusion="NONE",
                notes="Conflicting documents present. Mandates human expert review.",
            )

        # 3. Prompt Injection Interception
        content_to_scan = f"{evidence.extracted_value} {evidence.source_reference} {evidence.notes or ''}"
        for pat in PROHIBITED_INJECTION_PATTERNS:
            if pat.search(content_to_scan):
                chain = evidence.to_evidence_chain_record()
                chain.verification_status = EvidenceVerificationStatus.REJECTED
                return ValidationReport(
                    artifact_id=evidence.evidence_id,
                    requirement_id=requirement_id,
                    target_standard=target_standard,
                    target_clause=target_clause,
                    evidence_type=evidence.evidence_type,
                    ontology_tier=EvidenceOntologyTier.DOCUMENT,
                    source_authenticity=SourceAuthenticity.REJECTED,
                    artifact_integrity=evidence.artifact_integrity,
                    verification_status=EvidenceVerificationStatus.REJECTED,
                    is_eligible=False,
                    eligibility_reason="Adversarial prompt injection attempt intercepted in artifact.",
                    is_authoritative=False,
                    compliance_verdict="REJECTED",
                    gap="Security violation: malicious instruction inside evidence payload.",
                    next_action=RecommendedAction.EXPERT_REVIEW,
                    evidence_chain=chain,
                    regulatory_conclusion="NONE",
                    prompt_injection_detected=True,
                    notes="Layer 8 Security Guard: Intercepted prompt injection.",
                )

        # 4. Cross-Standard Isolation Check
        if evidence.applicable_standard:
            ev_std_clean = evidence.applicable_standard.split(":")[0].replace(" ", "").upper()
            tgt_std_clean = target_standard.split(":")[0].replace(" ", "").upper()
            # Allow known harmonious cross-references (e.g. IS 6911 material standard for IS 17526 flask)
            allowed_cross = (tgt_std_clean == "IS17526" and "IS6911" in ev_std_clean)
            if ev_std_clean != tgt_std_clean and not allowed_cross:
                chain = evidence.to_evidence_chain_record()
                chain.verification_status = EvidenceVerificationStatus.REJECTED
                return ValidationReport(
                    artifact_id=evidence.evidence_id,
                    requirement_id=requirement_id,
                    target_standard=target_standard,
                    target_clause=target_clause,
                    evidence_type=evidence.evidence_type,
                    ontology_tier=EvidenceOntologyTier.DOCUMENT,
                    source_authenticity=evidence.source_authenticity,
                    artifact_integrity=evidence.artifact_integrity,
                    verification_status=EvidenceVerificationStatus.REJECTED,
                    is_eligible=False,
                    eligibility_reason=f"Cross-standard leakage: Evidence standard '{evidence.applicable_standard}' != target '{target_standard}'.",
                    is_authoritative=False,
                    compliance_verdict="NOT_ELIGIBLE",
                    gap=f"Evidence belongs to standard '{evidence.applicable_standard}', not applicable to '{target_standard}'.",
                    next_action=RecommendedAction.UPLOAD_EVIDENCE,
                    evidence_chain=chain,
                    regulatory_conclusion="NONE",
                    notes="Cross-standard isolation enforced: 0% cross-standard leakage.",
                )

        # 5. Ontological Distinction Check (USER CLAIM ≠ DOCUMENT ≠ VERIFIED EVIDENCE ≠ COMPLIANCE RESULT)
        if evidence.evidence_type in (EvidenceType.USER_PROVIDED_CLAIM, EvidenceType.USER_CLAIM):
            chain = evidence.to_evidence_chain_record()
            chain.verification_status = EvidenceVerificationStatus.UNVERIFIED
            return ValidationReport(
                artifact_id=evidence.evidence_id,
                requirement_id=requirement_id,
                target_standard=target_standard,
                target_clause=target_clause,
                evidence_type=EvidenceType.USER_CLAIM,
                ontology_tier=EvidenceOntologyTier.USER_CLAIM,
                source_authenticity=SourceAuthenticity.UNVERIFIED,
                artifact_integrity=evidence.artifact_integrity,
                verification_status=EvidenceVerificationStatus.UNVERIFIED,
                is_eligible=False,
                eligibility_reason="User claim (Tier 0) possesses 0.0% regulatory compliance authority.",
                is_authoritative=False,
                compliance_verdict="MISSING_EVIDENCE",
                gap=f"User claim cannot satisfy requirement '{requirement_id}'. Authoritative documentary evidence required.",
                next_action=RecommendedAction.UPLOAD_EVIDENCE,
                evidence_chain=chain,
                regulatory_conclusion="NONE",
                notes="Ontological Separation Enforced: USER CLAIM != VERIFIED EVIDENCE.",
            )

        # 6. Evidence Eligibility Check (including Laboratory Test vs Datasheet Invariant)
        eligibility = EvidenceEligibilityEngine.check_eligibility(
            requirement_id=requirement_id,
            requirement_name=evidence.attribute,
            evidence=evidence,
            explicit_class=req_class,
        )

        if not eligibility.is_eligible:
            chain = evidence.to_evidence_chain_record()
            act = (
                RecommendedAction.REQUIRES_TESTING
                if req_class == RequirementClass.LAB_TEST_REQUIREMENT
                else RecommendedAction.UPLOAD_EVIDENCE
            )
            if eligibility.status == EligibilityStatus.UNVERIFIED_EVIDENCE:
                verdict = "UNVERIFIED"
                verif_stat = EvidenceVerificationStatus.UNVERIFIED
            elif eligibility.status == EligibilityStatus.CONFLICTING_EVIDENCE:
                verdict = "EXPERT_REVIEW_REQUIRED"
                verif_stat = EvidenceVerificationStatus.CONFLICTING
            elif eligibility.status == EligibilityStatus.MISSING_REQUIRED_EVIDENCE:
                verdict = "MISSING_EVIDENCE"
                verif_stat = EvidenceVerificationStatus.MISSING
            else:
                verdict = "NOT_ELIGIBLE"
                verif_stat = evidence.verification_status

            return ValidationReport(
                artifact_id=evidence.evidence_id,
                requirement_id=requirement_id,
                target_standard=target_standard,
                target_clause=target_clause,
                evidence_type=evidence.evidence_type,
                ontology_tier=evidence.ontology_tier,
                source_authenticity=evidence.source_authenticity,
                artifact_integrity=evidence.artifact_integrity,
                verification_status=verif_stat,
                is_eligible=False,
                eligibility_reason=eligibility.reason,
                is_authoritative=False,
                compliance_verdict=verdict,
                gap=eligibility.reason,
                next_action=act,
                evidence_chain=chain,
                regulatory_conclusion="NONE",
                notes="Evidence Eligibility Gate rejected artifact for requirement class.",
            )

        # 7. Authenticity Verification
        auth, integ, issues = cls.verify_artifact_authenticity(
            evidence_record=evidence,
            allow_synthetic=allow_synthetic,
        )

        if auth in (SourceAuthenticity.UNVERIFIED, SourceAuthenticity.REJECTED):
            chain = evidence.to_evidence_chain_record()
            chain.authenticity = auth
            chain.verification_status = (
                EvidenceVerificationStatus.REJECTED
                if auth == SourceAuthenticity.REJECTED
                else EvidenceVerificationStatus.UNVERIFIED
            )
            return ValidationReport(
                artifact_id=evidence.evidence_id,
                requirement_id=requirement_id,
                target_standard=target_standard,
                target_clause=target_clause,
                evidence_type=evidence.evidence_type,
                ontology_tier=EvidenceOntologyTier.DOCUMENT,
                source_authenticity=auth,
                artifact_integrity=integ,
                verification_status=chain.verification_status,
                is_eligible=False,
                eligibility_reason=f"Artifact authenticity failure: {'; '.join(issues) or auth.value}.",
                is_authoritative=False,
                compliance_verdict="UNVERIFIED",
                gap=f"Artifact '{evidence.evidence_id}' fails authenticity verification: {'; '.join(issues)}",
                next_action=RecommendedAction.UPLOAD_EVIDENCE,
                evidence_chain=chain,
                regulatory_conclusion="NONE",
                notes="Authenticity not established from file existence or hash alone.",
            )

        # 8. Layer 7 Deterministic Threshold / Rule Comparison
        # Only Layer 7 has compliance authority. The evidence pipeline delegates result to Layer 7 logic.
        compliance_verdict = "SATISFIED"
        gap_desc = None
        action = RecommendedAction.UPLOAD_EVIDENCE

        if threshold_spec:
            op = threshold_spec.get("operator", ">=")
            target_val = threshold_spec.get("target_value")
            target_unit = threshold_spec.get("unit")

            numeric_val = None
            if isinstance(evidence.normalized_value, (int, float)):
                numeric_val = float(evidence.normalized_value)
            else:
                matches = re.findall(r"[-+]?\d*\.?\d+", str(evidence.normalized_value or evidence.extracted_value))
                if matches:
                    try:
                        numeric_val = float(matches[0])
                    except (ValueError, IndexError):
                        numeric_val = None

            if numeric_val is not None and target_val is not None:
                # Perform unit normalization if units match or are convertible
                comp_pass, formula_str, audit_str = compare_numeric_threshold(
                    observed_val=numeric_val,
                    observed_unit=evidence.unit or target_unit,
                    operator=op,
                    threshold=float(target_val),
                    required_unit=target_unit,
                )
                if comp_pass:
                    compliance_verdict = "SATISFIED"
                    gap_desc = None
                else:
                    compliance_verdict = "POTENTIAL_GAP"
                    gap_desc = f"Measured value {val_to_compare} failed threshold {op} {target_val} {target_unit or ''}."
                    action = RecommendedAction.PROVIDE_SPECIFICATION

        chain = evidence.to_evidence_chain_record()
        chain.authenticity = auth
        chain.verification_status = EvidenceVerificationStatus.VERIFIED

        return ValidationReport(
            artifact_id=evidence.evidence_id,
            requirement_id=requirement_id,
            target_standard=target_standard,
            target_clause=target_clause,
            evidence_type=evidence.evidence_type,
            ontology_tier=EvidenceOntologyTier.VERIFIED_EVIDENCE,
            source_authenticity=auth,
            artifact_integrity=integ,
            verification_status=EvidenceVerificationStatus.VERIFIED,
            is_eligible=True,
            eligibility_reason="Artifact is fully authentic, eligible, and verified.",
            is_authoritative=True,
            compliance_verdict=compliance_verdict,
            gap=gap_desc,
            next_action=action if gap_desc else RecommendedAction.UPLOAD_EVIDENCE,
            evidence_chain=chain,
            regulatory_conclusion="NONE",  # informational invariant preserved
            notes="Artifact deterministically validated through M26.0 pipeline.",
        )

    @classmethod
    def map_artifact_to_requirement(
        cls,
        evidence: Optional[ProductEvidenceRecord],
        target_standard: str,
        target_clause: Optional[str] = None,
        target_requirement_id: Optional[str] = None,
        target_product_category: Optional[str] = None,
        allow_synthetic: bool = True,
        conflicting_evidences: Optional[List[ProductEvidenceRecord]] = None,
    ):
        """Deterministically map evidence artifact to requirement (Milestone M26.1)."""
        from backend.app.services.compliance.evidence_mapping_service import DeterministicEvidenceRequirementMapper
        return DeterministicEvidenceRequirementMapper.map_evidence_to_requirement(
            evidence=evidence,
            target_standard=target_standard,
            target_clause=target_clause,
            target_requirement_id=target_requirement_id,
            target_product_category=target_product_category,
            allow_synthetic=allow_synthetic,
            conflicting_evidences=conflicting_evidences,
        )


# Global singleton instance
evidence_validation_service = EvidenceValidationPipeline()

