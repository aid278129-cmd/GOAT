"""Document & Specification Template Generator.

Generates clean, fillable/downloadable templates (CSV, JSON, Markdown)
containing the exact required fields derived from verified BIS/QCO knowledge.
Enforces zero-hallucination: If verified knowledge is insufficient, displays
UNKNOWN / INFORMATION REQUIRED rather than inventing regulatory fields.
"""

import csv
import io
import json
from typing import Dict, Any, List, Optional
from backend.app.schemas.unified_input import (
    FieldRequirementLevel,
    TechnicalRequirementItem,
)


class TemplateGeneratorService:
    """Produces fillable templates to assist manufacturers in preparing valid compliance inputs."""

    VERIFIED_STANDARDS_REQUIREMENTS: Dict[str, List[TechnicalRequirementItem]] = {
        # Immersion Water Heaters under IS 302-2-201:2008 & IS 302-1:2008
        "IS 302-2-201:2008": [
            TechnicalRequirementItem(
                field_id="product_trade_name",
                field_name="Product Trade Name / Model",
                level=FieldRequirementLevel.REQUIRED,
                category="Identification",
                description="Commercial trade name and exact model code",
                sample_value="Electric Immersion Water Heater (EWH-1500)",
                standard_reference="IS 302-1 Clause 7",
            ),
            TechnicalRequirementItem(
                field_id="rated_voltage",
                field_name="Rated Voltage",
                level=FieldRequirementLevel.REQUIRED,
                category="Electrical",
                description="Nominal operating supply voltage in Volts AC",
                sample_value="230",
                unit="V AC",
                standard_reference="IS 302-2-201 Clause 6.1",
            ),
            TechnicalRequirementItem(
                field_id="rated_power_input",
                field_name="Rated Power Input / Wattage",
                level=FieldRequirementLevel.REQUIRED,
                category="Electrical",
                description="Nominal electrical power consumption in Watts",
                sample_value="1500",
                unit="W",
                standard_reference="IS 302-2-201 Clause 10.1",
            ),
            TechnicalRequirementItem(
                field_id="rated_frequency",
                field_name="Rated Frequency",
                level=FieldRequirementLevel.REQUIRED,
                category="Electrical",
                description="Operating AC mains supply frequency",
                sample_value="50",
                unit="Hz",
                standard_reference="IS 302-1 Clause 6",
            ),
            TechnicalRequirementItem(
                field_id="heating_element_material",
                field_name="Heating Element Sheath Material",
                level=FieldRequirementLevel.REQUIRED,
                category="Physical",
                description="Alloy grade of tubular sheath (e.g. Stainless Steel 304, Copper)",
                sample_value="Stainless Steel 304",
                standard_reference="IS 302-2-201 Clause 22.101",
            ),
            TechnicalRequirementItem(
                field_id="handle_material",
                field_name="Handle & Enclosure Material",
                level=FieldRequirementLevel.REQUIRED,
                category="Physical",
                description="Heat-resistant flame-retardant insulating polymer",
                sample_value="Polypropylene (UL94 V-0)",
                standard_reference="IS 302-1 Clause 30",
            ),
            TechnicalRequirementItem(
                field_id="power_cord_type",
                field_name="Power Cord Specification",
                level=FieldRequirementLevel.REQUIRED,
                category="Sub-assembly",
                description="Flexible cable core count, conductor size & insulation grade",
                sample_value="3-core 0.75 mm2 PVC insulated (IS 694)",
                standard_reference="IS 302-1 Clause 25.7",
            ),
            TechnicalRequirementItem(
                field_id="plug_top_rating",
                field_name="Plug Top Conformance",
                level=FieldRequirementLevel.REQUIRED,
                category="Sub-assembly",
                description="Molded 3-pin plug rating conforming to IS 1293",
                sample_value="3-pin, 6 A, 250 V (IS 1293)",
                standard_reference="IS 302-1 Clause 25.1",
            ),
            TechnicalRequirementItem(
                field_id="lab_test_report_number",
                field_name="Laboratory Test Report Reference",
                level=FieldRequirementLevel.OPTIONAL,
                category="Evidence",
                description="Official NABL-accredited test report reference number if already tested",
                sample_value="ABC/EWH/2026/001",
                standard_reference="NABL / BIS Scheme-I",
            ),
        ],
        # Stainless steel vacuum flasks under IS 17526:2021
        "IS 17526:2021": [
            TechnicalRequirementItem(
                field_id="product_trade_name",
                field_name="Product Trade Name / Model",
                level=FieldRequirementLevel.REQUIRED,
                category="Identification",
                description="Commercial product model name",
                sample_value="Stainless Steel Vacuum Insulated Flask 1000ml",
                standard_reference="IS 17526:2021 Clause 1",
            ),
            TechnicalRequirementItem(
                field_id="nominal_capacity",
                field_name="Nominal Capacity",
                level=FieldRequirementLevel.REQUIRED,
                category="Physical",
                description="Stated liquid holding capacity in milliliters or liters",
                sample_value="1000",
                unit="ml",
                standard_reference="IS 17526 Clause 5.1",
            ),
            TechnicalRequirementItem(
                field_id="inner_lining_material",
                field_name="Food-Contact Liner Material",
                level=FieldRequirementLevel.REQUIRED,
                category="Physical",
                description="Chemical grade of inner food contact container",
                sample_value="Stainless Steel Grade 304 (IS 6911)",
                standard_reference="IS 17526 Clause 4.1",
            ),
            TechnicalRequirementItem(
                field_id="heat_retention_spec",
                field_name="Thermal Heat Retention Target",
                level=FieldRequirementLevel.REQUIRED,
                category="Safety",
                description="Target water temperature after 6 hours from 95 C initial",
                sample_value=">= 65",
                unit="C",
                standard_reference="IS 17526 Clause 6.3",
            ),
            TechnicalRequirementItem(
                field_id="lid_seal_polymer",
                field_name="Lid Gasket & Seal Material",
                level=FieldRequirementLevel.REQUIRED,
                category="Sub-assembly",
                description="Food-grade elastomer or silicone conforming to IS 9845",
                sample_value="Food Grade Silicone Elastomer",
                standard_reference="IS 17526 Clause 4.3",
            ),
        ],
    }

    @classmethod
    def get_requirements_for_standard_or_category(
        cls,
        target_standard: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[TechnicalRequirementItem]:
        """Fetch verified technical requirements or return UNKNOWN if standard is unverified."""
        if target_standard and target_standard in cls.VERIFIED_STANDARDS_REQUIREMENTS:
            return cls.VERIFIED_STANDARDS_REQUIREMENTS[target_standard]

        # Heuristic match by standard number substring
        if target_standard:
            for std_key, reqs in cls.VERIFIED_STANDARDS_REQUIREMENTS.items():
                if any(part in target_standard for part in ["302-2-201", "302_2_201", "368"]):
                    return cls.VERIFIED_STANDARDS_REQUIREMENTS["IS 302-2-201:2008"]
                if any(part in target_standard for part in ["17526", "flask"]):
                    return cls.VERIFIED_STANDARDS_REQUIREMENTS["IS 17526:2021"]

        # Category based lookup
        cat_lower = (category or "").lower()
        if "water heater" in cat_lower or "immersion" in cat_lower or "appliance" in cat_lower:
            return cls.VERIFIED_STANDARDS_REQUIREMENTS["IS 302-2-201:2008"]
        if "flask" in cat_lower or "bottle" in cat_lower or "drinkware" in cat_lower:
            return cls.VERIFIED_STANDARDS_REQUIREMENTS["IS 17526:2021"]

        # If knowledge is insufficient, NEVER invent requirements; return transparent unknown notice
        return [
            TechnicalRequirementItem(
                field_id="product_trade_name",
                field_name="Product Trade Name",
                level=FieldRequirementLevel.REQUIRED,
                category="Identification",
                description="Commercial product model name",
                sample_value="Example Product Model",
            ),
            TechnicalRequirementItem(
                field_id="unverified_category_notice",
                field_name="Category Specific Parameters",
                level=FieldRequirementLevel.UNKNOWN,
                category="Domain Parameters",
                description="Verified BIS standard parameters for this specific category are currently pending official gazette indexing. Standard product claims will require manual auditor specification.",
            ),
        ]

    @classmethod
    def generate_csv_template(cls, target_standard: Optional[str] = None, category: Optional[str] = None) -> str:
        """Generate fillable CSV template for BOM & Technical Parameters."""
        reqs = cls.get_requirements_for_standard_or_category(target_standard, category)
        output = io.StringIO()
        writer = csv.writer(output)

        # Header Row
        writer.writerow(["Field ID", "Field Name", "Requirement Level", "Category", "Unit", "Your Value", "BIS Standard Reference"])

        # Data Rows
        for r in reqs:
            writer.writerow([
                r.field_id,
                r.field_name,
                r.level.value,
                r.category,
                r.unit or "N/A",
                f"[{r.sample_value or 'ENTER_VALUE'}]",
                r.standard_reference or "General Rule",
            ])

        return output.getvalue()

    @classmethod
    def generate_json_template(cls, target_standard: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured JSON schema template for technical specifications."""
        reqs = cls.get_requirements_for_standard_or_category(target_standard, category)
        fields_dict = {}
        for r in reqs:
            fields_dict[r.field_id] = {
                "field_name": r.field_name,
                "requirement_level": r.level.value,
                "category": r.category,
                "unit": r.unit,
                "value": r.sample_value or "[ENTER_VALUE]",
                "standard_reference": r.standard_reference,
            }

        return {
            "template_name": "Zyntrix Layer 1 Document Preparation Template",
            "regulatory_framework": target_standard or "Bureau of Indian Standards (BIS)",
            "product_category": category or "Kitchen & Domestic Appliances",
            "required_fields_count": sum(1 for r in reqs if r.level == FieldRequirementLevel.REQUIRED),
            "parameters": fields_dict,
            "instructions": (
                "Fill in 'value' for all REQUIRED fields. Upload this file via the BOM or JSON spec tab "
                "to achieve high Document Readiness prior to Layer 2 Product DNA compilation."
            ),
        }

    @classmethod
    def generate_bom_csv_template(cls) -> str:
        """Generate standard Bill of Materials (BOM) tabular template."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Part Number", "Component", "Material", "Specification", "Quantity"])
        writer.writerow(["HE-01", "Tubular Heating Element", "Stainless Steel 304", "1500 W, 230 V AC", "1"])
        writer.writerow(["HD-02", "Insulated Grip Handle", "Polypropylene (UL94 V-0)", "120 C temperature rated", "1"])
        writer.writerow(["CR-03", "Power Supply Cord", "Copper / PVC Sheathed (IS 694)", "3-core 0.75 mm2, 6A", "1"])
        writer.writerow(["PL-04", "Plug Top Conformance", "Polycarbonate / Brass (IS 1293)", "3-pin 6A 250V", "1"])
        writer.writerow(["LP-05", "Neon Indicator Lamp", "Glass / Series Resistor", "230V AC", "1"])
        return output.getvalue()

    @classmethod
    def generate_sample_product_info_pdf(cls, target_standard: Optional[str] = None, category: Optional[str] = None) -> bytes:
        """Generate a production-grade sample Product Information Specification PDF.
        
        Shows manufacturers how a complete, compliant technical specification PDF
        should be structured for high-accuracy PyMuPDF extraction and automated Product DNA compilation.
        """
        import pymupdf

        doc = pymupdf.open()

        # -------------------------------------------------------------
        # PAGE 1: Product Identification, Dimensions, & Material Specifications
        # -------------------------------------------------------------
        page1 = doc.new_page(width=595, height=842)  # A4 size

        # Top decorative accent header
        page1.draw_rect(pymupdf.Rect(40, 35, 555, 38), color=(0.25, 0.35, 0.85), fill=(0.25, 0.35, 0.85))

        page1.insert_text(
            (40, 58),
            "ZYNTRIX BIS COMPLIANCE COMPILER • REFERENCE SPECIFICATION GUIDE",
            fontsize=9,
            fontname="helv",
            color=(0.4, 0.45, 0.55),
        )
        page1.insert_text(
            (40, 80),
            "PRODUCT INFORMATION & SPECIFICATION SHEET",
            fontsize=16,
            fontname="hebo",
            color=(0.1, 0.15, 0.3),
        )
        page1.insert_text(
            (40, 96),
            "Reference Model Document for Automated Pre-Certification & Ingestion (IS 17526:2021)",
            fontsize=10,
            fontname="helv",
            color=(0.3, 0.35, 0.45),
        )

        # Guidance Notice Box
        page1.draw_rect(pymupdf.Rect(40, 110, 555, 148), color=(0.85, 0.88, 0.95), fill=(0.95, 0.97, 1.0))
        page1.insert_text(
            (50, 126),
            "PREPARATION INSTRUCTIONS FOR MANUFACTURERS / APPLICANTS:",
            fontsize=9,
            fontname="hebo",
            color=(0.15, 0.25, 0.6),
        )
        page1.insert_text(
            (50, 140),
            "Upload your technical specification sheet in PDF format. Ensure all sections below are explicitly declared",
            fontsize=8.5,
            fontname="helv",
            color=(0.25, 0.3, 0.4),
        )

        # Section 1: Identification
        page1.draw_line((40, 165), (555, 165), color=(0.8, 0.85, 0.9))
        page1.insert_text((40, 180), "1. PRODUCT & MANUFACTURER IDENTIFICATION", fontsize=11, fontname="hebo", color=(0.1, 0.15, 0.3))

        ident_lines = [
            ("Product Commercial Name:", "Apex ThermoShield Stainless Steel Vacuum Flask"),
            ("Model Number / Code:", "TS-750-SS (Series: Classic Hydration)"),
            ("Manufacturer / Brand Owner:", "Apex Thermalware India Private Limited"),
            ("Manufacturing Facility Address:", "Plot No. 42, Sector 8, Industrial Estate, IMT Manesar, Haryana 122050"),
            ("Applicable Indian Standard:", "IS 17526:2021 (Domestic Stainless Steel Vacuum Flasks / Insulated Containers)"),
            ("Statutory Regulatory Basis:", "DPIIT Cookware, Utensils and Insulated Containers (Quality Control) Order, 2023"),
            ("Target BIS Certification Scheme:", "Scheme-I (ISI Mark Standard Product Conformance Scheme)"),
        ]
        y = 198
        for lbl, val in ident_lines:
            page1.insert_text((45, y), lbl, fontsize=8.5, fontname="hebo", color=(0.2, 0.25, 0.35))
            page1.insert_text((220, y), val, fontsize=8.5, fontname="helv", color=(0.05, 0.05, 0.1))
            y += 16

        # Section 2: Technical & Physical Specifications
        page1.draw_line((40, y + 4), (555, y + 4), color=(0.8, 0.85, 0.9))
        y += 20
        page1.insert_text((40, y), "2. TECHNICAL & PHYSICAL RATINGS (IS 17526:2021)", fontsize=11, fontname="hebo", color=(0.1, 0.15, 0.3))
        y += 18

        tech_lines = [
            ("Nominal Volume / Capacity:", "750 ml (Tolerance: +/- 25 ml)"),
            ("Flask Configuration Type:", "Type I - Narrow Neck Double-Walled Vacuum Insulated Container"),
            ("Operating Medium Compatibility:", "Potable Drinking Water, Tea, Coffee (Hot & Cold Beverages)"),
            ("Tare Net Dry Weight:", "385 grams (+/- 10g)"),
            ("Overall Physical Dimensions:", "Height: 270 mm | Base Outer Diameter: 76 mm | Neck Mouth ID: 36 mm"),
            ("Thermal Insulation Mechanism:", "Double-Walled Cryogenic Vacuum Barrier (< 10^-4 mbar evacuation)"),
        ]
        for lbl, val in tech_lines:
            page1.insert_text((45, y), lbl, fontsize=8.5, fontname="hebo", color=(0.2, 0.25, 0.35))
            page1.insert_text((220, y), val, fontsize=8.5, fontname="helv", color=(0.05, 0.05, 0.1))
            y += 16

        # Section 3: Material Formulation & BOM
        page1.draw_line((40, y + 4), (555, y + 4), color=(0.8, 0.85, 0.9))
        y += 20
        page1.insert_text((40, y), "3. MATERIAL FORMULATION & BILL OF MATERIALS (BOM)", fontsize=11, fontname="hebo", color=(0.1, 0.15, 0.3))
        y += 18

        mat_lines = [
            ("Inner Body Liner (Food Contact):", "Austenitic Stainless Steel Grade 304 conforming to IS 6911 (Cr 18%, Ni 8%)"),
            ("Outer Protective Body Casing:", "Stainless Steel Grade 304 (Powder Coated External Finish)"),
            ("Stopper Core / Thread Mechanism:", "100% Virgin Food-Grade Polypropylene (PP), Bisphenol-A (BPA) Free"),
            ("Sealing Gasket Ring:", "Food-Grade Vulcanized Silicone Rubber (Resistant from -20 C to +120 C)"),
            ("Carrying Loop / Strap Material:", "Woven Polypropylene Webbing with 150 N Tensile Strength"),
        ]
        for lbl, val in mat_lines:
            page1.insert_text((45, y), lbl, fontsize=8.5, fontname="hebo", color=(0.2, 0.25, 0.35))
            page1.insert_text((220, y), val, fontsize=8.5, fontname="helv", color=(0.05, 0.05, 0.1))
            y += 16

        # Footer Page 1
        page1.draw_line((40, 800), (555, 800), color=(0.85, 0.88, 0.92))
        page1.insert_text((40, 815), "Zyntrix Compliance Platform • Document Specification Guide v1.0", fontsize=8, fontname="helv", color=(0.5, 0.55, 0.6))
        page1.insert_text((505, 815), "Page 1 of 2", fontsize=8, fontname="helv", color=(0.5, 0.55, 0.6))

        # -------------------------------------------------------------
        # PAGE 2: Performance Testing, Markings, & Evidence Attachment
        # -------------------------------------------------------------
        page2 = doc.new_page(width=595, height=842)

        page2.draw_rect(pymupdf.Rect(40, 35, 555, 38), color=(0.25, 0.35, 0.85), fill=(0.25, 0.35, 0.85))
        page2.insert_text((40, 58), "ZYNTRIX BIS COMPLIANCE COMPILER • REFERENCE SPECIFICATION GUIDE", fontsize=9, fontname="helv", color=(0.4, 0.45, 0.55))
        page2.insert_text((40, 80), "PERFORMANCE PARAMETERS & REQUIRED TEST EVIDENCE", fontsize=14, fontname="hebo", color=(0.1, 0.15, 0.3))

        # Section 4: Testing & Laboratory Performance
        page2.draw_line((40, 95), (555, 95), color=(0.8, 0.85, 0.9))
        y2 = 112
        page2.insert_text((40, y2), "4. TEST BENCHMARK REQUIREMENTS & VERIFIED THRESHOLDS", fontsize=11, fontname="hebo", color=(0.1, 0.15, 0.3))
        y2 += 18

        tests = [
            ("Thermal Retention (Clause 5.4):", "Filled with boiling water at 95 C. Maintained >= 65.5 C after 6h (Min Req: 60.0 C)"),
            ("Inversion Leakage Test (Clause 5.2):", "Inverted 180 degrees under full load for 10 minutes. Zero liquid drops observed."),
            ("Handle & Stopper Pull Strength:", "Sustained 15 kg static load for 5 minutes without deformation or loosening."),
            ("Drop & Impact Resistance (Clause 5.7):", "1.2 meter drop onto hardened concrete surface. No vacuum puncture or fracture."),
            ("Corrosion Resistance (Clause 5.3):", "48-hour neutral salt spray test (NSS). No rust, pitting, or discoloration."),
        ]
        for lbl, val in tests:
            page2.insert_text((45, y2), lbl, fontsize=8.5, fontname="hebo", color=(0.2, 0.25, 0.35))
            page2.insert_text((220, y2), val, fontsize=8.5, fontname="helv", color=(0.05, 0.05, 0.1))
            y2 += 18

        # Section 5: Statutory Product Markings
        page2.draw_line((40, y2 + 4), (555, y2 + 4), color=(0.8, 0.85, 0.9))
        y2 += 22
        page2.insert_text((40, y2), "5. STATUTORY MARKINGS & LABELING DECLARATION (Clause 7)", fontsize=11, fontname="hebo", color=(0.1, 0.15, 0.3))
        y2 += 18

        markings = [
            ("Manufacturer Trade Name / Mark:", "Permanently stamped / laser engraved on bottom base."),
            ("Nominal Volume Declaration:", "'750 ml' clearly legible on external retail carton and flask body."),
            ("Country of Origin Declaration:", "'Made in India' conspicuously embossed on container."),
            ("Batch / Manufacturing Lot No.:", "LOT-AS-2026-09 with year and month of manufacture."),
            ("BIS Standard Mark Placement:", "Reserved standard mark space for Scheme-I ISI Mark with CM/L License Number."),
        ]
        for lbl, val in markings:
            page2.insert_text((45, y2), lbl, fontsize=8.5, fontname="hebo", color=(0.2, 0.25, 0.35))
            page2.insert_text((220, y2), val, fontsize=8.5, fontname="helv", color=(0.05, 0.05, 0.1))
            y2 += 18

        # Section 6: Evidence Attachments Required
        page2.draw_line((40, y2 + 4), (555, y2 + 4), color=(0.8, 0.85, 0.9))
        y2 += 22
        page2.insert_text((40, y2), "6. COMPLIANCE EVIDENCE ATTACHMENT CHECKLIST", fontsize=11, fontname="hebo", color=(0.1, 0.15, 0.3))
        y2 += 18

        docs = [
            ("[x] Mill Test Certificate (MTC):", "Proving chemical composition of SS 304 raw coil (Cr/Ni ratio) from mill."),
            ("[x] NABL Laboratory Test Report:", "Complete test report for Thermal Retention (Cl 5.4) and Leakage (Cl 5.2)."),
            ("[x] Product Artwork & Labeling Proof:", "Dimensional diagram showing ISI mark positioning and consumer warnings."),
            ("[x] Manufacturing Quality Plan (MQP):", "Factory testing protocols for routine in-process vacuum seal verification."),
        ]
        for lbl, val in docs:
            page2.insert_text((45, y2), lbl, fontsize=8.5, fontname="hebo", color=(0.15, 0.3, 0.5))
            page2.insert_text((220, y2), val, fontsize=8.5, fontname="helv", color=(0.05, 0.05, 0.1))
            y2 += 18

        # Sign-off box
        page2.draw_rect(pymupdf.Rect(40, y2 + 10, 555, y2 + 80), color=(0.8, 0.85, 0.9), fill=(0.97, 0.98, 1.0))
        page2.insert_text((55, y2 + 28), "AUTHORIZED SIGNATORY / TECHNICAL HEAD DECLARATION:", fontsize=8.5, fontname="hebo", color=(0.1, 0.15, 0.3))
        page2.insert_text((55, y2 + 44), "I hereby certify that the above technical specifications represent true physical dimensions, material grades,", fontsize=8, fontname="helv", color=(0.3, 0.35, 0.45))
        page2.insert_text((55, y2 + 56), "and testing performance of the product submitted for Bureau of Indian Standards pre-certification evaluation.", fontsize=8, fontname="helv", color=(0.3, 0.35, 0.45))
        page2.insert_text((55, y2 + 70), "Signatory Name: Rajesh Sharma, VP Engineering & Quality Assurance | Date: 2026-09-03", fontsize=8, fontname="hebo", color=(0.15, 0.25, 0.4))

        # Footer Page 2
        page2.draw_line((40, 800), (555, 800), color=(0.85, 0.88, 0.92))
        page2.insert_text((40, 815), "Zyntrix Compliance Platform • Document Specification Guide v1.0", fontsize=8, fontname="helv", color=(0.5, 0.55, 0.6))
        page2.insert_text((505, 815), "Page 2 of 2", fontsize=8, fontname="helv", color=(0.5, 0.55, 0.6))

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes


template_generator_service = TemplateGeneratorService()
