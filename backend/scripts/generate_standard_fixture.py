import os
import pymupdf

def generate_fixture():
    os.makedirs("data/bis/standards", exist_ok=True)
    doc = pymupdf.open()
    rect = pymupdf.Rect(50, 50, 545, 800)

    # Page 1: Header, Scope, Normative References, Terminology
    page1 = doc.new_page(width=595, height=842)
    text_p1 = """BUREAU OF INDIAN STANDARDS
MANAK BHAVAN, 9 BAHADUR SHAH ZAFAR MARG, NEW DELHI 110002

IS 17526:2021
INDIAN STANDARD
COMMERCIAL BEVERAGE COOLERS AND INSULATED FLASKS — SPECIFICATION
(First Edition)

1 SCOPE
1.1 This standard prescribes the constructional, material, safety, and performance requirements and methods of sampling and test for insulated flasks, vacuum bottles, and commercial beverage containers.
1.2 This standard applies to portable containers intended for maintaining temperature of beverages.

2 NORMATIVE REFERENCES
2.1 IS 6911 Stainless steel plate, sheet and strip — Specification
2.2 IS 9845 Determination of overall migration of constituents of plastic materials and articles intended to come into contact with foodstuffs
2.3 IS 302-1 Safety of household and similar electrical appliances

3 TERMINOLOGY
3.1 Insulated Flask — A double-walled vessel with vacuum or thermal insulation between the walls intended to minimize heat transfer.
3.2 Nominal Capacity — The volume of liquid in millilitres (ml) that the container can hold when filled to the base of the stopper."""

    page1.insert_textbox(rect, text_p1, fontsize=10, fontname="helv")

    # Page 2: Requirements (Clause 4)
    page2 = doc.new_page(width=595, height=842)
    text_p2 = """IS 17526:2021

4 REQUIREMENTS
4.1 Construction and Workmanship
4.1.1 The container shall be free from sharp edges, burrs, dents, or manufacturing defects that could impair its safe operation or cleaning.
4.1.2 The stopper and lid mechanism shall securely seal the mouth and prevent accidental opening.

4.2 Material Requirements
4.2.1 Stainless Steel Parts
All metallic parts in direct contact with liquid or food shall be manufactured from stainless steel conforming to Grade 304 of IS 6911 or superior grade. Lead content shall not exceed 0.05 percent by mass.

4.2.2 Plastic and Polymeric Components
All polymeric components, stoppers, silicone seals, and gaskets coming into contact with beverages shall conform to food-grade migration limits as specified in IS 9845 and shall be BPA-free.

4.2.3 Outer Body Shell
The outer casing may be fabricated from stainless steel, aluminium alloy, or impact-resistant polymer."""

    page2.insert_textbox(rect, text_p2, fontsize=10, fontname="helv")

    # Page 3: Sampling and Testing (Clause 5)
    page3 = doc.new_page(width=595, height=842)
    text_p3 = """IS 17526:2021

5 SAMPLING AND METHODS OF TEST
5.1 Sampling Procedure
The scale of sampling and criteria for conformity shall be in accordance with Annex A of this standard.

5.2 Leakage Test
The container shall be filled to nominal capacity with water at ambient temperature (27 +/- 2 deg C), closed securely with its stopper, and inverted for a period of 10 minutes. The container shall show no evidence of leakage, weeping, or moisture seepage.

5.3 Impact Resistance (Drop) Test
The flask filled with water to nominal capacity shall be dropped freely from a height of 1.0 metre onto a solid concrete floor. After two successive drops, the container shall retain its thermal insulation integrity and show no liquid leakage.

5.4 Thermal Performance (Heat Retention) Test
When filled with hot water at an initial temperature of 95 deg C and sealed at room ambient temperature (27 deg C), the temperature of the water after 6 hours shall not be less than 60 deg C for containers of nominal capacity up to 1000 ml, and not less than 65 deg C for containers exceeding 1000 ml.

5.5 Cold Retention Performance Test
When filled with chilled water at 4 deg C and sealed at room ambient temperature (27 deg C), the temperature of the water after 6 hours shall not exceed 10 deg C."""

    page3.insert_textbox(rect, text_p3, fontsize=10, fontname="helv")

    # Page 4: Packaging and Marking (Clauses 6 & 7)
    page4 = doc.new_page(width=595, height=842)
    text_p4 = """IS 17526:2021

6 PACKAGING
6.1 Each flask shall be packaged in a suitable protective carton to prevent damage during transit and handling.

7 MARKING
7.1 Marking Requirements
Each insulated flask and its retail packaging shall be legibly and indelibly marked with the following details:
a) Name or registered trademark of the manufacturer;
b) Nominal capacity in millilitres (ml) or litres (L);
c) Model number and batch or lot identification;
d) Country of manufacture;
e) Care and cleaning instructions.

7.2 BIS Certification Marking (ISI Mark)
Each container may also be marked with the Standard Mark (ISI Mark) under Scheme I of the Bureau of Indian Standards (Conformity Assessment) Regulations, 2018, subject to obtaining a valid license from BIS.
The use of the Standard Mark is governed by the provisions of the Bureau of Indian Standards Act, 2016."""

    page4.insert_textbox(rect, text_p4, fontsize=10, fontname="helv")

    pdf_path = "data/bis/standards/IS_17526_2021.pdf"
    doc.save(pdf_path)
    doc.close()
    print("Regenerated wrapped standard fixture PDF:", pdf_path)

if __name__ == "__main__":
    generate_fixture()
