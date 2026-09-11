import re
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field


class StructuredEvidence(BaseModel):
    """Normalized structured evidence representation extracted from test reports, datasheets, or specs."""
    evidence_id: str
    assessment_id: Optional[str] = None
    document_id: Optional[str] = None
    evidence_type: str = "TEST_REPORT"  # TEST_REPORT | LAB_REPORT | MATERIAL_CERTIFICATE | etc.
    source_type: str = "LABORATORY"  # LABORATORY | MANUFACTURER | REGULATOR | USER_UPLOAD
    source_authority: str = "LAB_REPORT"  # NABL_ACCREDITED_LAB | BIS_OFFICIAL | etc.
    verification_status: str = "VERIFIED"  # VERIFIED | UNVERIFIED | REJECTED | REQUIRES_REVIEW
    extracted_claim: Optional[str] = None
    attribute: str
    raw_value: str
    normalized_value: Any
    normalized_unit: Optional[str] = None
    page_number: Optional[int] = None
    page: Optional[int] = None
    bounding_box: Optional[Dict[str, Any]] = None
    source_excerpt: Optional[str] = None
    source_text: str = ""
    extraction_method: str = "STRUCTURED_PARSE"
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    authority: str = "LAB_REPORT"
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_hash: Optional[str] = None

    # M9 Deep Evidence Metadata & Freshness
    report_number: Optional[str] = None
    issuing_authority: str = "LAB_REPORT"
    standard_tested: Optional[str] = None
    issue_date: Optional[str] = None
    document_identity: Optional[str] = None
    evidence_freshness_years: Optional[float] = 0.0
    verification_state: str = "VERIFIED"

    def model_post_init(self, __context: Any) -> None:
        if self.page is not None and self.page_number is None:
            self.page_number = self.page
        elif self.page_number is not None and self.page is None:
            self.page = self.page_number
        if not self.source_excerpt and self.source_text:
            self.source_excerpt = self.source_text
        elif not self.source_text and self.source_excerpt:
            self.source_text = self.source_excerpt
        if not self.authority and self.source_authority:
            self.authority = self.source_authority
        elif not self.source_authority and self.authority:
            self.source_authority = self.authority
        if not self.document_identity and self.document_id:
            self.document_identity = self.document_id
        elif not self.document_id and self.document_identity:
            self.document_id = self.document_identity
        if not self.verification_state and self.verification_status:
            self.verification_state = self.verification_status
        elif not self.verification_status and self.verification_state:
            self.verification_status = self.verification_state
        if not self.issuing_authority and self.source_authority:
            self.issuing_authority = self.source_authority
        elif not self.source_authority and self.issuing_authority:
            self.source_authority = self.issuing_authority
        if not self.evidence_hash and self.source_text:
            self.evidence_hash = hashlib.sha256(self.source_text.encode("utf-8")).hexdigest()


class StructuredTable(BaseModel):
    """Extracted technical table matrix."""
    table_id: str
    page: int
    headers: List[str]
    rows: List[List[str]]
    confidence: float = 1.0
    extraction_method: str = "LAYOUT_PARSER"


def normalize_evidence_units(raw_val: str) -> Tuple[Any, Optional[str]]:
    """Normalize values and technical units (e.g. 60 deg C -> (60.0, 'C'))."""
    clean = raw_val.strip()
    
    # Temperature: 60 °C, 60C, 60 degrees Celsius, 60 deg C
    temp_match = re.search(r"([\d\.]+)\s*(?:°\s*c|deg\s*c|celsius|c\b)", clean, re.I)
    if temp_match:
        try:
            return float(temp_match.group(1)), "C"
        except ValueError:
            pass

    # Percentage: 0.05%, 0.05 percent
    pct_match = re.search(r"([\d\.]+)\s*(?:%|percent)", clean, re.I)
    if pct_match:
        try:
            return float(pct_match.group(1)), "%"
        except ValueError:
            pass

    # Volume / Capacity: 1000 ml, 1 litre, 0.75 L
    vol_litre = re.search(r"([\d\.]+)\s*(?:litres?|liters?|l\b)", clean, re.I)
    if vol_litre:
        try:
            return float(vol_litre.group(1)) * 1000.0, "ml"
        except ValueError:
            pass

    vol_ml = re.search(r"([\d\.]+)\s*(?:ml|millilitres?|milliliters?)\b", clean, re.I)
    if vol_ml:
        try:
            return float(vol_ml.group(1)), "ml"
        except ValueError:
            pass

    # Duration: 6 hours, 6h, 10 minutes, 10 min
    hour_match = re.search(r"([\d\.]+)\s*(?:hours?|hrs?|h\b)", clean, re.I)
    if hour_match:
        return float(hour_match.group(1)), "hours"

    min_match = re.search(r"([\d\.]+)\s*(?:minutes?|mins?|m\b)", clean, re.I)
    if min_match:
        return float(min_match.group(1)), "minutes"

    # Numeric fallback
    num_match = re.search(r"^([\d\.]+)$", clean)
    if num_match:
        try:
            return float(num_match.group(1)), None
        except ValueError:
            pass

    return clean, None


def extract_evidence_from_snippet(
    snippet: str,
    evidence_type: str = "TEST_REPORT",
    document_id: Optional[str] = None,
    page: Optional[int] = None,
    authority: str = "LAB_REPORT",
    assessment_id: Optional[str] = None,
    target_standard: Optional[str] = None,
) -> List[StructuredEvidence]:
    """Extract structured evidence parameters from document snippet or lab test report text.
    
    Treats all incoming snippets as untrusted data, passing them through security prompt sanitization.
    Zero LLM compliance authority: returns raw structured attributes for deterministic evaluation.
    """
    from backend.app.services.security.prompt_guard import scan_and_sanitize_untrusted_text

    scan_res = scan_and_sanitize_untrusted_text(snippet)
    clean_snippet = scan_res.sanitized_text

    evidences: List[StructuredEvidence] = []
    text_lower = clean_snippet.lower()

    # Extract Document Identity, Report Number, Tested Standard, and Dates
    rep_search = re.search(r"(?:report|cert|ref|certificate|lab\s*no)[\s#:\.\-]*([A-Za-z0-9\/\-]{4,25})", clean_snippet, re.I)
    rep_num = rep_search.group(1) if rep_search else None

    std_search = re.search(r"\bis\s*(\d{4,6}(?:\s*\([^\)]+\))?(?::\d{4})?)\b", clean_snippet, re.I)
    std_num = f"IS {std_search.group(1)}" if std_search else None

    date_search = re.search(r"\b(20\d{2})\b", clean_snippet)
    issue_yr = int(date_search.group(1)) if date_search else None
    fresh_years = round(2026 - issue_yr, 1) if issue_yr else 0.0
    issue_d_str = f"{issue_yr}-01-01" if issue_yr else None
    is_outdated = fresh_years > 3.0

    # Incompatible Standard Gate
    is_incompatible = False
    if target_standard and std_num:
        clean_target = target_standard.lower().replace(" ", "").split(":")[0]
        clean_std = std_num.lower().replace(" ", "").split(":")[0]
        if clean_target[:7] != clean_std[:7]:
            is_incompatible = True
    elif not target_standard and std_num:
        # Default assessment scope is IS 17526:2021
        if any(bad in std_num.lower() for bad in ["9873", "302", "4151", "12345", "14643"]):
            is_incompatible = True

    if is_incompatible:
        return [
            StructuredEvidence(
                evidence_id=f"EV-WRONG-STD-{page or 1}",
                assessment_id=assessment_id,
                document_id=document_id or "DOC-INCOMPATIBLE",
                evidence_type="INCOMPATIBLE_STANDARD",
                source_type="OTHER",
                source_authority="INCOMPATIBLE_STANDARD",
                verification_status="REJECTED",
                verification_state="REJECTED",
                extracted_claim=f"Document references incompatible standard {std_num} outside assessment scope {target_standard or 'IS 17526:2021'}.",
                attribute="incompatible_standard",
                raw_value="INCOMPATIBLE",
                normalized_value=None,
                page_number=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                authority="INCOMPATIBLE_STANDARD",
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        ]

    # 1. Temperature / Heat retention parameter (e.g. 64.5 deg C)
    temp_search = re.search(
        r"(?:temperature|heat retention|thermal performance|water temp)[^\d\n]*([\d\.]+\s*(?:°\s*c|deg\s*c|c\b))",
        clean_snippet,
        re.I,
    )
    if temp_search:
        raw_v = temp_search.group(1)
        norm_v, unit = normalize_evidence_units(raw_v)
        ev_id = f"EV-TEMP-{page or 1}-{int(norm_v)}"
        claim_str = f"Tested heat retention water temperature {norm_v}°{unit} after 6 hours."
        if is_outdated:
            claim_str += f" [WARNING: Stale evidence - issued {fresh_years} years ago; annual verification required]"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-{authority}",
                evidence_type=evidence_type,
                source_type="LABORATORY" if "LAB" in authority else "MANUFACTURER",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if authority in ("LAB_REPORT", "NABL_ACCREDITED_LAB", "BIS_OFFICIAL") else "REQUIRES_REVIEW"),
                verification_state="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if authority in ("LAB_REPORT", "NABL_ACCREDITED_LAB", "BIS_OFFICIAL") else "REQUIRES_REVIEW"),
                extracted_claim=claim_str,
                attribute="tested_heat_retention_temp",
                raw_value=raw_v,
                normalized_value=norm_v,
                normalized_unit=unit,
                page_number=page,
                page=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                extraction_method="STRUCTURED_PARSE",
                extraction_confidence=0.98,
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        )

    # 2. Inversion / Leakage parameter
    if any(k in text_lower for k in ["leakage", "inverted", "seepage"]):
        passed = (
            "no leakage" in text_lower
            or "nil" in text_lower
            or "zero leakage" in text_lower
            or "passed" in text_lower
        ) and "leakage observed" not in text_lower.replace("zero leakage observed", "").replace("no leakage observed", "")
        
        # If text explicitly says 'leakage observed' without zero/no
        if "leakage observed" in text_lower and not ("zero leakage" in text_lower or "no leakage" in text_lower):
            passed = False

        ev_id = f"EV-LEAK-{page or 1}"
        claim_str = "10-minute inversion test: zero leakage or moisture seepage confirmed." if passed else "Leakage test failed."
        if is_outdated:
            claim_str += f" [WARNING: Stale evidence - issued {fresh_years} years ago; annual verification required]"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-{authority}",
                evidence_type=evidence_type,
                source_type="LABORATORY" if "LAB" in authority else "MANUFACTURER",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if authority in ("LAB_REPORT", "NABL_ACCREDITED_LAB", "BIS_OFFICIAL") else "REQUIRES_REVIEW"),
                verification_state="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if authority in ("LAB_REPORT", "NABL_ACCREDITED_LAB", "BIS_OFFICIAL") else "REQUIRES_REVIEW"),
                extracted_claim=claim_str,
                attribute="leakage_test_result",
                raw_value="PASSED" if passed else "FAILED",
                normalized_value=1.0 if passed else 0.0,
                normalized_unit=None,
                page_number=page,
                page=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                extraction_method="STRUCTURED_PARSE",
                extraction_confidence=0.95,
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        )

    # 3. Material Certificate parameter (e.g. Grade 304 chemical composition)
    if "grade 304" in text_lower or "ss 304" in text_lower or "grade 201" in text_lower or "grade 316" in text_lower:
        grade = "Grade 304"
        norm_grade = "stainless_steel_grade_304"
        if "grade 201" in text_lower or "ss 201" in text_lower:
            grade = "Grade 201"
            norm_grade = "stainless_steel_grade_201"
        elif "grade 316" in text_lower or "ss 316" in text_lower:
            grade = "Grade 316"
            norm_grade = "stainless_steel_grade_316"

        ev_id = f"EV-MAT-{page or 1}"
        ev_type = "MATERIAL_CERTIFICATE" if "cert" in text_lower or "mill" in text_lower else evidence_type
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-MAT-{grade.replace(' ', '')}",
                evidence_type=ev_type,
                source_type="MANUFACTURER" if "mill" in text_lower else "LABORATORY",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if ("mill" in text_lower or "cert" in text_lower or "LAB" in authority) else "REQUIRES_REVIEW"),
                verification_state="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if ("mill" in text_lower or "cert" in text_lower or "LAB" in authority) else "REQUIRES_REVIEW"),
                extracted_claim=f"Material grade certified as {grade} (IS 6911 chemical composition).",
                attribute="material_grade_verified",
                raw_value=grade,
                normalized_value=norm_grade,
                normalized_unit=None,
                page_number=page,
                page=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                extraction_method="STRUCTURED_PARSE",
                extraction_confidence=0.96,
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        )

    # 4. Capacity parameter
    cap_search = re.search(r"(?:capacity|volume)[^\d\n]*([\d\.]+\s*(?:ml|millilitres?|litres?|liter|l)\b)", clean_snippet, re.I)
    if cap_search:
        raw_c = cap_search.group(1)
        norm_c, u_c = normalize_evidence_units(raw_c)
        ev_id = f"EV-CAP-{page or 1}-{int(norm_c)}"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-{authority}",
                evidence_type=evidence_type,
                source_type="LABORATORY" if "LAB" in authority else "MANUFACTURER",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if authority in ("LAB_REPORT", "NABL_ACCREDITED_LAB", "BIS_OFFICIAL") else "REQUIRES_REVIEW"),
                verification_state="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if authority in ("LAB_REPORT", "NABL_ACCREDITED_LAB", "BIS_OFFICIAL") else "REQUIRES_REVIEW"),
                extracted_claim=f"Measured product nominal capacity: {norm_c} {u_c}.",
                attribute="capacity_ml",
                raw_value=raw_c,
                normalized_value=norm_c,
                normalized_unit=u_c,
                page_number=page,
                page=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                extraction_method="STRUCTURED_PARSE",
                extraction_confidence=0.97,
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
            )
        )

    # 5. Marking / Artwork parameter
    if any(k in text_lower for k in ["artwork", "label", "isi mark", "standard mark", "marking"]):
        marked = "isi" in text_lower or "standard mark" in text_lower or "trademark" in text_lower
        ev_id = f"EV-MARK-{page or 1}"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-ARTWORK",
                evidence_type="LABEL_PHOTO" if "photo" in text_lower else "PRODUCT_SPECIFICATION",
                source_type="MANUFACTURER",
                source_authority="MANUFACTURER_DECLARATION",
                verification_status="VERIFIED" if marked else "REQUIRES_REVIEW",
                extracted_claim="Product label artwork includes manufacturer trademark, nominal capacity, and ISI Standard Mark layout." if marked else "Marking incomplete.",
                attribute="artwork_label_verified",
                raw_value="VERIFIED" if marked else "UNVERIFIED",
                normalized_value=1.0 if marked else 0.0,
                normalized_unit=None,
                page_number=page,
                page=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                extraction_method="STRUCTURED_PARSE",
                extraction_confidence=0.95,
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
                verification_state="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if marked else "REQUIRES_REVIEW"),
            )
        )

    # 6. Toys: Small parts cylinder test (Clause 4.4 IS 9873)
    if any(k in text_lower for k in ["small part", "cylinder test", "choking"]):
        passed = ("no small part" in text_lower or "zero detachment" in text_lower or "pass" in text_lower) and "failed" not in text_lower
        ev_id = f"EV-TOY-CHOKE-{page or 1}"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-{authority}",
                evidence_type="TEST_REPORT",
                source_type="LABORATORY",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if "LAB" in authority else "REQUIRES_REVIEW"),
                extracted_claim="Small parts test: no detachment, no small parts fit into cylinder." if passed else "Failed small parts choking hazard test.",
                attribute="small_parts_choke_test",
                raw_value="PASSED" if passed else "FAILED",
                normalized_value=1.0 if passed else 0.0,
                page_number=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        )

    # 7. Toys: Sharp Edges and Sharp Points (Clause 4.6, 4.7 IS 9873)
    if any(k in text_lower for k in ["sharp edge", "sharp point", "ptfe tape"]):
        passed = ("no sharp" in text_lower or "passed" in text_lower or "zero sharp" in text_lower) and "failed" not in text_lower
        ev_id = f"EV-TOY-EDGE-{page or 1}"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-{authority}",
                evidence_type="TEST_REPORT",
                source_type="LABORATORY",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if "LAB" in authority else "REQUIRES_REVIEW"),
                extracted_claim="Sharp edge & point test: no sharp edges cutting PTFE tape, zero sharp points." if passed else "Sharp edges or points detected.",
                attribute="sharp_edges_test",
                raw_value="PASSED" if passed else "FAILED",
                normalized_value=1.0 if passed else 0.0,
                page_number=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        )

    # 8. Electrical Safety: Dielectric Strength (Clause 13 IS 302)
    if any(k in text_lower for k in ["dielectric", "high voltage", "breakdown", "insulation resistance"]):
        passed = ("no breakdown" in text_lower or "withstood" in text_lower or "passed" in text_lower) and "breakdown observed" not in text_lower
        ev_id = f"EV-ELEC-DIEL-{page or 1}"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-{authority}",
                evidence_type="TEST_REPORT",
                source_type="LABORATORY",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if "LAB" in authority else "REQUIRES_REVIEW"),
                extracted_claim="Dielectric strength: 1000V/1250V AC applied with no flashover or breakdown." if passed else "Dielectric insulation breakdown observed.",
                attribute="dielectric_strength_test",
                raw_value="PASSED" if passed else "FAILED",
                normalized_value=1.0 if passed else 0.0,
                page_number=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        )

    # 9. Electrical Safety: Abnormal Operation Boil-Dry (Clause 19 IS 302)
    if any(k in text_lower for k in ["boil dry", "abnormal operation", "thermal cut-out", "thermal cutoff"]):
        passed = ("operated" in text_lower or "cut off" in text_lower or "passed" in text_lower) and "failed" not in text_lower
        ev_id = f"EV-ELEC-BOILDRY-{page or 1}"
        evidences.append(
            StructuredEvidence(
                evidence_id=ev_id,
                assessment_id=assessment_id,
                document_id=document_id or f"DOC-{authority}",
                evidence_type="TEST_REPORT",
                source_type="LABORATORY",
                source_authority=authority,
                verification_status="REQUIRES_REVIEW" if is_outdated else ("VERIFIED" if "LAB" in authority else "REQUIRES_REVIEW"),
                extracted_claim="Abnormal operation test: thermal cut-out operated reliably under boil-dry condition." if passed else "Thermal cutoff failed to operate.",
                attribute="boil_dry_cutoff_test",
                raw_value="PASSED" if passed else "FAILED",
                normalized_value=1.0 if passed else 0.0,
                page_number=page,
                source_excerpt=clean_snippet[:250],
                source_text=clean_snippet[:250],
                authority=authority,
                report_number=rep_num,
                standard_tested=std_num,
                issue_date=issue_d_str,
                evidence_freshness_years=fresh_years,
            )
        )

    # If no technical parameters matched, check for wrong-standard or irrelevant document
    if not evidences:
        is_wrong_std = bool(re.search(r"\bis\s*(9873|302|4151|12345|14643)\b", text_lower))
        if is_wrong_std:
            evidences.append(
                StructuredEvidence(
                    evidence_id=f"EV-WRONG-STD-{page or 1}",
                    assessment_id=assessment_id,
                    document_id=document_id or "DOC-INCOMPATIBLE",
                    evidence_type="INCOMPATIBLE_STANDARD",
                    source_type="OTHER",
                    source_authority="INCOMPATIBLE_STANDARD",
                    verification_status="REJECTED",
                    extracted_claim="Document references an incompatible Indian Standard outside the assessment scope.",
                    attribute="incompatible_standard",
                    raw_value="INCOMPATIBLE",
                    normalized_value=None,
                    page_number=page,
                    page=page,
                    source_excerpt=clean_snippet[:250],
                    source_text=clean_snippet[:250],
                    extraction_method="STRUCTURED_PARSE",
                    extraction_confidence=0.99,
                    authority="INCOMPATIBLE_STANDARD",
                )
            )
        elif any(w in text_lower for w in ["bill", "invoice", "payment", "receipt", "brochure", "marketing", "advertisement"]):
            evidences.append(
                StructuredEvidence(
                    evidence_id=f"EV-IRRELEVANT-{page or 1}",
                    assessment_id=assessment_id,
                    document_id=document_id or "DOC-IRRELEVANT",
                    evidence_type="IRRELEVANT_DOCUMENT",
                    source_type="OTHER",
                    source_authority="IRRELEVANT_DOCUMENT",
                    verification_status="REJECTED",
                    extracted_claim="Uploaded document contains commercial or utility text with no technical compliance test data.",
                    attribute="irrelevant_document",
                    raw_value="IRRELEVANT",
                    normalized_value=None,
                    page_number=page,
                    page=page,
                    source_excerpt=clean_snippet[:250],
                    source_text=clean_snippet[:250],
                    extraction_method="STRUCTURED_PARSE",
                    extraction_confidence=0.99,
                    authority="IRRELEVANT_DOCUMENT",
                )
            )

    return evidences


def detect_evidence_conflicts(evidences: List[StructuredEvidence]) -> List[Dict[str, Any]]:
    """Deterministically detect evidentiary contradictions across documents and parameters.
    
    Checks:
    - Numeric conflicts (e.g. Report 1: 1000ml vs Report 2: 750ml, or 64.5°C vs 54°C)
    - Unit-normalized conflicts (e.g. 1 L vs 750 ml)
    - Textual attribute conflicts (e.g. Grade 304 vs Grade 201)
    - Distinguishes consistent evidence (multiple documents agreeing) from conflicting evidence.
    
    The system NEVER silently resolves conflicts via LLM guessing; returns CONFLICTING_EVIDENCE + EXPERT_REVIEW.
    """
    conflicts = []
    attr_grouped: Dict[str, List[StructuredEvidence]] = {}
    for ev in evidences:
        attr_grouped.setdefault(ev.attribute, []).append(ev)

    for attr, ev_list in attr_grouped.items():
        if len(ev_list) <= 1:
            continue

        # Extract normalized values
        distinct_vals = []
        for ev in ev_list:
            val = ev.normalized_value
            # Check if this val is significantly different from existing distinct_vals
            matched = False
            for dv in distinct_vals:
                if isinstance(val, (int, float)) and isinstance(dv, (int, float)):
                    # Within 0.5% tolerance is considered consistent
                    if abs(val - dv) <= max(0.005 * max(abs(val), abs(dv)), 0.1):
                        matched = True
                        break
                elif str(val).strip().lower() == str(dv).strip().lower():
                    matched = True
                    break
            if not matched:
                distinct_vals.append(val)

        if len(distinct_vals) > 1:
            conflicts.append({
                "attribute": attr,
                "conflict_type": (
                    "NUMERIC_CONFLICT"
                    if all(isinstance(v, (int, float)) for v in distinct_vals)
                    else "TEXTUAL_CONFLICT"
                ),
                "conflict_description": (
                    f"Conflicting evidentiary values detected for attribute '{attr}': {distinct_vals}. "
                    "Independent documents present contradictory findings."
                ),
                "distinct_values": distinct_vals,
                "competing_evidences": [
                    {
                        "evidence_id": ev.evidence_id,
                        "document_id": ev.document_id,
                        "authority": ev.source_authority or ev.authority,
                        "raw_value": ev.raw_value,
                        "normalized_value": ev.normalized_value,
                        "normalized_unit": ev.normalized_unit,
                        "page": ev.page_number or ev.page,
                    }
                    for ev in ev_list
                ],
                "recommended_action": "EXPERT_REVIEW",
            })

    return conflicts
