"""Demonstration fixture and reset state for the Golden SIH Demo Case.

Product: Domestic Stainless Steel Vacuum Flask 1000ml
Category: Drinkware & Food Contact Containers
Standard: IS 17526:2021
QCO: DPIIT Domestic Water Bottles Order 2023

Demonstrates the full evidence-first compliance evaluation workflow:
1. Initial Product text entry -> ZERO requirements SATISFIED.
2. Verified Lab report -> SATISFIED with traceable chain.
3. Missing photo -> MISSING_EVIDENCE + UPLOAD_EVIDENCE.
4. Physical test needed -> MISSING_EVIDENCE + REQUIRES_TESTING.
5. Contradictory evidence -> CONFLICTING_EVIDENCE + EXPERT_REVIEW.
"""
from typing import Dict, Any, List

GOLDEN_DEMO_PRODUCT = {
    "product_name": "ThermoSteel Domestic Stainless Steel Vacuum Flask 1000ml",
    "category": "Drinkware & Food Contact Containers",
    "description": "We manufacture a 1 litre stainless steel vacuum flask for domestic drinking water.",
    "authoritative_mode": False,
}

# Controlled demonstration evidence snippets
CONTROLLED_DEMO_EVIDENCE: List[Dict[str, Any]] = [
    {
        "id": "demo-ev-leak",
        "title": "NABL Accredited Lab Report (Leakage Inversion Test)",
        "snippet": "National Test House Accredited Laboratory Report NTH/2026/044: Product subjected to Clause 5.2 leakage test. Flask filled to nominal capacity and inverted for 10 minutes: zero leakage or moisture weeping observed. Clause 5.2 passed.",
        "evidence_type": "TEST_REPORT",
        "authority": "LAB_REPORT",
        "page": 2,
        "target_requirement": "REQ-PERF-LEAK",
        "expected_result": "SATISFIED",
    },
    {
        "id": "demo-ev-mat",
        "title": "Mill Test Certificate (IS 6911 Grade 304)",
        "snippet": "SAIL Raw Material Chemical Test Certificate MTC-2026-304: Material grade certified as Grade 304 austenitic stainless steel conforming to IS 6911.",
        "evidence_type": "MATERIAL_CERTIFICATE",
        "authority": "MILL_TEST_CERTIFICATE",
        "page": 1,
        "target_requirement": "REQ-MAT-304",
        "expected_result": "SATISFIED",
    },
    {
        "id": "demo-ev-conflict-a",
        "title": "Lab Volumetric Report (1000ml)",
        "snippet": "Laboratory Report NTH/2026/044: Measured nominal capacity is 1000 ml.",
        "evidence_type": "TEST_REPORT",
        "authority": "LAB_REPORT",
        "page": 3,
        "target_requirement": "capacity_ml",
        "expected_result": "CONSISTENT_WITH_CLAIM",
    },
    {
        "id": "demo-ev-conflict-b",
        "title": "Competitor Catalog / Conflicting Spec (750ml)",
        "snippet": "Datasheet DS-750: Product capacity declared as 750 ml.",
        "evidence_type": "PRODUCT_SPECIFICATION",
        "authority": "MANUFACTURER_DECLARATION",
        "page": 1,
        "target_requirement": "capacity_ml",
        "expected_result": "CONFLICTING_EVIDENCE",
    },
]


GOLDEN_DEMO_INITIAL_EVIDENCE = {
    "snippet": "Laboratory test report NTH/2026/044: Product subjected to Clause 5.4 heat retention. After 6 hours water temp was 64.5 deg C. Clause 5.2 inverted 10 mins: zero leakage observed.",
    "evidence_type": "TEST_REPORT",
    "authority": "LAB_REPORT",
    "page": 2,
}


def get_golden_demo_config() -> Dict[str, Any]:
    """Return the complete metadata configuration for the SIH Golden Demo Case."""
    return {
        "case_id": "GOLDEN-SIH-2026-DEMO",
        "title": "Golden SIH Demonstration Case: Evidence-First Vacuum Flask",
        "standard_number": "IS 17526:2021",
        "qco_regulation": "DPIIT Domestic Water Bottles (Quality Control) Order, 2023",
        "sample_protocol": "8-Flask Testing Protocol (BIS Product Manual PM/IS 17526/1)",
        "product_data": GOLDEN_DEMO_PRODUCT,
        "initial_evidence": GOLDEN_DEMO_INITIAL_EVIDENCE,
        "controlled_evidence": CONTROLLED_DEMO_EVIDENCE,
        "mode": "DEVELOPMENT_MODE (Interactive Demo with Evidence-First Gating)",
    }
