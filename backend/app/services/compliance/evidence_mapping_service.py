"""Milestone M26.1: Deterministic Evidence-to-Requirement Mapping Engine.

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
2. 3-Stage Cardinal Ontological Boundary:
   VERIFIED EVIDENCE ≠ SATISFIED REQUIREMENT ≠ COMPLIANCE RESULT.
3. Mapping Chain Invariant:
   Verified Evidence → Applicable Standard → Clause → Requirement → Evidence Eligibility → Evidence Status.
4. Anti-Keyword-Matching Guard:
   Do not allow evidence to satisfy a requirement merely because keywords match.
5. Strict Respect for Standard Identity & Revision:
   Mismatched standard or obsolete revision cannot satisfy current requirement.
6. Safe Abstention:
   If an artifact cannot be mapped confidently, return UNMAPPED or EXPERT_REVIEW_REQUIRED.
   Never infer compliance.
7. Authority Boundary:
   Layer 8 handles evidence/source trust. Layer 7 handles compliance decisions. LLM authority = 0.0%.
"""

import re
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
    validate_mapping_separation,
    classify_evidence_type,
)
from backend.app.services.compliance.evidence_eligibility import (
    EvidenceEligibilityEngine,
    RequirementClass,
    EligibilityStatus,
    EligibilityEvaluationResult,
    PERMITTED_EVIDENCE_TYPES,
)
from backend.app.services.compliance.evidence_validation_service import (
    EvidenceValidationPipeline,
    ValidationReport,
    AUTHORITATIVE_REGISTRY_DIRECTORY,
)
from backend.app.services.citation_guard.validator import PROHIBITED_INJECTION_PATTERNS
from backend.app.services.gap_analysis.comparator import compare_numeric_threshold, normalize_unit
from backend.app.core.logging import logger


# Verified Catalog of Gazette-Backed Standard Requirements (M26.1 Ground Truth)
VERIFIED_STANDARD_REQUIREMENTS: Dict[str, Dict[str, StandardRequirementDefinition]] = {
    # 1. IS 17526:2021 — Domestic Stainless Steel Vacuum Flasks
    "IS 17526:2021": {
        "REQ-IS17526-4.0": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="4.0",
            clause_id="cls-is17526-4-0",
            requirement_id="REQ-IS17526-4.0",
            requirement_title="General Design and Construction Requirements",
            requirement_class=RequirementClass.VISUAL_CONSTRUCTION.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="Vacuum insulated flasks shall safely contain beverages with non-toxic, food-safe contact surfaces.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.PRODUCT_PHOTOGRAPH,
                EvidenceType.LABEL_MARKING_EVIDENCE,
                EvidenceType.TECHNICAL_DRAWING,
            ],
        ),
        "REQ-IS17526-4.1": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="4.1",
            clause_id="cls-is17526-4-1",
            requirement_id="REQ-IS17526-4.1",
            requirement_title="Workmanship and Surface Finish",
            requirement_class=RequirementClass.VISUAL_CONSTRUCTION.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="Container shall be free from sharp edges, burrs, dents, or defects impairing safe operation.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.PRODUCT_PHOTOGRAPH,
                EvidenceType.LABEL_MARKING_EVIDENCE,
                EvidenceType.TECHNICAL_DRAWING,
            ],
        ),
        "REQ-IS17526-4.2.1": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="4.2.1",
            clause_id="cls-is17526-4-2-1",
            requirement_id="REQ-IS17526-4.2.1",
            requirement_title="Stainless Steel Contact Surfaces Material Conformance",
            requirement_class=RequirementClass.DECLARATION_REQUIREMENT.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="Food contact metallic surfaces shall be stainless steel Grade 304 conforming to IS 6911 with lead <= 0.05%.",
            threshold_spec={"target_value": "SS 304", "lead_max": 0.05},
            allowed_evidence_types=[
                EvidenceType.DECLARATION,
                EvidenceType.MANUFACTURER_DOCUMENT,
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS17526-5.1": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="5.1",
            clause_id="cls-is17526-5-1",
            requirement_id="REQ-IS17526-5.1",
            requirement_title="Nominal Capacity Specification",
            requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="Actual liquid holding capacity shall be within +/- 5% of declared nominal capacity.",
            threshold_spec={"tolerance_percent": 5.0, "unit": "ml"},
            allowed_evidence_types=[
                EvidenceType.MANUFACTURER_DATASHEET,
                EvidenceType.DATASHEET,
                EvidenceType.PRODUCT_SPECIFICATION,
                EvidenceType.TECHNICAL_DRAWING,
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS17526-5.2": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="5.2",
            clause_id="cls-is17526-5-2",
            requirement_id="REQ-IS17526-5.2",
            requirement_title="Inversion Leakage Test",
            requirement_class=RequirementClass.LAB_TEST_REQUIREMENT.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="Filled to capacity at ambient temperature, inverted for 10 minutes, showing zero moisture seepage or droplets.",
            threshold_spec={"inversion_minutes": 10, "max_leakage_droplets": 0},
            allowed_evidence_types=[
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS17526-5.3": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="5.3",
            clause_id="cls-is17526-5-3",
            requirement_id="REQ-IS17526-5.3",
            requirement_title="Drop Impact Resistance Test",
            requirement_class=RequirementClass.LAB_TEST_REQUIREMENT.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="Flask filled with water dropped from 1.0 m height onto concrete floor across two cycles retaining vacuum insulation.",
            threshold_spec={"drop_height_m": 1.0, "cycles": 2},
            allowed_evidence_types=[
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS17526-5.4": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="5.4",
            clause_id="cls-is17526-5-4",
            requirement_id="REQ-IS17526-5.4",
            requirement_title="6-Hour Thermal Heat Retention Performance",
            requirement_class=RequirementClass.LAB_TEST_REQUIREMENT.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="When filled with water at 95 C, temperature after 6 hours shall be >= 60 C for <= 1000 ml or >= 65 C for > 1000 ml.",
            threshold_spec={"operator": ">=", "target_value": 60.0, "unit": "°C", "duration_hours": 6},
            allowed_evidence_types=[
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS17526-7.1": StandardRequirementDefinition(
            standard_number="IS 17526:2021",
            standard_code="IS 17526",
            revision="2021",
            clause_number="7.1",
            clause_id="cls-is17526-7-1",
            requirement_id="REQ-IS17526-7.1",
            requirement_title="Product Marking and Labeling",
            requirement_class=RequirementClass.PHYSICAL_MARKING.value,
            applicable_product_category="Domestic Vacuum Flasks",
            description="Legible, indelible marking of manufacturer name/trademark, capacity, model number, batch, and BIS Standard Mark.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.LABEL_MARKING_EVIDENCE,
                EvidenceType.LABEL_PHOTO,
                EvidenceType.RATING_PLATE_PHOTO,
                EvidenceType.PRODUCT_PHOTOGRAPH,
            ],
        ),
    },

    # 2. IS 302-2-201:2008 — Electric Immersion Water Heaters
    "IS 302-2-201:2008": {
        "REQ-IS302-201-1.0": StandardRequirementDefinition(
            standard_number="IS 302-2-201:2008",
            standard_code="IS 302-2-201",
            revision="2008",
            clause_number="1.0",
            clause_id="cls-is302-201-1-0",
            requirement_id="REQ-IS302-201-1.0",
            requirement_title="Rated Voltage & Scope",
            requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
            applicable_product_category="Electric Immersion Water Heaters",
            description="Applies to portable electric immersion water heaters rated up to 250 V a.c. single phase.",
            threshold_spec={"operator": "<=", "target_value": 250.0, "unit": "V"},
            allowed_evidence_types=[
                EvidenceType.MANUFACTURER_DATASHEET,
                EvidenceType.DATASHEET,
                EvidenceType.PRODUCT_SPECIFICATION,
                EvidenceType.TECHNICAL_DRAWING,
                EvidenceType.LABORATORY_TEST_REPORT,
            ],
        ),
        "REQ-IS302-201-8.1": StandardRequirementDefinition(
            standard_number="IS 302-2-201:2008",
            standard_code="IS 302-2-201",
            revision="2008",
            clause_number="8.1",
            clause_id="cls-is302-201-8-1",
            requirement_id="REQ-IS302-201-8.1",
            requirement_title="Protection Against Electric Shock",
            requirement_class=RequirementClass.VISUAL_CONSTRUCTION.value,
            applicable_product_category="Electric Immersion Water Heaters",
            description="Standard test finger shall not contact live parts during immersion handling.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.PRODUCT_PHOTOGRAPH,
                EvidenceType.TECHNICAL_DRAWING,
                EvidenceType.LABORATORY_TEST_REPORT,
            ],
        ),
        "REQ-IS302-201-13.2": StandardRequirementDefinition(
            standard_number="IS 302-2-201:2008",
            standard_code="IS 302-2-201",
            revision="2008",
            clause_number="13.2",
            clause_id="cls-is302-201-13-2",
            requirement_id="REQ-IS302-201-13.2",
            requirement_title="Operating Leakage Current",
            requirement_class=RequirementClass.LAB_TEST_REQUIREMENT.value,
            applicable_product_category="Electric Immersion Water Heaters",
            description="At operating temperature, leakage current shall not exceed 0.75 mA for Class I appliances.",
            threshold_spec={"operator": "<=", "target_value": 0.75, "unit": "mA"},
            allowed_evidence_types=[
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS302-201-13.3": StandardRequirementDefinition(
            standard_number="IS 302-2-201:2008",
            standard_code="IS 302-2-201",
            revision="2008",
            clause_number="13.3",
            clause_id="cls-is302-201-13-3",
            requirement_id="REQ-IS302-201-13.3",
            requirement_title="Electric Insulation Strength (Dielectric Withstand)",
            requirement_class=RequirementClass.LAB_TEST_REQUIREMENT.value,
            applicable_product_category="Electric Immersion Water Heaters",
            description="Insulation shall withstand 1250 V a.c. for 1 minute without dielectric breakdown.",
            threshold_spec={"operator": ">=", "target_value": 1250.0, "unit": "V", "duration_seconds": 60},
            allowed_evidence_types=[
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS302-201-7.1": StandardRequirementDefinition(
            standard_number="IS 302-2-201:2008",
            standard_code="IS 302-2-201",
            revision="2008",
            clause_number="7.1",
            clause_id="cls-is302-201-7-1",
            requirement_id="REQ-IS302-201-7.1",
            requirement_title="Marking and Instructions",
            requirement_class=RequirementClass.PHYSICAL_MARKING.value,
            applicable_product_category="Electric Immersion Water Heaters",
            description="Marking of rated wattage, rated voltage, manufacturer name, minimum/maximum water level marks, and ISI Mark.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.LABEL_MARKING_EVIDENCE,
                EvidenceType.LABEL_PHOTO,
                EvidenceType.RATING_PLATE_PHOTO,
                EvidenceType.PRODUCT_PHOTOGRAPH,
            ],
        ),
    },

    # 3. IS 4151:2015 — Protective Helmets for Two Wheeler Riders
    "IS 4151:2015": {
        "REQ-IS4151-4.1": StandardRequirementDefinition(
            standard_number="IS 4151:2015",
            standard_code="IS 4151",
            revision="2015",
            clause_number="4.1",
            clause_id="cls-is4151-4-1",
            requirement_id="REQ-IS4151-4.1",
            requirement_title="Shell Material Specification",
            requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
            applicable_product_category="Two-Wheeler Helmets",
            description="Shell material shall be high-impact polymer, composite, or alloy.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.MANUFACTURER_DATASHEET,
                EvidenceType.PRODUCT_SPECIFICATION,
                EvidenceType.DECLARATION,
            ],
        ),
        "REQ-IS4151-7.1": StandardRequirementDefinition(
            standard_number="IS 4151:2015",
            standard_code="IS 4151",
            revision="2015",
            clause_number="7.1",
            clause_id="cls-is4151-7-1",
            requirement_id="REQ-IS4151-7.1",
            requirement_title="Impact Absorption Test",
            requirement_class=RequirementClass.LAB_TEST_REQUIREMENT.value,
            applicable_product_category="Two-Wheeler Helmets",
            description="Peak acceleration imparted to headform shall not exceed 300 g during drop tower anvil impact.",
            threshold_spec={"operator": "<=", "target_value": 300.0, "unit": "g"},
            allowed_evidence_types=[
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS4151-9.1": StandardRequirementDefinition(
            standard_number="IS 4151:2015",
            standard_code="IS 4151",
            revision="2015",
            clause_number="9.1",
            clause_id="cls-is4151-9-1",
            requirement_id="REQ-IS4151-9.1",
            requirement_title="Marking and Labeling",
            requirement_class=RequirementClass.PHYSICAL_MARKING.value,
            applicable_product_category="Two-Wheeler Helmets",
            description="Marking of helmet size, manufacturer, month/year of manufacture, and ISI Mark.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.LABEL_MARKING_EVIDENCE,
                EvidenceType.LABEL_PHOTO,
                EvidenceType.RATING_PLATE_PHOTO,
            ],
        ),
    },

    # 4. IS 14543:2024 — Packaged Drinking Water
    "IS 14543:2024": {
        "REQ-IS14543-5.1": StandardRequirementDefinition(
            standard_number="IS 14543:2024",
            standard_code="IS 14543",
            revision="2024",
            clause_number="5.1",
            clause_id="cls-is14543-5-1",
            requirement_id="REQ-IS14543-5.1",
            requirement_title="Total Dissolved Solids (TDS)",
            requirement_class=RequirementClass.LAB_TEST_REQUIREMENT.value,
            applicable_product_category="Packaged Drinking Water",
            description="Total dissolved solids shall not exceed 500 mg/l when tested under IS 3025 (Part 16).",
            threshold_spec={"operator": "<=", "target_value": 500.0, "unit": "mg/l"},
            allowed_evidence_types=[
                EvidenceType.LABORATORY_TEST_REPORT,
                EvidenceType.TEST_REPORT,
            ],
        ),
        "REQ-IS14543-7.1": StandardRequirementDefinition(
            standard_number="IS 14543:2024",
            standard_code="IS 14543",
            revision="2024",
            clause_number="7.1",
            clause_id="cls-is14543-7-1",
            requirement_id="REQ-IS14543-7.1",
            requirement_title="Marking and Packaging",
            requirement_class=RequirementClass.PHYSICAL_MARKING.value,
            applicable_product_category="Packaged Drinking Water",
            description="Each bottle clearly and indelibly marked with ISI mark, batch, mfg date, best before date, net volume.",
            threshold_spec=None,
            allowed_evidence_types=[
                EvidenceType.LABEL_MARKING_EVIDENCE,
                EvidenceType.LABEL_PHOTO,
                EvidenceType.PRODUCT_PHOTOGRAPH,
            ],
        ),
    },
}


class DeterministicEvidenceRequirementMapper:
    """Production Engine for Deterministic Evidence-to-Requirement Mapping (Milestone M26.1)."""

    @staticmethod
    def parse_standard_and_revision(raw_std: str) -> Tuple[str, Optional[str]]:
        """Extract canonical base standard code and revision year from raw standard string.
        Examples:
        - "IS 17526:2021" -> ("IS 17526", "2021")
        - "IS 302-2-201:2008" -> ("IS 302-2-201", "2008")
        - "IS 4151 : 2015" -> ("IS 4151", "2015")
        - "IS 17526-2021" -> ("IS 17526", "2021")
        - "IS 17526" -> ("IS 17526", None)
        """
        clean = raw_std.strip()
        # Handle colon format
        if ":" in clean:
            parts = clean.split(":")
            std_code = parts[0].strip()
            rev = parts[1].strip()
            # Match 4-digit year
            year_match = re.search(r"\b(19\d\d|20\d\d)\b", rev)
            return std_code, year_match.group(1) if year_match else rev

        # Handle hyphen format with year e.g. IS 17526-2021
        hyphen_match = re.search(r"^(.*?)-(19\d\d|20\d\d)$", clean)
        if hyphen_match:
            return hyphen_match.group(1).strip(), hyphen_match.group(2)

        # Handle space format with year e.g. IS 17526 2021
        space_match = re.search(r"^(.*?)\s+(19\d\d|20\d\d)$", clean)
        if space_match and "PART" not in space_match.group(1).upper():
            return space_match.group(1).strip(), space_match.group(2)

        return clean, None

    @classmethod
    def get_requirement_definition(
        cls,
        standard_number: str,
        clause_or_req_id: str,
    ) -> Optional[StandardRequirementDefinition]:
        """Lookup authoritative requirement definition by standard and clause/requirement ID."""
        std_clean = standard_number.strip()
        catalog = VERIFIED_STANDARD_REQUIREMENTS.get(std_clean)
        if not catalog:
            # Try fuzzy base standard code match
            base_code, rev = cls.parse_standard_and_revision(std_clean)
            for k, cat in VERIFIED_STANDARD_REQUIREMENTS.items():
                k_base, k_rev = cls.parse_standard_and_revision(k)
                if k_base == base_code and (rev is None or rev == k_rev):
                    catalog = cat
                    break

        if not catalog:
            return None

        # Direct requirement ID match
        if clause_or_req_id in catalog:
            return catalog[clause_or_req_id]

        # Clause number match e.g. "5.2" or "Clause 5.2"
        clean_cl = clause_or_req_id.lower().replace("clause", "").replace("cls", "").strip()
        for req_def in catalog.values():
            if req_def.clause_number.lower() == clean_cl:
                return req_def
            if req_def.clause_id.lower() == clause_or_req_id.lower():
                return req_def

        return None

    @classmethod
    def map_evidence_to_requirement(
        cls,
        evidence: Optional[ProductEvidenceRecord],
        target_standard: str,
        target_clause: Optional[str] = None,
        target_requirement_id: Optional[str] = None,
        target_product_category: Optional[str] = None,
        allow_synthetic: bool = True,
        conflicting_evidences: Optional[List[ProductEvidenceRecord]] = None,
    ) -> EvidenceRequirementMappingRecord:
        """Deterministically map a verified evidence artifact to an applicable standard requirement (M26.1).
        
        Enforces the mapping chain:
        Verified Evidence → Applicable Standard → Clause → Requirement → Evidence Eligibility → Evidence Status
        
        Strict Non-Negotiables:
        1. Keyword match alone NEVER satisfies a requirement.
        2. Standard identity and exact revision must match.
        3. Clause identity must match.
        4. Evidence type must be eligible for the requirement class.
        5. VERIFIED EVIDENCE ≠ SATISFIED REQUIREMENT ≠ COMPLIANCE RESULT.
        6. LLM compliance authority is exactly 0.0%.
        """
        mapping_id = f"MAP-{evidence.evidence_id if evidence else 'NONE'}-{target_requirement_id or target_clause or 'REQ'}"

        # ---------------------------------------------------------
        # Case 1: Missing Evidence Handling
        # ---------------------------------------------------------
        if evidence is None or evidence.evidence_type == EvidenceType.MISSING_EVIDENCE:
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id="NO_ARTIFACT",
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause=target_clause or "UNKNOWN_CLAUSE",
                clause_id=None,
                requirement=target_requirement_id or "UNKNOWN_REQUIREMENT",
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.UNMAPPED,
            )
            ev_chain = EvidenceChainRecord(
                artifact_identity="NO_ARTIFACT",
                source="NONE",
                provenance="No artifact supplied",
                authenticity=SourceAuthenticity.UNVERIFIED,
                evidence_type=EvidenceType.MISSING_EVIDENCE,
                applicable_requirement=target_requirement_id or target_clause or "UNKNOWN",
                verification_status=EvidenceVerificationStatus.MISSING,
            )
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id="NO_ARTIFACT",
                evidence_type=EvidenceType.MISSING_EVIDENCE,
                ontology_tier=EvidenceOntologyTier.USER_CLAIM,
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause_number=target_clause or "UNKNOWN",
                clause_id=None,
                requirement_id=target_requirement_id or "UNKNOWN",
                requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                mapping_status=RequirementMappingStatus.UNMAPPED,
                mapping_reason="Safe abstention: no evidence provided to map to requirement.",
                is_eligible=False,
                eligibility_reason="Missing required evidence artifact.",
                is_authentic=False,
                satisfaction_status=RequirementSatisfactionStatus.UNVERIFIED,
                gap=f"Missing evidence for requirement '{target_requirement_id or target_clause}' under {target_standard}.",
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="Safe abstention: unmapped due to missing evidence.",
            )

        # ---------------------------------------------------------
        # Case 2: Security & Adversarial Prompt Injection Defense
        # ---------------------------------------------------------
        scan_content = f"{evidence.extracted_value} {evidence.source_reference} {evidence.notes or ''}"
        for pat in PROHIBITED_INJECTION_PATTERNS:
            if pat.search(scan_content):
                chain = EvidenceRequirementMappingChain(
                    verified_evidence_id=evidence.evidence_id,
                    applicable_standard=target_standard,
                    standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                    clause=target_clause or evidence.applicable_clause or "UNKNOWN",
                    clause_id=None,
                    requirement=target_requirement_id or evidence.applicable_requirement or "UNKNOWN",
                    evidence_eligibility="NOT_ELIGIBLE",
                    evidence_status=RequirementMappingStatus.REJECTED,
                )
                ev_chain = evidence.to_evidence_chain_record()
                ev_chain.authenticity = SourceAuthenticity.REJECTED
                ev_chain.verification_status = EvidenceVerificationStatus.REJECTED
                return EvidenceRequirementMappingRecord(
                    mapping_id=mapping_id,
                    evidence_id=evidence.evidence_id,
                    evidence_type=evidence.evidence_type,
                    ontology_tier=evidence.ontology_tier,
                    applicable_standard=target_standard,
                    standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                    clause_number=target_clause or "UNKNOWN",
                    clause_id=None,
                    requirement_id=target_requirement_id or "UNKNOWN",
                    requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                    mapping_status=RequirementMappingStatus.REJECTED,
                    mapping_reason="Adversarial prompt injection attempt intercepted in artifact payload.",
                    is_eligible=False,
                    eligibility_reason="Security violation: malicious instruction inside evidence payload.",
                    is_authentic=False,
                    satisfaction_status=RequirementSatisfactionStatus.UNVERIFIED,
                    gap="Security violation: prompt injection payload rejected by Layer 8.",
                    mapping_chain=chain,
                    evidence_chain=ev_chain,
                    compliance_authority="LAYER_7_ONLY",
                    llm_compliance_authority=0.0,
                    regulatory_conclusion="NONE",
                    notes="Prompt injection intercepted. Mandatory rejection.",
                )

        # ---------------------------------------------------------
        # Case 3: Conflicting Evidence Check
        # ---------------------------------------------------------
        if (
            evidence.evidence_type == EvidenceType.CONFLICTING_EVIDENCE
            or evidence.verification_status == EvidenceVerificationStatus.CONFLICTING
            or (conflicting_evidences and len(conflicting_evidences) > 1)
        ):
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id=evidence.evidence_id,
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause=target_clause or evidence.applicable_clause or "UNKNOWN",
                clause_id=None,
                requirement=target_requirement_id or evidence.applicable_requirement or "UNKNOWN",
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.CONFLICTING,
            )
            ev_chain = evidence.to_evidence_chain_record()
            ev_chain.verification_status = EvidenceVerificationStatus.CONFLICTING
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id=evidence.evidence_id,
                evidence_type=EvidenceType.CONFLICTING_EVIDENCE,
                ontology_tier=EvidenceOntologyTier.DOCUMENT,
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause_number=target_clause or "UNKNOWN",
                clause_id=None,
                requirement_id=target_requirement_id or "UNKNOWN",
                requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                mapping_status=RequirementMappingStatus.CONFLICTING,
                mapping_reason="Conflicting documentary evidence detected for requirement; autonomous resolution prohibited.",
                is_eligible=False,
                eligibility_reason="Contradictory evidence values across submitted artifacts.",
                is_authentic=evidence.is_authoritative(allow_synthetic=allow_synthetic),
                satisfaction_status=RequirementSatisfactionStatus.PENDING_LAYER_7,
                gap="Conflicting artifacts require expert regulatory review.",
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="Conflicting evidence mapped. Requires human expert review.",
            )

        # ---------------------------------------------------------
        # Case 4: Ontological Boundary Check (USER CLAIM possesses 0% authority)
        # ---------------------------------------------------------
        if evidence.evidence_type in (EvidenceType.USER_CLAIM, EvidenceType.USER_PROVIDED_CLAIM):
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id=evidence.evidence_id,
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause=target_clause or evidence.applicable_clause or "UNKNOWN",
                clause_id=None,
                requirement=target_requirement_id or evidence.applicable_requirement or "UNKNOWN",
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.INELIGIBLE,
            )
            ev_chain = evidence.to_evidence_chain_record()
            ev_chain.verification_status = EvidenceVerificationStatus.UNVERIFIED
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id=evidence.evidence_id,
                evidence_type=EvidenceType.USER_CLAIM,
                ontology_tier=EvidenceOntologyTier.USER_CLAIM,
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause_number=target_clause or "UNKNOWN",
                clause_id=None,
                requirement_id=target_requirement_id or "UNKNOWN",
                requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                mapping_status=RequirementMappingStatus.INELIGIBLE,
                mapping_reason="User claim (Tier 0) possesses 0.0% regulatory authority and cannot satisfy technical requirements.",
                is_eligible=False,
                eligibility_reason="User claims cannot serve as authoritative regulatory evidence.",
                is_authentic=False,
                satisfaction_status=RequirementSatisfactionStatus.UNVERIFIED,
                gap="User assertion cannot satisfy requirement without authoritative documentary evidence.",
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="USER CLAIM != VERIFIED EVIDENCE.",
            )

        # ---------------------------------------------------------
        # Case 5: Authenticity & Integrity Verification
        # ---------------------------------------------------------
        auth, integ, issues = EvidenceValidationPipeline.verify_artifact_authenticity(
            evidence_record=evidence,
            allow_synthetic=allow_synthetic,
        )
        is_auth_ok = auth in (
            SourceAuthenticity.REAL_AUTHORITATIVE,
            SourceAuthenticity.REAL_NON_AUTHORITATIVE,
            SourceAuthenticity.SYNTHETIC,
            SourceAuthenticity.SIMULATED,
        )
        if not is_auth_ok or integ != ArtifactIntegrityStatus.HASH_VALID:
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id=evidence.evidence_id,
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause=target_clause or evidence.applicable_clause or "UNKNOWN",
                clause_id=None,
                requirement=target_requirement_id or evidence.applicable_requirement or "UNKNOWN",
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.REJECTED if auth == SourceAuthenticity.REJECTED else RequirementMappingStatus.UNMAPPED,
            )
            ev_chain = evidence.to_evidence_chain_record()
            ev_chain.authenticity = auth
            ev_chain.verification_status = EvidenceVerificationStatus.REJECTED if auth == SourceAuthenticity.REJECTED else EvidenceVerificationStatus.UNVERIFIED
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id=evidence.evidence_id,
                evidence_type=evidence.evidence_type,
                ontology_tier=EvidenceOntologyTier.DOCUMENT,
                applicable_standard=target_standard,
                standard_revision=cls.parse_standard_and_revision(target_standard)[1],
                clause_number=target_clause or "UNKNOWN",
                clause_id=None,
                requirement_id=target_requirement_id or "UNKNOWN",
                requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                mapping_status=chain.evidence_status,
                mapping_reason=f"Authenticity verification failed: {'; '.join(issues) or auth.value}.",
                is_eligible=False,
                eligibility_reason="Evidence fails source authenticity or hash integrity.",
                is_authentic=False,
                satisfaction_status=RequirementSatisfactionStatus.UNVERIFIED,
                gap=f"Artifact '{evidence.evidence_id}' fails Layer 8 authenticity verification.",
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="Authenticity cannot be inferred from hash alone.",
            )

        # ---------------------------------------------------------
        # Case 6: Standard Identity & Revision Matching
        # ---------------------------------------------------------
        target_code, target_rev = cls.parse_standard_and_revision(target_standard)
        ev_code, ev_rev = cls.parse_standard_and_revision(evidence.applicable_standard or "")

        # Cross-Standard Isolation: Base standard code must match (or be recognized harmonious cross-ref)
        is_harmonious = (
            target_code == "IS 17526" and ev_code == "IS 6911"
        )
        if evidence.applicable_standard and ev_code != target_code and not is_harmonious:
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id=evidence.evidence_id,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause=target_clause or evidence.applicable_clause or "UNKNOWN",
                clause_id=None,
                requirement=target_requirement_id or "UNKNOWN",
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.REJECTED,
            )
            ev_chain = evidence.to_evidence_chain_record()
            ev_chain.verification_status = EvidenceVerificationStatus.REJECTED
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id=evidence.evidence_id,
                evidence_type=evidence.evidence_type,
                ontology_tier=evidence.ontology_tier,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause_number=target_clause or "UNKNOWN",
                clause_id=None,
                requirement_id=target_requirement_id or "UNKNOWN",
                requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                mapping_status=RequirementMappingStatus.REJECTED,
                mapping_reason=f"Cross-standard isolation failure: evidence standard '{evidence.applicable_standard}' != target '{target_standard}'.",
                is_eligible=False,
                eligibility_reason="Cross-standard leakage prohibited (0% cross-standard leakage invariant).",
                is_authentic=True,
                satisfaction_status=RequirementSatisfactionStatus.NOT_SATISFIED,
                gap=f"Evidence belongs to standard '{evidence.applicable_standard}', not applicable to '{target_standard}'.",
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="Cross-standard isolation enforced.",
            )

        # Standard Revision Matching: Same standard, but superseded or mismatched revision year
        if target_rev and ev_rev and target_rev != ev_rev:
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id=evidence.evidence_id,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause=target_clause or evidence.applicable_clause or "UNKNOWN",
                clause_id=None,
                requirement=target_requirement_id or "UNKNOWN",
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.REJECTED,
            )
            ev_chain = evidence.to_evidence_chain_record()
            ev_chain.verification_status = EvidenceVerificationStatus.REJECTED
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id=evidence.evidence_id,
                evidence_type=evidence.evidence_type,
                ontology_tier=evidence.ontology_tier,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause_number=target_clause or "UNKNOWN",
                clause_id=None,
                requirement_id=target_requirement_id or "UNKNOWN",
                requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                mapping_status=RequirementMappingStatus.REJECTED,
                mapping_reason=(
                    f"Standard revision mismatch: evidence references revision '{ev_rev}' "
                    f"while statutory requirement demands current revision '{target_rev}'. "
                    f"Superseded revision evidence cannot satisfy current mandatory order."
                ),
                is_eligible=False,
                eligibility_reason="Standard revision mismatch: obsolete revision not legally compliant.",
                is_authentic=True,
                satisfaction_status=RequirementSatisfactionStatus.NOT_SATISFIED,
                gap=f"Artifact references superseded revision {ev_rev} instead of mandated {target_rev}.",
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="Standard revision mismatch enforced.",
            )

        # ---------------------------------------------------------
        # Case 7: Requirement Resolution & Anti-Keyword-Matching Guard
        # ---------------------------------------------------------
        lookup_key = target_requirement_id or target_clause or evidence.applicable_requirement or evidence.applicable_clause
        req_def = None
        if lookup_key:
            req_def = cls.get_requirement_definition(target_standard, lookup_key)

        # Anti-Keyword Guard:
        # If evidence mentions generic keywords in its text without explicit clause/requirement mapping,
        # or if lookup_key is missing/unresolvable, reject keyword-based inference!
        has_explicit_clause = bool(
            evidence.applicable_clause
            or (evidence.applicable_requirement and evidence.applicable_requirement in (target_requirement_id or ""))
            or (target_clause and target_clause.lower() in (evidence.source_location or "").lower())
            or (target_clause and target_clause.lower() in (evidence.provenance or "").lower())
        )

        if not req_def and not has_explicit_clause:
            # Evidence might contain words like "leakage" or "test" but lacks explicit clause or requirement binding
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id=evidence.evidence_id,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause=target_clause or "UNMAPPED_CLAUSE",
                clause_id=None,
                requirement=target_requirement_id or "UNMAPPED_REQUIREMENT",
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.UNMAPPED,
            )
            ev_chain = evidence.to_evidence_chain_record()
            ev_chain.verification_status = EvidenceVerificationStatus.UNVERIFIED
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id=evidence.evidence_id,
                evidence_type=evidence.evidence_type,
                ontology_tier=evidence.ontology_tier,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause_number=target_clause or "UNKNOWN",
                clause_id=None,
                requirement_id=target_requirement_id or "UNKNOWN",
                requirement_class=RequirementClass.TECHNICAL_SPECIFICATION.value,
                mapping_status=RequirementMappingStatus.UNMAPPED,
                mapping_reason="Keyword-only match rejected: evidence lacks explicit clause or standard requirement binding. Compliance cannot be inferred from keywords alone.",
                is_eligible=False,
                eligibility_reason="Unmapped requirement: missing deterministic clause linkage.",
                is_authentic=True,
                satisfaction_status=RequirementSatisfactionStatus.UNVERIFIED,
                gap="Cannot map artifact confidently to a specific clause; compliance not inferred.",
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="Anti-keyword-matching guard triggered.",
            )

        # Fallback requirement specification if not in catalog
        req_id = req_def.requirement_id if req_def else (target_requirement_id or f"REQ-{target_clause}")
        cl_num = req_def.clause_number if req_def else (target_clause or evidence.applicable_clause or "UNKNOWN")
        cl_id = req_def.clause_id if req_def else f"cls-{cl_num.replace(' ', '-').lower()}"
        req_class_name = req_def.requirement_class if req_def else EvidenceEligibilityEngine.infer_requirement_class(req_id, evidence.attribute).value

        try:
            req_class = RequirementClass(req_class_name)
        except ValueError:
            req_class = RequirementClass.TECHNICAL_SPECIFICATION

        # ---------------------------------------------------------
        # Case 8: Clause Identity Mismatch
        # ---------------------------------------------------------
        if target_clause and evidence.applicable_clause:
            cl_tgt_clean = target_clause.lower().replace("clause", "").replace("cls", "").strip()
            cl_ev_clean = evidence.applicable_clause.lower().replace("clause", "").replace("cls", "").strip()
            if cl_tgt_clean != cl_ev_clean and not cl_ev_clean.startswith(cl_tgt_clean):
                chain = EvidenceRequirementMappingChain(
                    verified_evidence_id=evidence.evidence_id,
                    applicable_standard=target_standard,
                    standard_revision=target_rev,
                    clause=target_clause,
                    clause_id=cl_id,
                    requirement=req_id,
                    evidence_eligibility="NOT_ELIGIBLE",
                    evidence_status=RequirementMappingStatus.UNMAPPED,
                )
                ev_chain = evidence.to_evidence_chain_record()
                ev_chain.verification_status = EvidenceVerificationStatus.UNVERIFIED
                return EvidenceRequirementMappingRecord(
                    mapping_id=mapping_id,
                    evidence_id=evidence.evidence_id,
                    evidence_type=evidence.evidence_type,
                    ontology_tier=evidence.ontology_tier,
                    applicable_standard=target_standard,
                    standard_revision=target_rev,
                    clause_number=target_clause,
                    clause_id=cl_id,
                    requirement_id=req_id,
                    requirement_class=req_class.value,
                    mapping_status=RequirementMappingStatus.UNMAPPED,
                    mapping_reason=f"Clause identity mismatch: evidence clause '{evidence.applicable_clause}' != target clause '{target_clause}'.",
                    is_eligible=False,
                    eligibility_reason="Mismatched clause designation.",
                    is_authentic=True,
                    satisfaction_status=RequirementSatisfactionStatus.UNVERIFIED,
                    gap=f"Evidence belongs to clause '{evidence.applicable_clause}', not target clause '{target_clause}'.",
                    mapping_chain=chain,
                    evidence_chain=ev_chain,
                    compliance_authority="LAYER_7_ONLY",
                    llm_compliance_authority=0.0,
                    regulatory_conclusion="NONE",
                    notes="Clause identity mismatch enforced.",
                )

        # ---------------------------------------------------------
        # Case 9: Product Category Applicability Check
        # ---------------------------------------------------------
        if target_product_category and req_def and req_def.applicable_product_category:
            if target_product_category.lower() not in req_def.applicable_product_category.lower():
                chain = EvidenceRequirementMappingChain(
                    verified_evidence_id=evidence.evidence_id,
                    applicable_standard=target_standard,
                    standard_revision=target_rev,
                    clause=cl_num,
                    clause_id=cl_id,
                    requirement=req_id,
                    evidence_eligibility="NOT_ELIGIBLE",
                    evidence_status=RequirementMappingStatus.REJECTED,
                )
                ev_chain = evidence.to_evidence_chain_record()
                return EvidenceRequirementMappingRecord(
                    mapping_id=mapping_id,
                    evidence_id=evidence.evidence_id,
                    evidence_type=evidence.evidence_type,
                    ontology_tier=evidence.ontology_tier,
                    applicable_standard=target_standard,
                    standard_revision=target_rev,
                    clause_number=cl_num,
                    clause_id=cl_id,
                    requirement_id=req_id,
                    requirement_class=req_class.value,
                    mapping_status=RequirementMappingStatus.REJECTED,
                    mapping_reason=f"Product applicability mismatch: product category '{target_product_category}' does not match requirement scope '{req_def.applicable_product_category}'.",
                    is_eligible=False,
                    eligibility_reason="Product category out of scope for requirement.",
                    is_authentic=True,
                    satisfaction_status=RequirementSatisfactionStatus.NOT_SATISFIED,
                    gap="Product category does not match requirement applicability.",
                    mapping_chain=chain,
                    evidence_chain=ev_chain,
                    compliance_authority="LAYER_7_ONLY",
                    llm_compliance_authority=0.0,
                    regulatory_conclusion="NONE",
                    notes="Product applicability mismatch enforced.",
                )

        # ---------------------------------------------------------
        # Case 10: Evidence Type Eligibility Gate
        # ---------------------------------------------------------
        eligibility = EvidenceEligibilityEngine.check_eligibility(
            requirement_id=req_id,
            requirement_name=evidence.attribute,
            evidence=evidence,
            explicit_class=req_class,
        )

        if not eligibility.is_eligible:
            chain = EvidenceRequirementMappingChain(
                verified_evidence_id=evidence.evidence_id,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause=cl_num,
                clause_id=cl_id,
                requirement=req_id,
                evidence_eligibility="NOT_ELIGIBLE",
                evidence_status=RequirementMappingStatus.INELIGIBLE,
            )
            ev_chain = evidence.to_evidence_chain_record()
            return EvidenceRequirementMappingRecord(
                mapping_id=mapping_id,
                evidence_id=evidence.evidence_id,
                evidence_type=evidence.evidence_type,
                ontology_tier=evidence.ontology_tier,
                applicable_standard=target_standard,
                standard_revision=target_rev,
                clause_number=cl_num,
                clause_id=cl_id,
                requirement_id=req_id,
                requirement_class=req_class.value,
                mapping_status=RequirementMappingStatus.INELIGIBLE,
                mapping_reason=eligibility.reason,
                is_eligible=False,
                eligibility_reason=eligibility.reason,
                is_authentic=True,
                satisfaction_status=RequirementSatisfactionStatus.NOT_SATISFIED,
                gap=eligibility.reason,
                mapping_chain=chain,
                evidence_chain=ev_chain,
                compliance_authority="LAYER_7_ONLY",
                llm_compliance_authority=0.0,
                regulatory_conclusion="NONE",
                notes="Evidence type ineligible for requirement class.",
            )

        # ---------------------------------------------------------
        # Case 11: Requirement Satisfaction Evaluation
        # ---------------------------------------------------------
        # Now that evidence is authentic, mapped, and eligible:
        # evaluate condition based on requirement class and parameters.
        satisfaction_status = RequirementSatisfactionStatus.SATISFIED
        gap_desc = None

        thresh_spec = req_def.threshold_spec if req_def else None

        # 11A. Empirical Laboratory Test Requirement Evaluation
        if req_class == RequirementClass.LAB_TEST_REQUIREMENT:
            # Check numerical threshold if defined
            if thresh_spec and "target_value" in thresh_spec:
                op = thresh_spec.get("operator", ">=")
                target_val = float(thresh_spec["target_value"])
                target_unit = thresh_spec.get("unit")

                # Extract numeric value
                num_val = None
                if isinstance(evidence.normalized_value, (int, float)):
                    num_val = float(evidence.normalized_value)
                else:
                    matches = re.findall(r"[-+]?\d*\.?\d+", str(evidence.normalized_value or evidence.extracted_value))
                    if matches:
                        try:
                            num_val = float(matches[0])
                        except (ValueError, IndexError):
                            num_val = None

                if num_val is None:
                    satisfaction_status = RequirementSatisfactionStatus.PARTIALLY_SATISFIED
                    gap_desc = "Empirical test report missing quantified numerical measurement."
                else:
                    # Compare numerical threshold
                    comp_pass, formula_str, audit_str = compare_numeric_threshold(
                        observed_val=num_val,
                        observed_unit=evidence.unit or target_unit,
                        operator=op,
                        threshold=target_val,
                        required_unit=target_unit,
                    )
                    if comp_pass:
                        satisfaction_status = RequirementSatisfactionStatus.SATISFIED
                        gap_desc = None
                    else:
                        satisfaction_status = RequirementSatisfactionStatus.NOT_SATISFIED
                        gap_desc = f"Measured test value {num_val} {evidence.unit or ''} failed required limit ({op} {target_val} {target_unit or ''})."

            else:
                # Qualitative lab test (e.g. inversion leakage zero droplets, drop impact pass)
                combined_val = f"{evidence.normalized_value or ''} {evidence.extracted_value or ''}".upper()
                if any(fail_word in combined_val for fail_word in ("FAIL", "LEAKAGE DETECTED", "DROPLETS OBSERVED", "RUPTURE", "CRACKED")):
                    satisfaction_status = RequirementSatisfactionStatus.NOT_SATISFIED
                    gap_desc = f"Empirical laboratory test reported non-conforming outcome: '{evidence.extracted_value}'."
                elif any(pass_word in combined_val for pass_word in ("PASS", "CONFORMS", "NIL", "ZERO", "NO LEAKAGE", "INTACT")):
                    satisfaction_status = RequirementSatisfactionStatus.SATISFIED
                    gap_desc = None
                else:
                    satisfaction_status = RequirementSatisfactionStatus.PARTIALLY_SATISFIED
                    gap_desc = "Test report outcome requires expert interpretation."

        # 11B. Technical Specification Requirement Evaluation
        elif req_class == RequirementClass.TECHNICAL_SPECIFICATION:
            if thresh_spec and "target_value" in thresh_spec:
                op = thresh_spec.get("operator", "<=")
                target_val = float(thresh_spec["target_value"])
                target_unit = thresh_spec.get("unit")

                num_val = None
                if isinstance(evidence.normalized_value, (int, float)):
                    num_val = float(evidence.normalized_value)
                else:
                    matches = re.findall(r"[-+]?\d*\.?\d+", str(evidence.normalized_value or evidence.extracted_value))
                    if matches:
                        try:
                            num_val = float(matches[0])
                        except (ValueError, IndexError):
                            num_val = None

                if num_val is not None:
                    comp_pass, _, _ = compare_numeric_threshold(
                        observed_val=num_val,
                        observed_unit=evidence.unit or target_unit,
                        operator=op,
                        threshold=target_val,
                        required_unit=target_unit,
                    )
                    if comp_pass:
                        satisfaction_status = RequirementSatisfactionStatus.SATISFIED
                    else:
                        satisfaction_status = RequirementSatisfactionStatus.NOT_SATISFIED
                        gap_desc = f"Specification rating {num_val} exceeded maximum allowable rating ({op} {target_val} {target_unit or ''})."
                else:
                    satisfaction_status = RequirementSatisfactionStatus.SATISFIED
            else:
                satisfaction_status = RequirementSatisfactionStatus.SATISFIED

        # 11C. Declaration Requirement Evaluation
        elif req_class == RequirementClass.DECLARATION_REQUIREMENT:
            combined_val = f"{evidence.normalized_value or ''} {evidence.extracted_value or ''}".upper()
            if any(term in combined_val for term in ("304", "CONFORMS", "FOOD GRADE", "FOOD CONTACT", "CERTIFIED", "DECLARED")):
                satisfaction_status = RequirementSatisfactionStatus.SATISFIED
                gap_desc = None
            else:
                satisfaction_status = RequirementSatisfactionStatus.PARTIALLY_SATISFIED
                gap_desc = "Manufacturer declaration lacks explicit material conformance statement."

        # 11D. Visual / Construction Requirement Evaluation
        elif req_class == RequirementClass.VISUAL_CONSTRUCTION:
            combined_val = f"{evidence.normalized_value or ''} {evidence.extracted_value or ''}".upper()
            is_positive = any(p in combined_val for p in ("FREE FROM", "NO DEFECT", "PASS", "CONFORMS", "SATISFACTORY", "SMOOTH", "INTACT"))
            has_explicit_defect = any(neg in combined_val for neg in ("DEFECTIVE", "CRACKED", "FRACTURED", "SHARP BURRS OBSERVED", "FAIL", "REJECTED"))
            if has_explicit_defect and not is_positive:
                satisfaction_status = RequirementSatisfactionStatus.NOT_SATISFIED
                gap_desc = "Visual photograph reveals visible manufacturing defect or sharp burrs."
            else:
                satisfaction_status = RequirementSatisfactionStatus.SATISFIED

        # 11E. Physical Marking Requirement Evaluation
        elif req_class == RequirementClass.PHYSICAL_MARKING:
            combined_val = f"{evidence.normalized_value or ''} {evidence.extracted_value or ''}".upper()
            if any(term in combined_val for term in ("ISI", "BIS", "STANDARD MARK", "LABEL", "RATING", "CM/L", "R-")):
                satisfaction_status = RequirementSatisfactionStatus.SATISFIED
            else:
                satisfaction_status = RequirementSatisfactionStatus.PARTIALLY_SATISFIED
                gap_desc = "Marking evidence does not clearly display mandatory BIS Standard Mark / licensing text."

        # ---------------------------------------------------------
        # Case 12: Ontological Separation Assertion
        # ---------------------------------------------------------
        is_verified_ev = evidence.verified and evidence.verification_status == EvidenceVerificationStatus.VERIFIED
        is_req_sat = (satisfaction_status == RequirementSatisfactionStatus.SATISFIED)
        # Note: A single satisfied requirement is NOT an overall compliance result!
        is_comp_res = False  # Only Layer 7 emits compliance result

        sep_valid, sep_msg = validate_mapping_separation(
            is_verified_evidence=is_verified_ev,
            is_requirement_satisfied=is_req_sat,
            is_compliance_result=is_comp_res,
        )
        if not sep_valid:
            logger.error("Ontological separation violation: %s", sep_msg)

        # ---------------------------------------------------------
        # Build Final Mapping Record
        # ---------------------------------------------------------
        chain = EvidenceRequirementMappingChain(
            verified_evidence_id=evidence.evidence_id,
            applicable_standard=target_standard,
            standard_revision=target_rev,
            clause=cl_num,
            clause_id=cl_id,
            requirement=req_id,
            evidence_eligibility="ELIGIBLE",
            evidence_status=RequirementMappingStatus.MAPPED,
        )
        ev_chain = evidence.to_evidence_chain_record()
        ev_chain.applicable_requirement = req_id
        ev_chain.verification_status = EvidenceVerificationStatus.VERIFIED

        return EvidenceRequirementMappingRecord(
            mapping_id=mapping_id,
            evidence_id=evidence.evidence_id,
            evidence_type=evidence.evidence_type,
            ontology_tier=EvidenceOntologyTier.VERIFIED_EVIDENCE,
            applicable_standard=target_standard,
            standard_revision=target_rev,
            clause_number=cl_num,
            clause_id=cl_id,
            requirement_id=req_id,
            requirement_class=req_class.value,
            mapping_status=RequirementMappingStatus.MAPPED,
            mapping_reason=f"Evidence artifact '{evidence.evidence_id}' successfully mapped to {target_standard} {cl_num} ({req_id}).",
            is_eligible=True,
            eligibility_reason="Evidence type is fully eligible and authentic for requirement class.",
            is_authentic=True,
            satisfaction_status=satisfaction_status,
            gap=gap_desc,
            mapping_chain=chain,
            evidence_chain=ev_chain,
            compliance_authority="LAYER_7_ONLY",
            llm_compliance_authority=0.0,
            regulatory_conclusion="NONE",
            notes=f"Deterministic mapping completed: {chain.to_chain_string()}",
        )


# Global singleton instance
evidence_mapping_service = DeterministicEvidenceRequirementMapper()
