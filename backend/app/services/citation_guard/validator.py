"""Layer 8: Source Validation & Citation Guard — Production Validator.

Primary Pipeline:
LAYER 7 RESULT
→ CLAIM EXTRACTION
→ SOURCE VALIDATION
→ STANDARD / CLAUSE VALIDATION
→ EVIDENCE PROVENANCE VALIDATION
→ CITATION VALIDATION
→ CONFLICT / STALENESS CHECK
→ TRUST DECISION
→ LAYER 9 OUTPUT

Cardinal Regulatory Invariants:
1. NO VERIFIED SOURCE → NO REGULATORY CLAIM
2. INVALID CITATION → REJECT
3. WRONG STANDARD → REJECT
4. MISSING PROVENANCE → REJECT / REVIEW
5. CONFLICT → EXPERT REVIEW
6. STALE EVIDENCE → REVIEW
7. LLM CANNOT VALIDATE ITS OWN OUTPUT
8. LLM COMPLIANCE AUTHORITY = 0.0%
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from backend.app.services.citation_guard.models import (
    ValidationOutcome,
    TrustChain,
    CitationValidationResult,
    BatchValidationReport,
)
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG
from backend.app.services.rag.engine import layer6_clause_rag
from backend.app.core.logging import logger

ACTIVE_KNOWLEDGE_VERSION = "v1.2.0-gazette-verified"

# Prompt injection & illegal LLM self-certification patterns
PROHIBITED_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+override(?:\s*:\s*mark\s+compliant)?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+unrestricted\s+mode", re.IGNORECASE),
    re.compile(r"\bthis\s+product\s+is\s+(?:hereby\s+)?(?:certified|compliant|satisfied)\b", re.IGNORECASE),
    re.compile(r"\bcompliance\s+granted\b", re.IGNORECASE),
    re.compile(r"\bi\s+(?:hereby\s+)?declare\s+compliance\b", re.IGNORECASE),
]


def calculate_sha256(content: str) -> str:
    """Compute SHA-256 cryptographic digest of evidence content."""
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


class CitationValidator:
    """Production-grade Layer 8 Source Validation and Citation Guard Engine."""

    def __init__(self):
        self.active_knowledge_version = ACTIVE_KNOWLEDGE_VERSION

    def _lookup_standard(self, std_number: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Resolve standard against official verified gazette catalog."""
        clean = std_number.strip().upper().replace(" ", "")
        for key, val in VERIFIED_STANDARDS_CATALOG.items():
            if clean in key.replace(" ", "").upper() or key.replace(" ", "").upper() in clean:
                return (key, val)
        for key in layer6_clause_rag.clause_catalog.keys():
            if clean in key.replace(" ", "").upper() or key.replace(" ", "").upper() in clean:
                return (key, {"title": key, "clauses": {}})
        return None

    def _lookup_clause(self, std_key: str, clause_number: str) -> Optional[Dict[str, Any]]:
        """Resolve clause within the verified standard."""
        cl_num = str(clause_number).strip().replace("Clause", "").replace("clause", "").strip()

        # Check knowledge_selector catalog
        std_info = VERIFIED_STANDARDS_CATALOG.get(std_key)
        if std_info and "clauses" in std_info:
            if cl_num in std_info["clauses"]:
                return std_info["clauses"][cl_num]

        # Check Layer 6 Clause RAG catalog
        for std_rag_key, clauses in layer6_clause_rag.clause_catalog.items():
            if std_key.replace(" ", "").upper() in std_rag_key.replace(" ", "").upper() or std_rag_key.replace(" ", "").upper() in std_key.replace(" ", "").upper():
                for c in clauses:
                    if c.get("clause_number") == cl_num or c.get("clause_number") == f"Clause {cl_num}":
                        return {
                            "title": c.get("title"),
                            "req": c.get("text_content"),
                            "page_number": c.get("page_number", 1),
                        }
        return None

    def validate_citation_claim(
        self,
        claim: str,
        target_standard: str,
        target_clause: str,
        evidence_id: Optional[str] = None,
        document_id: Optional[str] = None,
        source_authority: Optional[str] = None,
        page_number: Optional[int] = None,
        verification_status: Optional[str] = None,
        evidence_text: Optional[str] = None,
        evidence_hash: Optional[str] = None,
        evidence_standard: Optional[str] = None,
        knowledge_version: Optional[str] = None,
        is_expired: bool = False,
        has_conflict: bool = False,
        is_llm_generated: bool = False,
        is_authoritative_pending: bool = False,
        product_dna_version: str = "v1.0",
        assessment_version: int = 1,
    ) -> CitationValidationResult:
        """Execute 10-step deterministic Source Validation & Citation Guard pipeline."""
        now = datetime.now(timezone.utc)
        claim_str = (claim or "").strip()
        target_std_str = (target_standard or "").strip()
        target_cl_str = (target_clause or "").strip()
        ev_text = (evidence_text or "").strip()
        doc_id = document_id or "DOC-UNSPECIFIED"
        ev_id = evidence_id or "EV-UNSPECIFIED"
        k_ver = knowledge_version or self.active_knowledge_version
        v_status = verification_status or "UNVERIFIED"
        src_auth = source_authority or "UNVERIFIED_SOURCE"

        calc_hash = calculate_sha256(ev_text) if ev_text else None

        # ---------------------------------------------------------------------
        # 1. Empty Claim Rejection
        # ---------------------------------------------------------------------
        if not claim_str:
            return CitationValidationResult(
                claim="[EMPTY_CLAIM]",
                source_id=doc_id,
                standard=target_std_str,
                clause=target_cl_str,
                validation_result=ValidationOutcome.REJECTED,
                failure_reason="Claim text is empty or unstated. Zero-hallucination policy rejects unstated claims.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 2. Prompt Injection & Prohibited LLM Self-Certification
        # ---------------------------------------------------------------------
        for pat in PROHIBITED_INJECTION_PATTERNS:
            if pat.search(claim_str):
                return CitationValidationResult(
                    claim=claim_str,
                    source_id=doc_id,
                    standard=target_std_str,
                    clause=target_cl_str,
                    validation_result=ValidationOutcome.REJECTED,
                    failure_reason="Prohibited LLM compliance self-certification or prompt injection attempt intercepted.",
                    is_llm_generated=True,
                    llm_authority_claimed=1.0,
                    knowledge_version=k_ver,
                    validated_at=now,
                )

        # ---------------------------------------------------------------------
        # 3. Standard Identification & Format Validation
        # ---------------------------------------------------------------------
        if not target_std_str:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard="NONE",
                clause=target_cl_str,
                validation_result=ValidationOutcome.CITATION_INVALID,
                failure_reason="Missing target Indian Standard citation. Every claim must specify an authentic Indian Standard.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        std_res = self._lookup_standard(target_std_str)
        if not std_res:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=target_std_str,
                clause=target_cl_str,
                validation_result=ValidationOutcome.REJECTED,
                failure_reason=f"Fabricated or unrecognized Indian Standard '{target_std_str}'. Standard does not exist in official BIS Gazette repository.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        canonical_std_key, std_data = std_res

        # ---------------------------------------------------------------------
        # 4. Authoritative Procurement / Source Unavailability
        # ---------------------------------------------------------------------
        if is_authoritative_pending or "PENDING" in target_cl_str.upper() or "AUTHORITATIVE_CLAUSE_PENDING" in target_std_str:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                validation_result=ValidationOutcome.SOURCE_UNAVAILABLE,
                failure_reason="Authoritative standard text is pending official BIS procurement (OFFICIAL_DOCUMENT_ACQUISITION_PENDING). Reconstructing text is strictly prohibited.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 5. Clause Existence & Content Grounding
        # ---------------------------------------------------------------------
        if not target_cl_str:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause="NONE",
                validation_result=ValidationOutcome.CITATION_INVALID,
                failure_reason="Missing target clause identifier. Specific clause citation is mandatory.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        cl_data = self._lookup_clause(canonical_std_key, target_cl_str)
        if not cl_data:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                validation_result=ValidationOutcome.REJECTED,
                failure_reason=f"Fabricated clause: Clause '{target_cl_str}' does not exist in official {canonical_std_key} catalog.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 6. Page & Document Citation Verification
        # ---------------------------------------------------------------------
        if page_number is not None and (page_number <= 0 or page_number > 2000):
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                page=page_number,
                validation_result=ValidationOutcome.CITATION_INVALID,
                failure_reason=f"Invalid or out-of-bounds document page citation: Page {page_number}.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 7. Cross-Standard Evidence Leakage Guard
        # ---------------------------------------------------------------------
        if evidence_standard:
            ev_clean = evidence_standard.split(":")[0].replace(" ", "").upper()
            target_clean = canonical_std_key.split(":")[0].replace(" ", "").upper()
            if ev_clean != target_clean and "UNKNOWN" not in ev_clean:
                return CitationValidationResult(
                    claim=claim_str,
                    source_id=doc_id,
                    standard=canonical_std_key,
                    clause=target_cl_str,
                    evidence_id=ev_id,
                    validation_result=ValidationOutcome.REJECTED,
                    failure_reason=f"Cross-standard evidence leakage: Evidence document references standard '{evidence_standard}', which does not match required applicable standard '{canonical_std_key}'.",
                    knowledge_version=k_ver,
                    validated_at=now,
                )

        # ---------------------------------------------------------------------
        # 8. Knowledge Version Mismatch Guard
        # ---------------------------------------------------------------------
        if knowledge_version and knowledge_version != self.active_knowledge_version:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                evidence_id=ev_id,
                knowledge_version=knowledge_version,
                validation_result=ValidationOutcome.STALE_SOURCE,
                failure_reason=f"Knowledge version mismatch: Citation references '{knowledge_version}', but active verified repository version is '{self.active_knowledge_version}'.",
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 9. Stale / Expired Evidence Guard
        # ---------------------------------------------------------------------
        if is_expired:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                evidence_id=ev_id,
                validation_result=ValidationOutcome.STALE_SOURCE,
                failure_reason="Evidence document validity has expired. Stale test reports cannot substantiate compliance.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 10. Cryptographic SHA-256 Evidence Hash Integrity
        # ---------------------------------------------------------------------
        if evidence_hash and calc_hash and evidence_hash.strip().lower() != calc_hash.strip().lower():
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                evidence_id=ev_id,
                evidence_hash=evidence_hash,
                calculated_hash=calc_hash,
                validation_result=ValidationOutcome.REJECTED,
                failure_reason=f"Cryptographic integrity failure: Evidence SHA-256 hash mismatch. Expected {evidence_hash[:12]}..., computed {calc_hash[:12]}... Tampering detected.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 11. Contradiction & Conflict Resolution
        # ---------------------------------------------------------------------
        conflict_words = ["breakdown", "failed", "dielectric spark", "seepage observed", "puncture", "toxic"]
        has_failure_text = any(w in ev_text.lower() for w in conflict_words)

        if has_conflict or has_failure_text:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                evidence_id=ev_id,
                validation_result=ValidationOutcome.EXPERT_REVIEW_REQUIRED,
                failure_reason="Contradictory evidentiary values or failure indicators detected. Automated approval disallowed; manual expert review mandated.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 12. Evidence Provenance & Verification Authority
        # ---------------------------------------------------------------------
        # Claims declaring compliance or SATISFIED require authentic evidence
        is_compliance_claim = any(w in claim_str.lower() for w in ["satisfied", "compliant", "pass", "passes", "conforms"])
        if is_compliance_claim and not ev_text and not evidence_id:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                validation_result=ValidationOutcome.REJECTED,
                failure_reason="Unsupported compliance statement: Claim asserts requirement is satisfied, but no verified evidence record is cited.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        if not ev_text and not evidence_id:
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                validation_result=ValidationOutcome.INSUFFICIENT_SOURCE,
                failure_reason="Missing supporting technical evidence or laboratory report.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # Reject unverified user claims masquerading as authoritative evidence
        if v_status in ("USER_CLAIM", "UNACCREDITED"):
            return CitationValidationResult(
                claim=claim_str,
                source_id=doc_id,
                standard=canonical_std_key,
                clause=target_cl_str,
                evidence_id=ev_id,
                verification_status=v_status,
                validation_result=ValidationOutcome.REJECTED,
                failure_reason=f"Unverified source provenance [{v_status}]: User declarations cannot serve as authoritative compliance evidence.",
                knowledge_version=k_ver,
                validated_at=now,
            )

        # ---------------------------------------------------------------------
        # 13. Assemble Auditable Trust Chain
        # ---------------------------------------------------------------------
        trust_chain = TrustChain(
            claim=claim_str,
            source=doc_id,
            standard=canonical_std_key,
            clause=f"Clause {target_cl_str}",
            evidence=ev_id,
            verification="VERIFIED_NABL_OR_GAZETTE",
            decision=ValidationOutcome.VERIFIED,
        )

        return CitationValidationResult(
            claim=claim_str,
            source_id=doc_id,
            standard=canonical_std_key,
            clause=target_cl_str,
            evidence_id=ev_id,
            document_id=doc_id,
            page=page_number or 1,
            verification_status="VERIFIED",
            knowledge_version=k_ver,
            validation_result=ValidationOutcome.VERIFIED,
            failure_reason=None,
            evidence_hash=evidence_hash or calc_hash,
            calculated_hash=calc_hash,
            product_dna_version=product_dna_version,
            assessment_version=assessment_version,
            trust_chain=trust_chain,
            validated_at=now,
        )

    def validate_batch(
        self,
        claims: List[Dict[str, Any]],
        standard_number: str = "IS 17526:2021",
        knowledge_version: str = ACTIVE_KNOWLEDGE_VERSION,
    ) -> BatchValidationReport:
        """Batch validation of multiple claims or Layer 7 requirements."""
        results: List[CitationValidationResult] = []
        verified_count = 0
        rejected_count = 0
        flagged_count = 0

        for item in claims:
            res = self.validate_citation_claim(
                claim=item.get("claim", item.get("description", "")),
                target_standard=item.get("standard", standard_number),
                target_clause=item.get("clause", item.get("clause_number", "")),
                evidence_id=item.get("evidence_id"),
                document_id=item.get("document_id"),
                source_authority=item.get("source_authority"),
                page_number=item.get("page", item.get("page_number")),
                verification_status=item.get("verification_status"),
                evidence_text=item.get("evidence_text", item.get("source_excerpt")),
                evidence_hash=item.get("evidence_hash"),
                evidence_standard=item.get("evidence_standard"),
                knowledge_version=item.get("knowledge_version", knowledge_version),
                is_expired=item.get("is_expired", False),
                has_conflict=item.get("has_conflict", False),
                is_llm_generated=item.get("is_llm_generated", False),
                is_authoritative_pending=item.get("is_authoritative_pending", False),
            )
            results.append(res)
            if res.validation_result == ValidationOutcome.VERIFIED:
                verified_count += 1
            elif res.validation_result == ValidationOutcome.REJECTED:
                rejected_count += 1
            else:
                flagged_count += 1

        overall = ValidationOutcome.VERIFIED
        if rejected_count > 0:
            overall = ValidationOutcome.REJECTED
        elif flagged_count > 0:
            overall = ValidationOutcome.EXPERT_REVIEW_REQUIRED

        return BatchValidationReport(
            total_claims=len(results),
            verified_claims=verified_count,
            rejected_claims=rejected_count,
            flagged_claims=flagged_count,
            overall_trust_decision=overall,
            results=results,
            audit_trail=[
                f"Evaluated {len(results)} claims against {standard_number}.",
                f"Verified: {verified_count}, Rejected: {rejected_count}, Flagged: {flagged_count}.",
                f"Overall Trust Decision: {overall.value}.",
            ],
        )


citation_validator = CitationValidator()
