"""Product Category Taxonomy and Required Attribute Profiles for Indian Standards.

Defines:
1. Canonical product categories, aliases, and distinguishing features.
2. RequiredAttributeProfile specifying blocking, conditional, and optional attributes per standard.
3. Attribute status states: KNOWN | UNKNOWN | MISSING | CONFLICTING | NOT_PROVIDED | NOT_APPLICABLE_TO_THIS_RULE
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class AttributeState(str, Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
    NOT_PROVIDED = "NOT_PROVIDED"
    NOT_APPLICABLE_TO_THIS_RULE = "NOT_APPLICABLE_TO_THIS_RULE"


class RequiredAttributeProfile(BaseModel):
    """Deterministic profile specifying required product attributes for standard applicability."""
    standard_or_rule_id: str
    product_category: str
    blocking_attributes: List[str] = Field(description="Attributes strictly required to establish applicability")
    conditionally_required_attributes: Dict[str, str] = Field(
        default_factory=dict,
        description="Attribute -> Condition (e.g. 'capacity_ml' -> 'required if insulated is true')",
    )
    optional_attributes: List[str] = Field(default_factory=list)
    clarification_priority: Dict[str, str] = Field(
        default_factory=dict,
        description="Attribute -> Criticality (HIGH | MEDIUM | LOW)",
    )
    applicability_dependencies: List[str] = Field(default_factory=list)
    evidence_dependencies: List[str] = Field(default_factory=list)


class ProductCategoryDefinition(BaseModel):
    """Controlled Product Taxonomy Category Definition."""
    canonical_category_id: str
    category_name: str
    aliases: List[str] = Field(default_factory=list)
    distinguishing_attributes: List[str] = Field(default_factory=list)
    supported_rules: List[str] = Field(default_factory=list)
    supported_standards: List[str] = Field(default_factory=list)
    coverage_state: str = "COVERED"  # COVERED | PARTIAL_COVERAGE | CATALOG_NOT_COVERED


# ==========================================
# Controlled Taxonomy Registry
# ==========================================

TAXONOMY_REGISTRY: Dict[str, ProductCategoryDefinition] = {
    "CAT-DRINKWARE": ProductCategoryDefinition(
        canonical_category_id="CAT-DRINKWARE",
        category_name="Drinkware & Food Contact Containers",
        aliases=[
            "vacuum flask", "insulated bottle", "thermal thermos", "hydro flask",
            "drinkware", "water bottle", "sipper", "carafe", "insulated jug"
        ],
        distinguishing_attributes=["materials", "insulated", "capacity_ml", "intended_use"],
        supported_rules=["APP-DRINKWARE-001"],
        supported_standards=["IS 17526:2021"],
        coverage_state="COVERED",
    ),
    "CAT-ELECTRICAL": ProductCategoryDefinition(
        canonical_category_id="CAT-ELECTRICAL",
        category_name="Electrical & Domestic Appliances",
        aliases=[
            "electric kettle", "water heater", "geyser", "heating appliance",
            "toaster", "electric iron", "immersion heater"
        ],
        distinguishing_attributes=["electrical", "voltage", "wattage", "product_name"],
        supported_rules=["APP-ELECTRICAL-001", "APP-ELECTRICAL-002"],
        supported_standards=["IS 302-2-15:2009", "IS 302-2-201:2008"],
        coverage_state="COVERED",
    ),
    "CAT-TOYS": ProductCategoryDefinition(
        canonical_category_id="CAT-TOYS",
        category_name="Toys & Children's Products",
        aliases=[
            "toy", "toys", "children toy", "kids toy", "plastic toy", "plush toy",
            "rattle", "doll", "toy car", "puzzle toy", "teether", "action figure"
        ],
        distinguishing_attributes=["target_age_months", "materials", "has_small_parts"],
        supported_rules=["APP-TOYS-001"],
        supported_standards=["IS 9873 (Part 1):2019"],
        coverage_state="COVERED",
    ),
    "CAT-HELMETS": ProductCategoryDefinition(
        canonical_category_id="CAT-HELMETS",
        category_name="Protective Equipment & Helmets",
        aliases=[
            "helmet", "helmets", "two wheeler helmet", "motorcycle helmet", "rider helmet",
            "protective headgear", "scooter helmet", "full face helmet"
        ],
        distinguishing_attributes=["vehicle_type", "materials", "has_visor"],
        supported_rules=["APP-HELMET-001"],
        supported_standards=["IS 4151:2015"],
        coverage_state="COVERED",
    ),
    "CAT-GENERAL-GOODS": ProductCategoryDefinition(
        canonical_category_id="CAT-GENERAL-GOODS",
        category_name="General Goods",
        aliases=["ceramic mug", "glass tumbler", "copper jug", "earthenware pot", "wooden bowl"],
        distinguishing_attributes=["materials"],
        supported_rules=[],
        supported_standards=[],
        coverage_state="CATALOG_NOT_COVERED",
    ),
}

# ==========================================
# Required Attribute Profiles
# ==========================================

REQUIRED_ATTRIBUTE_PROFILES: Dict[str, RequiredAttributeProfile] = {
    "IS 17526:2021": RequiredAttributeProfile(
        standard_or_rule_id="IS 17526:2021",
        product_category="Drinkware & Food Contact Containers",
        blocking_attributes=["materials", "insulated"],
        conditionally_required_attributes={"capacity_ml": "Required to verify <= 1000ml scope limits and thermal test duration"},
        optional_attributes=["intended_use", "color", "stopper_type"],
        clarification_priority={
            "materials": "HIGH",
            "capacity_ml": "MEDIUM",
            "intended_use": "LOW",
        },
        applicability_dependencies=["DPIIT Domestic Water Bottles QCO 2023"],
        evidence_dependencies=["Raw Material Mill Test Certificate (IS 6911)", "Clause 5.4 Heat Retention Test Report"],
    ),
    "IS 302-2-15:2009": RequiredAttributeProfile(
        standard_or_rule_id="IS 302-2-15:2009",
        product_category="Electrical & Domestic Appliances",
        blocking_attributes=["electrical", "voltage"],
        conditionally_required_attributes={"wattage": "Required for heating element endurance check"},
        optional_attributes=["intended_use"],
        clarification_priority={
            "voltage": "HIGH",
            "wattage": "MEDIUM",
        },
        applicability_dependencies=["Electrical Appliances for Domestic Use QCO"],
        evidence_dependencies=["IS 302-1 Electrical Safety Test Report"],
    ),
    "IS 302-2-201:2008": RequiredAttributeProfile(
        standard_or_rule_id="IS 302-2-201:2008",
        product_category="Electrical & Domestic Appliances",
        blocking_attributes=["electrical", "voltage"],
        conditionally_required_attributes={"wattage": "Required for immersion heating element endurance check"},
        optional_attributes=["intended_use"],
        clarification_priority={
            "voltage": "HIGH",
            "wattage": "MEDIUM",
        },
        applicability_dependencies=["Electrical Appliances (Quality Control) Order, 2003 (S.O. 189(E))"],
        evidence_dependencies=["IS 302-1 / IS 302-2-201 Electrical Safety Test Report"],
    ),
    "IS 9873 (Part 1):2019": RequiredAttributeProfile(
        standard_or_rule_id="IS 9873 (Part 1):2019",
        product_category="Toys & Children's Products",
        blocking_attributes=["target_age_months"],
        conditionally_required_attributes={"has_small_parts": "Required to assess choking hazard cylinder test under 36 months"},
        optional_attributes=["materials", "battery_operated"],
        clarification_priority={
            "target_age_months": "HIGH",
            "has_small_parts": "HIGH",
        },
        applicability_dependencies=["DPIIT Toys (Quality Control) Order 2020"],
        evidence_dependencies=["NABL Accredited Mechanical Toy Test Report (Clause 4.4 Small Parts, Clause 4.6 Sharp Edges)"],
    ),
    "IS 4151:2015": RequiredAttributeProfile(
        standard_or_rule_id="IS 4151:2015",
        product_category="Protective Equipment & Helmets",
        blocking_attributes=["vehicle_type"],
        conditionally_required_attributes={"shell_size": "Required for impact drop test headform selection"},
        optional_attributes=["has_visor", "color"],
        clarification_priority={
            "vehicle_type": "HIGH",
            "shell_size": "MEDIUM",
        },
        applicability_dependencies=["MoRTH Protective Helmets for Two-Wheeler Riders QCO 2020"],
        evidence_dependencies=["Accredited Impact Absorption & Retention System Dynamic Test Report"],
    ),
}


def get_taxonomy_category(category_or_text: str) -> Optional[ProductCategoryDefinition]:
    """Find matching canonical taxonomy category using text or category name."""
    clean = category_or_text.lower().strip()
    for cat in TAXONOMY_REGISTRY.values():
        if cat.category_name.lower() == clean:
            return cat
        if any(alias in clean for alias in cat.aliases):
            return cat

    # Check against verified dataset categories
    try:
        from backend.app.services.retrieval.knowledge_registry import search_standards
        matches = search_standards(category_or_text, top_k=1)
        if matches:
            m = matches[0]
            cat_name = m.get("product_category", "Verified BIS Category")
            return ProductCategoryDefinition(
                canonical_category_id=f"CAT-DATASET-{m.get('standard_id')}",
                category_name=cat_name,
                aliases=[m.get("short_title", "").lower(), m.get("standard_number", "").lower()],
                distinguishing_attributes=["product_name", "category"],
                supported_rules=[f"APP-DATASET-{m.get('standard_id')}"],
                supported_standards=[m.get("full_standard_code", m.get("standard_number"))],
                coverage_state="COVERED",
            )
    except Exception:
        pass

    return None


def get_required_attribute_profile(standard_or_rule_id: str) -> Optional[RequiredAttributeProfile]:
    """Lookup RequiredAttributeProfile by standard or rule ID."""
    return REQUIRED_ATTRIBUTE_PROFILES.get(standard_or_rule_id)
