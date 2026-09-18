"""Deterministic Traceability Matrix Builder for Phase 5 Regulatory Dossier."""

from typing import List, Dict, Any, Optional


def build_traceability_matrix(
    requirements: List[Dict[str, Any]],
    dna_parameters: List[Dict[str, Any]],
    evidence_items: List[Dict[str, Any]],
    cad_measurements: List[Dict[str, Any]],
    assessment_results: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
    reviews: List[Dict[str, Any]],
    attestations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Construct a deterministic traceability chain:
    Requirement -> Product DNA -> Evidence -> CAD Measurement -> Assessment Result -> Finding -> Review -> Attestation.
    
    Stable identifiers are preserved. Missing links are never invented.
    """
    # Index lookup maps by ID and matching keys
    dna_by_param: Dict[str, Dict[str, Any]] = {}
    for d in dna_parameters:
        p_key = str(d.get("parameter", "")).strip().lower()
        if p_key:
            dna_by_param[p_key] = d

    ev_by_id: Dict[str, Dict[str, Any]] = {
        str(e.get("id", "")): e for e in evidence_items
    }

    results_by_req_id: Dict[str, Dict[str, Any]] = {}
    results_by_clause: Dict[str, Dict[str, Any]] = {}
    for res in assessment_results:
        r_id = str(res.get("requirement_id", "") or "")
        c_num = str(res.get("clause_number", "") or "")
        if r_id:
            results_by_req_id[r_id] = res
        if c_num:
            results_by_clause[c_num] = res

    findings_by_req_id: Dict[str, Dict[str, Any]] = {}
    for f in findings:
        fr_id = str(f.get("requirement_id", "") or "")
        if fr_id:
            findings_by_req_id[fr_id] = f

    reviews_by_req_id: Dict[str, Dict[str, Any]] = {}
    reviews_by_res_id: Dict[str, Dict[str, Any]] = {}
    reviews_by_find_id: Dict[str, Dict[str, Any]] = {}
    for rev in reviews:
        req_ref = str(rev.get("requirement_id", "") or "")
        res_ref = str(rev.get("assessment_result_id", "") or "")
        find_ref = str(rev.get("finding_id", "") or "")
        if req_ref:
            reviews_by_req_id[req_ref] = rev
        if res_ref:
            reviews_by_res_id[res_ref] = rev
        if find_ref:
            reviews_by_find_id[find_ref] = rev

    # Active attestation map (or latest active attestation)
    active_attestations = [a for a in attestations if a.get("status") == "ACTIVE"]

    # Index CAD measurements by associated requirement or parameter
    cad_by_param: Dict[str, Dict[str, Any]] = {}
    for m in cad_measurements:
        m_type = str(m.get("measurement_type", "")).strip().lower()
        cad_by_param[m_type] = m

    matrix_rows = []

    for req in sorted(requirements, key=lambda x: str(x.get("clause_reference", x.get("clause_number", "")))):
        req_id = str(req.get("id", ""))
        req_code = str(req.get("requirement_id", req_id))
        clause = str(req.get("clause_reference", req.get("clause_number", "N/A")))
        param_key = str(req.get("parameter_key", "") or "").strip().lower()

        # 1. Product DNA
        dna_fact = dna_by_param.get(param_key)
        dna_id = dna_fact.get("id") if dna_fact else None
        dna_val = f"{dna_fact.get('value')} {dna_fact.get('unit', '')}".strip() if dna_fact else "DATA_REQUIRED"
        extraction_method = dna_fact.get("extraction_method") if dna_fact else None

        # 2. Evidence Link
        ev_id = None
        ev_sha256 = None
        ev_status = None
        if dna_fact and dna_fact.get("source_evidence_id"):
            ev_id = str(dna_fact.get("source_evidence_id"))
            ev_item = ev_by_id.get(ev_id)
            if ev_item:
                ev_sha256 = ev_item.get("sha256_hash")
                ev_status = ev_item.get("acceptance_status")
        
        # 3. CAD Measurement link (if extraction method is CAD or measurement matches)
        cad_meas_id = None
        cad_meas_val = None
        cad_meas = cad_by_param.get(param_key)
        if cad_meas:
            cad_meas_id = cad_meas.get("id")
            cad_meas_val = f"{cad_meas.get('value')} {cad_meas.get('unit', 'mm')}"

        # 4. Assessment Result
        res = results_by_req_id.get(req_id) or results_by_clause.get(clause)
        res_id = res.get("id") if res else None
        assessment_state = res.get("assessment_state") if res else "NOT_ASSESSED"

        # 5. Finding
        finding = findings_by_req_id.get(req_id)
        if not finding and res_id:
            for f in findings:
                if str(f.get("assessment_result_id", "")) == res_id:
                    finding = f
                    break
        finding_id = finding.get("id") if finding else None
        finding_status = finding.get("status") if finding else None

        # 6. Human Review
        review = reviews_by_req_id.get(req_id)
        if not review and res_id:
            review = reviews_by_res_id.get(res_id)
        if not review and finding_id:
            review = reviews_by_find_id.get(finding_id)
        review_id = review.get("id") if review else None
        review_decision = review.get("decision") if review else (review.get("status") if review else None)

        # 7. Human Attestation
        attestation_id = None
        attestation_type = None
        if active_attestations:
            # Check if covered in scope
            for att in active_attestations:
                scope = att.get("scope", {})
                clauses_covered = scope.get("clauses_covered", [])
                if not clauses_covered or clause in clauses_covered:
                    attestation_id = att.get("id")
                    attestation_type = att.get("attestation_type")
                    break

        matrix_rows.append({
            "requirement_id": req_code,
            "clause": clause,
            "section": str(req.get("section", "")),
            "parameter_key": param_key or "N/A",
            "dna_id": dna_id or "NOT_PROVIDED",
            "dna_value": dna_val,
            "extraction_method": extraction_method or "NONE",
            "evidence_id": ev_id or "NOT_PROVIDED",
            "evidence_sha256": ev_sha256 or "NONE",
            "evidence_acceptance": ev_status or "NONE",
            "cad_measurement_id": cad_meas_id or "N/A",
            "cad_measurement_value": cad_meas_val or "N/A",
            "assessment_result_id": res_id or "NOT_ASSESSED",
            "assessment_state": assessment_state,
            "finding_id": finding_id or "NONE",
            "finding_status": finding_status or "NONE",
            "review_id": review_id or "NONE",
            "review_decision": review_decision or "NONE",
            "attestation_id": attestation_id or "NONE",
            "attestation_type": attestation_type or "NONE",
        })

    return matrix_rows
