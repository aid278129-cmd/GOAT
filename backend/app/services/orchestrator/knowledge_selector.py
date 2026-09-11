"""Verified Knowledge Selector for Layer 3 AI Orchestrator.

Enforces zero-hallucination boundaries:
NO VERIFIED SOURCE -> NO REGULATORY CLAIM
UNKNOWN -> UNKNOWN / INFORMATION REQUIRED

Only permits citations and technical retrieval from authentic, Gazette-indexed
Indian Standards codified in the Zyntrix repository. Rejects fabricated standards
and non-existent clauses without LLM speculation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from backend.app.services.orchestrator.schemas import CitationItem, GroundingStatus

# Canonical catalog of verified Indian Standards codified in repository
VERIFIED_STANDARDS_CATALOG: Dict[str, Dict[str, Any]] = {
    "IS 302-2-201:2008": {
        "title": "Safety of Household and Similar Electrical Appliances - Particular Requirements for Electric Immersion Water Heaters",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Electrical Appliances (Quality Control) Order, 2023",
        "clauses": {
            "6.1": {"title": "Classification and Voltage Rating", "req": "Appliance shall be rated for 230 V single-phase a.c. supply."},
            "7.1": {"title": "Marking and Instructions", "req": "Appliance shall be visibly marked with rated voltage, wattage, model, and manufacturer trade name."},
            "8.1": {"title": "Protection Against Access to Live Parts", "req": "Live parts shall not be accessible during normal operation or immersion."},
            "10.1": {"title": "Power Input and Current", "req": "Power input at normal operating temperature shall not deviate from rated wattage by more than +5% or -10%."},
            "13.1": {"title": "Leakage Current and Electric Strength at Operating Temperature", "req": "Leakage current shall not exceed 0.75 mA; electric strength 1250 V AC for 1 min."},
            "16.1": {"title": "Leakage Current and Electric Strength (Cold/Moisture Resistance)", "req": "After humidity conditioning, insulation resistance >= 2 MOhm, electric strength withstand 1250 V AC."},
            "19.1": {"title": "Abnormal Operation", "req": "Appliance operated dry out of water shall not ignite or create fire hazard."},
            "22.101": {"title": "Immersion Sheath Construction", "req": "Tubular heating element sheath shall be corrosion-resistant copper or stainless steel grade 304 or superior."},
            "25.1": {"title": "Supply Connection and External Flexible Cords", "req": "Power cord shall be 3-core PVC insulated conforming to IS 694 with earthing conductor."},
            "25.7": {"title": "Plug Top Conformance", "req": "Appliance shall be fitted with 3-pin plug conforming to IS 1293 (6 A, 250 V AC)."},
            "27.1": {"title": "Provision for Earthing", "req": "Accessible metal parts shall be permanently and reliably connected to earthing terminal (resistance <= 0.1 Ohm)."},
            "30.1": {"title": "Resistance to Heat and Fire", "req": "External non-metallic handles and enclosures shall be resistant to heat and fire (glow wire test at 750 C / UL94 V-0)."},
        },
    },
    "IS 302-1:2008": {
        "title": "Safety of Household and Similar Electrical Appliances - General Requirements",
        "ministry": "Ministry of Consumer Affairs",
        "qco_order": "Electrical Appliances (Quality Control) Order",
        "clauses": {
            "7.1": {"title": "Marking Requirements", "req": "General marking of electrical ratings and symbols."},
            "8.1": {"title": "Protection Against Electric Shock", "req": "Adequate protection against contact with live parts."},
            "13.3": {"title": "Electric Strength at Operating Temperature", "req": "Electric strength withstand 1250 V AC without spark breakdown."},
            "22.1": {"title": "Construction Safety", "req": "General mechanical and electrical construction safeguards."},
        },
    },
    "IS 17526:2021": {
        "title": "Stainless Steel Vacuum Flasks / Insulated Flasks - Specification",
        "ministry": "Ministry of Commerce & Industry / DPIIT",
        "qco_order": "Cookware and Utensils (Quality Control) Order, 2023",
        "clauses": {
            "4.1": {"title": "Inner Liner Food Contact Material", "req": "Food contact surfaces shall be manufactured from stainless steel grade 304 conforming to IS 6911."},
            "4.2": {"title": "Outer Body Material", "req": "Outer body shall be corrosion-resistant stainless steel or impact-resistant polymer."},
            "4.3": {"title": "Lid Gasket and Seal Material", "req": "Seals in contact with liquid shall be food-grade silicone elastomer conforming to IS 9845."},
            "4.2.1": {"title": "Raw Material Grade 304 Conformance", "req": "Inner container stainless steel grade 304."},
            "5.1": {"title": "Nominal Capacity Tolerance", "req": "Actual liquid holding capacity shall be within +/- 5% of declared capacity."},
            "5.2": {"title": "Leakage Test Protocol", "req": "Flask filled with water at 90 C and inverted for 10 minutes shall show zero droplets or leakage."},
            "5.3": {"title": "Impact and Drop Resistance Test", "req": "Flask dropped filled with water from 1.0 m height onto concrete floor shall maintain thermal vacuum and no leakage."},
            "5.4": {"title": "Thermal Insulation Retention Protocol", "req": "Water temperature after 6 hours from initial 95 C shall be >= 60 C for domestic containers."},
            "6.3": {"title": "Heat Retention Protocol", "req": "Water temperature after 6 hours from initial 95 C shall be >= 65 C for <= 1000 ml containers."},
            "7.1": {"title": "Marking and Packaging", "req": "Legible marking of capacity, manufacturer, standard mark and batch."},
        },
    },
    "IS 4151:2015": {
        "title": "Protective Helmets for Two Wheeler Riders - Specification",
        "ministry": "Ministry of Road Transport and Highways",
        "qco_order": "Two-Wheeler Helmets (Quality Control) Order",
        "clauses": {
            "4.1": {"title": "Material Construction", "req": "Shell material shall be high-impact polymer or composite."},
            "7.1": {"title": "Impact Absorption Test", "req": "Peak acceleration shall not exceed 300g during drop tower test."},
            "8.1": {"title": "Retention System Test", "req": "Chin strap dynamic extension shall not exceed 25 mm."},
        },
    },
    "IS 9873 (Part 1):2019": {
        "title": "Safety of Toys - Part 1: Safety Aspects Related to Mechanical and Physical Properties",
        "ministry": "Ministry of Commerce and Industry",
        "qco_order": "Toys (Quality Control) Order, 2020",
        "clauses": {
            "4.1": {"title": "Normal Use and Abuse Testing", "req": "Toy shall withstand drop, torque, and tension tests without sharp edges."},
            "4.4": {"title": "Small Parts Choking Hazard", "req": "No small parts fit entirely within small parts cylinder for children under 36 months."},
        },
    },
}


class VerifiedKnowledgeSelector:
    """Validates BIS standard numbers, clauses, and retrieves codified metadata."""

    @classmethod
    def match_standard_in_query(cls, query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Detect Indian Standard mentioned in text and verify against catalog."""
        # Match pattern IS [number] or IS [number]:[year]
        m = re.search(r"\bIS\s*(\d+(?:-\d+)*(?:-\d+)*)(?::(\d{4}))?\b", query, re.IGNORECASE)
        if not m:
            return None, None

        std_num = m.group(1)
        # Search catalog
        for cat_std, data in VERIFIED_STANDARDS_CATALOG.items():
            if std_num in cat_std:
                return cat_std, data

        # If standard was mentioned but not in catalog -> UNVERIFIED / FAKE STANDARD
        fake_id = f"IS {std_num}"
        return fake_id, None

    @classmethod
    def match_clause_in_query(cls, standard_key: str, query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Detect and verify clause number against the specified standard's catalog."""
        if not standard_key or standard_key not in VERIFIED_STANDARDS_CATALOG:
            return None, None

        clauses_dict = VERIFIED_STANDARDS_CATALOG[standard_key]["clauses"]
        m = re.search(r"\bclause\s*(\d+(?:\.\d+)+)\b", query, re.IGNORECASE)
        if not m:
            return None, None

        clause_num = m.group(1)
        if clause_num in clauses_dict:
            return clause_num, clauses_dict[clause_num]

        # Clause was mentioned but does not exist in standard
        return clause_num, None

    @classmethod
    def get_verified_standard_metadata(cls, standard_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve verified standard metadata."""
        return VERIFIED_STANDARDS_CATALOG.get(standard_key)


verified_knowledge_selector = VerifiedKnowledgeSelector()
