"""Deterministic Product Fact Extraction and Clarification Engine for Layer 2.

Implements the SIH Presentation Layer 2 workflow:
RAW MULTI-MODAL INPUT -> PRODUCT FACT EXTRACTION -> FACT NORMALIZATION
-> PROVENANCE + CONFIDENCE -> MISSING/CONFLICTING FACT DETECTION
-> CLARIFICATION QUEUE -> USER CONFIRMATION -> FINAL PRODUCT DNA -> LAYER 3 AI ORCHESTRATOR.

Enforces cardinal invariants:
USER_TEXT != PRODUCT FACT != EVIDENCE != COMPLIANCE
NO SUFFICIENT PRODUCT INFORMATION -> ASK / UNKNOWN
NO VERIFIED EVIDENCE -> NO SATISFIED
LLM COMPLIANCE AUTHORITY = 0%
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from backend.app.schemas.product_dna import (
    ProductDNACore,
    DNAAttribute,
    AttributeProvenance,
    ClarificationRequirement,
    ProvenanceClassification,
    ProductFact,
    FactProvenanceType,
    FactVerificationState,
    ProductDNAVersionRecord,
)
from backend.app.services.product_dna.normalizer import (
    normalize_capacity,
    normalize_electrical,
    normalize_material,
    check_physical_plausibility,
)
from backend.app.services.product_dna.detector import fact_anomaly_detector


def extract_structured_facts_from_payload(
    text: str,
    source_name: Optional[str] = None,
    default_provenance: FactProvenanceType = FactProvenanceType.USER_CLAIM,
    bom_components: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[ProductFact], str, str, Optional[str], Optional[str]]:
    """Extract granular typed facts with provenance and confidence from input text and BOM."""
    clean_text, injection_warnings = fact_anomaly_detector.sanitize_adversarial_input(text)
    raw_lower = clean_text.lower()

    facts: List[ProductFact] = []
    product_name = "Specified Product"
    category = "General Goods"
    sub_category = None
    intended_use = None

    # 1. Product Classification
    if any(k in raw_lower for k in ["kettle", "electric kettle"]):
        product_name = "Electric Kettle"
        category = "Electrical & Domestic Appliances"
        sub_category = "Water Heating Appliances"
        intended_use = "domestic_boiling"
    elif any(k in raw_lower for k in ["immersion water heater", "water heater", "immersion heater"]):
        product_name = "Electric Immersion Water Heater"
        category = "Kitchen & Domestic Appliances"
        sub_category = "Liquid Heating Appliances"
        intended_use = "domestic_water_heating"
    elif any(k in raw_lower for k in ["flask", "bottle", "drinkware", "thermos", "is 17526"]):
        product_name = "Vacuum Insulated Flask"
        category = "Drinkware & Food Contact Containers"
        sub_category = "Vacuum Insulated Containers"
        intended_use = "domestic_drinking"
    elif any(k in raw_lower for k in ["helmet", "headgear"]):
        product_name = "Two-Wheeler Protective Helmet"
        category = "Protective Equipment & Helmets"
        sub_category = "Rider Protective Equipment"
        intended_use = "motorcycle_safety"

    # 2. Extract Electrical Ratings
    elec_data = normalize_electrical(clean_text)
    if "voltage" in elec_data:
        facts.append(
            ProductFact(
                fact_id="FACT-VOLTAGE-01",
                field_name="rated_voltage",
                display_name="Rated Supply Voltage",
                value=elec_data["voltage"],
                raw_value=elec_data.get("voltage"),
                unit=elec_data.get("voltage_unit", "V"),
                source=source_name,
                provenance=default_provenance,
                confidence=0.95,
                verification_state=FactVerificationState.NEEDS_CONFIRMATION,
            )
        )
    if "wattage" in elec_data:
        facts.append(
            ProductFact(
                fact_id="FACT-POWER-01",
                field_name="rated_power_input",
                display_name="Rated Power Input / Wattage",
                value=elec_data["wattage"],
                raw_value=str(elec_data.get("wattage")),
                unit=elec_data.get("wattage_unit", "W"),
                source=source_name,
                provenance=default_provenance,
                confidence=0.95,
                verification_state=FactVerificationState.NEEDS_CONFIRMATION,
            )
        )
    if "frequency" in elec_data:
        facts.append(
            ProductFact(
                fact_id="FACT-FREQ-01",
                field_name="rated_frequency",
                display_name="Rated Operating Frequency",
                value=elec_data["frequency"],
                raw_value=str(elec_data.get("frequency")),
                unit=elec_data.get("frequency_unit", "Hz"),
                source=source_name,
                provenance=default_provenance,
                confidence=0.95,
                verification_state=FactVerificationState.NEEDS_CONFIRMATION,
            )
        )

    # 3. Extract Capacity
    cap_match = re.search(r"(\d+(?:\.\d+)?\s*(?:ml|millilitres?|litres?|liter|l)\b)", raw_lower)
    if cap_match:
        cap_val, cap_unit = normalize_capacity(cap_match.group(1))
        if cap_val is not None:
            facts.append(
                ProductFact(
                    fact_id="FACT-CAPACITY-01",
                    field_name="nominal_capacity",
                    display_name="Nominal Fluid Capacity",
                    value=cap_val,
                    raw_value=str(cap_val),
                    unit=cap_unit or "ml",
                    source=source_name,
                    provenance=default_provenance,
                    confidence=0.98,
                    verification_state=FactVerificationState.NEEDS_CONFIRMATION,
                )
            )

    # 4. Extract Materials
    for mat_candidate in ["stainless steel 304", "ss 304", "stainless steel 316", "polypropylene", "copper", "aluminum", "silicone"]:
        if mat_candidate in raw_lower:
            norm_mat = normalize_material(mat_candidate)
            field = "inner_lining_material" if "flask" in product_name.lower() else "sheath_material"
            facts.append(
                ProductFact(
                    fact_id=f"FACT-MAT-{len(facts)+1}",
                    field_name=field,
                    display_name="Primary Construction Material",
                    value=norm_mat,
                    raw_value=mat_candidate,
                    source=source_name,
                    provenance=default_provenance,
                    confidence=0.90,
                    verification_state=FactVerificationState.NEEDS_CONFIRMATION,
                )
            )
            break

    # 5. Extract BOM Facts if available (and detect conflicts!)
    if bom_components:
        for c in bom_components:
            part_name = c.get("name", "")
            part_spec = c.get("specification", "")

            bom_elec = normalize_electrical(part_spec)
            if "wattage" in bom_elec:
                facts.append(
                    ProductFact(
                        fact_id=f"FACT-BOM-POWER-{len(facts)+1}",
                        field_name="rated_power_input",
                        display_name="Heating Element Wattage (BOM)",
                        value=bom_elec["wattage"],
                        raw_value=part_spec,
                        unit="W",
                        source=f"BOM Part {c.get('part_number', '')} ({part_name})",
                        provenance=FactProvenanceType.BOM_FACT,
                        confidence=0.98,
                        verification_state=FactVerificationState.NEEDS_CONFIRMATION,
                    )
                )

    # 6. Calculate DERIVED_VALUE facts deterministically (Never invent!)
    p_fact = next((f for f in facts if f.field_name == "rated_power_input" and f.value), None)
    v_fact = next((f for f in facts if f.field_name == "rated_voltage" and f.value), None)
    if p_fact and v_fact:
        try:
            p_num = float(p_fact.value)
            v_num = float(str(v_fact.value).split("-")[0])
            if v_num > 0:
                current_calc = round(p_num / v_num, 2)
                facts.append(
                    ProductFact(
                        fact_id="FACT-DERIVED-CURRENT-01",
                        field_name="nominal_current_calculated",
                        display_name="Calculated Nominal Operating Current",
                        value=current_calc,
                        unit="A",
                        source="Deterministic Ohm's Law Calculator",
                        provenance=FactProvenanceType.DERIVED_VALUE,
                        confidence=1.0,
                        verification_state=FactVerificationState.CONFIRMED,
                        derivation_rule="Current (A) = Rated Power (W) / Supply Voltage (V)",
                        source_fact_ids=[p_fact.fact_id, v_fact.fact_id],
                    )
                )
        except Exception:
            pass

    # 7. Check physical plausibility and cross-source conflicts
    facts = fact_anomaly_detector.validate_facts_plausibility(facts, category)
    facts = fact_anomaly_detector.detect_conflicts_between_facts(facts)

    return facts, product_name, category, sub_category, intended_use


def extract_product_dna_from_text(
    text: str,
    source_document: Optional[str] = None,
    source_page: Optional[int] = None,
    bom_components: Optional[List[Dict[str, Any]]] = None,
) -> ProductDNACore:
    """Complete product DNA extractor ensuring 100% backward compatibility and rich facts."""
    prov_type = (
        ProvenanceClassification.DOCUMENT_EVIDENCE
        if source_document
        else ProvenanceClassification.USER_CLAIM
    )

    clean_text, _ = fact_anomaly_detector.sanitize_adversarial_input(text)
    raw_lower = clean_text.lower()
    attributes: List[DNAAttribute] = []
    materials: List[str] = []

    # 1. Product Name & Category detection
    product_name = "Specified Product"
    category = "General Goods"
    sub_category = None
    intended_use = None
    insulated = False
    electrical = False

    # Drinkware / Flasks / Bottles / Standards Queries
    if any(k in raw_lower for k in ["flask", "bottle", "drinkware", "cooler", "sipper", "thermos", "heat retention", "leakage test", "is 17526", "clause 4.2.1", "clause 5.2", "clause 5.4"]):
        category = "Drinkware & Food Contact Containers"
        sub_category = "Vacuum Insulated Containers"
        if "flask" in raw_lower:
            product_name = "Vacuum Insulated Flask"
        elif "bottle" in raw_lower:
            product_name = "Vacuum Insulated Bottle"
        elif "thermos" in raw_lower:
            product_name = "Vacuum Insulated Thermos"
        else:
            product_name = "Drinkware Container"

        if any(k in raw_lower for k in ["domestic", "household", "drinking", "personal"]):
            intended_use = "domestic_drinking"
        elif "commercial" in raw_lower:
            intended_use = "commercial_beverage"
        elif "general storage" in raw_lower or "chemical" in raw_lower:
            intended_use = "general_storage"

        if any(k in raw_lower for k in ["insulated", "vacuum", "double wall", "double-wall", "thermal", "heat retention", "thermos"]):
            insulated = True

    # Electrical Appliances
    elif any(k in raw_lower for k in ["kettle", "toaster", "heater", "iron", "geyser", "oven"]):
        category = "Electrical & Domestic Appliances"
        electrical = True
        if "kettle" in raw_lower:
            product_name = "Electric Kettle"
            sub_category = "Water Heating Appliances"
        elif "toaster" in raw_lower:
            product_name = "Electric Toaster"
        if "domestic" in raw_lower or "household" in raw_lower:
            intended_use = "domestic_household"

    # Toys & Children's Products
    elif any(k in raw_lower for k in ["toy", "toys", "rattle", "plush", "doll", "puzzle", "teether"]):
        category = "Toys & Children's Products"
        product_name = "Children's Toy"
        sub_category = "Play and Learning Goods"
        intended_use = "children_play"

    # Protective Equipment & Helmets
    elif any(k in raw_lower for k in ["helmet", "helmets", "headgear"]):
        category = "Protective Equipment & Helmets"
        product_name = "Two-Wheeler Protective Helmet"
        sub_category = "Rider Protective Equipment"
        intended_use = "motorcycle_safety"

    # Material Extraction
    raw_materials = []
    if re.search(r"\b(grade\s*304|ss\s*304|304\s*stainless|stainless[-\s]*steel\s*304|18/8\s*(?:austenitic\s*)?stainless)\b", raw_lower):
        raw_materials.append("Stainless Steel Grade 304")
    elif re.search(r"\b(stainless[-\s]*steel|ss|stainless\s*liner)\b", raw_lower):
        raw_materials.append("Stainless Steel")

    if re.search(r"\b(polypropylene|pp\b|bpa-free\s*plastic)", raw_lower):
        raw_materials.append("Polypropylene")
    if re.search(r"\b(silicone|food-grade\s*silicone)", raw_lower):
        raw_materials.append("Food-grade Silicone")
    if re.search(r"\b(copper)\b", raw_lower):
        raw_materials.append("Copper")
    if re.search(r"\b(aluminum|aluminium)\b", raw_lower):
        raw_materials.append("Aluminum")

    materials = [normalize_material(m) for m in raw_materials]

    # Material attribute with provenance
    if materials:
        attributes.append(
            DNAAttribute(
                name="materials",
                value=materials,
                data_type="list",
                unit=None,
                provenance=AttributeProvenance(
                    provenance_type=prov_type,
                    source_document=source_document,
                    page=source_page,
                    source_text=text[:200],
                    confidence=0.95,
                    extraction_method="rule_based_parse",
                ),
            )
        )

    # 2. Capacity Extraction
    cap_match = re.search(r"(\d+(?:\.\d+)?\s*(?:ml|millilitres?|litres?|liter|l)\b)", raw_lower)
    if cap_match:
        cap_val, cap_unit = normalize_capacity(cap_match.group(1))
        if cap_val is not None:
            attributes.append(
                DNAAttribute(
                    name="capacity_ml",
                    value=cap_val,
                    data_type="integer",
                    unit=cap_unit or "ml",
                    provenance=AttributeProvenance(
                        provenance_type=prov_type,
                        source_document=source_document,
                        page=source_page,
                        source_text=cap_match.group(0),
                        confidence=0.98,
                        extraction_method="structured_regex",
                    ),
                )
            )

    # 3. Electrical Characteristics Extraction
    if electrical or re.search(r"(\d+\s*v(?:olts)?|\d+\s*hz|\d+\s*w(?:atts)?)", raw_lower):
        elec_info = normalize_electrical(text)
        if "voltage" in elec_info:
            attributes.append(
                DNAAttribute(
                    name="voltage",
                    value=elec_info["voltage"],
                    data_type="string",
                    unit=elec_info.get("voltage_unit", "V"),
                    provenance=AttributeProvenance(
                        provenance_type=prov_type,
                        source_document=source_document,
                        page=source_page,
                        source_text=text[:150],
                        confidence=0.96,
                        extraction_method="structured_regex",
                    ),
                )
            )
        if "wattage" in elec_info:
            attributes.append(
                DNAAttribute(
                    name="wattage",
                    value=elec_info["wattage"],
                    data_type="integer",
                    unit=elec_info.get("wattage_unit", "W"),
                    provenance=AttributeProvenance(
                        provenance_type=prov_type,
                        source_document=source_document,
                        page=source_page,
                        source_text=text[:150],
                        confidence=0.96,
                        extraction_method="structured_regex",
                    ),
                )
            )

    # 4. Insulation Flag Attribute
    if insulated:
        attributes.append(
            DNAAttribute(
                name="insulated",
                value=True,
                data_type="boolean",
                unit=None,
                provenance=AttributeProvenance(
                    provenance_type=prov_type,
                    source_document=source_document,
                    page=source_page,
                    source_text=text[:150],
                    confidence=0.95,
                    extraction_method="keyword_inference",
                ),
            )
        )

    # 5. Food Contact Safety Flag
    if any(k in raw_lower for k in ["food contact", "drinking", "beverage", "flask", "bottle"]):
        attributes.append(
            DNAAttribute(
                name="food_contact",
                value=True,
                data_type="boolean",
                unit=None,
                provenance=AttributeProvenance(
                    provenance_type=prov_type,
                    source_document=source_document,
                    page=source_page,
                    source_text=text[:150],
                    confidence=0.92,
                    extraction_method="contextual_parse",
                ),
            )
        )

    # Also build the rich ProductFact list for Layer 2
    facts, _, _, _, _ = extract_structured_facts_from_payload(
        text=text,
        source_name=source_document,
        default_provenance=(
            FactProvenanceType.VERIFIED_DOCUMENT_FACT
            if source_document
            else FactProvenanceType.USER_CLAIM
        ),
        bom_components=bom_components,
    )

    return ProductDNACore(
        product_name=product_name,
        category=category,
        sub_category=sub_category,
        intended_use=intended_use,
        materials=materials,
        electrical=electrical,
        insulated=insulated,
        attributes=attributes,
        pending_clarifications=[],
        version="v1.0",
        facts=facts,
    )
