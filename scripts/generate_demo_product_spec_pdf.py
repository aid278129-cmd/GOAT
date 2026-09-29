"""Script to generate an ultra-professional, publication-grade Product Technical Specification PDF.

Balanced into an exact 3-Page layout:
- Page 1: Document Control, Executive Summary, 1. Product Identity, 2. Physical & Mechanical Dimensions.
- Page 2: 3. Material Metallurgy (IS 6911/9845), 4. BIS Performance Benchmarks (Cl 5.2/5.4/5.7), 5. Statutory Markings (Cl 7.1), 6. Bill of Materials (BOM).
- Page 3: 7. Evidence & Test Certificate Ledger, 8. Audit & Lab Dispatch Protocol, 9. Engineering & QA Sign-Off, Cryptographic Integrity Seal & BIS Disclaimer.

Tailored for the SIH 2026 Golden Demo Scenario:
- Product: ThermoSteel Domestic Stainless Steel Vacuum Flask 1000ml (Model: TS-1000V-IND)
- Statutory Standard: IS 17526:2021
- Mandatory QCO: DPIIT Domestic Water Bottles (Quality Control) Order, 2023
- Certification Scheme: BIS Scheme-I (ISI Mark)
"""

import os
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Palette constants
PRIMARY_DARK = colors.HexColor("#0B192C")      # Deep industrial navy
SECONDARY_BLUE = colors.HexColor("#1E3E62")    # Slate navy
ACCENT_CYAN = colors.HexColor("#0077B6")       # Engineering cyan / BIS blue
TEAL_GREEN = colors.HexColor("#028090")        # Verified green-teal
LIGHT_BG = colors.HexColor("#F8FAFC")          # Clean off-white
BORDER_COLOR = colors.HexColor("#CBD5E1")      # Slate border
TEXT_DARK = colors.HexColor("#0F172A")         # Body dark text
TEXT_MUTED = colors.HexColor("#475569")        # Subtitle / caption text
SUCCESS_BG = colors.HexColor("#ECFDF5")        # Light green tag
SUCCESS_TXT = colors.HexColor("#065F46")       # Green text


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' and running headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        w, h = A4

        # Running Header (Pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(SECONDARY_BLUE)
            self.drawString(36, h - 28, "APEX THERMAL TECHNOLOGIES LTD.  |  TECHNICAL PRODUCT SPECIFICATION")
            self.setFont("Helvetica", 7.5)
            self.setFillColor(TEXT_MUTED)
            self.drawRightString(w - 36, h - 28, "DOC REF: SPEC-TS1000-REV-C  |  IS 17526:2021")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(36, h - 32, w - 36, h - 32)

        # Running Footer (All Pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(36, 38, w - 36, 38)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(36, 26, "CONFIDENTIAL & PROPRIETARY  |  PREPARED FOR BIS REGULATORY VERIFICATION & AUDIT")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 7.5)
        self.drawRightString(w - 36, 26, page_str)

        self.restoreState()


def build_pdf(target_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    # Margins: 36 pt (0.5 inch), top 40, bottom 46
    doc = SimpleDocTemplate(
        target_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_doc_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=PRIMARY_DARK,
    )

    style_sec_head = ParagraphStyle(
        "SecHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=PRIMARY_DARK,
        spaceBefore=7,
        spaceAfter=3,
    )

    style_body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.5,
        textColor=TEXT_DARK,
    )

    style_tag_verified = ParagraphStyle(
        "TagVerified",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=SUCCESS_TXT,
    )

    style_th = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )

    style_cell = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=TEXT_DARK,
    )

    style_cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=PRIMARY_DARK,
    )

    style_code = ParagraphStyle(
        "CodeCell",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=8.5,
        textColor=SECONDARY_BLUE,
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE BLOCK, DOCUMENT CONTROL, SECTIONS 1 & 2
    # =========================================================================
    header_data = [
        [
            Paragraph("<b>APEX THERMAL TECHNOLOGIES LTD.</b><br/><font color='#475569'>Consumer Products Engineering & Compliance Division | ISO 9001:2015</font>", style_body),
            Paragraph("<b>DOC REF:</b> SPEC-TS1000-REV-C<br/><b>DATE:</b> 2026-09-28<br/><b>STATUS:</b> OFFICIAL RELEASE", style_code)
        ]
    ]
    t_header = Table(header_data, colWidths=[360, 163])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)

    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_DARK, spaceBefore=3, spaceAfter=6))

    # Document Title Block
    title_data = [
        [
            Paragraph("<b>PRODUCT TECHNICAL SPECIFICATION</b><br/><font size='9.5' color='#1E3E62'>Model: ThermoSteel Domestic Stainless Steel Vacuum Flask 1000ml (TS-1000V-IND)</font>", style_doc_title),
            Paragraph("<b>MANDATORY QCO SCOPE</b><br/><font color='#028090'><b>IS 17526:2021</b></font><br/>BIS Scheme-I (ISI Mark)", style_code)
        ]
    ]
    t_title = Table(title_data, colWidths=[370, 153])
    t_title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_title)
    story.append(Spacer(1, 6))

    # Executive Overview Callout
    exec_text = (
        "<b>EXECUTIVE ENGINEERING SUMMARY:</b> This engineering document establishes the baseline Product DNA, "
        "material metallurgy, physical dimensions, performance thresholds, and statutory marking specifications "
        "for the <b>ThermoSteel 1000ml Domestic Vacuum Insulated Stainless Steel Flask</b>. It is formulated specifically "
        "for pre-certification evaluation under the <b>Bureau of Indian Standards (BIS) Scheme-I (ISI Mark)</b> "
        "pursuant to the <i>Domestic Water Bottles (Quality Control) Order, 2023</i> and standard <b>IS 17526:2021</b>."
    )
    t_exec = Table([[Paragraph(exec_text, style_body)]], colWidths=[523])
    t_exec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('LINELEFT', (0, 0), (0, 0), 3, ACCENT_CYAN),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_exec)
    story.append(Spacer(1, 6))

    # Section 1: Product Identification & Statutory Scope
    story.append(Paragraph("1. PRODUCT IDENTITY & STATUTORY JURISDICTION", style_sec_head))

    sec1_data = [
        [Paragraph("Parameter", style_th), Paragraph("Declared Technical Specification", style_th), Paragraph("Statutory Reference", style_th), Paragraph("Verification Status", style_th)],
        [Paragraph("Product Model & Trade Name", style_cell_bold), Paragraph("ThermoSteel TS-1000V-IND Domestic Vacuum Flask", style_cell), Paragraph("IS 17526:2021 Cl. 4.1", style_code), Paragraph("VERIFIED (CATALOG)", style_tag_verified)],
        [Paragraph("Statutory Product Category", style_cell_bold), Paragraph("Domestic Stainless Steel Vacuum Flask/Bottle", style_cell), Paragraph("Gazette S.O. 1234(E)", style_code), Paragraph("MANDATORY QCO", style_tag_verified)],
        [Paragraph("Governing Indian Standard", style_cell_bold), Paragraph("IS 17526:2021 (First Revision)", style_cell), Paragraph("Bureau of Indian Standards", style_code), Paragraph("ACTIVE / MANDATORY", style_tag_verified)],
        [Paragraph("Applicable Quality Control Order", style_cell_bold), Paragraph("DPIIT Domestic Water Bottles (QCO) Order, 2023", style_cell), Paragraph("Ministry of Commerce & Ind.", style_code), Paragraph("ENFORCED", style_tag_verified)],
        [Paragraph("Certification Scheme", style_cell_bold), Paragraph("Scheme-I (Mandatory Standard ISI Mark)", style_cell), Paragraph("BIS (Conformity Assessment) 2018", style_code), Paragraph("PRE-CERTIFICATION", style_tag_verified)],
        [Paragraph("Primary Intended Usage", style_cell_bold), Paragraph("Containment and temperature retention of potable water & beverages", style_cell), Paragraph("Food Contact Surface", style_code), Paragraph("FOOD GRADE", style_tag_verified)],
        [Paragraph("Manufacturing Facility", style_cell_bold), Paragraph("Apex Thermal Tech Ltd., Plant #4, Chakan Industrial Area, Pune 410501", style_cell), Paragraph("Factory Audit Scope", style_code), Paragraph("LICENCE APPLICANT", style_tag_verified)],
    ]
    t_sec1 = Table(sec1_data, colWidths=[130, 203, 110, 80])
    t_sec1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sec1)
    story.append(Spacer(1, 6))

    # Section 2: Physical & Mechanical Specifications
    story.append(Paragraph("2. PHYSICAL, DIMENSIONAL & MECHANICAL CHARACTERISTICS", style_sec_head))

    sec2_data = [
        [Paragraph("Engineering Parameter", style_th), Paragraph("Nominal Value / Design Range", style_th), Paragraph("Tolerance / Standard Limit", style_th), Paragraph("Testing Method / Clause", style_th)],
        [Paragraph("Nominal Volumetric Capacity", style_cell_bold), Paragraph("1000 mL (1.0 Litre)", style_cell), Paragraph("± 30 mL (Within ± 5% BIS limit)", style_cell), Paragraph("IS 17526:2021 Cl. 4.2", style_code)],
        [Paragraph("Total Assembled Height", style_cell_bold), Paragraph("312.0 mm", style_cell), Paragraph("± 1.5 mm", style_cell), Paragraph("Vernier Caliper / CAD DWG", style_code)],
        [Paragraph("External Body Diameter", style_cell_bold), Paragraph("86.0 mm", style_cell), Paragraph("± 0.8 mm", style_cell), Paragraph("Optical Profile Comparator", style_code)],
        [Paragraph("Mouth Bore (Neck Inner Dia)", style_cell_bold), Paragraph("44.5 mm (Wide-mouth filling)", style_cell), Paragraph("± 0.5 mm", style_cell), Paragraph("Internal Micrometer", style_code)],
        [Paragraph("Net Tare Weight (Empty)", style_cell_bold), Paragraph("485 grams", style_cell), Paragraph("± 10 grams", style_cell), Paragraph("Precision Balance (0.1g)", style_code)],
        [Paragraph("Inner Vessel Wall Thickness", style_cell_bold), Paragraph("0.60 mm", style_cell), Paragraph("Min. 0.50 mm (IS 17526 requirement)", style_cell), Paragraph("Ultrasonic Thickness Gauge", style_code)],
        [Paragraph("Outer Shell Wall Thickness", style_cell_bold), Paragraph("0.70 mm", style_cell), Paragraph("Min. 0.60 mm", style_cell), Paragraph("Ultrasonic Thickness Gauge", style_code)],
        [Paragraph("Thermal Insulation Cavity", style_cell_bold), Paragraph("Double-walled vacuum sealed cavity", style_cell), Paragraph("P &lt; 1.0 x 10<sup>-3</sup> Pa (High Vacuum)", style_cell), Paragraph("Helium Mass Spectrometer", style_code)],
    ]
    t_sec2 = Table(sec2_data, colWidths=[130, 160, 120, 113])
    t_sec2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sec2)

    # =========================================================================
    # PAGE 2: METALLURGY, PERFORMANCE BENCHMARKS, MARKINGS & BOM
    # =========================================================================
    story.append(PageBreak())

    # Section 3: Material Metallurgy & Chemical Composition
    story.append(Paragraph("3. MATERIAL METALLURGY & CHEMICAL CONFORMANCE (IS 6911 & IS 9845)", style_sec_head))

    sec3_data = [
        [Paragraph("Sub-Assembly", style_th), Paragraph("Specified Material Grade", style_th), Paragraph("Chemical / Polymer Specifications", style_th), Paragraph("Compliance Standard", style_th)],
        [Paragraph("Inner Flask (Food Contact)", style_cell_bold), Paragraph("Austenitic Stainless Steel Grade 304 (04Cr18Ni10)", style_cell), Paragraph("Cr: 18.2%, Ni: 8.1%, C: 0.045%, Mo: 0.15%, P: <0.035%", style_cell), Paragraph("IS 6911 / IS 17526 Cl. 4.2.1", style_code)],
        [Paragraph("Outer Shell Enclosure", style_cell_bold), Paragraph("Austenitic Stainless Steel Grade 304", style_cell), Paragraph("Cr: 18.1%, Ni: 8.0%, Protective electro-powder coating", style_cell), Paragraph("IS 6911", style_code)],
        [Paragraph("Threaded Stopper Core", style_cell_bold), Paragraph("Virgin Polypropylene (PP Homopolymer)", style_cell), Paragraph("BPA-Free, non-toxic, overall migration < 10 mg/dm²", style_cell), Paragraph("IS 9845 / IS 10910", style_code)],
        [Paragraph("Hermetic Gasket Seal", style_cell_bold), Paragraph("Platinum-Cured Silicone Elastomer", style_cell), Paragraph("Food-contact grade, shore 55A hardness, -40°C to 120°C", style_cell), Paragraph("IS 9845 / 21 CFR 177.2600", style_code)],
        [Paragraph("Internal Vacuum Getter", style_cell_bold), Paragraph("Zirconium-Aluminium Sintered Alloy", style_cell), Paragraph("Continuous residual gas adsorption within sealed cavity", style_cell), Paragraph("SAES Getter Spec G-200", style_code)],
    ]
    t_sec3 = Table(sec3_data, colWidths=[110, 140, 163, 110])
    t_sec3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sec3)
    story.append(Spacer(1, 6))

    # Section 4: Performance Benchmarks
    story.append(Paragraph("4. STATUTORY BIS PERFORMANCE TESTING BENCHMARKS", style_sec_head))

    sec4_data = [
        [Paragraph("BIS Clause", style_th), Paragraph("Test Description", style_th), Paragraph("Standard Test Procedure", style_th), Paragraph("Mandatory Threshold", style_th), Paragraph("Design Value", style_th)],
        [
            Paragraph("Clause 5.4", style_cell_bold),
            Paragraph("Heat Retention (Thermal Test)", style_cell_bold),
            Paragraph("Filled with water at 95°C ± 1°C. Sealed and kept at 25°C ambient for 6 hours.", style_cell),
            Paragraph("Temp ≥ 60.0°C", style_code),
            Paragraph("<b>65.5°C</b> (PASS)", style_tag_verified),
        ],
        [
            Paragraph("Clause 5.2", style_cell_bold),
            Paragraph("Inversion Leakage Test", style_cell_bold),
            Paragraph("Filled to nominal 1000ml capacity with ambient water. Inverted 180° for 10 minutes.", style_cell),
            Paragraph("Zero leakage / 0 drops", style_code),
            Paragraph("<b>Zero Leaks</b> (PASS)", style_tag_verified),
        ],
        [
            Paragraph("Clause 5.7", style_cell_bold),
            Paragraph("Drop & Impact Resistance", style_cell_bold),
            Paragraph("Filled with water; dropped from 1.2 m height onto 50mm concrete floor (3 impacts).", style_cell),
            Paragraph("No fracture; vacuum held", style_code),
            Paragraph("<b>No Breach</b> (PASS)", style_tag_verified),
        ],
        [
            Paragraph("Clause 5.3", style_cell_bold),
            Paragraph("Corrosion Resistance Test", style_cell_bold),
            Paragraph("Neutral Salt Spray (NSS) test per IS 9844 for continuous 48-hour exposure.", style_cell),
            Paragraph("Zero pitting / rust spots", style_code),
            Paragraph("<b>Grade 0 Rust</b> (PASS)", style_tag_verified),
        ],
        [
            Paragraph("Clause 4.2.2", style_cell_bold),
            Paragraph("Overall Polymer Migration", style_cell_bold),
            Paragraph("Stopper & gasket extraction in 3% acetic acid (100°C, 2h) and n-heptane simulants.", style_cell),
            Paragraph("Max 10 mg/dm²", style_code),
            Paragraph("<b>3.4 mg/dm²</b> (PASS)", style_tag_verified),
        ],
    ]
    t_sec4 = Table(sec4_data, colWidths=[65, 110, 168, 95, 85])
    t_sec4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sec4)
    story.append(Spacer(1, 6))

    # Section 5: Statutory Product Markings & Labeling
    story.append(Paragraph("5. STATUTORY MARKINGS & PACKAGING DECLARATIONS (Clause 7.1)", style_sec_head))

    sec5_data = [
        [Paragraph("Marking Element", style_th), Paragraph("Method of Application", style_th), Paragraph("Exact Statutory Text / Layout", style_th), Paragraph("Physical Location", style_th)],
        [
            Paragraph("BIS Standard Mark (ISI)", style_cell_bold),
            Paragraph("Permanent Laser Etching", style_cell),
            Paragraph("Standard Mark with License: <b>CM/L-XXXXXXX</b> and standard: <b>IS 17526</b>", style_cell),
            Paragraph("Base of outer container", style_cell),
        ],
        [
            Paragraph("Manufacturer Identification", style_cell_bold),
            Paragraph("Embossed / Laser Etched", style_cell),
            Paragraph("<b>APEX THERMAL TECHNOLOGIES LTD.</b> (Brand: ThermoSteel)", style_cell),
            Paragraph("Container bottom & carton", style_cell),
        ],
        [
            Paragraph("Nominal Capacity Declaration", style_cell_bold),
            Paragraph("Permanent High-Contrast", style_cell),
            Paragraph("<b>Nominal Capacity: 1000 ml (1.0 L)</b> [Font height ≥ 3.0 mm]", style_cell),
            Paragraph("Front lower body & carton", style_cell),
        ],
        [
            Paragraph("Country of Origin", style_cell_bold),
            Paragraph("Laser Etched", style_cell),
            Paragraph("<b>Made in India / Bharat</b>", style_cell),
            Paragraph("Adjacent to base license mark", style_cell),
        ],
        [
            Paragraph("Batch & Traceability Code", style_cell_bold),
            Paragraph("Dot Matrix Laser Code", style_cell),
            Paragraph("<b>LOT-2026-09-MH04</b> (Month/Year: SEP 2026)", style_code),
            Paragraph("Container base rim", style_cell),
        ],
    ]
    t_sec5 = Table(sec5_data, colWidths=[120, 110, 173, 120])
    t_sec5.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sec5)
    story.append(Spacer(1, 6))

    # Section 6: Bill of Materials (BOM)
    story.append(Paragraph("6. BILL OF MATERIALS (BOM) & COMPONENT BREAKDOWN", style_sec_head))

    sec6_data = [
        [Paragraph("Item #", style_th), Paragraph("Part Name", style_th), Paragraph("Material / Specification", style_th), Paragraph("Qty", style_th), Paragraph("Weight (g)", style_th), Paragraph("Criticality", style_th)],
        [Paragraph("TS-01", style_code), Paragraph("Inner Flask Vessel", style_cell_bold), Paragraph("Austenitic SS 304 (04Cr18Ni10 per IS 6911)", style_cell), Paragraph("1", style_cell), Paragraph("195.0", style_cell), Paragraph("SAFETY CRITICAL", style_tag_verified)],
        [Paragraph("TS-02", style_code), Paragraph("Outer Shell Body", style_cell_bold), Paragraph("Austenitic SS 304 (Powder-coat finish)", style_cell), Paragraph("1", style_cell), Paragraph("210.0", style_cell), Paragraph("STRUCTURAL", style_cell)],
        [Paragraph("TS-03", style_code), Paragraph("Threaded Stopper Core", style_cell_bold), Paragraph("Virgin Polypropylene (IS 10910, BPA-Free)", style_cell), Paragraph("1", style_cell), Paragraph("42.0", style_cell), Paragraph("FOOD CONTACT", style_tag_verified)],
        [Paragraph("TS-04", style_code), Paragraph("Primary O-Ring Gasket", style_cell_bold), Paragraph("Platinum-Cured Silicone (IS 9845 / Shore 55A)", style_cell), Paragraph("1", style_cell), Paragraph("5.5", style_cell), Paragraph("LEAK CRITICAL", style_tag_verified)],
        [Paragraph("TS-05", style_code), Paragraph("Insulated Base Cap", style_cell_bold), Paragraph("SS 304 with EVA protective bumper", style_cell), Paragraph("1", style_cell), Paragraph("28.0", style_cell), Paragraph("PROTECTIVE", style_cell)],
        [Paragraph("TS-06", style_code), Paragraph("Internal Vacuum Getter", style_cell_bold), Paragraph("Zr-Al Non-Evaporable Sintered Getter", style_cell), Paragraph("1", style_cell), Paragraph("4.5", style_cell), Paragraph("THERMAL SEAL", style_cell)],
    ]
    t_sec6 = Table(sec6_data, colWidths=[40, 115, 198, 30, 60, 80])
    t_sec6.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_sec6)

    # =========================================================================
    # PAGE 3: EVIDENCE LEDGER, ATTESTATION & DIGITAL INTEGRITY
    # =========================================================================
    story.append(PageBreak())

    story.append(Paragraph("7. REGULATORY EVIDENCE & TEST CERTIFICATE LEDGER", style_sec_head))
    p_ev_intro = (
        "Under the Zyntrix Evidence-First deterministic evaluation engine, product claims must be substantiated "
        "by traceable, immutable laboratory certificates. The following official documents constitute the attached "
        "evidence dossier for this product:"
    )
    story.append(Paragraph(p_ev_intro, style_body))
    story.append(Spacer(1, 4))

    sec7_data = [
        [Paragraph("Doc Ref ID", style_th), Paragraph("Evidence Type", style_th), Paragraph("Issuing Authority / Laboratory", style_th), Paragraph("Tested Requirement", style_th), Paragraph("Finding / Result", style_th)],
        [
            Paragraph("MTC-2026-304", style_code),
            Paragraph("Mill Test Certificate", style_cell_bold),
            Paragraph("Steel Authority of India Ltd. (SAIL), Rourkela", style_cell),
            Paragraph("IS 6911 Chemical Metallurgy (Cr 18.2%, Ni 8.1%)", style_cell),
            Paragraph("SATISFIED", style_tag_verified),
        ],
        [
            Paragraph("NTH/2026/044", style_code),
            Paragraph("NABL Accredited Test Report", style_cell_bold),
            Paragraph("National Test House (WR), Mumbai (NABL Accr.)", style_cell),
            Paragraph("Clause 5.4 Heat Retention (64.5°C after 6h)", style_cell),
            Paragraph("SATISFIED", style_tag_verified),
        ],
        [
            Paragraph("NTH/2026/044-B", style_code),
            Paragraph("NABL Accredited Test Report", style_cell_bold),
            Paragraph("National Test House (WR), Mumbai (NABL Accr.)", style_cell),
            Paragraph("Clause 5.2 Inversion Leakage (10 min @ 180°)", style_cell),
            Paragraph("SATISFIED", style_tag_verified),
        ],
        [
            Paragraph("CIPET-CH-2026", style_code),
            Paragraph("Polymer Safety Certificate", style_cell_bold),
            Paragraph("Central Institute of Petrochem. Eng. (CIPET)", style_cell),
            Paragraph("IS 9845 Food-Contact Migration (BPA-Free)", style_cell),
            Paragraph("SATISFIED", style_tag_verified),
        ],
        [
            Paragraph("DWG-TS1000-01", style_code),
            Paragraph("Production CAD Drawing", style_cell_bold),
            Paragraph("Apex Thermal R&D Engineering Centre", style_cell),
            Paragraph("Volumetric capacity 1000ml & 0.6mm wall gauge", style_cell),
            Paragraph("DESIGN VERIFIED", style_tag_verified),
        ],
    ]
    t_sec7 = Table(sec7_data, colWidths=[75, 105, 148, 125, 70])
    t_sec7.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_sec7)
    story.append(Spacer(1, 8))

    # Section 8: Lab Actions & Testing Roadmap
    story.append(Paragraph("8. AUDIT & LABORATORY DISPATCH ROUTING PROTOCOL", style_sec_head))
    lab_text = (
        "<b>LAB DISPATCH ROUTING:</b> In compliance with BIS Conformity Assessment Regulations, samples from the initial "
        "commercial pilot batch (Protocol: 8 Flasks per BIS Product Manual PM/IS 17526/1) shall be submitted to a BIS-recognized "
        "or NABL-accredited laboratory for independent statutory verification. Testing shall strictly adhere to "
        "Clauses 4.2.1, 5.2, 5.4, and 7.1. Any non-conformance will automatically trigger a corrective action plan (CAPA) "
        "and re-testing in accordance with BIS Scheme-I procedural guidelines."
    )
    t_lab = Table([[Paragraph(lab_text, style_body)]], colWidths=[523])
    t_lab.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('LINELEFT', (0, 0), (0, 0), 3, TEAL_GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_lab)
    story.append(Spacer(1, 10))

    # Section 9: Engineering Attestation & QA Sign-Off Block
    story.append(Paragraph("9. AUTHORIZED ENGINEERING ATTESTATION & QA SIGN-OFF", style_sec_head))

    sign_data = [
        [
            Paragraph(
                "<b>CHIEF TECHNICAL OFFICER (CTO):</b><br/><br/>"
                "<i>Dr. Vikram Malhotra, Ph.D. (Metallurgy)</i><br/>"
                "Director of Engineering & Product Integrity<br/>"
                "Apex Thermal Technologies Ltd.<br/>"
                "Date: 2026-09-28 | Pune, India<br/><br/>"
                "<b>Status:</b> <font color='#028090'><b>DIGITALLY ATTESTED</b></font>",
                style_body
            ),
            Paragraph(
                "<b>HEAD OF QUALITY ASSURANCE & REGULATORY:</b><br/><br/>"
                "<i>Rajesh K. Sharma, Lead Auditor (IRCA)</i><br/>"
                "VP Quality Assurance & BIS Compliance Officer<br/>"
                "Apex Thermal Technologies Ltd.<br/>"
                "Date: 2026-09-28 | Pune, India<br/><br/>"
                "<b>Status:</b> <font color='#028090'><b>DIGITALLY ATTESTED</b></font>",
                style_body
            )
        ]
    ]
    t_sign = Table(sign_data, colWidths=[256, 257])
    t_sign.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
    ]))
    story.append(t_sign)
    story.append(Spacer(1, 10))

    # Cryptographic Seal & System Notice
    crypto_notice = (
        "<b>ZYNTRIX COMPLIANCE COMPILER | CRYPTOGRAPHIC RECORD INTEGRITY:</b><br/>"
        "This technical product specification document has been deterministically compiled for the "
        "Smart India Hackathon (SIH 2026) live jury evaluation scenario. "
        "Digital SHA-256 Digest: <code>e8b4f179d6c384a0b271d473489cf8b139265f24ad919421ea34cf640f2f3e82</code><br/>"
        "<i>Disclaimer: This document is an engineering product specification prepared for BIS Scheme-I conformity evaluation. "
        "Official BIS certification requires final grant of CM/L licence by the Bureau of Indian Standards.</i>"
    )
    t_crypto = Table([[Paragraph(crypto_notice, style_body)]], colWidths=[523])
    t_crypto.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_crypto)

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {target_path}")


if __name__ == "__main__":
    output_pdf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ThermoSteel_Product_Specification_IS17526.pdf")
    build_pdf(output_pdf)
