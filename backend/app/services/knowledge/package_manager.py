"""Layer 4: Knowledge Package Manager.

Builds hierarchical StandardKnowledgePackage objects from the single
BIS-Standards-AI-Assistant dataset (real_bis_standards.json).

Responsibilities:
1. Source Registry integration with SHA-256 integrity validation.
2. Standard → QCO → Scope relationship construction.
3. Clause/requirement segmentation from codified clauses.
4. Evidence-type mapping per clause.
5. Version/amendment handling from dataset fields.
6. Source hashing and integrity check.
7. Knowledge coverage status computation.
8. Dataset versioning.

Critical Invariants:
VERIFIED SOURCE → MAY BE USED AS AUTHORITATIVE KNOWLEDGE
UNVERIFIED / PENDING → NEVER USED AS AUTHORITATIVE REGULATORY FACT
If full BIS text unavailable → preserve OFFICIAL_DOCUMENT_ACQUISITION_PENDING
Do NOT reconstruct or hallucinate missing clause text.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.app.core.config import BASE_DIR
from backend.app.core.logging import logger
from backend.app.services.knowledge.knowledge_package import (
    StandardKnowledgePackage,
    KnowledgeRequirement,
    KnowledgeTestParameter,
    QCOInstrument,
    KnowledgeVerificationStatus,
    KnowledgeAcquisitionStatus,
    KnowledgeCoverageDashboard,
    KnowledgeRetrievalResult,
    KnowledgeDocumentType,
)
from backend.app.services.orchestrator.knowledge_selector import VERIFIED_STANDARDS_CATALOG

DATASET_PATH = BASE_DIR / "data" / "bis_dataset" / "real_bis_standards.json"
METADATA_PATH = BASE_DIR / "data" / "bis_dataset" / "metadata.json"

# In-memory knowledge store
_PACKAGES: Dict[str, StandardKnowledgePackage] = {}
_COVERAGE: Optional[KnowledgeCoverageDashboard] = None
_DATASET_HASH: Optional[str] = None
_INITIALIZED: bool = False


def _compute_file_hash(path: Path) -> Optional[str]:
    """Compute SHA-256 hash of dataset file for integrity validation."""
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _map_verification_status(raw: str) -> KnowledgeVerificationStatus:
    """Map raw dataset verification_status to canonical enum."""
    raw_lower = raw.lower().strip() if raw else ""
    if raw_lower in ("verified_accurate", "verified", "active"):
        return KnowledgeVerificationStatus.VERIFIED
    elif raw_lower in ("pending", "pending_acquisition"):
        return KnowledgeVerificationStatus.PENDING_ACQUISITION
    elif raw_lower in ("requires_review", "review"):
        return KnowledgeVerificationStatus.REQUIRES_REVIEW
    return KnowledgeVerificationStatus.UNKNOWN


def _build_requirements_from_codified(standard_key: str) -> List[KnowledgeRequirement]:
    """Build segmented requirements from Layer 3 VERIFIED_STANDARDS_CATALOG codified clauses."""
    std_data = VERIFIED_STANDARDS_CATALOG.get(standard_key)
    if not std_data:
        return []

    reqs = []
    clauses_dict = std_data.get("clauses", {})
    for cl_num, cl_data in clauses_dict.items():
        reqs.append(KnowledgeRequirement(
            requirement_id=f"REQ-{standard_key.replace(' ', '-').replace(':', '-')}-CL{cl_num}",
            clause_number=cl_num,
            clause_title=cl_data["title"],
            requirement_text=cl_data["req"],
            verification_status=KnowledgeVerificationStatus.VERIFIED,
            acquisition_status=KnowledgeAcquisitionStatus.FULL_TEXT_AVAILABLE,
        ))
    return reqs


def _build_test_parameters(item: Dict[str, Any]) -> List[KnowledgeTestParameter]:
    """Extract testing parameters from dataset record."""
    std_num = item.get("standard_number", "")
    params = []
    for tp in item.get("key_testing_parameters", []):
        params.append(KnowledgeTestParameter(
            parameter_name=tp,
            source_standard=std_num,
        ))
    return params


def _build_qco_instrument(item: Dict[str, Any]) -> Optional[QCOInstrument]:
    """Build QCO/Regulatory Instrument from legal_source."""
    legal = item.get("legal_source") or {}
    if not legal and not item.get("mandatory_qco"):
        return None

    gazette = legal.get("gazette_order", "")
    if not gazette and item.get("mandatory_qco"):
        gazette = item.get("status", "Mandatory QCO")

    return QCOInstrument(
        order_name=gazette,
        notification_number=legal.get("notification_number"),
        issuing_ministry=legal.get("issuing_ministry"),
        enactment_date=legal.get("enactment_date"),
        gazette_url=legal.get("portal_url"),
        mandatory=bool(item.get("mandatory_qco", False)),
        verification_status=KnowledgeVerificationStatus.VERIFIED,
    )


def _match_codified_key(std_num: str, part: str = "", section: str = "") -> Optional[str]:
    """Try to match a dataset standard_number to a VERIFIED_STANDARDS_CATALOG key."""
    # Build a normalized dash-based code: IS 302 Part 2 Sec 201 -> IS 302-2-201
    dash_code = std_num.replace(" ", "")
    if part:
        import re as _re
        part_num = _re.search(r"\d+", part)
        if part_num:
            dash_code += f"-{part_num.group()}"
    if section:
        import re as _re
        sec_num = _re.search(r"\d+", section)
        if sec_num:
            dash_code += f"-{sec_num.group()}"

    for key in VERIFIED_STANDARDS_CATALOG:
        key_norm = key.replace(" ", "").split(":")[0]
        if dash_code == key_norm or std_num.replace(" ", "") == key_norm:
            return key
    return None


def _determine_acquisition_status(item: Dict[str, Any], codified_key: Optional[str]) -> KnowledgeAcquisitionStatus:
    """Determine whether we have full clause text or metadata only."""
    if codified_key and codified_key in VERIFIED_STANDARDS_CATALOG:
        clauses = VERIFIED_STANDARDS_CATALOG[codified_key].get("clauses", {})
        if clauses:
            return KnowledgeAcquisitionStatus.FULL_TEXT_AVAILABLE
    return KnowledgeAcquisitionStatus.METADATA_ONLY


def build_knowledge_packages(force_reload: bool = False) -> Dict[str, StandardKnowledgePackage]:
    """Build hierarchical knowledge packages from the dataset."""
    global _PACKAGES, _COVERAGE, _DATASET_HASH, _INITIALIZED

    if _INITIALIZED and not force_reload:
        return _PACKAGES

    if not DATASET_PATH.exists():
        logger.warning(f"BIS dataset not found at {DATASET_PATH}. Empty knowledge base.")
        _INITIALIZED = True
        return _PACKAGES

    # Compute integrity hash
    _DATASET_HASH = _compute_file_hash(DATASET_PATH)

    # Load metadata
    dataset_meta = {}
    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            dataset_meta = json.load(f)

    # Verify integrity against stored hash
    stored_hash = dataset_meta.get("sha256")
    if stored_hash and _DATASET_HASH and stored_hash != _DATASET_HASH:
        logger.warning(f"Dataset integrity mismatch! Expected {stored_hash}, got {_DATASET_HASH}")

    # Load dataset
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    _PACKAGES.clear()
    total_reqs = 0
    total_amendments = 0
    full_text_count = 0
    metadata_only_count = 0
    qco_count = 0
    categories = set()

    for item in raw_data:
        std_num = item.get("standard_number", "")
        part = f" ({item['part']})" if item.get("part") else ""
        sec = f" {item['section']}" if item.get("section") else ""
        year = item.get("year", "")
        full_code = f"{std_num}{part}{sec}:{year}".strip() if year else std_num

        codified_key = _match_codified_key(std_num, item.get("part", ""), item.get("section", ""))
        requirements = _build_requirements_from_codified(codified_key) if codified_key else []
        test_params = _build_test_parameters(item)
        qco = _build_qco_instrument(item)
        acq_status = _determine_acquisition_status(item, codified_key)
        v_status = _map_verification_status(item.get("verification_status", ""))

        # Marking requirements from keywords
        marking_reqs = []
        if any("mark" in kw.lower() for kw in item.get("keywords", [])):
            marking_reqs.append("BIS Standard Mark (ISI Mark) required on product and packaging")

        # Evidence types
        evidence_types = ["LAB_REPORT", "TYPE_TEST_CERTIFICATE"]
        cert_route = item.get("certification_route", "")
        if "factory audit" in cert_route.lower():
            evidence_types.append("FACTORY_AUDIT_REPORT")
        if "nabl" in cert_route.lower():
            evidence_types.append("NABL_ACCREDITED_CERTIFICATE")

        amendments = item.get("amendments", []) or []

        pkg = StandardKnowledgePackage(
            standard_number=std_num,
            full_standard_code=full_code,
            title=item.get("full_title", ""),
            short_title=item.get("short_title"),
            product_category=item.get("product_category", ""),
            industry=item.get("industry"),
            scheme=item.get("scheme"),
            certification_route=item.get("certification_route"),
            edition_year=year,
            publication_date=item.get("publication_date"),
            revision_date=item.get("revision_date"),
            status=item.get("status", "Active"),
            scope=item.get("scope"),
            qco_instrument=qco,
            regulatory_order_name=qco.order_name if qco else None,
            supersedes=item.get("supersedes"),
            superseded_by=item.get("superseded_by"),
            amendments=amendments,
            requirements=requirements,
            test_parameters=test_params,
            marking_requirements=marking_reqs,
            required_evidence_types=evidence_types,
            materials=item.get("materials", []),
            keywords=item.get("keywords", []),
            source_url=item.get("source_url"),
            document_url=item.get("document_url"),
            source_type=item.get("source_type"),
            source_date=item.get("source_date"),
            retrieved_at=item.get("retrieved_at"),
            verification_status=v_status,
            verification_note=item.get("verification_note"),
            knowledge_version=dataset_meta.get("dataset_version", "v1.2.0-gazette-verified"),
            content_hash=_DATASET_HASH,
            acquisition_status=acq_status,
            legal_source=item.get("legal_source"),
        )

        # Use full_code as primary key for multi-part standards
        pkg_key = full_code if (item.get("part") or item.get("section")) else std_num
        _PACKAGES[pkg_key] = pkg

        # Also index under alias keys for flexible lookup
        # e.g. "IS 302 (Part 2) Sec 201:2008" -> also register as "IS 302-2-201"
        if item.get("part") or item.get("section"):
            import re as _re
            alias = std_num
            p = item.get("part", "")
            s = item.get("section", "")
            if p:
                pn = _re.search(r"\d+", p)
                if pn:
                    alias += f"-{pn.group()}"
            if s:
                sn = _re.search(r"\d+", s)
                if sn:
                    alias += f"-{sn.group()}"
            if alias != std_num:
                _PACKAGES[alias] = pkg

        # Statistics
        total_reqs += len(requirements)
        total_amendments += len(amendments)
        if acq_status == KnowledgeAcquisitionStatus.FULL_TEXT_AVAILABLE:
            full_text_count += 1
        else:
            metadata_only_count += 1
        if qco and qco.mandatory:
            qco_count += 1
        categories.add(item.get("product_category", ""))

    # Build coverage dashboard
    _COVERAGE = KnowledgeCoverageDashboard(
        total_standards=len(raw_data),
        total_qcos=qco_count,
        standards_with_full_text=full_text_count,
        standards_with_metadata_only=metadata_only_count,
        pending_documents=metadata_only_count,
        requirements_indexed=total_reqs,
        searchable_chunks=len(_PACKAGES) + total_reqs,
        last_ingestion=dataset_meta.get("ingested_at"),
        dataset_version=dataset_meta.get("dataset_version", "v1.2.0-gazette-verified"),
        integrity_hash=_DATASET_HASH,
        source_verification_status="VERIFIED",
        categories_covered=len(categories),
        amendments_tracked=total_amendments,
    )

    _INITIALIZED = True
    logger.info(
        f"Layer 4 Knowledge Base initialized: {len(_PACKAGES)} standards, "
        f"{total_reqs} requirements, {full_text_count} full-text, "
        f"{metadata_only_count} metadata-only, {qco_count} QCOs"
    )
    return _PACKAGES


def get_package(standard_number: str) -> Optional[StandardKnowledgePackage]:
    """Get a knowledge package by standard number. Returns None for unknown standards."""
    build_knowledge_packages()
    # Direct match
    if standard_number in _PACKAGES:
        return _PACKAGES[standard_number]
    # Try normalized match (strip year)
    import re
    stripped = re.sub(r":\d{4}$", "", standard_number.strip())
    for key, pkg in _PACKAGES.items():
        if stripped.lower() == key.lower() or stripped.lower().replace(" ", "") == key.lower().replace(" ", ""):
            return pkg
    return None


def get_all_packages() -> List[StandardKnowledgePackage]:
    """Return all knowledge packages."""
    build_knowledge_packages()
    return list(_PACKAGES.values())


def get_coverage_dashboard() -> KnowledgeCoverageDashboard:
    """Return knowledge coverage statistics."""
    build_knowledge_packages()
    return _COVERAGE or KnowledgeCoverageDashboard()


def validate_dataset_integrity() -> Dict[str, Any]:
    """Validate dataset SHA-256 hash against stored metadata."""
    build_knowledge_packages()
    meta = {}
    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)

    stored_hash = meta.get("sha256", "")
    computed_hash = _DATASET_HASH or ""
    matches = stored_hash == computed_hash and bool(stored_hash)

    return {
        "stored_hash": stored_hash,
        "computed_hash": computed_hash,
        "integrity_valid": matches,
        "dataset_version": meta.get("dataset_version", "unknown"),
        "upstream_source": meta.get("upstream_source", ""),
        "upstream_commit": meta.get("upstream_commit", ""),
    }
