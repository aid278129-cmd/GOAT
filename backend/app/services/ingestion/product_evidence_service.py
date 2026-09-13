"""Product Evidence Ingestion & Normalization Service (Milestone M25.2).

Enforces Cardinal Non-Negotiables:
1. USER INPUT IS NOT REGULATORY EVIDENCE.
2. AI-DERIVED INFORMATION IS NOT VERIFIED EVIDENCE.
3. NO INFERRED APPLICABILITY AT INGESTION TIME (Belongs strictly to Layer 5).
4. Full audit trail: raw value, normalized value, source reference, page/row, extraction method, SHA-256 hash.
"""

import os
import re
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union, Tuple

from backend.app.schemas.product_evidence import (
    EvidenceType,
    EvidenceHierarchyLevel,
    EvidenceVerificationStatus,
    SourceAuthenticity,
    ArtifactIntegrityStatus,
    ProductEvidenceRecord,
    get_hierarchy_for_evidence_type,
)
from backend.app.schemas.product_dna import (
    ProductFact,
    FactProvenanceType,
    FactVerificationState,
    FactCategory,
)
from backend.app.core.logging import logger


def calculate_sha256(data: Union[str, bytes]) -> str:
    """Compute SHA-256 hash of byte or string content."""
    if isinstance(data, str):
        if os.path.exists(data):
            hasher = hashlib.sha256()
            with open(data, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def normalize_fact_value(attribute: str, raw_str: str) -> Dict[str, Any]:
    """Deterministically parse and normalize physical product parameters."""
    raw = raw_str.strip()
    attr_lower = attribute.lower()

    # 1. Voltage normalization
    if "volt" in attr_lower or attr_lower in ("rated_voltage", "supply_voltage"):
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*V(?:olts?)?\s*(AC|DC)?", raw, re.IGNORECASE)
        if m:
            val = float(m.group(1)) if not m.group(2) else f"{m.group(1)}-{m.group(2)}"
            ac_dc = (m.group(3) or "AC").upper()
            return {"normalized": val, "unit": "V", "ac_dc": ac_dc, "raw": raw}

    # 2. Power / Wattage normalization
    if "watt" in attr_lower or "power" in attr_lower or attr_lower in ("rated_power", "wattage"):
        m_kw = re.search(r"(\d+(?:\.\d+)?)\s*k(?:W|Watts?)", raw, re.IGNORECASE)
        if m_kw:
            return {"normalized": float(m_kw.group(1)) * 1000.0, "unit": "W", "raw": raw}
        m_w = re.search(r"(\d+(?:\.\d+)?)\s*(?:W|Watts?)", raw, re.IGNORECASE)
        if m_w:
            return {"normalized": float(m_w.group(1)), "unit": "W", "raw": raw}

    # 3. Capacity / Volume normalization
    if "capacity" in attr_lower or "volume" in attr_lower:
        m_l = re.search(r"(\d+(?:\.\d+)?)\s*(?:L|Litres?|Liters?)", raw, re.IGNORECASE)
        if m_l:
            return {"normalized": float(m_l.group(1)), "unit": "L", "raw": raw}
        m_ml = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|millilitres?)", raw, re.IGNORECASE)
        if m_ml:
            return {"normalized": float(m_ml.group(1)) / 1000.0, "unit": "L", "raw": raw}

    # 4. Material normalization
    if "material" in attr_lower or "grade" in attr_lower:
        if re.search(r"304|grade\s*304|ss\s*304", raw, re.IGNORECASE):
            return {"normalized": "Grade 304", "unit": None, "material_type": "STAINLESS_STEEL", "raw": raw}
        if re.search(r"316|grade\s*316|ss\s*316", raw, re.IGNORECASE):
            return {"normalized": "Grade 316", "unit": None, "material_type": "STAINLESS_STEEL", "raw": raw}
        if re.search(r"abs|thermoplastic", raw, re.IGNORECASE):
            return {"normalized": "Thermoplastic ABS", "unit": None, "material_type": "POLYMER", "raw": raw}
        if re.search(r"frp|fiberglass|fibre", raw, re.IGNORECASE):
            return {"normalized": "Fiber Reinforced Plastic", "unit": None, "material_type": "COMPOSITE", "raw": raw}

    # 5. Pressure normalization
    if "pressure" in attr_lower:
        m_mpa = re.search(r"(\d+(?:\.\d+)?)\s*(?:MPa|megapascals?)", raw, re.IGNORECASE)
        if m_mpa:
            return {"normalized": float(m_mpa.group(1)), "unit": "MPa", "raw": raw}
        m_bar = re.search(r"(\d+(?:\.\d+)?)\s*bar", raw, re.IGNORECASE)
        if m_bar:
            return {"normalized": float(m_bar.group(1)) * 0.1, "unit": "MPa", "raw": raw}

    # Default fallback
    return {"normalized": raw, "unit": None, "raw": raw}


def create_evidence_record(
    evidence_id: str,
    product_id: str,
    evidence_type: EvidenceType,
    source_type: str,
    source_reference: str,
    extracted_value: str,
    attribute: str,
    source_location: Optional[str] = None,
    extraction_method: str = "MANUAL",
    sha256: Optional[str] = None,
    verified: bool = False,
    verification_status: EvidenceVerificationStatus = EvidenceVerificationStatus.UNVERIFIED,
    source_authenticity: Optional[SourceAuthenticity] = None,
    artifact_integrity: ArtifactIntegrityStatus = ArtifactIntegrityStatus.HASH_VALID,
    source_identity: Optional[str] = None,
    source_identity_verification: Optional[str] = None,
    authority_status: Optional[str] = None,
    acquisition_status: Optional[str] = None,
    verification_method: Optional[str] = None,
    verification_timestamp: Optional[datetime] = None,
    verifier: Optional[str] = None,
    source_url: Optional[str] = None,
    canonical_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> ProductEvidenceRecord:
    """Create a strictly typed ProductEvidenceRecord enforcing hierarchy and authenticity invariants."""
    # Enforce non-negotiable: USER_PROVIDED_CLAIM is always UNTRUSTED_USER_CLAIM and unverified
    if evidence_type == EvidenceType.USER_PROVIDED_CLAIM:
        hierarchy = EvidenceHierarchyLevel.UNTRUSTED_USER_CLAIM
        verified = False
        verification_status = EvidenceVerificationStatus.UNVERIFIED
        source_authenticity = SourceAuthenticity.UNVERIFIED
    else:
        hierarchy = get_hierarchy_for_evidence_type(evidence_type)
        if source_authenticity is None:
            if verified and verification_status == EvidenceVerificationStatus.VERIFIED:
                source_authenticity = SourceAuthenticity.REAL_AUTHORITATIVE
            else:
                source_authenticity = SourceAuthenticity.UNVERIFIED

    norm = normalize_fact_value(attribute, extracted_value)
    digest = sha256 or calculate_sha256(extracted_value)

    return ProductEvidenceRecord(
        evidence_id=evidence_id,
        product_id=product_id,
        evidence_type=evidence_type,
        hierarchy_level=hierarchy,
        source_type=source_type,
        source_reference=source_reference,
        source_location=source_location,
        extracted_value=extracted_value,
        normalized_value=norm["normalized"],
        unit=norm.get("unit"),
        attribute=attribute,
        extraction_method=extraction_method,
        confidence=1.0 if verified else 0.85,
        provenance=(
            f"Evidence '{evidence_id}' from {source_reference} ({source_type}"
            f"{f' at {source_location}' if source_location else ''}), SHA-256: {digest[:12]}..."
        ),
        sha256=digest,
        verified=verified,
        verification_status=verification_status,
        source_authenticity=source_authenticity,
        artifact_integrity=artifact_integrity,
        source_identity=source_identity,
        source_identity_verification=source_identity_verification,
        authority_status=authority_status,
        acquisition_status=acquisition_status,
        verification_method=verification_method,
        verification_timestamp=verification_timestamp,
        verifier=verifier,
        source_url=source_url,
        canonical_url=canonical_url,
        notes=notes,
    )


def evidence_to_product_dna_fact(record: ProductEvidenceRecord, fact_id: str) -> ProductFact:
    """Map a ProductEvidenceRecord into a deterministic ProductFact for Layer 2 Product DNA."""
    # Determine explicit fact category and provenance
    if record.evidence_type == EvidenceType.USER_PROVIDED_CLAIM:
        cat = FactCategory.UNRESOLVED
        prov = FactProvenanceType.USER_CLAIM
        state = FactVerificationState.NEEDS_CONFIRMATION
    elif record.is_authoritative():
        cat = FactCategory.VERIFIED_DOCUMENTARY_EVIDENCE
        prov = FactProvenanceType.VERIFIED_DOCUMENT_FACT
        state = FactVerificationState.CONFIRMED
    elif record.normalized_value is not None and record.normalized_value != record.extracted_value:
        cat = FactCategory.NORMALIZED_FACT
        prov = FactProvenanceType.BOM_FACT if record.source_type == "BOM" else FactProvenanceType.OCR_EXTRACTED
        state = FactVerificationState.NEEDS_CONFIRMATION
    else:
        cat = FactCategory.DIRECTLY_OBSERVED
        prov = FactProvenanceType.VERIFIED_DOCUMENT_FACT if record.verified else FactProvenanceType.USER_CLAIM
        state = FactVerificationState.CONFIRMED if record.verified else FactVerificationState.NEEDS_CONFIRMATION

    return ProductFact(
        fact_id=fact_id,
        field_name=record.attribute,
        display_name=record.attribute.replace("_", " ").title(),
        value=record.normalized_value if record.normalized_value is not None else record.extracted_value,
        raw_value=record.extracted_value,
        unit=record.unit,
        source=record.source_reference,
        source_location=record.source_location,
        provenance=prov,
        fact_category=cat,
        evidence_references=[record.evidence_id],
        evidence_sha256=record.sha256,
        confidence=record.confidence,
        verification_state=state,
        conflict_notes=record.notes,
    )
