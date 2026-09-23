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

# Canonical catalog of verified BIS Certification Schemes
VERIFIED_SCHEMES_CATALOG: Dict[str, Dict[str, Any]] = {
    "SCHEME_I": {
        "scheme_code": "SCHEME_I",
        "scheme_name": "Scheme I — Product Certification Scheme (Standard Mark / ISI)",
        "governing_regulation": "BIS (Conformity Assessment) Regulations, 2018, Schedule II, Scheme I",
        "statutory_act": "BIS Act 2016, Section 13",
        "mark": "ISI Mark (Standard Mark)",
        "description": "Scheme I enables manufacturers to use the ISI Standard Mark. It requires preliminary factory inspection, independent sampling, testing against Indian Standards, and continuous factory surveillance audit.",
        "key_features": "Preliminary factory audit required; independent testing in BIS/recognized labs; continuous surveillance audits; applicable to mandatory safety and industrial products (helmets, water heaters, steel, cement).",
        "applicable_categories": ["helmet", "helmets", "heater", "water heater", "immersion heater", "electrical appliance", "appliances", "steel", "tmt bar", "cement", "toy", "toys", "cylinder", "cables", "conductor"],
        "applicable_standards": ["IS 4151:2015", "IS 302-2-201:2008", "IS 1786:2008", "IS 8112:2013", "IS 9873 (Part 1):2019"],
        "required_documents": [
            "Factory registration certificate / Business constitution proof",
            "Manufacturing machinery list and plant layout",
            "In-house testing equipment list with valid calibration certificates",
            "Manufacturing process flowchart with quality inspection checkpoints",
            "Competent testing personnel details and appointment records",
            "Consent / authorization for preliminary factory inspection",
            "Agreement with Authorized Indian Representative (AIR) (for foreign manufacturers under FMCS)",
        ],
        "major_testing_and_application_steps": [
            "Step 1: Standard Identification — Identify applicable Indian Standard and conformity requirements.",
            "Step 2: Online e-Application — Register and submit application with factory documentation via Manakonline portal.",
            "Step 3: Preliminary Factory Inspection — BIS technical auditor inspects plant, quality controls, and in-house testing facility.",
            "Step 4: Sample Drawing & Lab Testing — Officer draws representative samples for independent testing in BIS/recognized labs.",
            "Step 5: Scrutiny & Grant of Licence (GoL) — Scrutiny of test report and factory audit; grant of CML number for ISI mark.",
            "Step 6: Post-Grant Surveillance — Periodic unannounced factory audits and market sample surveillance.",
        ],
        "official_guideline_url": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/product_certification",
    },
    "SCHEME_II": {
        "scheme_code": "SCHEME_II_CRS",
        "scheme_name": "Scheme II — Compulsory Registration Scheme (CRS)",
        "governing_regulation": "BIS (Conformity Assessment) Regulations, 2018, Schedule II, Scheme II",
        "statutory_act": "BIS Act 2016, Section 13 & MeitY/MNRE Quality Control Orders",
        "mark": "Standard Mark with Registration Number (R-XXXXXXXX)",
        "description": "Compulsory Registration Scheme for electronics and IT goods notified under MeitY and MNRE Quality Control Orders. Manufacturers register products based on self-declaration of conformity and valid test reports from BIS-recognized laboratories without preliminary factory inspection.",
        "key_features": "Self-declaration of conformity; testing exclusively in BIS-recognized laboratories; no preliminary factory audit; product marked with unique R-number.",
        "applicable_categories": ["laptop", "laptops", "notebook", "tablet", "tablets", "mobile phone", "mobile phones", "smart watch", "power adapter", "adapter", "led light", "led lamps", "solar inverter", "inverter", "it equipment", "printer", "printers", "scanner", "server", "electronic"],
        "applicable_standards": ["IS 13252 (Part 1):2010", "IS 16046 (Part 1/2):2018", "IS 15885 (Part 2/Sec 13):2012"],
        "required_documents": [
            "Valid test report from a BIS-recognized laboratory (issued within 90 days of application)",
            "Brand owner trademark registration certificate / Brand authorization letter",
            "Undertaking for compliance and affidavit per official format",
            "Business license / company incorporation certificate of manufacturing unit",
            "Authorized Indian Representative (AIR) appointment letter (for overseas applicants)",
        ],
        "major_testing_and_application_steps": [
            "Step 1: Product Sample Testing — Submit product samples to a BIS-recognized testing laboratory in India.",
            "Step 2: Obtain Valid Test Report — Lab issues formal test report (valid for 90 days for application filing).",
            "Step 3: Online CRS Portal Filing — Register and file application with test report and affidavit on crsbis.in.",
            "Step 4: Document Scrutiny — BIS officers examine report integrity and brand authorizations (no factory inspection required).",
            "Step 5: Grant of Registration — Issuance of unique Registration number (R-XXXXXXXX).",
            "Step 6: Market Surveillance — Random market sample purchase and verification testing.",
        ],
        "official_guideline_url": "https://www.crsbis.in/BIS/",
    },
    "HALLMARKING": {
        "scheme_code": "HALLMARKING_SCHEME",
        "scheme_name": "BIS Hallmarking Scheme for Precious Metals",
        "governing_regulation": "Hallmarking of Gold and Silver Artefacts Order, 2021",
        "statutory_act": "BIS Act 2016, Section 14",
        "mark": "BIS logo, purity/fineness mark, and 6-digit alphanumeric HUID",
        "description": "Statutory hallmarking certifying the fineness and purity of gold and silver jewelry. Managed through BIS recognized Assaying & Hallmarking Centres (AHC) using digital HUID (Hallmark Unique Identification).",
        "key_features": "Assay testing (XRF / Fire Assay); 3 mandatory marks (BIS logo, fineness, 6-digit HUID); verification through BIS CARE app.",
        "applicable_categories": ["gold", "silver", "jewellery", "jewelry", "artefacts", "ornaments", "bullion"],
        "applicable_standards": ["IS 1417 (Gold)", "IS 2112 (Silver)"],
        "required_documents": [
            "Premises proof / GST registration certificate of jewellery outlet",
            "Proof of firm constitution / partnership deed / certificate of incorporation",
            "Authorized signatory identity and address proof",
        ],
        "major_testing_and_application_steps": [
            "Step 1: Jeweller Online Registration — Apply on Manakonline for instant registration certificate.",
            "Step 2: Submission to AHC — Submit precious metal items to a BIS-recognized Assaying and Hallmarking Centre.",
            "Step 3: Assay Testing — Non-destructive XRF screening and cupellation/fire assay testing.",
            "Step 4: Laser HUID Marking — Laser etching of BIS logo, purity grade, and 6-digit alphanumeric HUID.",
            "Step 5: Consumer Verification — Verification of HUID authenticity via the BIS CARE mobile app.",
        ],
        "official_guideline_url": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/hallmarking",
    },
}

# Canonical catalog of verified BIS Services
VERIFIED_SERVICES_CATALOG: Dict[str, Dict[str, Any]] = {
    "PRODUCT_CERTIFICATION": {
        "service_name": "Product Certification (Grant of License under Scheme I)",
        "service_type": "PRODUCT_CERTIFICATION",
        "description": "Authoritative grant of license to manufacture and mark products with the standard ISI mark under Indian Standards.",
        "step_by_step_procedure": "Step 1: Identify applicable IS standard.\nStep 2: Submit e-application via Manakonline portal with fee.\nStep 3: Factory verification by BIS officer.\nStep 4: Independent sample testing.\nStep 5: Issue of License certificate upon compliance.",
        "portal_url": "https://www.manakonline.in",
        "statutory_source_ref": "BIS Act 2016, Section 13",
    },
    "COMPULSORY_REGISTRATION": {
        "service_name": "Compulsory Registration (CRS) for Electronic and Solar Products",
        "service_type": "PRODUCT_CERTIFICATION",
        "description": "Simplified self-declaration registration process for electronics and solar equipment under MeitY / MNRE CRO schedules.",
        "step_by_step_procedure": "Step 1: Submit product sample to a BIS recognized testing laboratory.\nStep 2: Obtain valid test report within 90 days.\nStep 3: Submit online CRS application with Test Report and Affidavit.\nStep 4: Scrutiny by BIS Officers.\nStep 5: Registration granted with R-Number.",
        "portal_url": "https://www.crsbis.in",
        "statutory_source_ref": "Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order",
    },
    "JEWELLER_REGISTRATION": {
        "service_name": "Jeweller Registration for Hallmarking",
        "service_type": "HALLMARKING",
        "description": "Mandatory online registration for jewelers selling hallmarked gold and silver articles to consumers.",
        "step_by_step_procedure": "Step 1: Apply online through Manakonline portal.\nStep 2: Automatic issuance of registration certificate upon successful fee submission.\nStep 3: Deliver jewelry to recognized AHC for laser hallmarking.",
        "portal_url": "https://www.manakonline.in/MANAK/hallmarkingJewellerRegistration",
        "statutory_source_ref": "BIS Hallmarking Regulations 2018",
    },
    "CONSUMER_GRIEVANCE": {
        "service_name": "Consumer Grievance Redressal & BIS CARE Verification",
        "service_type": "CONSUMER_AFFAIRS",
        "description": "Public consumer service to verify genuine ISI marks, check jeweler HUID authenticity, and register formal complaints regarding substandard products.",
        "step_by_step_procedure": "Step 1: Download official BIS CARE Mobile App or visit BIS portal.\nStep 2: Enter 6-digit alphanumeric HUID or License/Registration R-number.\nStep 3: View verified manufacturer/jeweler details and registration validity.\nStep 4: Lodge complaint with photo evidence if product or mark is counterfeit.",
        "portal_url": "https://www.bis.gov.in/consumer-affairs/",
        "statutory_source_ref": "Consumer Protection Act 2019 & BIS Act 2016",
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

    @classmethod
    def match_scheme_in_query(cls, query: str) -> Optional[Dict[str, Any]]:
        """Detect and match BIS certification scheme in query."""
        q_lower = query.lower()
        if "scheme i" in q_lower or "scheme 1" in q_lower or "isi mark" in q_lower or "product certification scheme" in q_lower:
            return VERIFIED_SCHEMES_CATALOG["SCHEME_I"]
        if "scheme ii" in q_lower or "scheme 2" in q_lower or "crs" in q_lower or "compulsory registration scheme" in q_lower:
            return VERIFIED_SCHEMES_CATALOG["SCHEME_II"]
        if "hallmark" in q_lower or "huid" in q_lower:
            return VERIFIED_SCHEMES_CATALOG["HALLMARKING"]
        if "scheme" in q_lower:
            # Return general schemes overview dict
            return {
                "general_schemes": True,
                "schemes": VERIFIED_SCHEMES_CATALOG,
            }
        return None

    @classmethod
    def match_service_in_query(cls, query: str) -> Optional[Dict[str, Any]]:
        """Detect and match BIS service in query."""
        q_lower = query.lower()
        if "hallmark" in q_lower or "jewel" in q_lower:
            return VERIFIED_SERVICES_CATALOG["JEWELLER_REGISTRATION"]
        if "crs" in q_lower or "electronic" in q_lower or "solar" in q_lower:
            return VERIFIED_SERVICES_CATALOG["COMPULSORY_REGISTRATION"]
        if "care" in q_lower or "grievance" in q_lower or "complaint" in q_lower:
            return VERIFIED_SERVICES_CATALOG["CONSUMER_GRIEVANCE"]
        if "service" in q_lower or "procedure" in q_lower or "how does" in q_lower or "process" in q_lower:
            return {
                "general_services": True,
                "services": VERIFIED_SERVICES_CATALOG,
            }
        return None

    @classmethod
    def check_unverified_scheme(cls, query: str) -> Optional[str]:
        """Detect if an unverified / invalid scheme number is requested."""
        q_lower = query.lower()
        matches = re.findall(r"\bscheme\s+([0-9]+|[ivxlcdm]+)\b", q_lower)
        valid_schemes = {"i", "1", "ii", "2", "iv", "4"}
        for sch in matches:
            if sch not in valid_schemes:
                return f"Scheme {sch.upper()}"
        return None

    @classmethod
    def check_obsolete_procedure(cls, query: str) -> Optional[Dict[str, Any]]:
        """Detect if the query refers to obsolete, superseded, or discontinued procedures."""
        q_lower = query.lower()
        obsolete_indicators = [
            "offline paper", "physical application", "manual submission", "submit by post",
            "paper form", "branch office submission", "offline submission", "offline application",
            "paper application", "manual paper", "dgs&d", "superseded 1987",
        ]
        if any(ind in q_lower for ind in obsolete_indicators):
            return {
                "is_obsolete": True,
                "obsolete_practice": "Manual offline physical paper application",
                "governing_regulation": "BIS (Conformity Assessment) Regulations, 2018, Regulation 3(1)",
                "modern_portals": "Manakonline (manakonline.in) for Scheme I / crsbis.in for Scheme II (CRS)",
                "explanation": (
                    "Manual offline paper applications have been completely discontinued by the Bureau of Indian Standards. "
                    "Under the BIS (Conformity Assessment) Regulations 2018, all applications for Grant of Licence (Scheme I) "
                    "and Compulsory Registration (Scheme II) must be submitted electronically through official portals "
                    "(Manakonline for Scheme I and crsbis.in for Scheme II). Physical paper applications are no longer accepted."
                ),
            }
        return None

    @classmethod
    def determine_applicable_scheme(cls, query: str, product_dna: Optional[Any] = None) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
        """Determine applicable BIS certification scheme based on query and product context."""
        q_lower = query.lower()
        prod_text = ""
        if product_dna:
            if isinstance(product_dna, dict):
                prod_text = f"{product_dna.get('product_name', '')} {product_dna.get('category', '')}".lower()
            elif hasattr(product_dna, "product_name"):
                prod_text = f"{getattr(product_dna, 'product_name', '')} {getattr(product_dna, 'category', '')}".lower()

        combined = f"{q_lower} {prod_text}"

        # 1. Check Scheme I keywords
        sch1 = VERIFIED_SCHEMES_CATALOG["SCHEME_I"]
        if any(kw in combined for kw in sch1["applicable_categories"]) or any(std.lower() in combined for std in sch1["applicable_standards"]):
            return (
                "SCHEME_I",
                sch1,
                "Scheme I (Product Certification Scheme — ISI Mark) applies. This scheme mandates preliminary factory inspection, independent sample testing, and continuous surveillance audits under the BIS (Conformity Assessment) Regulations, 2018.",
            )

        # 2. Check Scheme II keywords
        sch2 = VERIFIED_SCHEMES_CATALOG["SCHEME_II"]
        if any(kw in combined for kw in sch2["applicable_categories"]) or any(std.lower() in combined for std in sch2["applicable_standards"]):
            return (
                "SCHEME_II",
                sch2,
                "Scheme II (Compulsory Registration Scheme — CRS) applies. This scheme operates on self-declaration of conformity based on valid test reports from BIS-recognized laboratories without preliminary factory inspection.",
            )

        # 3. Check Hallmarking keywords
        sch_h = VERIFIED_SCHEMES_CATALOG["HALLMARKING"]
        if any(kw in combined for kw in sch_h["applicable_categories"]):
            return (
                "HALLMARKING",
                sch_h,
                "BIS Hallmarking Scheme applies for precious metal articles (gold/silver jewellery) under the Hallmarking of Gold and Silver Artefacts Order, 2021, requiring assay testing and a 6-digit HUID.",
            )

        # 4. If query explicitly asks which scheme applies but no recognizable product is specified
        if any(phrase in q_lower for phrase in ["which bis certification scheme applies", "which scheme applies", "what scheme applies", "which certification scheme applies", "determine scheme"]):
            return (
                None,
                None,
                "MORE_INFORMATION_REQUIRED: Please specify the product type, category, or Indian Standard number (e.g. electric water heater, laptop, helmet, gold jewellery) to determine whether Scheme I (ISI Mark), Scheme II (CRS), or Hallmarking applies.",
            )

        return (None, None, "UNKNOWN: Unable to determine applicable BIS certification scheme from the provided query.")

    @classmethod
    def get_required_documents(cls, scheme_key: str) -> List[str]:
        """Retrieve authoritative list of required documents for a scheme."""
        sch = VERIFIED_SCHEMES_CATALOG.get(scheme_key)
        if sch and "required_documents" in sch:
            return sch["required_documents"]
        return []

    @classmethod
    def get_testing_and_application_steps(cls, scheme_key: str) -> List[str]:
        """Retrieve authoritative list of testing and application steps for a scheme."""
        sch = VERIFIED_SCHEMES_CATALOG.get(scheme_key)
        if sch and "major_testing_and_application_steps" in sch:
            return sch["major_testing_and_application_steps"]
        return []


verified_knowledge_selector = VerifiedKnowledgeSelector()

