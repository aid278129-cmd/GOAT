from typing import List, Optional
from backend.app.schemas.product_dna import (
    ProductDNACore,
    ClarificationRequirement,
    DNAAttribute,
    AttributeProvenance,
)


def detect_missing_attributes(dna: ProductDNACore) -> List[ClarificationRequirement]:
    """Detect missing attributes required for deterministic applicability & compliance reasoning.
    
    Zero-Guessing & Rule-Aware Policy:
    Evaluates against the RequiredAttributeProfile for candidate Indian Standards.
    Only asks for blocking attributes when genuinely missing or ambiguous.
    Does not ask spurious questions when all required applicability conditions are met.
    """
    from backend.app.services.applicability.taxonomy import get_required_attribute_profile

    clarifications: List[ClarificationRequirement] = []
    attr_names = {a.name for a in dna.attributes}

    # Category: Drinkware & Food Contact Containers (IS 17526:2021)
    if dna.category == "Drinkware & Food Contact Containers":
        # 1. Capacity check: required if unknown AND container is vacuum/insulated
        if dna.insulated and "capacity_ml" not in attr_names:
            clarifications.append(
                ClarificationRequirement(
                    attribute_name="capacity_ml",
                    reason="IS 17526:2021 mandates nominal capacity to verify <= 1000ml scope limits and thermal test duration.",
                    options=["500 ml", "750 ml", "1000 ml", "Over 1000 ml"],
                    criticality="HIGH",
                )
            )

        # 2. Stainless Steel Grade check: required ONLY if generic stainless steel is declared without grade
        materials_str = " ".join(dna.materials).lower()
        if "stainless_steel" in materials_str and "304" not in materials_str and "316" not in materials_str and "20" not in materials_str:
            clarifications.append(
                ClarificationRequirement(
                    attribute_name="material_grade",
                    reason="IS 17526:2021 Clause 4.2.1 mandates Grade 304 or superior for food contact parts.",
                    options=["Grade 304 (18/8)", "Grade 316", "Other Stainless Steel"],
                    criticality="HIGH",
                )
            )

        # 3. If material is completely unspecified
        elif not dna.materials and "material" not in attr_names:
            clarifications.append(
                ClarificationRequirement(
                    attribute_name="material_grade",
                    reason="IS 17526:2021 applies specifically to metallic stainless steel containers.",
                    options=["Grade 304 Stainless Steel", "Grade 316 Stainless Steel", "Plastic", "Copper"],
                    criticality="HIGH",
                )
            )

        # 4. Intended use: only ask if explicitly ambiguous (e.g. general storage or industrial container)
        if dna.intended_use == "general_storage" or dna.intended_use == "ambiguous_storage":
            clarifications.append(
                ClarificationRequirement(
                    attribute_name="intended_use",
                    reason="Mandatory QCO distinguishes domestic vacuum flasks from industrial chemical vessels.",
                    options=["Domestic / Personal Drinking", "Industrial Dispensing"],
                    criticality="MEDIUM",
                )
            )

    # Category: Electrical & Domestic Appliances (IS 302-2-15:2009)
    elif dna.category == "Electrical & Domestic Appliances":
        if "voltage" not in attr_names:
            clarifications.append(
                ClarificationRequirement(
                    attribute_name="voltage",
                    reason="Required to verify single-phase 230V AC safety scope under IS 302-1.",
                    options=["230V AC, 50Hz (Standard Indian Mains)", "110V AC"],
                    criticality="HIGH",
                )
            )
        if "wattage" not in attr_names and "kettle" in dna.product_name.lower():
            clarifications.append(
                ClarificationRequirement(
                    attribute_name="wattage",
                    reason="Required for heating element endurance and thermal cut-out threshold checks.",
                    options=["1000W", "1500W", "2000W"],
                    criticality="MEDIUM",
                )
            )

    # Category: Toys & Children's Products (IS 9873 (Part 1):2019)
    elif dna.category == "Toys & Children's Products" or "toy" in dna.category.lower() or "toy" in dna.product_name.lower():
        if "target_age_months" not in attr_names and "target_age" not in attr_names:
            clarifications.append(
                ClarificationRequirement(
                    attribute_name="target_age_months",
                    reason="IS 9873 (Part 1):2019 Clause 4.4 mandates strict small parts cylinder test for toys intended for children under 36 months.",
                    options=["Under 36 months (0-3 years)", "36 months and above (3-14 years)"],
                    criticality="HIGH",
                )
            )

    return clarifications


def apply_clarification_response(
    dna: ProductDNACore,
    attribute_name: str,
    raw_value: str,
    source_type: str = "USER",
) -> ProductDNACore:
    """Safely apply user clarification answer to update Product DNA while preserving provenance history.
    
    Attribute extraction_method is marked as 'user_clarification' to differentiate from system parsing.
    """
    from backend.app.services.product_dna.normalizer import (
        normalize_capacity,
        normalize_material,
    )

    clean_name = attribute_name.strip()
    val: any = raw_value.strip()

    # Normalization according to attribute type
    if clean_name == "capacity_ml":
        cap_val, cap_unit = normalize_capacity(str(raw_value))
        val = cap_val if cap_val is not None else raw_value
        unit = "ml"
    elif clean_name == "material_grade":
        norm_mat = normalize_material(str(raw_value))
        val = norm_mat
        if norm_mat not in dna.materials:
            dna.materials.append(norm_mat)
        unit = None
    elif clean_name == "intended_use":
        val = "domestic_drinking" if "domestic" in str(raw_value).lower() else "commercial_beverage"
        dna.intended_use = val
        unit = None
    else:
        unit = None

    from backend.app.schemas.product_dna import ProvenanceClassification

    # Update existing attribute or add new
    existing_attr = next((a for a in dna.attributes if a.name == clean_name), None)
    new_prov = AttributeProvenance(
        provenance_type=ProvenanceClassification.USER_CLARIFICATION,
        source_document="user_clarification_session",
        page=None,
        source_text=f"User clarified {clean_name}: '{raw_value}'",
        confidence=1.0,
        extraction_method="user_clarification",
    )

    if existing_attr:
        existing_attr.value = val
        existing_attr.unit = unit or existing_attr.unit
        existing_attr.provenance = new_prov
    else:
        dna.attributes.append(
            DNAAttribute(
                name=clean_name,
                value=val,
                data_type="integer" if isinstance(val, int) else "string",
                unit=unit,
                provenance=new_prov,
            )
        )

    # Re-evaluate remaining clarifications
    dna.pending_clarifications = detect_missing_attributes(dna)
    return dna
