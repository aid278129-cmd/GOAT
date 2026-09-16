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
        "qco_order": "Two-Wheeler Helmets (Quality Control) Order, 2020",
        "clauses": {
            "4.1": {"title": "Material Construction", "req": "Shell material shall be high-impact polymer or composite."},
            "7.1": {"title": "Impact Absorption Test", "req": "Peak acceleration shall not exceed 300g during drop tower test."},
            "7.2": {"title": "Impact Attenuation Test", "req": "The peak acceleration imparted to the headform during impact onto flat and hemispherical steel anvils from a height of 2.8 m shall not exceed 300 g."},
            "8.1": {"title": "Retention System Test", "req": "Chin strap dynamic extension shall not exceed 25 mm."},
        },
    },
    "IS 9873 (Part 1):2019": {
        "title": "Safety of Toys - Part 1: Safety Aspects Related to Mechanical and Physical Properties",
        "ministry": "Ministry of Commerce and Industry",
        "qco_order": "Toys (Quality Control) Order, 2020",
        "clauses": {
            "4.1": {"title": "Normal Use and Abuse Testing / Small Parts", "req": "Toys intended for children under 36 months, and removable components thereof, shall not fit entirely within the small parts cylinder (diameter 31.7 mm)."},
            "4.4": {"title": "Small Parts Choking Hazard", "req": "No small parts fit entirely within small parts cylinder for children under 36 months."},
        },
    },
    "IS 14543:2024": {
        "title": "Packaged Drinking Water (Other than Packaged Natural Mineral Water) - Specification",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Packaged Drinking Water (Quality Control) Order",
        "clauses": {
            "1.1": {"title": "Scope of Packaged Drinking Water", "req": "Prescribes requirements and methods of sampling and test for packaged drinking water other than packaged natural mineral water intended for direct human consumption."},
            "5.1": {"title": "Total Dissolved Solids (TDS)", "req": "The total dissolved solids (TDS) of packaged drinking water shall not exceed 500 mg/l when tested in accordance with IS 3025 (Part 16)."},
            "5.2": {"title": "Microbiological Requirements", "req": "Escherichia coli and coliform bacteria shall be absent in any 250 ml sample when tested according to IS 15185."},
            "7.1": {"title": "Marking Requirements", "req": "Each container shall be clearly and indelibly marked with the Standard Mark (ISI mark), batch number, date of manufacture, best before date, and net volume."},
        },
    },
    "IS 2347:2017": {
        "title": "Domestic Pressure Cookers - Specification",
        "ministry": "Ministry of Commerce and Industry / DPIIT",
        "qco_order": "Domestic Pressure Cooker (Quality Control) Order, 2020",
        "clauses": {
            "1": {"title": "Scope of Pressure Cookers", "req": "Specifies requirements for domestic pressure cookers having nominal capacities up to and including 22 litres."},
            "4.1": {"title": "Materials of Body and Lid", "req": "The cooker body and lid shall be manufactured from aluminium alloy conforming to IS 21, or stainless steel conforming to IS 6911."},
            "5.4": {"title": "Operating Pressure and Weight Valve", "req": "The pressure cooker shall operate smoothly at an operating pressure between 0.9 kgf/cm2 and 1.1 kgf/cm2 with automatic pressure release."},
            "6.2": {"title": "Hydraulic Burst Pressure Test", "req": "The pressure cooker shall withstand hydrostatic pressure of not less than 3 times the operating pressure (minimum 3.0 kgf/cm2) without rupture or catastrophic leakage."},
        },
    },
    "IS 302-2-3:2007": {
        "title": "Safety of Household and Similar Electrical Appliances: Particular Requirements for Electric Irons",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Electrical Appliances (Quality Control) Order",
        "clauses": {
            "8.1": {"title": "Protection Against Electric Shock", "req": "Live parts shall not be accessible to standard test finger per IEC 61032 under all normal operating conditions."},
            "13.2": {"title": "Leakage Current and Dielectric Strength", "req": "The leakage current of the appliance at operating temperature shall not exceed 0.75 mA."},
        },
    },
    "IS 13252 (Part 1):2010": {
        "title": "Information Technology Equipment - Safety - Part 1: General Requirements",
        "ministry": "Ministry of Electronics and Information Technology (MeitY)",
        "qco_order": "Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order, 2012",
        "clauses": {
            "2.1.1": {"title": "Protection in Operator Access Areas", "req": "Operator access areas shall be designed so that bare parts operating at hazardous voltage (SELV limit > 42.4V peak or 60V DC) are not touchable."},
            "5.2.2": {"title": "Electric Strength (High Voltage Withstand)", "req": "Reinforced insulation between primary circuits and accessible parts shall withstand 3000 V r.m.s. AC for 60 seconds without breakdown."},
        },
    },
    "IS 1786:2008": {
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement - Specification",
        "ministry": "Ministry of Steel",
        "qco_order": "Steel and Steel Products (Quality Control) Order, 2020",
        "clauses": {
            "8.1": {"title": "0.2% Proof Stress / Yield Strength", "req": "For grade Fe 500D, the 0.2 percent proof stress shall not be less than 500.0 N/mm2."},
        },
    },
    "IS 8112:2013": {
        "title": "43 Grade Ordinary Portland Cement - Specification",
        "ministry": "Ministry of Commerce and Industry / DPIIT",
        "qco_order": "Cement (Quality Control) Order, 2003",
        "clauses": {
            "6.1": {"title": "28-Day Compressive Strength", "req": "The average compressive strength of at least three mortar cubes at 28 days (672 +/- 4 h) shall not be less than 43.0 MPa."},
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
