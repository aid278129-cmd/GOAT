"""Multi-dimensional Compliance Passport state evaluator (Phase 5).

Strictly adheres to the core principle:
- Zero misleading '100% COMPLIANT' badges.
- Independently derived truthful engineering and regulatory states.
"""

from typing import Dict, Any, List, Optional


def evaluate_passport_states(
    job: Dict[str, Any],
    standards: List[Dict[str, Any]],
    requirements: List[Dict[str, Any]],
    evidence_items: List[Dict[str, Any]],
    dna_parameters: List[Dict[str, Any]],
    assessment_results: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
    reviews: List[Dict[str, Any]],
    attestations: List[Dict[str, Any]],
    latest_dossier: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Derive independent, truthful statutory and engineering states.
    Never collapses results into a single artificial boolean.
    """
    # 1. Scope State
    has_product = bool(job.get("product_name") and job.get("model_number"))
    has_standards = len(standards) > 0
    scope_state = "DEFINED" if (has_product and has_standards) else "INCOMPLETE"

    # 2. Evidence State
    total_ev = len(evidence_items)
    accepted_ev = sum(1 for e in evidence_items if e.get("acceptance_status") == "ACCEPTED")
    rejected_ev = sum(1 for e in evidence_items if e.get("acceptance_status") == "REJECTED")

    if total_ev == 0 or accepted_ev == 0:
        evidence_state = "NO_ACCEPTED_EVIDENCE"
    elif rejected_ev > 0:
        evidence_state = "REJECTED_PRESENT"
    elif accepted_ev == total_ev:
        evidence_state = "FULLY_ACCEPTED"
    else:
        evidence_state = "PARTIALLY_ACCEPTED"

    # 3. DNA State
    total_dna = len(dna_parameters)
    verified_dna = sum(1 for d in dna_parameters if d.get("status") == "VERIFIED")
    conflict_dna = sum(1 for d in dna_parameters if d.get("status") == "CONFLICT")

    if total_dna == 0:
        dna_state = "INCOMPLETE"
    elif conflict_dna > 0:
        dna_state = "CONFLICT_DETECTED"
    elif verified_dna == total_dna:
        dna_state = "FULLY_VERIFIED"
    else:
        dna_state = "PARTIALLY_VERIFIED"

    # 4. Assessment State
    total_res = len(assessment_results)
    gap_count = sum(1 for r in assessment_results if r.get("assessment_state") == "ENGINEERING_GAP")
    data_req_count = sum(1 for r in assessment_results if r.get("assessment_state") == "DATA_REQUIRED")
    pass_count = sum(1 for r in assessment_results if r.get("assessment_state") == "ENGINEERING_PASS")

    if total_res == 0:
        assessment_state = "NOT_ASSESSED"
    elif gap_count > 0:
        assessment_state = "ENGINEERING_GAP"
    elif data_req_count > 0:
        assessment_state = "DATA_REQUIRED"
    elif pass_count > 0:
        assessment_state = "ENGINEERING_PASS"
    else:
        assessment_state = "NOT_ASSESSED"

    # 5. Review State
    total_rev = len(reviews)
    pending_rev = sum(1 for r in reviews if r.get("status") in ("PENDING", "IN_REVIEW", "ASSIGNED"))
    rejected_rev = sum(1 for r in reviews if r.get("decision") in ("REJECT", "REJECTED"))

    if total_rev == 0:
        review_state = "NOT_REQUIRED"
    elif rejected_rev > 0:
        review_state = "REJECTED_ITEMS"
    elif pending_rev > 0:
        review_state = "PENDING"
    else:
        review_state = "COMPLETED"

    # 6. Attestation State
    active_attestations = [a for a in attestations if a.get("status") == "ACTIVE"]
    superseded_attestations = [a for a in attestations if a.get("status") == "SUPERSEDED"]
    revoked_attestations = [a for a in attestations if a.get("status") == "REVOKED"]

    if active_attestations:
        attestation_state = "ACTIVE"
    elif revoked_attestations:
        attestation_state = "REVOKED"
    elif superseded_attestations:
        attestation_state = "SUPERSEDED"
    else:
        attestation_state = "NONE"

    # 7. Finding State
    total_findings = len(findings)
    open_findings = sum(1 for f in findings if f.get("status") in ("OPEN", "UNDER_REVIEW"))
    waived_findings = sum(1 for f in findings if f.get("status") == "WAIVED")
    resolved_findings = sum(1 for f in findings if f.get("status") == "RESOLVED")

    if total_findings == 0:
        finding_state = "NONE"
    elif open_findings > 0:
        finding_state = "OPEN"
    elif waived_findings > 0:
        finding_state = "WAIVED"
    else:
        finding_state = "RESOLVED"

    # 8. Dossier State
    if not latest_dossier:
        dossier_state = "NOT_GENERATED"
    else:
        # Check if latest dossier assessment_run matches current run
        current_run_id = assessment_results[0].get("assessment_run_id") if assessment_results else None
        dossier_run_id = latest_dossier.get("assessment_run_id")
        if current_run_id and dossier_run_id and current_run_id != dossier_run_id:
            dossier_state = "NEEDS_UPDATE"
        else:
            dossier_state = "GENERATED"

    return {
        "scope_state": scope_state,
        "evidence_state": evidence_state,
        "dna_state": dna_state,
        "assessment_state": assessment_state,
        "review_state": review_state,
        "attestation_state": attestation_state,
        "finding_state": finding_state,
        "dossier_state": dossier_state,
        "counts": {
            "standards_count": len(standards),
            "requirements_count": len(requirements),
            "total_evidence": total_ev,
            "accepted_evidence": accepted_ev,
            "rejected_evidence": rejected_ev,
            "total_dna_parameters": total_dna,
            "verified_dna_parameters": verified_dna,
            "assessment_results_count": total_res,
            "engineering_pass_count": pass_count,
            "engineering_gap_count": gap_count,
            "data_required_count": data_req_count,
            "total_findings": total_findings,
            "open_findings": open_findings,
            "total_reviews": total_rev,
            "pending_reviews": pending_rev,
            "active_attestations_count": len(active_attestations),
        }
    }
