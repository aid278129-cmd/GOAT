"""Normative and Allied Standards Relationship Graph for Bureau of Indian Standards (BIS).

Maintains deterministic inter-standard relationships:
- PRIMARY_STANDARD
- NORMATIVE_REFERENCE
- RELATED_STANDARD
- SUPERSEDES
- SUPERSEDED_BY
- AMENDMENT_OF
- APPLICABILITY_DEPENDENCY

Critical Invariants:
1. Do not treat every referenced standard as automatically applicable to the parent product.
2. A normative reference is a dependency candidate, not automatic primary applicability.
3. Designed as a deterministic relational model that can later be projected directly into Neo4j.
"""

from typing import Dict, List, Optional, Tuple
from backend.app.services.applicability.applicability_models import (
    NormativeRelationType,
    NormativeStandardReference,
    NormativeDependencyStatus,
    StandardStatus,
)


# Deterministic Directed Relationship Graph: Standard -> List of outgoing references
BIS_RELATIONSHIP_GRAPH: Dict[str, List[NormativeStandardReference]] = {
    # 1. Domestic Stainless Steel Vacuum Flasks (IS 17526:2021)
    "IS 17526:2021": [
        NormativeStandardReference(
            standard_number="IS 6911:2017",
            title="Stainless Steel Plate, Sheet and Strip - Specification",
            relationship_type=NormativeRelationType.NORMATIVE_REFERENCE,
            clause_reference="Clause 4.1 / 4.2.1",
            description="Normative requirement for inner liner food contact grade 304 / 316 stainless steel.",
            is_mandatory_dependency=True,
            dependency_condition="Applies to inner liner material specification.",
            standard_status=StandardStatus.ACTIVE,
        ),
        NormativeStandardReference(
            standard_number="IS 9845:1998",
            title="Overall Migration Testing for Food-Contact Plastics and Elastomers",
            relationship_type=NormativeRelationType.NORMATIVE_REFERENCE,
            clause_reference="Clause 4.3",
            description="Normative test method for food-grade silicone seals and lid gaskets.",
            is_mandatory_dependency=True,
            dependency_condition="Applies if product includes non-metallic seals or lid gaskets in food contact.",
            standard_status=StandardStatus.ACTIVE,
        ),
        NormativeStandardReference(
            standard_number="IS 17526:2021/Amd 1:2023",
            title="Domestic Stainless Steel Vacuum Flask/Bottle - Amendment No. 1",
            relationship_type=NormativeRelationType.AMENDMENT_OF,
            clause_reference="Clause 5.4 / Table 1",
            description="Official gazette amendment revising thermal insulation retention tolerances.",
            is_mandatory_dependency=True,
            dependency_condition="Active gazette amendment.",
            standard_status=StandardStatus.ACTIVE,
        ),
    ],

    # 2. Electric Immersion Water Heaters (IS 302-2-201:2008)
    "IS 302-2-201:2008": [
        NormativeStandardReference(
            standard_number="IS 302-1:2008",
            title="Safety of Household and Similar Electrical Appliances - General Requirements",
            relationship_type=NormativeRelationType.PRIMARY_STANDARD,
            clause_reference="General / Scope",
            description="Normative parent general safety standard. Particular requirements supplement or modify Part 1.",
            is_mandatory_dependency=True,
            dependency_condition="Mandatory base standard for all electrical appliances.",
            standard_status=StandardStatus.ACTIVE,
        ),
        NormativeStandardReference(
            standard_number="IS 694:2010",
            title="Polyvinyl Chloride Insulated Cables/Cords up to 1100 V",
            relationship_type=NormativeRelationType.NORMATIVE_REFERENCE,
            clause_reference="Clause 25.1",
            description="Normative standard for 3-core PVC insulated flexible power supply cord with earthing conductor.",
            is_mandatory_dependency=True,
            dependency_condition="Applies to external flexible power cord subcomponent.",
            standard_status=StandardStatus.ACTIVE,
        ),
        NormativeStandardReference(
            standard_number="IS 1293:2019",
            title="Plugs and Socket-Outlets of Rated Voltage up to 250 V and Current up to 16 A",
            relationship_type=NormativeRelationType.NORMATIVE_REFERENCE,
            clause_reference="Clause 25.7",
            description="Normative standard for 3-pin 6 A / 16 A plug top attachment.",
            is_mandatory_dependency=True,
            dependency_condition="Applies to plug top termination subcomponent.",
            standard_status=StandardStatus.ACTIVE,
        ),
    ],

    # 3. Appliances for Heating Liquids (IS 302-2-15:2009)
    "IS 302-2-15:2009": [
        NormativeStandardReference(
            standard_number="IS 302-1:2008",
            title="Safety of Household and Similar Electrical Appliances - General Requirements",
            relationship_type=NormativeRelationType.PRIMARY_STANDARD,
            clause_reference="General / Scope",
            description="Normative parent general safety standard for liquid heaters.",
            is_mandatory_dependency=True,
            dependency_condition="Mandatory general safety foundation.",
            standard_status=StandardStatus.ACTIVE,
        ),
        NormativeStandardReference(
            standard_number="IS 1293:2019",
            title="Plugs and Socket-Outlets",
            relationship_type=NormativeRelationType.NORMATIVE_REFERENCE,
            clause_reference="Clause 25",
            description="Normative plug top requirement.",
            is_mandatory_dependency=True,
            dependency_condition="Subcomponent plug attachment.",
            standard_status=StandardStatus.ACTIVE,
        ),
    ],

    # 4. Toys Mechanical Safety (IS 9873 (Part 1):2019)
    "IS 9873 (Part 1):2019": [
        NormativeStandardReference(
            standard_number="IS 9873 (Part 2):2017",
            title="Safety of Toys - Part 2: Flammability",
            relationship_type=NormativeRelationType.RELATED_STANDARD,
            clause_reference="Cross-Reference",
            description="Allied standard covering toy flammability testing.",
            is_mandatory_dependency=False,
            dependency_condition="Evaluated if toy contains textile, plush, or flammable polymers.",
            standard_status=StandardStatus.ACTIVE,
        ),
        NormativeStandardReference(
            standard_number="IS 9873 (Part 3):2020",
            title="Safety of Toys - Part 3: Migration of Certain Elements",
            relationship_type=NormativeRelationType.NORMATIVE_REFERENCE,
            clause_reference="Normative Chemical",
            description="Normative heavy metal migration limits for toy materials and paints.",
            is_mandatory_dependency=True,
            dependency_condition="Mandatory for all toy surfaces accessible to children.",
            standard_status=StandardStatus.ACTIVE,
        ),
    ],

    # 5. Protective Helmets (IS 4151:2015)
    "IS 4151:2015": [
        NormativeStandardReference(
            standard_number="IS 4151:1993",
            title="Protective Helmets for Motorcycle Riders (Third Revision)",
            relationship_type=NormativeRelationType.SUPERSEDES,
            clause_reference="Foreword",
            description="Superseded previous edition withdrawn by BIS upon publication of fourth revision.",
            is_mandatory_dependency=False,
            dependency_condition="Historical supersession.",
            standard_status=StandardStatus.SUPERSEDED,
        ),
    ],

    # 6. Domestic Pressure Cookers (IS 2347:2017)
    "IS 2347:2017": [
        NormativeStandardReference(
            standard_number="IS 2347:2006",
            title="Domestic Pressure Cookers - Specification (Fourth Revision)",
            relationship_type=NormativeRelationType.SUPERSEDES,
            clause_reference="Foreword",
            description="Superseded previous edition.",
            is_mandatory_dependency=False,
            dependency_condition="Historical supersession.",
            standard_status=StandardStatus.SUPERSEDED,
        ),
    ],
}


def get_normative_references_for_standard(std_number: str) -> List[NormativeStandardReference]:
    """Retrieve all normative references and allied relationships for a standard."""
    clean = std_number.strip()
    if clean in BIS_RELATIONSHIP_GRAPH:
        return BIS_RELATIONSHIP_GRAPH[clean]
    
    # Try match without revision year
    prefix = clean.split(":")[0]
    for key, refs in BIS_RELATIONSHIP_GRAPH.items():
        if key.split(":")[0] == prefix:
            return refs
    return []


def get_allied_standards(std_number: str, relation_filter: Optional[NormativeRelationType] = None) -> List[NormativeStandardReference]:
    """Retrieve filtered relationships for a standard."""
    refs = get_normative_references_for_standard(std_number)
    if relation_filter is None:
        return refs
    return [r for r in refs if r.relationship_type == relation_filter]


def check_normative_dependency_satisfaction(
    std_number: str,
    declared_subcomponents: List[str],
) -> Tuple[NormativeDependencyStatus, List[str]]:
    """Evaluate whether product satisfies subcomponent normative references."""
    refs = get_normative_references_for_standard(std_number)
    mandatory_refs = [r for r in refs if r.is_mandatory_dependency and r.relationship_type == NormativeRelationType.NORMATIVE_REFERENCE]
    
    if not mandatory_refs:
        return NormativeDependencyStatus.PRIMARY_ONLY, []
    
    unmet: List[str] = []
    subcomps_lower = [s.lower() for s in declared_subcomponents]
    
    for r in mandatory_refs:
        std_clean = r.standard_number.lower()
        matched = any(std_clean in sc or r.standard_number.split(":")[0].lower() in sc for sc in subcomps_lower)
        if not matched:
            unmet.append(f"{r.standard_number} ({r.description})")
    
    if unmet:
        return NormativeDependencyStatus.HAS_NORMATIVE_DEPENDENCIES, unmet
    return NormativeDependencyStatus.HAS_NORMATIVE_DEPENDENCIES, []
