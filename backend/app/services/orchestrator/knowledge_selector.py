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
            "6.1": {"title": "Stopper Leakage and Tilt Test", "req": "The stopper and pourer seal shall show no liquid leakage when inverted for 10 minutes."},
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
    "IS 1417:2016": {
        "title": "Gold and Gold Alloys, Jewellery/Artefacts — Fineness and Marking — Specification",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Hallmarking of Gold Jewellery and Gold Artefacts Order, 2020",
        "clauses": {
            "4.1": {"title": "Fineness and Purity Grades", "req": "Gold jewellery shall be hallmarked in standard fineness grades: 14K (585), 18K (750), 20K (833), 22K (916), 23K (958), and 24K (995/999)."},
            "5.1": {"title": "Hallmark Components", "req": "Hallmark shall consist of 3 marks: BIS Logo, Purity/Fineness, and 6-digit alphanumeric HUID."},
            "6.1": {"title": "Assaying Method", "req": "Purity determination by XRF followed by cupellation (fire assay) conforming to IS 1418."},
        },
    },
    "IS 2112:2014": {
        "title": "Silver and Silver Alloys, Jewellery/Artefacts — Fineness and Marking — Specification",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Bureau of Indian Standards (Hallmarking) Regulations, 2018",
        "clauses": {
            "4.1": {"title": "Fineness and Purity Grades", "req": "Silver jewellery/artefacts shall conform to fineness grades: 999, 990, 970, 925 (sterling silver), 900, 835, and 800."},
            "5.1": {"title": "Marking Requirements", "req": "Silver articles shall bear the BIS Logo, purity/fineness mark, and identification/HUID mark."},
        },
    },
    "IS 15820:2018": {
        "title": "General Requirements for Competence of Assaying and Hallmarking Centres",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Bureau of Indian Standards (Hallmarking) Regulations, 2018",
        "clauses": {
            "5.1": {"title": "Management and Technical Competence", "req": "Assaying and Hallmarking Centres (AHC) must have accredited testing equipment, trained assayers, and secure storage."},
            "6.2": {"title": "Laser Marking and Traceability", "req": "AHCs shall apply the 6-digit alphanumeric HUID generated by the central BIS hallmarking portal."},
        },
    },
    "IS 1418:1999": {
        "title": "Assaying of Gold in Gold Bullion, Gold Alloys and Gold Jewellery/Artefacts — Cupellation (Fire Assay) Method",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Bureau of Indian Standards (Hallmarking) Regulations, 2018",
        "clauses": {
            "5.1": {"title": "Fire Assay Protocol", "req": "Determination of gold fineness by cupellation (fire assay) method."},
        },
    },
    "IS 2113:2014": {
        "title": "Assaying of Silver in Silver Bullion, Silver Alloys and Silver Jewellery/Artefacts — Chemical Analysis Protocol",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Bureau of Indian Standards (Hallmarking) Regulations, 2018",
        "clauses": {
            "5.1": {"title": "Assaying Method", "req": "Determination of silver fineness by chemical analysis or gravimetric method."},
        },
    },
    "IS 9845:1998": {
        "title": "Determination of Overall Migration of Constituents of Plastics Materials and Articles Intended to Come into Contact with Foodstuffs",
        "ministry": "Ministry of Consumer Affairs, Food & Public Distribution",
        "qco_order": "Bureau of Indian Standards Food Contact Regulations",
        "clauses": {
            "4.1": {"title": "Overall Migration Limits", "req": "Overall migration limit shall not exceed 60 mg/kg or 10 mg/dm2 for food contact materials."},
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

    @classmethod
    def match_consumer_query_topic(cls, query: str) -> Optional[Dict[str, Any]]:
        """Classify consumer inquiry into verified consumer assistance topic."""
        q_lower = query.lower()

        # 1. Suspected Non-Conforming / Fake / Counterfeit Product (Priority)
        if any(phrase in q_lower for phrase in [
            "suspected non-conforming", "non-conforming product", "defective product",
            "fake isi", "fake mark", "counterfeit mark", "substandard product",
            "suspected product", "what should a consumer do about a suspected",
            "what should a consumer do", "found fake mark", "fake bis", "counterfeit", "fake",
        ]):
            return VERIFIED_CONSUMER_SERVICES_CATALOG["SUSPECTED_NON_CONFORMING_PRODUCT"]

        # 2. Raise a BIS Consumer Complaint
        if any(phrase in q_lower for phrase in [
            "raise a bis consumer complaint", "raise a complaint", "consumer complaint",
            "file a complaint", "register a complaint", "lodge a complaint", "how to complain",
            "how can i raise a bis consumer complaint", "report substandard", "complaint against bis",
            "bis care complaint", "complain about product",
        ]):
            return VERIFIED_CONSUMER_SERVICES_CATALOG["CONSUMER_COMPLAINT"]

        # 3. Check BIS Licence or Registration
        if any(phrase in q_lower for phrase in [
            "check a bis licence", "check a bis license", "check bis licence", "check bis license",
            "check a registration", "check registration", "search a licence", "search license",
            "is the licence valid", "is the license valid", "licence status", "license status",
            "how do i check a bis licence", "how do i check a bis license", "verify licence", "verify license",
        ]):
            return VERIFIED_CONSUMER_SERVICES_CATALOG["LICENCE_REGISTRATION_CHECK"]

        # 4. Verification of BIS / ISI / CRS / Hallmark Mark
        if any(phrase in q_lower for phrase in [
            "verify a bis", "verify bis", "verify isi", "verify a isi", "verify an isi",
            "verify mark", "verify the mark", "check bis mark", "check isi mark", "how to verify",
            "how can i verify", "verify licence details", "verify license details", "verify huid",
            "check a bis mark", "check an isi mark",
        ]):
            return VERIFIED_CONSUMER_SERVICES_CATALOG["MARK_VERIFICATION"]

        # 5. What does a BIS Mark indicate?
        if any(phrase in q_lower for phrase in [
            "what does a bis mark indicate", "what does bis mark mean", "what does isi mark indicate",
            "meaning of bis mark", "significance of bis mark", "what does a mark indicate",
            "why bis mark", "importance of bis mark",
        ]):
            return VERIFIED_CONSUMER_SERVICES_CATALOG["BIS_MARK_SIGNIFICANCE"]

        return None

    @classmethod
    def check_unsupported_consumer_claim(cls, query: str) -> Optional[Dict[str, Any]]:
        """Detect and intercept unsupported consumer assumptions (e.g. monetary refunds from BIS, informal WhatsApp complaint channels)."""
        q_lower = query.lower()
        if any(w in q_lower for w in ["refund from bis", "bis will refund", "bis pay compensation", "cash compensation from bis", "bis guarantee money back", "money refund from bis"]):
            return {
                "claim_type": "MONETARY_REFUND_GUARANTEE",
                "explanation": (
                    "The Bureau of Indian Standards (BIS) is a statutory conformity assessment and standards body; "
                    "BIS does NOT provide direct cash refunds, monetary warranties, or financial compensation to consumers. "
                    "Product refunds and financial damages must be pursued against the seller/manufacturer through Consumer "
                    "Disputes Redressal Commissions (Consumer Courts) under the Consumer Protection Act, 2019."
                ),
                "statutory_authority": "Consumer Protection Act, 2019 & BIS Act 2016",
            }
        if any(w in q_lower for w in ["whatsapp complaint", "telegram complaint", "informal complaint", "sms complaint"]):
            return {
                "claim_type": "UNOFFICIAL_COMPLAINT_CHANNEL",
                "explanation": (
                    "BIS does not accept formal consumer complaints through WhatsApp, Telegram, or personal messaging services. "
                    "Statutory consumer complaints must be lodged exclusively via the official 'BIS CARE' Mobile App or the "
                    "official online portal at www.bis.gov.in per Rule 30 of the BIS Rules, 2018."
                ),
                "statutory_authority": "BIS Rules 2018, Rule 30",
            }
        return None

    @classmethod
    def match_hallmarking_topic(cls, query: str) -> Optional[Dict[str, Any]]:
        """Classify hallmarking inquiry into verified hallmarking assistance topic."""
        q_lower = query.lower()

        # 1. HUID Meaning & Verification
        if any(phrase in q_lower for phrase in [
            "verify huid", "huid verification", "what is huid", "huid meaning",
            "meaning of huid", "how to verify huid", "huid code", "6-digit huid",
            "verify the huid", "check huid", "how do i verify huid",
        ]):
            return VERIFIED_HALLMARKING_CATALOG["HUID_VERIFICATION"]

        # 2. Gold Hallmark & Purity Grades (IS 1417) - Prioritize when purity/grades asked
        if any(phrase in q_lower for phrase in [
            "gold hallmark", "gold hallmarking", "hallmark gold", "gold purity",
            "gold purity grade", "22k916", "18k750", "14k585", "24k995", "23k958", "20k833",
            "is 1417", "gold jewellery hallmark", "gold jewelry hallmark", "gold marks",
            "3 marks on gold", "three marks on gold", "purity grade", "purity",
        ]) or ("gold" in q_lower and "purity" in q_lower):
            return VERIFIED_HALLMARKING_CATALOG["GOLD_HALLMARK_VERIFICATION"]

        # 3. What is BIS Hallmarking? (Definition)
        if any(phrase in q_lower for phrase in [
            "what is bis hallmarking", "what is hallmarking", "hallmarking definition",
            "define hallmarking", "explain hallmarking", "meaning of hallmarking",
            "what does hallmarking mean", "purpose of hallmarking",
        ]):
            return VERIFIED_HALLMARKING_CATALOG["HALLMARKING_DEFINITION"]

        # 3. Gold Hallmark & Purity Grades (IS 1417)
        if any(phrase in q_lower for phrase in [
            "gold hallmark", "gold hallmarking", "hallmark gold", "gold purity",
            "gold purity grade", "22k916", "18k750", "14k585", "24k995", "23k958", "20k833",
            "is 1417", "gold jewellery hallmark", "gold jewelry hallmark", "gold marks",
            "3 marks on gold", "three marks on gold",
        ]):
            return VERIFIED_HALLMARKING_CATALOG["GOLD_HALLMARK_VERIFICATION"]

        # 4. Silver Hallmark & Fineness Grades (IS 2112)
        if any(phrase in q_lower for phrase in [
            "silver hallmark", "silver hallmarking", "hallmark silver", "silver purity",
            "silver purity grade", "is 2112", "925 silver", "sterling silver",
            "silver fineness", "silver jewellery hallmark", "silver jewelry hallmark",
            "silver marks", "hallmark on silver",
        ]):
            return VERIFIED_HALLMARKING_CATALOG["SILVER_HALLMARK_VERIFICATION"]

        # 5. Hallmarking Registration & Assaying Process Guidance
        if any(phrase in q_lower for phrase in [
            "hallmarking registration", "jeweller registration", "jeweler registration",
            "how to get hallmarked", "hallmarking process", "how does hallmarking work",
            "ahc process", "assaying process", "hallmarking workflow", "register jeweller",
            "registration for jewellers", "how jewellers get hallmark",
        ]):
            return VERIFIED_HALLMARKING_CATALOG["HALLMARKING_REGISTRATION_PROCESS"]

        # 6. Consumer Hallmarking Guidance (Testing personal jewellery, compensation, complaints)
        if any(phrase in q_lower for phrase in [
            "consumer hallmark", "hallmark compensation", "hallmarking fee", "testing jewellery",
            "test gold at ahc", "test jewellery", "consumer gold testing", "lesser purity",
            "compensation under regulation 18", "hallmark complaint", "testing fee",
            "can consumer test jewellery", "can consumer get hallmark",
        ]):
            return VERIFIED_HALLMARKING_CATALOG["CONSUMER_HALLMARKING_GUIDANCE"]

        # 7. Official BIS Hallmarking Services
        if any(phrase in q_lower for phrase in [
            "hallmark services", "hallmarking service", "official hallmarking service",
            "bis hallmarking services", "hallmarking portal", "ahc network",
        ]):
            return VERIFIED_HALLMARKING_CATALOG["HALLMARKING_SERVICES"]

        # Default fallback for generic hallmark query
        if "hallmark" in q_lower or "huid" in q_lower:
            return VERIFIED_HALLMARKING_CATALOG["HALLMARKING_DEFINITION"]

        return None

    @classmethod
    def check_unsupported_hallmarking_claim(cls, query: str) -> Optional[Dict[str, Any]]:
        """Detect and intercept unsupported hallmarking assumptions and myths."""
        q_lower = query.lower()

        # 1. Price Fixation / Gold Rate Guarantee
        if any(w in q_lower for w in ["gold price", "gold rate", "bis gold price", "fix gold rate", "gold rate today", "silver price", "silver rate", "price guarantee"]) or (
            any(w in q_lower for w in ["gold", "silver"]) and any(w in q_lower for w in ["price", "rate", "cost", "value"]) and any(w in q_lower for w in ["guarantee", "fix", "determine", "today"])
        ):
            return {
                "claim_type": "PRICE_FIXATION_OR_RATE_GUARANTEE",
                "explanation": (
                    "The Bureau of Indian Standards (BIS) regulates exclusively the technical purity, testing methodology, "
                    "and physical conformity of precious metals under IS 1417 and IS 2112. BIS does NOT determine, fix, "
                    "or guarantee daily gold or silver market prices, making charges, or retail buyback values. Commercial "
                    "pricing is governed by open market commodity exchanges and local jeweller associations."
                ),
                "statutory_authority": "BIS Act 2016, Chapter IV & Consumer Affairs Guidelines",
            }

        # 2. DIY / Home Hallmarking
        if ("hallmark" in q_lower or "huid" in q_lower or "stamp" in q_lower) and any(w in q_lower for w in ["at home", "myself", "diy", "without ahc", "without centre", "without center"]):
            return {
                "claim_type": "UNAUTHORIZED_HALLMARKING_OR_DIY",
                "explanation": (
                    "Hallmarking cannot be performed by individuals or jewellers at home or without an accredited centre. "
                    "Under Section 14 and Section 15 of the BIS Act, 2016, hallmarking and HUID generation may only be carried "
                    "out by a BIS-recognized Assaying and Hallmarking Centre (AHC) accredited under IS 15820. Unauthorized "
                    "marking or counterfeiting of the hallmark constitutes a criminal offence under Section 29."
                ),
                "statutory_authority": "BIS Act 2016, Section 15 & Section 29",
            }

        # 3. Base Metals / Non-Precious Materials
        if any(w in q_lower for w in ["brass", "copper", "imitation", "artificial", "platinum", "palladium"]) and any(h in q_lower for h in ["hallmark", "916", "huid", "gold"]):
            return {
                "claim_type": "NON_PRECIOUS_METAL_HALLMARKING",
                "explanation": (
                    "BIS hallmarking is restricted strictly to gold (IS 1417:2016) and silver (IS 2112:2014) jewellery and artefacts. "
                    "Base metals such as brass, copper, or artificial/imitation jewellery are legally ineligible for BIS hallmarking. "
                    "Attempting to apply hallmark markings to non-precious metals is strictly prohibited."
                ),
                "statutory_authority": "IS 1417:2016 & IS 2112:2014",
            }

        # 4. Unofficial messaging channels (WhatsApp/Telegram/SMS HUID verification)
        if any(w in q_lower for w in ["whatsapp", "telegram", "sms"]) and any(h in q_lower for h in ["huid", "hallmark", "jewellery", "jewelry"]):
            return {
                "claim_type": "UNOFFICIAL_HUID_CHANNEL",
                "explanation": (
                    "BIS does not verify HUID or hallmarking through WhatsApp, Telegram, or personal messaging bots. "
                    "HUID verification is provided exclusively through the official 'BIS CARE' Mobile App or the official "
                    "Manakonline web portal at www.manakonline.in."
                ),
                "statutory_authority": "BIS (Hallmarking) Regulations, 2018",
            }

        # 5. Selling Unhallmarked Jewellery in Mandatory Districts
        if ("unhallmarked" in q_lower or "without hallmark" in q_lower or "without huid" in q_lower) and any(w in q_lower for w in ["sell", "selling", "jeweller", "jeweler"]):
            return {
                "claim_type": "UNHALLMARKED_SALE_IN_MANDATORY_DISTRICT",
                "explanation": (
                    "Under the Hallmarking of Gold Jewellery and Gold Artefacts Order, registered jewellers are legally "
                    "prohibited from selling gold jewellery or artefacts without the mandatory 6-digit HUID hallmark in "
                    "notified mandatory hallmarking districts across India. Violations attract statutory penalties and license cancellation."
                ),
                "statutory_authority": "Hallmarking of Gold Jewellery and Gold Artefacts Order & BIS Act 2016, Section 29",
            }

        return None

    @classmethod
    def match_laboratory_topic(cls, query: str) -> Optional[Dict[str, Any]]:
        """Classify laboratory inquiry into verified laboratory guidance topic."""
        q_lower = query.lower()

        # 1. Verification of Laboratory Recognition Status
        if any(phrase in q_lower for phrase in [
            "verify a laboratory's bis recognition status", "verify a lab's bis recognition status",
            "verify laboratory's bis recognition status", "verify lab's bis recognition status",
            "verify laboratory recognition status", "verify lab recognition status",
            "verify a laboratory", "verify a lab", "verify laboratory", "verify lab",
            "recognition status", "recognition of laboratory", "check recognition status",
            "how do i verify a laboratory", "how do i verify a lab", "is the lab recognized",
            "is the laboratory recognized", "check lab status", "check laboratory status",
        ]):
            return VERIFIED_LABORATORY_TOPICS["LABORATORY_RECOGNITION_STATUS"]

        # 2. What laboratory information is available
        if any(phrase in q_lower for phrase in [
            "which laboratory information is available", "laboratory information is available",
            "lab information is available", "laboratory information available",
            "what laboratory information is available", "what lab information is available",
            "which lab information is available", "available laboratory information",
            "information is available for laboratories",
        ]):
            return VERIFIED_LABORATORY_TOPICS["AVAILABLE_LABORATORY_INFORMATION"]

        # 3. What type of testing is required for a given standard / Testing category
        if any(phrase in q_lower for phrase in [
            "what type of testing is required", "what testing is required", "type of testing is required",
            "type of testing", "testing category", "testing categories", "tests required",
            "testing required", "what tests are required", "which tests are required",
            "testing scope", "test methods", "required tests",
        ]):
            return VERIFIED_LABORATORY_TOPICS["TESTING_CATEGORY_GUIDANCE"]

        # 4. Where can I find BIS-recognized laboratories / Laboratory discovery
        if any(phrase in q_lower for phrase in [
            "where can i find bis-recognized", "where can i find bis recognized",
            "where can i find laboratory", "where can i find lab", "where can i find laboratories",
            "where can i find labs", "find bis-recognized", "find bis recognized",
            "find a laboratory", "find a lab", "find laboratories", "find labs",
            "which bis-recognized laboratory can test", "which bis recognized laboratory can test",
            "which laboratory can test", "which lab can test", "who can test my product",
            "can test my product", "laboratory directory", "lab directory", "directory of laboratories",
            "directory of labs", "lims portal", "lims", "official laboratory directory",
        ]):
            return VERIFIED_LABORATORY_TOPICS["LABORATORY_DISCOVERY"]

        return None

    @classmethod
    def get_testing_categories_for_standard(cls, query_or_std: str) -> Optional[Dict[str, Any]]:
        """Retrieve deterministic testing categories mapped to a standard or product keyword."""
        q_lower = query_or_std.lower()

        # Check explicit IS numbers and product keywords
        if "302-2-201" in q_lower or ("302" in q_lower and ("heater" in q_lower or "immersion" in q_lower)) or "heater" in q_lower or "immersion" in q_lower:
            return VERIFIED_TESTING_CATEGORIES_CATALOG["IS 302-2-201:2008"]
        if "17526" in q_lower or "flask" in q_lower or "insulated" in q_lower:
            return VERIFIED_TESTING_CATEGORIES_CATALOG["IS 17526:2021"]
        if "4151" in q_lower or "helmet" in q_lower or "headgear" in q_lower:
            return VERIFIED_TESTING_CATEGORIES_CATALOG["IS 4151:2020"]
        if "13252" in q_lower or "laptop" in q_lower or "computer" in q_lower or "it equipment" in q_lower:
            return VERIFIED_TESTING_CATEGORIES_CATALOG["IS 13252 (Part 1):2010"]
        if "1417" in q_lower or ("gold" in q_lower and "jewel" in q_lower):
            return VERIFIED_TESTING_CATEGORIES_CATALOG["IS 1417:2016"]
        if "1786" in q_lower or "rebar" in q_lower or "steel bar" in q_lower or "tmt" in q_lower:
            return VERIFIED_TESTING_CATEGORIES_CATALOG["IS 1786:2008"]
        if "8112" in q_lower or "cement" in q_lower:
            return VERIFIED_TESTING_CATEGORIES_CATALOG["IS 8112:2013"]

        return None

    @classmethod
    def check_unsupported_laboratory_claim(cls, query: str) -> Optional[Dict[str, Any]]:
        """Intercept unsupported lab operations: booking, payment, commercial rankings, or compliance claims."""
        q_lower = query.lower()

        # 1. Laboratory Booking / Appointment Requests
        if any(w in q_lower for w in ["book", "booking", "schedule appointment", "schedule slot", "reserve slot", "reserve test", "book test", "book a test", "book lab"]):
            return {
                "claim_type": "LABORATORY_BOOKING_OR_APPOINTMENT",
                "explanation": (
                    "Zyntrix is an informational regulatory compliance intelligence system and does not execute laboratory "
                    "bookings, appointments, or sample intake reservations. Testing requests and sample consignments must be "
                    "initiated directly with the respective BIS-recognized laboratory or submitted through the official BIS LIMS "
                    "portal at https://lims.bis.gov.in."
                ),
                "statutory_authority": "BIS (Laboratory Recognition Scheme) Regulations, 2020",
            }

        # 2. Payment / Fee Transaction Requests
        if (
            any(w in q_lower for w in ["pay fee", "pay fees", "pay lab", "payment for test", "pay testing", "transfer fee", "wire testing fee", "checkout"])
            or ("pay" in q_lower and any(w in q_lower for w in ["fee", "fees", "cost", "costs", "charge", "charges", "testing", "lab", "laboratory", "portal", "system"]))
            or any(phrase in q_lower for phrase in ["pay the laboratory", "pay testing fee", "pay the fee", "payment through"])
        ):
            return {
                "claim_type": "PAYMENT_OR_FEE_TRANSACTION",
                "explanation": (
                    "Zyntrix does not process financial transactions, testing fee payments, or laboratory billing. Testing charges "
                    "are levied directly by recognized testing laboratories according to their audited fee schedules, and statutory "
                    "application fees must be paid exclusively through the official BIS Manakonline portal (www.manakonline.in)."
                ),
                "statutory_authority": "BIS (Conformity Assessment) Regulations, 2018",
            }

        # 3. Commercial Ranking, Rating, or Price Comparison Recommendations
        if (
            any(phrase in q_lower for phrase in [
                "cheapest lab", "cheapest laboratory", "lowest price lab", "lowest fee lab",
                "fastest lab", "fastest laboratory", "quickest lab", "best rated lab",
                "best rated laboratory", "highest rated lab", "highest rated laboratory",
                "top rated lab", "top rated laboratory", "recommend the best lab", "rank laboratories",
            ])
            or (
                any(w in q_lower for w in ["cheapest", "fastest", "lowest price", "lowest fee", "best rated", "highest rated", "top rated"])
                and any(w in q_lower for w in ["lab", "labs", "laboratory", "laboratories"])
            )
        ):
            return {
                "claim_type": "COMMERCIAL_RANKING_OR_RECOMMENDATION",
                "explanation": (
                    "The Bureau of Indian Standards and government regulations treat all BIS-recognized laboratories equally "
                    "based strictly on their audited accreditation status under ISO/IEC 17025 and approved statutory scope. "
                    "BIS does not publish commercial reviews, popularity rankings, or price comparison indices. Users must "
                    "select recognized laboratories based strictly on geographic proximity and approved testing scope on the LIMS portal."
                ),
                "statutory_authority": "BIS (Laboratory Recognition Scheme) Regulations, 2020 & ISO/IEC 17025:2017",
            }

        # 4. Test Completion Equals BIS Certification / Compliance
        if (
            any(phrase in q_lower for phrase in [
                "does passing test mean certified", "if my product passes test is it certified",
                "if test passes is it compliant", "test report means bis certified",
                "does test report give me isi mark", "passing test means isi mark",
                "is product certified after testing", "does lab grant certification",
                "does laboratory issue certificate", "does lab issue isi mark",
                "completing a test means the product is bis compliant", "test means compliant",
                "passes the laboratory test", "pass the laboratory test",
            ])
            or (
                ("passes" in q_lower or "passed" in q_lower or "passing" in q_lower)
                and ("test" in q_lower or "testing" in q_lower)
                and ("certified" in q_lower or "certification" in q_lower or "compliant" in q_lower or "isi mark" in q_lower)
            )
        ):
            return {
                "claim_type": "TEST_COMPLETION_EQUALS_CERTIFICATION",
                "explanation": (
                    "Completing a test or obtaining a conforming test report from a BIS-recognized laboratory does NOT constitute "
                    "BIS certification, nor does it authorize the application of the Standard Mark (ISI / CRS). A test report is "
                    "merely an evidentiary submission. BIS certification is granted exclusively by the Bureau of Indian Standards "
                    "after comprehensive evaluation, factory inspection (under Scheme I), and administrative scrutiny under the "
                    "BIS (Conformity Assessment) Regulations, 2018."
                ),
                "statutory_authority": "BIS Act 2016, Section 13 & BIS (Conformity Assessment) Regulations, 2018",
            }

        # 5. Unverified / Foreign / Fictional Laboratory Recognition
        if any(w in q_lower for w in ["acme lab", "fake lab", "unregistered lab", "xyz lab", "foreign lab in china", "foreign lab in usa"]) and any(l in q_lower for l in ["recognized", "bis", "certify", "test"]):
            return {
                "claim_type": "UNVERIFIED_LABORATORY_RECOGNITION",
                "explanation": (
                    "The specified laboratory is not recognized in the official Bureau of Indian Standards laboratory network. "
                    "Only laboratories formally recognized under the BIS Laboratory Recognition Scheme (LRS) or operated directly "
                    "by BIS are authorized to perform statutory conformity assessment testing for BIS schemes."
                ),
                "statutory_authority": "BIS (Laboratory Recognition Scheme) Regulations, 2020, Regulation 3",
            }

        return None

    @classmethod
    def get_laboratory_record(cls, lab_identifier: str) -> Optional[Dict[str, Any]]:
        """Look up a laboratory record by catalog key, lab_code, or exact/partial name."""
        if lab_identifier in VERIFIED_LABORATORIES_CATALOG:
            return VERIFIED_LABORATORIES_CATALOG[lab_identifier]
        ident_lower = lab_identifier.lower().strip()
        for key, rec in VERIFIED_LABORATORIES_CATALOG.items():
            if rec.get("lab_code", "").lower() == ident_lower:
                return rec
            if ident_lower in rec.get("name", "").lower():
                return rec
            if ident_lower in key.lower():
                return rec
        return None

    @classmethod
    def get_laboratory_by_query(cls, query: str) -> Optional[Dict[str, Any]]:
        """Detect whether a query specifically targets an identifiable laboratory record."""
        q_lower = query.lower()
        if "central laboratory" in q_lower or "bis-cl" in q_lower or "sahibabad" in q_lower:
            return VERIFIED_LABORATORIES_CATALOG.get("CENTRAL_LABORATORY")
        if "western regional" in q_lower or "bis-wrl" in q_lower or ("wrl" in q_lower and "lab" in q_lower):
            return VERIFIED_LABORATORIES_CATALOG.get("WESTERN_REGIONAL_LABORATORY")
        if "southern regional" in q_lower or "bis-srl" in q_lower or ("srl" in q_lower and "lab" in q_lower):
            return VERIFIED_LABORATORIES_CATALOG.get("SOUTHERN_REGIONAL_LABORATORY")
        if "eastern regional" in q_lower or "bis-erl" in q_lower or ("erl" in q_lower and "lab" in q_lower):
            return VERIFIED_LABORATORIES_CATALOG.get("EASTERN_REGIONAL_LABORATORY")
        if "northern regional" in q_lower or "bis-nrl" in q_lower or ("nrl" in q_lower and "lab" in q_lower):
            return VERIFIED_LABORATORIES_CATALOG.get("NORTHERN_REGIONAL_LABORATORY")
        if "branch laboratories" in q_lower or "branch lab" in q_lower or "bis-branch" in q_lower:
            return VERIFIED_LABORATORIES_CATALOG.get("BRANCH_LABORATORIES")
        if "stale" in q_lower or "stale annex" in q_lower or "stale-099" in q_lower or "stale-test" in q_lower or "sample_stale_laboratory" in q_lower:
            return VERIFIED_LABORATORIES_CATALOG.get("SAMPLE_STALE_LABORATORY")
        if "acme" in q_lower or "acme lab" in q_lower or "acme industrial" in q_lower or "sample_unverified_third_party" in q_lower or "unverified third-party" in q_lower:
            return VERIFIED_LABORATORIES_CATALOG.get("SAMPLE_UNVERIFIED_THIRD_PARTY")
        return None

    @classmethod
    def audit_laboratory_record(cls, record_or_key: Any) -> Dict[str, Any]:
        """Audit laboratory record against explicit 6-link provenance chain:
        laboratory -> official BIS source -> source/version/date -> authenticity -> current recognition status -> testing scope.
        
        Where authoritative evidence is missing, stale, or insufficient,
        downgrades to UNVERIFIED / VERIFICATION_REQUIRED so the orchestrator can abstain safely.
        """
        record: Optional[Dict[str, Any]]
        if isinstance(record_or_key, str):
            record = cls.get_laboratory_record(record_or_key)
        elif isinstance(record_or_key, dict):
            record = record_or_key
        else:
            record = None

        if not record:
            return {
                "laboratory_name": "UNKNOWN",
                "lab_code": "UNKNOWN",
                "is_verified": False,
                "verification_status": "UNVERIFIED",
                "failure_reasons": ["Laboratory record not found in authoritative catalog"],
                "audit_notes": "Record not found.",
                "provenance_chain": {},
            }

        reasons: List[str] = []

        # Link 1: Laboratory
        lab_name = record.get("name", "")
        lab_code = record.get("lab_code", "")
        if not lab_name or not lab_code:
            reasons.append("Missing laboratory identification (name or code)")

        # Link 2: Official BIS Source
        official_source = record.get("official_bis_source", "")
        if not official_source or "None" in official_source or "Missing" in official_source:
            reasons.append("Authoritative BIS source document or portal is missing")

        # Link 3: Source / Version / Date
        source_ver_date = record.get("source_version_date", "")
        if not source_ver_date or source_ver_date == "N/A" or "Zero-byte" in source_ver_date:
            reasons.append("Authoritative source version, date, or snapshot hash is missing or invalid")

        # Link 4: Authenticity
        authenticity = record.get("authenticity", "")
        if authenticity != "AUTHENTIC_BIS_SOURCE":
            reasons.append(f"Authenticity status '{authenticity}' is not verified as authentic BIS source")

        # Link 5: Current Recognition Status
        status = record.get("current_recognition_status", "")
        if status not in ("OPERATIVE_RECOGNIZED", "ACTIVE", "BIS_OWNED_OPERATIONAL"):
            reasons.append(f"Recognition status '{status}' is not active or operative")

        # Link 6: Testing Scope
        scope = record.get("testing_scope", "")
        if not scope or "UNVERIFIED" in scope or "VERIFICATION_REQUIRED" in scope:
            reasons.append("Testing scope is unverified, missing clause-level schedules, or requires external verification")

        # Declared verification status check
        declared_status = record.get("verification_status", "UNVERIFIED")
        if declared_status != "VERIFIED":
            reasons.append(f"Record explicitly flagged as {declared_status}: {record.get('audit_notes', '')}")

        is_verified = (len(reasons) == 0 and declared_status == "VERIFIED")
        effective_status = "VERIFIED" if is_verified else declared_status

        return {
            "laboratory_name": lab_name,
            "lab_code": lab_code,
            "is_verified": is_verified,
            "verification_status": effective_status,
            "failure_reasons": reasons,
            "audit_notes": record.get("audit_notes", ""),
            "provenance_chain": record.get("provenance_chain", {}),
        }


# Canonical catalog of verified BIS Consumer Assistance Topics
VERIFIED_CONSUMER_SERVICES_CATALOG: Dict[str, Dict[str, Any]] = {
    "MARK_VERIFICATION": {
        "topic": "MARK_VERIFICATION",
        "title": "Verification of BIS / ISI / CRS / Hallmark Marks",
        "instructions": (
            "1. **ISI Mark Verification (Scheme I)**:\n"
            "   - Genuine ISI products carry the ISI monogram with a mandatory 7 or 8 digit CM/L (Certification Marks Licence) number beneath it.\n"
            "   - Open the official **BIS CARE** mobile app (available on Google Play & Apple App Store) and tap **'Verify Licence Details'**.\n"
            "   - Enter the CM/L number to view the authentic licensee name, brand, factory address, valid Indian Standard, and operative status.\n\n"
            "2. **CRS Mark Verification (Scheme II — Electronics/IT)**:\n"
            "   - Check the Standard Mark for the unique Registration R-number (format: R-XXXXXXXX).\n"
            "   - Verify on the BIS CARE app under **'Verify Registration No.'** or search public records at `www.crsbis.in`.\n\n"
            "3. **Gold & Silver Hallmark Verification**:\n"
            "   - Inspect the mandatory 3 marks: BIS Logo, Purity mark (e.g. 22K916), and the 6-digit alphanumeric **HUID** (Hallmark Unique Identification).\n"
            "   - In the BIS CARE app, tap **'Verify HUID'** to confirm the jeweller registration, Assaying Centre (AHC) details, and article type."
        ),
        "official_portal": "BIS CARE Mobile App & www.manakonline.in",
        "statutory_provenance": "BIS Act 2016, Sections 15 & 16; BIS (Conformity Assessment) Regulations, 2018",
    },
    "LICENCE_REGISTRATION_CHECK": {
        "topic": "LICENCE_REGISTRATION_CHECK",
        "title": "Checking BIS Licence or Registration Status",
        "instructions": (
            "To verify the operational legitimacy of a manufacturer's license or registration:\n"
            "1. **Public Online Directory**: Access the official Manakonline portal (`www.manakonline.in`) and select **'Search a Licence'**.\n"
            "2. **Search Parameters**: Search by CM/L number, manufacturer name, brand name, or Indian Standard (IS) number.\n"
            "3. **Verification Details**: Confirm whether the status is **Operative**, **Expired**, **Suspended**, or **Cancelled**.\n"
            "4. **Scope Verification**: Confirm that the exact product model and category are included within the approved scope of licence."
        ),
        "official_portal": "www.manakonline.in (e-BIS Portal)",
        "statutory_provenance": "BIS Act 2016, Section 13(2); BIS Rules 2018",
    },
    "CONSUMER_COMPLAINT": {
        "topic": "CONSUMER_COMPLAINT",
        "title": "Filing a Formal BIS Consumer Complaint",
        "instructions": (
            "Consumers can lodge statutory grievances regarding substandard or counterfeit goods under Rule 30 of the BIS Rules, 2018:\n"
            "1. **Channels**: Open the **BIS CARE App** and tap **'Complaints' -> 'Register Complaint'**, or visit the web portal at `www.bis.gov.in`.\n"
            "2. **Complaint Classification**:\n"
            "   - Quality defect in genuine ISI marked product.\n"
            "   - Misuse or unauthorized forging of ISI Mark / CRS Mark / Hallmark.\n"
            "   - Misleading advertisement or non-conformance.\n"
            "3. **Evidence Required**: Upload purchase bill/cash memo, photographs showing the product label with CM/L or R-number, and a clear description of the defect.\n"
            "4. **Tracking**: The system issues a unique Complaint Registration Number for tracking investigation and redressal."
        ),
        "official_portal": "BIS CARE Mobile App & www.bis.gov.in/consumer-affairs/",
        "statutory_provenance": "BIS Rules 2018, Rule 30; BIS Act 2016, Section 30",
    },
    "SUSPECTED_NON_CONFORMING_PRODUCT": {
        "topic": "SUSPECTED_NON_CONFORMING_PRODUCT",
        "title": "Protocol for Suspected Non-Conforming or Counterfeit Products",
        "instructions": (
            "When encountering a product suspected of lacking genuine BIS conformity:\n"
            "1. **Cease Use Immediately**: Discontinue using any electrical, chemical, or safety item that appears non-conforming.\n"
            "2. **Verify on BIS CARE App**: Enter the CM/L or R-number. If the number does not exist, belongs to a different firm, or is cancelled, the product is counterfeit.\n"
            "3. **Retain Evidence**: Preserve the original purchase tax invoice, manufacturer packaging, warranty card, and sample.\n"
            "4. **Report to BIS**: Register a complaint on the BIS CARE app or send detailed intimation to the Head of Consumer Affairs Department (CAD) or nearest BIS Regional/Branch Office.\n"
            "5. **Statutory Enforcement**: Under BIS Act 2016 Section 28, BIS enforcement teams possess legal powers of search and seizure to raid unauthorized premises and initiate criminal prosecution."
        ),
        "official_portal": "BIS Consumer Affairs Department (CAD) & BIS CARE App",
        "statutory_provenance": "BIS Act 2016, Section 28 (Search and Seizure) & Section 30",
    },
    "BIS_MARK_SIGNIFICANCE": {
        "topic": "BIS_MARK_SIGNIFICANCE",
        "title": "What a BIS Mark Indicates",
        "instructions": (
            "A Bureau of Indian Standards (BIS) mark on a product signifies:\n"
            "1. **Third-Party Conformity Guarantee**: Independent statutory assurance that the product complies with codified Indian Standards (IS) for safety, quality, and performance.\n"
            "2. **Continuous Quality Surveillance**: The manufacturer operates an audited quality control system with factory testing and is subject to unannounced surveillance audits and market sampling by BIS.\n"
            "3. **Statutory Traceability**: Direct accountability through an assigned, traceable licence (CM/L) or registration (R-number).\n\n"
            "*Important Distinction*: A BIS mark indicates product conformity to standards; it is NOT a commercial manufacturer warranty, nor does it imply government manufacturing."
        ),
        "official_portal": "Bureau of Indian Standards Official Guidelines",
        "statutory_provenance": "BIS Act 2016, Sections 13, 14 & 15",
    },
}

# Canonical catalog of verified BIS Hallmarking Assistance Topics (Milestone M25.4D)
VERIFIED_HALLMARKING_CATALOG: Dict[str, Dict[str, Any]] = {
    "HALLMARKING_DEFINITION": {
        "topic": "HALLMARKING_DEFINITION",
        "title": "What is BIS Hallmarking?",
        "instructions": (
            "**BIS Hallmarking Definition & Legal Framework**:\n"
            "1. **Statutory Definition**: Hallmarking is the official, accurate determination and recording of the proportionate content of precious metal (gold or silver) in jewellery or artefacts.\n"
            "2. **Statutory Authority**: Governed under Chapter IV (Sections 14–18) of the BIS Act, 2016 and the Bureau of Indian Standards (Hallmarking) Regulations, 2018.\n"
            "3. **Objective**: Protects consumers against adulteration and under-karatage, enforces declared purity, and establishes transparent digital accountability.\n"
            "4. **Mandatory Hallmarking**: Since April 1, 2023, the sale of gold jewellery without the mandatory 6-digit alphanumeric HUID hallmark is prohibited by law in notified districts across India."
        ),
        "official_portal": "www.manakonline.in & BIS CARE App",
        "statutory_provenance": "BIS Act 2016, Chapter IV; BIS (Hallmarking) Regulations, 2018; Hallmarking of Gold Jewellery Order",
    },
    "HUID_VERIFICATION": {
        "topic": "HUID_VERIFICATION",
        "title": "HUID (Hallmark Unique Identification) Meaning & Verification",
        "instructions": (
            "**What is HUID?**\n"
            "- HUID (Hallmark Unique Identification) is a 6-digit alphanumeric code laser-engraved onto every piece of hallmarked jewellery at a BIS-recognized Assaying and Hallmarking Centre (AHC).\n"
            "- **Unique Digital Identity**: Every individual piece receives a distinct HUID; no two articles share the same code.\n"
            "- **Digital Traceability**: Securely logs in the central BIS system: registered jeweller name & licence number, AHC details, hallmarking date, article type (e.g. ring, bangle, necklace), and declared purity.\n\n"
            "**How to Verify HUID Step-by-Step**:\n"
            "1. Open the official **BIS CARE** mobile app (available on Google Play Store & Apple App Store).\n"
            "2. Tap the **'Verify HUID'** feature on the home screen.\n"
            "3. Enter the 6-character alphanumeric code marked on the jewellery article.\n"
            "4. The app reveals: Jeweller's registration number, Assaying Centre (AHC) name, hallmarking date, and purity grade.\n"
            "5. Verify that the displayed article details and purity match your purchase invoice and physical jewellery."
        ),
        "official_portal": "BIS CARE Mobile App ('Verify HUID' feature)",
        "statutory_provenance": "BIS (Hallmarking) Regulations, 2018; Guidelines for Hallmarking through HUID",
    },
    "GOLD_HALLMARK_VERIFICATION": {
        "topic": "GOLD_HALLMARK_VERIFICATION",
        "title": "Gold Hallmark Components & Recognized Purity Grades",
        "instructions": (
            "**Mandatory 3 Marks on Genuine Gold Jewellery**:\n"
            "1. **BIS Triangular Logo**: The official triangular hallmark monogram of the Bureau of Indian Standards.\n"
            "2. **Purity in Karat and Fineness**: Declared purity grade (e.g., 22K916 for 91.6% pure gold).\n"
            "3. **6-Digit Alphanumeric HUID**: Unique laser-engraved identification code.\n\n"
            "**Recognized Official Gold Purity Grades (IS 1417:2016)**:\n"
            "- **24K995 / 24K999**: 99.5% / 99.9% Pure Gold (Bullion / Artefacts)\n"
            "- **23K958**: 23 Karat (95.8% Pure Gold)\n"
            "- **22K916**: 22 Karat (91.6% Pure Gold — standard traditional jewellery)\n"
            "- **20K833**: 20 Karat (83.3% Pure Gold)\n"
            "- **18K750**: 18 Karat (75.0% Pure Gold — studded / diamond jewellery)\n"
            "- **14K585**: 14 Karat (58.5% Pure Gold)\n\n"
            "*Note*: Tax invoice issued by registered jewellers must explicitly state the HUID number, karatage/purity, and gross/net weight."
        ),
        "official_portal": "BIS CARE App & www.manakonline.in",
        "statutory_provenance": "IS 1417:2016; Hallmarking of Gold Jewellery and Gold Artefacts Order; BIS Act 2016",
    },
    "SILVER_HALLMARK_VERIFICATION": {
        "topic": "SILVER_HALLMARK_VERIFICATION",
        "title": "Silver Hallmark Components & Recognized Fineness Grades",
        "instructions": (
            "**Silver Hallmarking Framework (IS 2112:2014)**:\n"
            "Hallmarking of silver jewellery and artefacts conforms to Indian Standard IS 2112:2014 (Fineness and marking of silver and silver alloys).\n\n"
            "**Recognized Silver Fineness Grades (IS 2112)**:\n"
            "- **999**: Fine Silver (99.9% purity)\n"
            "- **990**: 99.0% purity\n"
            "- **970**: 97.0% purity\n"
            "- **925**: Sterling Silver (92.5% purity — most widely used for jewellery and cutlery)\n"
            "- **900**: 90.0% purity\n"
            "- **835**: 83.5% purity\n"
            "- **800**: 80.0% purity\n\n"
            "**Marks on Genuine Silver Articles**:\n"
            "1. **BIS Logo**: Official triangular mark.\n"
            "2. **Purity / Fineness Mark**: Numerical fineness (e.g. 925 for Sterling Silver).\n"
            "3. **AHC Identification / HUID**: Where implemented at BIS-recognized Assaying Centres."
        ),
        "official_portal": "BIS CARE Mobile App & www.bis.gov.in",
        "statutory_provenance": "IS 2112:2014; BIS (Hallmarking) Regulations, 2018",
    },
    "HALLMARKING_REGISTRATION_PROCESS": {
        "topic": "HALLMARKING_REGISTRATION_PROCESS",
        "title": "Jeweller Registration & Assaying Process Guidance",
        "instructions": (
            "**1. Jeweller Registration Process**:\n"
            "- Jewellers obtain registration from BIS online via the e-BIS Manakonline portal (`www.manakonline.in`).\n"
            "- Registration is automated, paperless, and one-time (no renewal fees required per Government notification).\n"
            "- Any jeweller selling hallmarked jewellery in mandatory districts must be registered with BIS.\n\n"
            "**2. Assaying and Hallmarking Workflow at AHC**:\n"
            "1. **Batch Submission**: Registered jeweller submits jewellery batch with online delivery challan via e-BIS.\n"
            "2. **Preliminary Testing**: AHC performs non-destructive X-ray Fluorescence (XRF) screening.\n"
            "3. **Confirmatory Fire Assay**: Representative samples undergo cupellation / fire assay conforming to IS 1418 for gold or IS 2113 for silver.\n"
            "4. **Portal Verification & HUID Generation**: On conforming test results, the central BIS portal generates unique 6-digit HUIDs.\n"
            "5. **Laser Marking**: The AHC laser-engraves the 3 marks (BIS logo, purity, HUID) under CCTV surveillance.\n"
            "6. **Return to Jeweller**: Conforming hallmarked articles returned with official assay certificate and job sheet."
        ),
        "official_portal": "www.manakonline.in (e-BIS Portal)",
        "statutory_provenance": "BIS Act 2016, Section 14; BIS (Hallmarking) Regulations, 2018; IS 15820:2018",
    },
    "CONSUMER_HALLMARKING_GUIDANCE": {
        "topic": "CONSUMER_HALLMARKING_GUIDANCE",
        "title": "Consumer Rights, Testing of Personal Jewellery & Redressal",
        "instructions": (
            "**1. Testing Personal Jewellery at AHC**:\n"
            "- Any ordinary consumer can take their personal gold or silver jewellery to any BIS-recognized Assaying and Hallmarking Centre (AHC) for purity testing on priority.\n"
            "- Prescribed nominal testing fee: Rs 45 per gold article (plus applicable taxes).\n"
            "- The AHC issues an authentic, official assay test report detailing the exact tested purity.\n\n"
            "**2. Statutory Compensation for Under-Purity (Regulation 18)**:\n"
            "- Under Regulation 18 of the BIS (Hallmarking) Regulations, 2018, if hallmarked jewellery is tested and found of lesser purity than marked:\n"
            "  - The registered jeweller is legally bound to compensate the consumer **twice the cost of purity deficiency**.\n"
            "  - The jeweller must also refund all testing charges incurred by the consumer.\n\n"
            "**3. Consumer Grievance Redressal**:\n"
            "- Consumers can file formal hallmarking complaints via the **BIS CARE** mobile app under 'Complaints' or report to the Consumer Affairs Department, BIS."
        ),
        "official_portal": "BIS CARE Mobile App & BIS Consumer Affairs Department",
        "statutory_provenance": "BIS (Hallmarking) Regulations, 2018, Regulation 18; BIS Rules 2018, Rule 30",
    },
    "HALLMARKING_SERVICES": {
        "topic": "HALLMARKING_SERVICES",
        "title": "Official BIS Hallmarking Services & Portals",
        "instructions": (
            "**Official BIS Hallmarking Infrastructure & Digital Services**:\n"
            "1. **e-BIS / Manakonline Portal** (`www.manakonline.in`):\n"
            "   - Online Jeweller Registration system.\n"
            "   - Recognition, auditing, and renewal of Assaying and Hallmarking Centres (AHC).\n"
            "   - Real-time central repository for HUID generation and tracking.\n"
            "2. **BIS CARE Mobile App**:\n"
            "   - Consumer-facing 'Verify HUID' service for real-time authentication.\n"
            "   - Search registered jewellers and recognized AHC directories.\n"
            "   - Formal grievance redressal for spurious or under-karat jewellery.\n"
            "3. **Network of Recognized AHCs**:\n"
            "   - Over 1,500 BIS-recognized centres across India audited under IS 15820:2018 for assaying competence."
        ),
        "official_portal": "www.manakonline.in & BIS CARE Mobile App",
        "statutory_provenance": "BIS Act 2016, Section 14; Bureau of Indian Standards Official Guidelines",
    },
}

# Canonical catalog of verified BIS Laboratories (Milestone M25.4E / Audit M25.4E.1)
VERIFIED_LABORATORIES_CATALOG: Dict[str, Dict[str, Any]] = {
    "CENTRAL_LABORATORY": {
        "lab_code": "BIS-CL",
        "name": "BIS Central Laboratory (CL)",
        "location": "Sahibabad, Ghaziabad, Uttar Pradesh (NCR)",
        "status": "BIS Owned & Operated Central Apex Laboratory",
        "scope": "Comprehensive multi-disciplinary testing: Electrical & Electronics, Mechanical, Chemical, Microbiological, Civil, and Textile disciplines.",
        "jurisdiction": "National Apex Laboratory",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "BIS Act 2016, Section 32; BIS Laboratory Network",
        "verification_status": "VERIFIED",
        "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
        "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory; SHA256: 234fc422da85adabad202f7d27fe923654c435533621469958212499c52f1b97)",
        "authenticity": "AUTHENTIC_BIS_SOURCE",
        "current_recognition_status": "OPERATIVE_RECOGNIZED",
        "testing_scope": "Comprehensive multi-disciplinary testing: Electrical & Electronics, Mechanical, Chemical, Microbiological, Civil, and Textile disciplines.",
        "audit_notes": "Authoritative BIS source confirmed in acquired corpus manifest with matching SHA-256 and operative apex status under BIS Act 2016 Section 32.",
        "provenance_chain": {
            "laboratory": "BIS Central Laboratory (CL) [BIS-CL], Sahibabad Industrial Area, Ghaziabad, UP",
            "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
            "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory; SHA256: 234fc422da85adabad202f7d27fe923654c435533621469958212499c52f1b97)",
            "authenticity": "AUTHENTIC_BIS_SOURCE",
            "current_recognition_status": "OPERATIVE_RECOGNIZED",
            "testing_scope": "Comprehensive multi-disciplinary testing: Electrical & Electronics, Mechanical, Chemical, Microbiological, Civil, and Textile disciplines.",
        },
    },
    "WESTERN_REGIONAL_LABORATORY": {
        "lab_code": "BIS-WRL",
        "name": "BIS Western Regional Laboratory (WRL)",
        "location": "Andheri (East), Mumbai, Maharashtra",
        "status": "BIS Owned & Operated Regional Laboratory",
        "scope": "Electrical appliances, Electronics, Chemical products, Plastics, Food & Agro testing, Mechanical materials.",
        "jurisdiction": "Western Region (Maharashtra, Gujarat, Goa, Madhya Pradesh)",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "BIS Act 2016, Section 32; BIS Regional Laboratory Network",
        "verification_status": "VERIFIED",
        "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
        "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory; SHA256: 234fc422da85adabad202f7d27fe923654c435533621469958212499c52f1b97)",
        "authenticity": "AUTHENTIC_BIS_SOURCE",
        "current_recognition_status": "OPERATIVE_RECOGNIZED",
        "testing_scope": "Electrical appliances, Electronics, Chemical products, Plastics, Food & Agro testing, Mechanical materials.",
        "audit_notes": "Authoritative BIS source confirmed in acquired corpus manifest with matching SHA-256 and operative regional status.",
        "provenance_chain": {
            "laboratory": "BIS Western Regional Laboratory (WRL) [BIS-WRL], Manakalaya, Andheri (East), Mumbai",
            "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
            "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory)",
            "authenticity": "AUTHENTIC_BIS_SOURCE",
            "current_recognition_status": "OPERATIVE_RECOGNIZED",
            "testing_scope": "Electrical appliances, Electronics, Chemical products, Plastics, Food & Agro testing, Mechanical materials.",
        },
    },
    "SOUTHERN_REGIONAL_LABORATORY": {
        "lab_code": "BIS-SRL",
        "name": "BIS Southern Regional Laboratory (SRL)",
        "location": "CIT Campus, Taramani, Chennai, Tamil Nadu",
        "status": "BIS Owned & Operated Regional Laboratory",
        "scope": "Domestic electrical appliances, Electronics, Motors & Pumps, Cables, Chemical analysis.",
        "jurisdiction": "Southern Region (Tamil Nadu, Karnataka, Kerala, Andhra Pradesh, Telangana)",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "BIS Act 2016, Section 32; BIS Regional Laboratory Network",
        "verification_status": "VERIFIED",
        "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
        "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory; SHA256: 234fc422da85adabad202f7d27fe923654c435533621469958212499c52f1b97)",
        "authenticity": "AUTHENTIC_BIS_SOURCE",
        "current_recognition_status": "OPERATIVE_RECOGNIZED",
        "testing_scope": "Domestic electrical appliances, Electronics, Motors & Pumps, Cables, Chemical analysis.",
        "audit_notes": "Authoritative BIS source confirmed in acquired corpus manifest with matching SHA-256 and operative regional status.",
        "provenance_chain": {
            "laboratory": "BIS Southern Regional Laboratory (SRL) [BIS-SRL], CIT Campus, Taramani, Chennai",
            "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
            "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory)",
            "authenticity": "AUTHENTIC_BIS_SOURCE",
            "current_recognition_status": "OPERATIVE_RECOGNIZED",
            "testing_scope": "Domestic electrical appliances, Electronics, Motors & Pumps, Cables, Chemical analysis.",
        },
    },
    "EASTERN_REGIONAL_LABORATORY": {
        "lab_code": "BIS-ERL",
        "name": "BIS Eastern Regional Laboratory (ERL)",
        "location": "Salt Lake, Sector V, Kolkata, West Bengal",
        "status": "BIS Owned & Operated Regional Laboratory",
        "scope": "Metallurgy, Iron & Steel products, Mechanical testing, Chemical analysis, Electrical accessories.",
        "jurisdiction": "Eastern Region (West Bengal, Odisha, Bihar, Jharkhand, North-East)",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "BIS Act 2016, Section 32; BIS Regional Laboratory Network",
        "verification_status": "VERIFIED",
        "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
        "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory; SHA256: 234fc422da85adabad202f7d27fe923654c435533621469958212499c52f1b97)",
        "authenticity": "AUTHENTIC_BIS_SOURCE",
        "current_recognition_status": "OPERATIVE_RECOGNIZED",
        "testing_scope": "Metallurgy, Iron & Steel products, Mechanical testing, Chemical analysis, Electrical accessories.",
        "audit_notes": "Authoritative BIS source confirmed in acquired corpus manifest with matching SHA-256 and operative regional status.",
        "provenance_chain": {
            "laboratory": "BIS Eastern Regional Laboratory (ERL) [BIS-ERL], Salt Lake, Sector V, Kolkata",
            "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
            "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory)",
            "authenticity": "AUTHENTIC_BIS_SOURCE",
            "current_recognition_status": "OPERATIVE_RECOGNIZED",
            "testing_scope": "Metallurgy, Iron & Steel products, Mechanical testing, Chemical analysis, Electrical accessories.",
        },
    },
    "NORTHERN_REGIONAL_LABORATORY": {
        "lab_code": "BIS-NRL",
        "name": "BIS Northern Regional Laboratory (NRL)",
        "location": "Mohali, Punjab",
        "status": "BIS Owned & Operated Regional Laboratory",
        "scope": "Mechanical testing, Building & Construction materials, Chemical analysis, Electrical safety.",
        "jurisdiction": "Northern Region (Punjab, Haryana, Himachal Pradesh, Jammu & Kashmir, Rajasthan)",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "BIS Act 2016, Section 32; BIS Regional Laboratory Network",
        "verification_status": "VERIFIED",
        "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
        "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory; SHA256: 234fc422da85adabad202f7d27fe923654c435533621469958212499c52f1b97)",
        "authenticity": "AUTHENTIC_BIS_SOURCE",
        "current_recognition_status": "OPERATIVE_RECOGNIZED",
        "testing_scope": "Mechanical testing, Building & Construction materials, Chemical analysis, Electrical safety.",
        "audit_notes": "Authoritative BIS source confirmed in acquired corpus manifest with matching SHA-256 and operative regional status.",
        "provenance_chain": {
            "laboratory": "BIS Northern Regional Laboratory (NRL) [BIS-NRL], Mohali, Punjab",
            "official_bis_source": "Bureau of Indian Standards Official Laboratory Directory (https://www.bis.gov.in/directory/laboratory/?lang=hi); BIS Act 2016, Section 32",
            "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory)",
            "authenticity": "AUTHENTIC_BIS_SOURCE",
            "current_recognition_status": "OPERATIVE_RECOGNIZED",
            "testing_scope": "Mechanical testing, Building & Construction materials, Chemical analysis, Electrical safety.",
        },
    },
    "BRANCH_LABORATORIES": {
        "lab_code": "BIS-BRANCH-NET",
        "name": "BIS Branch Laboratories Network",
        "location": "Bengaluru (Peenya, Karnataka), Guwahati (Assam), Patna (Bihar)",
        "status": "BIS Owned & Operated Branch Laboratories (Verification Required for Specific Testing Scopes)",
        "scope": "Targeted physical, chemical, and electrical conformity testing (Specific clause-level schedule verification required on LIMS).",
        "jurisdiction": "Zonal Branch Laboratories",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "BIS Act 2016, Section 32",
        "verification_status": "VERIFICATION_REQUIRED",
        "official_bis_source": "Bureau of Indian Standards Branch Office Directory (https://www.bis.gov.in/branch-office/?lang=hi)",
        "source_version_date": "2026-09-12T17:34:35+00:00 (Corpus Manifest: LABORATORIES_प_रय_गश_ल_laboratory)",
        "authenticity": "AUTHENTIC_BIS_SOURCE",
        "current_recognition_status": "VERIFICATION_REQUIRED",
        "testing_scope": "UNVERIFIED / VERIFICATION_REQUIRED (Specific branch testing scopes not individually codified in acquired authoritative source)",
        "audit_notes": "Downgraded to VERIFICATION_REQUIRED: Acquired corpus contains aggregate branch listing but lacks individual accredited testing schedules and clause-level scopes. Specific branch recognition and testing capability must be verified on official LIMS portal.",
        "provenance_chain": {
            "laboratory": "BIS Branch Laboratories Network [BIS-BRANCH-NET]",
            "official_bis_source": "Bureau of Indian Standards Branch Office Directory (https://www.bis.gov.in/branch-office/?lang=hi)",
            "source_version_date": "2026-09-12T17:34:35+00:00",
            "authenticity": "AUTHENTIC_BIS_SOURCE",
            "current_recognition_status": "VERIFICATION_REQUIRED",
            "testing_scope": "UNVERIFIED / VERIFICATION_REQUIRED",
        },
    },
    "SAMPLE_STALE_LABORATORY": {
        "lab_code": "BIS-STALE-TEST-099",
        "name": "National Testing House Stale Annex",
        "location": "Kolkata, West Bengal",
        "status": "Expired / Stale Recognition (Historical Listing Only)",
        "scope": "UNVERIFIED (Historical mechanical testing; current operative scope missing)",
        "jurisdiction": "Eastern Region",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "Historical Record TEST-SAVE-RELOAD-99 (Stale / Expired)",
        "verification_status": "UNVERIFIED",
        "official_bis_source": "Historical Listing (TEST-SAVE-RELOAD-99; https://www.bis.gov.in/lab.pdf)",
        "source_version_date": "2026-09-13 (Acquisition status: DISCOVERED; zero bytes; no valid sha256)",
        "authenticity": "STALE_OR_UNVERIFIED_SOURCE",
        "current_recognition_status": "EXPIRED / UNVERIFIED",
        "testing_scope": "UNVERIFIED / VERIFICATION_REQUIRED",
        "audit_notes": "Downgraded to UNVERIFIED / VERIFICATION_REQUIRED: Source is stale/expired. Authoritative evidence of current operative recognition is absent in the acquired BIS corpus. Current recognition and scope cannot be inferred.",
        "provenance_chain": {
            "laboratory": "National Testing House Stale Annex [BIS-STALE-TEST-099]",
            "official_bis_source": "Historical Listing (TEST-SAVE-RELOAD-99; https://www.bis.gov.in/lab.pdf)",
            "source_version_date": "2026-09-13 (Zero-byte unverified snapshot)",
            "authenticity": "STALE_OR_UNVERIFIED_SOURCE",
            "current_recognition_status": "EXPIRED / UNVERIFIED",
            "testing_scope": "UNVERIFIED / VERIFICATION_REQUIRED",
        },
    },
    "SAMPLE_UNVERIFIED_THIRD_PARTY": {
        "lab_code": "LAB-UNVERIFIED-ACME",
        "name": "Acme Industrial Testing Laboratory",
        "location": "Unknown / Third-Party Commercial",
        "status": "Unverified / Non-Recognized Commercial Facility",
        "scope": "UNVERIFIED",
        "jurisdiction": "Unregistered",
        "official_portal": "https://lims.bis.gov.in",
        "statutory_provenance": "None — Missing from Official BIS Directory",
        "verification_status": "UNVERIFIED",
        "official_bis_source": "None (Missing authoritative BIS source)",
        "source_version_date": "N/A",
        "authenticity": "MISSING_SOURCE",
        "current_recognition_status": "UNVERIFIED",
        "testing_scope": "UNVERIFIED",
        "audit_notes": "Downgraded to UNVERIFIED / VERIFICATION_REQUIRED: No authoritative BIS source exists in the acquired corpus. Not listed in official BIS LIMS database.",
        "provenance_chain": {
            "laboratory": "Acme Industrial Testing Laboratory [LAB-UNVERIFIED-ACME]",
            "official_bis_source": "None (Missing authoritative BIS source)",
            "source_version_date": "N/A",
            "authenticity": "MISSING_SOURCE",
            "current_recognition_status": "UNVERIFIED",
            "testing_scope": "UNVERIFIED",
        },
    },
}


# Canonical catalog of verified Testing Categories per Standard / Product (Milestone M25.4E)
VERIFIED_TESTING_CATEGORIES_CATALOG: Dict[str, Dict[str, Any]] = {
    "IS 302-2-201:2008": {
        "standard_number": "IS 302-2-201:2008",
        "product_name": "Electric Immersion Water Heater",
        "governing_qco": "Electrical Appliances (Quality Control) Order",
        "testing_categories": [
            {
                "category": "Electrical Safety Testing",
                "clauses": "Clause 8 (Protection against electric shock), Clause 10 (Power input and current), Clause 13 (Leakage current and dielectric strength at operating temperature), Clause 29 (Creepage distances, clearances and solid insulation)",
                "description": "Verifies electrical shock safety under standard test finger probing, leakage current <= 0.75 mA, and dielectric withstand without breakdown.",
            },
            {
                "category": "Thermal & Abnormal Performance Testing",
                "clauses": "Clause 11 (Heating / Temperature rise test), Clause 19 (Abnormal operation / Dry boiling test)",
                "description": "Evaluates maximum temperature rise on handles and terminals, and safety cutoff performance during dry-boil conditions.",
            },
            {
                "category": "Mechanical Integrity & Construction Testing",
                "clauses": "Clause 20 (Stability and mechanical hazards), Clause 21 (Mechanical strength / impact resistance)",
                "description": "Ensures structural rigidity against spring hammer impacts and mechanical drops.",
            },
            {
                "category": "Moisture Resistance & Corrosion Testing",
                "clauses": "Clause 15 (Moisture resistance), Clause 31 (Resistance to rusting / corrosion of immersion heating sheath)",
                "description": "Assesses sheath durability against continuous water immersion and humidity exposure.",
            },
        ],
    },
    "IS 17526:2021": {
        "standard_number": "IS 17526:2021",
        "product_name": "Stainless Steel Vacuum Flask",
        "governing_qco": "Domestic Water Bottles / Insulated Flasks QCO",
        "testing_categories": [
            {
                "category": "Thermal Performance Testing",
                "clauses": "Clause 5.1 & Clause 6.2 (Heat retention and cold insulation test)",
                "description": "Evaluates temperature retention after 6 hours (minimum 65 deg C) and 24 hours (minimum 40 deg C).",
            },
            {
                "category": "Mechanical Durability & Impact Testing",
                "clauses": "Clause 6.3 (Impact drop test), Clause 6.4 (Handle, strap, and knob attachment strength)",
                "description": "Assesses vessel integrity and vacuum seal survival following free-fall impact drops.",
            },
            {
                "category": "Stopper Leakage & Seal Integrity Testing",
                "clauses": "Clause 6.1 (Stopper leakage and tilt test)",
                "description": "Verifies that the stopper closure prevents liquid leakage under inverted and tilted positions.",
            },
            {
                "category": "Food Contact & Chemical Migration Safety",
                "clauses": "Clause 4.2 (Food-grade contact material compatibility conforming to IS 9845 / overall migration)",
                "description": "Tests for non-toxicity and chemical inertness of inner steel liner and silicone gasket seals.",
            },
        ],
    },
    "IS 4151:2020": {
        "standard_number": "IS 4151:2020",
        "product_name": "Two-Wheeler Protective Helmet",
        "governing_qco": "Helmet for Two-Wheeler Riders (Quality Control) Order",
        "testing_categories": [
            {
                "category": "Impact Shock Absorption Attenuation Testing",
                "clauses": "Clause 7.2 (Impact absorption test under ambient, heat, cold, and water immersion conditioning)",
                "description": "Drop-tower impact testing onto flat and kerbstone anvils measuring peak headform acceleration (<= 300g).",
            },
            {
                "category": "Dynamic Retention System & Chin Strap Testing",
                "clauses": "Clause 7.3 & Clause 7.4 (Dynamic retention test and quick-release slippage)",
                "description": "Measures dynamic extension and permanent displacement under statutory drop-weight loads.",
            },
            {
                "category": "Peripheral Vision & Physical Clearance Testing",
                "clauses": "Clause 7.5 (Field of vision angle check: horizontal >= 105 deg each side, vertical clearances)",
                "description": "Verifies unobstructed peripheral visibility and auditory penetration.",
            },
        ],
    },
    "IS 13252 (Part 1):2010": {
        "standard_number": "IS 13252 (Part 1):2010",
        "product_name": "Information Technology Equipment (Laptops, Servers, Adapters)",
        "governing_qco": "Electronics and Information Technology Goods (Compulsory Registration) Order",
        "testing_categories": [
            {
                "category": "Electrical Shock & Dielectric Breakdown Testing",
                "clauses": "Clause 2.1 (Operator access protection), Clause 5.2 (High voltage withstand at 3000V AC)",
                "description": "Tests insulation strength between primary mains and accessible secondary SELV circuits.",
            },
            {
                "category": "Touch Current & Earth Continuity Testing",
                "clauses": "Clause 2.6 (Protective earthing continuity), Clause 5.1 (Touch current limits)",
                "description": "Ensures earth bond resistance <= 0.1 ohm and touch leakage current within safe physiological limits.",
            },
            {
                "category": "Fire Hazard & Enclosure Flammability Testing",
                "clauses": "Clause 4.7 (Flammability of polymeric enclosures conforming to UL94/V-0, V-1)",
                "description": "Verifies resistance of external plastic casings against ignition and flame spread.",
            },
        ],
    },
    "IS 1417:2016": {
        "standard_number": "IS 1417:2016",
        "product_name": "Gold Jewellery & Artefacts",
        "governing_qco": "Hallmarking of Gold Jewellery and Gold Artefacts Order",
        "testing_categories": [
            {
                "category": "Non-Destructive Alloy Screening",
                "clauses": "Clause 6.1 (X-ray Fluorescence / XRF Spectrometry screening)",
                "description": "Multi-point surface composition analysis of gold, silver, copper, and zinc proportions.",
            },
            {
                "category": "Confirmatory Fire Assay / Cupellation Testing",
                "clauses": "Clause 6.1 (Fire assay / cupellation conforming to IS 1418)",
                "description": "Definitive chemical assaying measuring exact gold fineness to an accuracy of 0.1 parts per thousand.",
            },
        ],
    },
    "IS 1786:2008": {
        "standard_number": "IS 1786:2008",
        "product_name": "High Strength Deformed Steel Bars & Wires",
        "governing_qco": "Steel and Steel Products (Quality Control) Order",
        "testing_categories": [
            {
                "category": "Mechanical Tensile & Yield Strength Testing",
                "clauses": "Clause 8.1 (0.2% Proof stress / Yield stress, Tensile strength, and Percentage elongation)",
                "description": "Tensile testing ensuring Fe 500D yield strength >= 500 N/mm2 and elongation >= 16%.",
            },
            {
                "category": "Bend & Rebend Ductility Testing",
                "clauses": "Clause 9.3 & Clause 9.4 (Cold bend and rebend around cylindrical mandrel)",
                "description": "Verifies surface ductility without rupture or transverse cracking.",
            },
            {
                "category": "Chemical Composition Analysis",
                "clauses": "Clause 4.2 (Carbon, Sulphur, and Phosphorus concentration limits)",
                "description": "Optical emission spectrometry ensuring controlled carbon equivalent for weldability.",
            },
        ],
    },
    "IS 8112:2013": {
        "standard_number": "IS 8112:2013",
        "product_name": "43 Grade Ordinary Portland Cement",
        "governing_qco": "Cement (Quality Control) Order",
        "testing_categories": [
            {
                "category": "Compressive Strength Testing",
                "clauses": "Clause 6.1 (Compressive strength of mortar cubes at 3, 7, and 28 days)",
                "description": "Tests 28-day compressive strength (minimum 43.0 MPa) using standard Ennore sand.",
            },
            {
                "category": "Physical Fineness & Setting Time Testing",
                "clauses": "Clause 5.1 (Blaine air permeability fineness, Vicat initial and final setting times, Le Chatelier soundness)",
                "description": "Measures specific surface (>= 225 m2/kg), initial set (>= 30 min), and expansion soundness (<= 10 mm).",
            },
            {
                "category": "Chemical Composition Testing",
                "clauses": "Clause 5.2 (Lime saturation factor, Insoluble residue, Magnesia, Loss on ignition)",
                "description": "Ensures chemical purity and limits harmful impurities.",
            },
        ],
    },
}

# Canonical catalog of verified BIS Laboratory Guidance Topics (Milestone M25.4E)
VERIFIED_LABORATORY_TOPICS: Dict[str, Dict[str, Any]] = {
    "LABORATORY_DISCOVERY": {
        "topic": "LABORATORY_DISCOVERY",
        "title": "BIS-Recognized Laboratory Discovery & Testing Infrastructure",
        "instructions": (
            "**Finding BIS-Recognized Testing Laboratories**:\n"
            "1. **BIS In-House Laboratories Network**:\n"
            "   - **Central Laboratory (CL)**: Sahibabad, Ghaziabad (National multi-disciplinary apex testing facility).\n"
            "   - **Western Regional Lab (WRL)**: Mumbai, Maharashtra (Electrical, mechanical, chemical, food).\n"
            "   - **Southern Regional Lab (SRL)**: Chennai, Tamil Nadu (Electrical appliances, electronics, motors, chemical).\n"
            "   - **Eastern Regional Lab (ERL)**: Kolkata, West Bengal (Metallurgy, steel, chemical, mechanical).\n"
            "   - **Northern Regional Lab (NRL)**: Mohali, Punjab (Mechanical, building materials, chemical, electrical).\n"
            "   - **Branch Labs**: Bengaluru (Peenya), Guwahati, Patna.\n\n"
            "2. **Recognized Third-Party Laboratories Network**:\n"
            "   - Over 200 external commercial, institutional, and government laboratories are recognized under the **BIS Laboratory Recognition Scheme (LRS)**.\n"
            "   - All recognized laboratories must hold formal **NABL accreditation under ISO/IEC 17025**.\n\n"
            "3. **Official Public Directory Access**:\n"
            "   - Visit the official **BIS LIMS Portal**: `https://lims.bis.gov.in`\n"
            "   - Access via Manakonline (`www.manakonline.in`) under **'Conformity Assessment' -> 'Laboratory Directory'**.\n"
            "   - Search dynamically by: **Indian Standard (IS number)**, **Product Name**, or **State / City**."
        ),
        "official_portal": "https://lims.bis.gov.in & www.manakonline.in",
        "statutory_provenance": "BIS Act 2016, Section 13 & Section 32; BIS (Laboratory Recognition Scheme) Regulations, 2020",
    },
    "LABORATORY_RECOGNITION_STATUS": {
        "topic": "LABORATORY_RECOGNITION_STATUS",
        "title": "Verifying a Laboratory's BIS Recognition Status",
        "instructions": (
            "**How to Authenticate a Laboratory's BIS Recognition Status**:\n"
            "1. **Access the Official BIS LIMS Portal**: Open `https://lims.bis.gov.in` and navigate to **'Search Laboratory'**.\n"
            "2. **Verify Operative Status**:\n"
            "   - **Operative / Recognized**: The laboratory holds an active, valid BIS recognition certificate.\n"
            "   - **Suspended**: The laboratory is temporarily debarred from statutory sample testing.\n"
            "   - **Expired / Derecognized**: Test reports from this laboratory will NOT be accepted by BIS.\n"
            "3. **Verify Specific Scope of Recognition**:\n"
            "   - Recognition is NOT generic; it is strictly granted for specific Indian Standards (IS), specific product categories, and specific test parameters.\n"
            "   - Download the official scope schedule from LIMS and confirm that the exact IS standard (e.g. IS 302-2-201, IS 17526) is explicitly listed.\n"
            "4. **ISO/IEC 17025 Accreditation**:\n"
            "   - Cross-verify the laboratory's NABL accreditation validity period on `www.nabl-india.org`."
        ),
        "official_portal": "https://lims.bis.gov.in & www.nabl-india.org",
        "statutory_provenance": "BIS (Laboratory Recognition Scheme) Regulations, 2020, Regulation 4 & 5; ISO/IEC 17025:2017",
    },
    "TESTING_CATEGORY_GUIDANCE": {
        "topic": "TESTING_CATEGORY_GUIDANCE",
        "title": "Mandatory Testing Categories Under Codified Indian Standards",
        "instructions": (
            "**Testing Category Framework Under Indian Standards**:\n"
            "Conformity assessment testing is divided into deterministic, standardized categories:\n"
            "1. **Electrical Safety & Insulation**: Leakage current, dielectric withstand, earth continuity, clearance/creepage distances, and shock protection under IEC/IS safety norms.\n"
            "2. **Mechanical Performance & Durability**: Tensile strength, impact absorption, drop test, burst pressure, fatigue resistance, and structural stability.\n"
            "3. **Thermal & Environmental Withstand**: Temperature rise, heating under abnormal operating conditions, dry boil withstand, moisture and ingress resistance.\n"
            "4. **Chemical & Material Composition**: Spectrometric alloy assay, migration of toxic metals (for food-contact items), and corrosion resistance of metallic components.\n\n"
            "*All tests must be conducted strictly in accordance with test methods prescribed in the respective Indian Standard.*"
        ),
        "official_portal": "Bureau of Indian Standards Official Gazette & Technical Specifications",
        "statutory_provenance": "BIS (Conformity Assessment) Regulations, 2018, Schedule II; Bureau of Indian Standards",
    },
    "AVAILABLE_LABORATORY_INFORMATION": {
        "topic": "AVAILABLE_LABORATORY_INFORMATION",
        "title": "Available Official BIS Laboratory Records & Attributes",
        "instructions": (
            "**Governed Laboratory Attributes Available in Official Records**:\n"
            "1. **Laboratory Identification**: Official legal name, laboratory registration/recognition code, and ownership category (BIS Owned vs. Third-Party Recognized).\n"
            "2. **Geographic Location**: Registered physical address, city, state, regional branch jurisdiction, and contact coordinates.\n"
            "3. **Recognition Status**: Operative recognition status, recognition certificate issue date, and expiry/renewal timeline.\n"
            "4. **Approved Testing Scope**: Exact list of codified Indian Standards (IS), product categories, and specific test parameters authorized by BIS.\n"
            "5. **Accreditation Provenance**: NABL accreditation certificate number and validity under ISO/IEC 17025.\n\n"
            "*Notice*: Commercial pricing, fee schedules, sample delivery turnaround times, and booking availability are NOT governed by BIS public records; applicants must contact the recognized laboratory directly."
        ),
        "official_portal": "https://lims.bis.gov.in (BIS LIMS Portal)",
        "statutory_provenance": "BIS Act 2016, Section 32; BIS (Laboratory Recognition Scheme) Regulations, 2020",
    },
}

verified_knowledge_selector = VerifiedKnowledgeSelector()



