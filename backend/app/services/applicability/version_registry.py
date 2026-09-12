"""Standard Version & Revision Registry for Bureau of Indian Standards (BIS).

Maintains authoritative metadata regarding standard editions, revisions,
gazette notifications, active statuses, supersessions, and amendments.

Critical Invariants:
1. Withdrawn/superseded standards must NEVER silently become current applicable standards.
2. An obsolete standard revision must be explicitly flagged with StandardStatus.SUPERSEDED.
3. Superseded standards must point to their active replacement standard where codified.
4. Acquisition-pending standards must preserve their ACQUISITION_PENDING status without fabrication.
"""

from typing import Dict, List, Optional, Tuple
from backend.app.services.applicability.applicability_models import (
    StandardStatus,
    StandardRevisionInfo,
)


# Authoritative catalog of BIS standards, versions, and lifecycle statuses
BIS_VERSION_REGISTRY: Dict[str, StandardRevisionInfo] = {
    # 1. Domestic Stainless Steel Vacuum Flasks
    "IS 17526:2021": StandardRevisionInfo(
        standard_number="IS 17526:2021",
        standard_title="Domestic Stainless Steel Vacuum Flask/Bottle - Specification",
        revision_edition="First Edition (2021)",
        status=StandardStatus.ACTIVE,
        publication_year=2021,
        effective_date="2021-08-15",
        superseded_by=None,
        supersedes=None,
        amendments=["Amendment No. 1 (August 2023)"],
        gazette_order_ref="DPIIT S.O. 4452(E) dated 2023-10-10",
        provenance="Bureau of Indian Standards / Gazette of India",
    ),
    # 2. Electric Immersion Water Heaters
    "IS 302-2-201:2008": StandardRevisionInfo(
        standard_number="IS 302-2-201:2008",
        standard_title="Safety of Household and Similar Electrical Appliances - Particular Requirements for Electric Immersion Water Heaters",
        revision_edition="Edition 2.0 (Reaffirmed 2019)",
        status=StandardStatus.ACTIVE,
        publication_year=2008,
        effective_date="2008-05-20",
        superseded_by=None,
        supersedes="IS 302-2-201:1992",
        amendments=["Amendment No. 1 (2012)", "Amendment No. 2 (2018)"],
        gazette_order_ref="Electrical Appliances (Quality Control) Order, 2003 (S.O. 189(E))",
        provenance="Bureau of Indian Standards",
    ),
    # 3. Electric Appliances General Safety
    "IS 302-1:2008": StandardRevisionInfo(
        standard_number="IS 302-1:2008",
        standard_title="Safety of Household and Similar Electrical Appliances - General Requirements",
        revision_edition="Edition 6.0",
        status=StandardStatus.ACTIVE,
        publication_year=2008,
        effective_date="2008-01-01",
        superseded_by=None,
        supersedes="IS 302-1:1979",
        amendments=["Amendment No. 1 (2015)"],
        gazette_order_ref="Electrical Appliances (Quality Control) Order",
        provenance="Bureau of Indian Standards",
    ),
    # 4. Appliances for Heating Liquids
    "IS 302-2-15:2009": StandardRevisionInfo(
        standard_number="IS 302-2-15:2009",
        standard_title="Safety of Household and Similar Electrical Appliances - Particular Requirements for Appliances for Heating Liquids",
        revision_edition="Edition 3.0",
        status=StandardStatus.ACTIVE,
        publication_year=2009,
        effective_date="2009-06-01",
        superseded_by=None,
        supersedes="IS 302-2-15:1998",
        amendments=[],
        gazette_order_ref="Electrical Appliances for Domestic Use (Quality Control) Order",
        provenance="Bureau of Indian Standards",
    ),
    # 5. Safety of Toys - Mechanical and Physical Properties
    "IS 9873 (Part 1):2019": StandardRevisionInfo(
        standard_number="IS 9873 (Part 1):2019",
        standard_title="Safety of Toys - Part 1: Safety Aspects Related to Mechanical and Physical Properties",
        revision_edition="Third Revision",
        status=StandardStatus.ACTIVE,
        publication_year=2019,
        effective_date="2019-11-01",
        superseded_by=None,
        supersedes="IS 9873 (Part 1):2012",
        amendments=["Amendment No. 1 (2020)"],
        gazette_order_ref="Toys (Quality Control) Order, 2020 (S.O. 858(E))",
        provenance="Bureau of Indian Standards / DPIIT",
    ),
    # 6. Safety of Toys - Superseded Revision
    "IS 9873 (Part 1):2012": StandardRevisionInfo(
        standard_number="IS 9873 (Part 1):2012",
        standard_title="Safety of Toys - Part 1: Safety Aspects Related to Mechanical and Physical Properties (Second Revision)",
        revision_edition="Second Revision (2012)",
        status=StandardStatus.SUPERSEDED,
        publication_year=2012,
        effective_date="2012-07-01",
        superseded_by="IS 9873 (Part 1):2019",
        supersedes="IS 9873 (Part 1):2001",
        amendments=[],
        gazette_order_ref=None,
        provenance="Bureau of Indian Standards",
    ),
    # 7. Protective Helmets for Two Wheeler Riders - Current
    "IS 4151:2015": StandardRevisionInfo(
        standard_number="IS 4151:2015",
        standard_title="Protective Helmets for Two Wheeler Riders - Specification",
        revision_edition="Fourth Revision",
        status=StandardStatus.ACTIVE,
        publication_year=2015,
        effective_date="2016-03-01",
        superseded_by=None,
        supersedes="IS 4151:1993",
        amendments=["Amendment No. 1 (2018)", "Amendment No. 2 (2020)"],
        gazette_order_ref="Helmet (Quality Control) Order, 2020 (MoRTH)",
        provenance="Bureau of Indian Standards / MoRTH",
    ),
    # 8. Protective Helmets - Superseded / Withdrawn Revision
    "IS 4151:1993": StandardRevisionInfo(
        standard_number="IS 4151:1993",
        standard_title="Protective Helmets for Motorcycle Riders (Third Revision)",
        revision_edition="Third Revision (1993)",
        status=StandardStatus.SUPERSEDED,
        publication_year=1993,
        effective_date="1993-11-01",
        superseded_by="IS 4151:2015",
        supersedes="IS 4151:1982",
        amendments=[],
        gazette_order_ref=None,
        provenance="Bureau of Indian Standards",
    ),
    # 9. Domestic Pressure Cookers - Current
    "IS 2347:2017": StandardRevisionInfo(
        standard_number="IS 2347:2017",
        standard_title="Domestic Pressure Cookers - Specification",
        revision_edition="Fifth Revision",
        status=StandardStatus.ACTIVE,
        publication_year=2017,
        effective_date="2017-09-01",
        superseded_by=None,
        supersedes="IS 2347:2006",
        amendments=["Amendment No. 1 (2020)"],
        gazette_order_ref="Domestic Pressure Cooker (Quality Control) Order, 2020",
        provenance="Bureau of Indian Standards / DPIIT",
    ),
    # 10. Domestic Pressure Cookers - Superseded Revision
    "IS 2347:2006": StandardRevisionInfo(
        standard_number="IS 2347:2006",
        standard_title="Domestic Pressure Cookers - Specification (Fourth Revision)",
        revision_edition="Fourth Revision (2006)",
        status=StandardStatus.SUPERSEDED,
        publication_year=2006,
        effective_date="2006-04-01",
        superseded_by="IS 2347:2017",
        supersedes="IS 2347:1987",
        amendments=[],
        gazette_order_ref=None,
        provenance="Bureau of Indian Standards",
    ),
    # 11. PVC Insulated Cables (Normative Reference)
    "IS 694:2010": StandardRevisionInfo(
        standard_number="IS 694:2010",
        standard_title="Polyvinyl Chloride Insulated Unsheathed and Sheathed Cables/Cords with Rigid and Flexible Conductors for Working Voltages up to and Including 1100 V - Specification",
        revision_edition="Fourth Revision",
        status=StandardStatus.ACTIVE,
        publication_year=2010,
        effective_date="2010-04-01",
        superseded_by=None,
        supersedes="IS 694:1990",
        amendments=[],
        gazette_order_ref="Cables (Quality Control) Order",
        provenance="Bureau of Indian Standards",
    ),
    # 12. Plugs and Socket-Outlets (Normative Reference) - Current
    "IS 1293:2019": StandardRevisionInfo(
        standard_number="IS 1293:2019",
        standard_title="Plugs and Socket-Outlets of Rated Voltage up to and Including 250 Volts and Rated Current up to and Including 16 Amperes - Specification",
        revision_edition="Fourth Revision",
        status=StandardStatus.ACTIVE,
        publication_year=2019,
        effective_date="2019-12-01",
        superseded_by=None,
        supersedes="IS 1293:2005",
        amendments=["Amendment No. 1 (2021)"],
        gazette_order_ref="Electrical Accessories (Quality Control) Order, 2020",
        provenance="Bureau of Indian Standards",
    ),
    # 13. Plugs and Socket-Outlets - Superseded
    "IS 1293:2005": StandardRevisionInfo(
        standard_number="IS 1293:2005",
        standard_title="Plugs and Socket-Outlets for Household and Similar Purposes - Specification (Third Revision)",
        revision_edition="Third Revision (2005)",
        status=StandardStatus.SUPERSEDED,
        publication_year=2005,
        effective_date="2005-08-01",
        superseded_by="IS 1293:2019",
        supersedes="IS 1293:1988",
        amendments=[],
        gazette_order_ref=None,
        provenance="Bureau of Indian Standards",
    ),
    # 14. Stainless Steel Plate, Sheet, Strip (Normative Reference)
    "IS 6911:2017": StandardRevisionInfo(
        standard_number="IS 6911:2017",
        standard_title="Stainless Steel Plate, Sheet and Strip - Specification",
        revision_edition="Second Revision",
        status=StandardStatus.ACTIVE,
        publication_year=2017,
        effective_date="2017-10-01",
        superseded_by=None,
        supersedes="IS 6911:1992",
        amendments=[],
        gazette_order_ref="Steel and Steel Products (Quality Control) Order",
        provenance="Bureau of Indian Standards",
    ),
    # 15. Overall Migration Testing (Normative Reference)
    "IS 9845:1998": StandardRevisionInfo(
        standard_number="IS 9845:1998",
        standard_title="Method of Analysis for the Determination of Specific and/or Overall Migration of Constituents of Plastics and Elastomers Intended to Come into Contact with Foodstuffs",
        revision_edition="Second Revision (Reaffirmed 2019)",
        status=StandardStatus.ACTIVE,
        publication_year=1998,
        effective_date="1998-05-01",
        superseded_by=None,
        supersedes=None,
        amendments=[],
        gazette_order_ref=None,
        provenance="Bureau of Indian Standards",
    ),
    # 16. LED Lamps (Acquisition Pending / Catalog Only)
    "IS 16102 (Part 1):2012": StandardRevisionInfo(
        standard_number="IS 16102 (Part 1):2012",
        standard_title="Self-Ballasted LED Lamps for General Lighting Services - Part 1: Safety Requirements",
        revision_edition="First Edition",
        status=StandardStatus.ACQUISITION_PENDING,
        publication_year=2012,
        effective_date="2012-09-01",
        superseded_by=None,
        supersedes=None,
        amendments=["Amendment No. 1 (2017)"],
        gazette_order_ref="Electronics and Information Technology Goods (Compulsory Registration Order), 2012",
        provenance="Bureau of Indian Standards / MeitY",
    ),
}


def normalize_standard_key(std_number: str) -> str:
    """Normalize standard number string for robust key lookup."""
    clean = std_number.strip()
    clean = " ".join(clean.split())
    return clean


def get_standard_revision_info(std_number: str) -> Optional[StandardRevisionInfo]:
    """Retrieve authoritative revision and status info for a standard."""
    key = normalize_standard_key(std_number)
    if key in BIS_VERSION_REGISTRY:
        return BIS_VERSION_REGISTRY[key]
    
    for reg_key, info in BIS_VERSION_REGISTRY.items():
        if key == reg_key.split(":")[0]:
            return info
    return None


def is_standard_superseded(std_number: str) -> Tuple[bool, Optional[str]]:
    """Determine if standard is superseded and return active replacement if known."""
    info = get_standard_revision_info(std_number)
    if not info:
        return False, None
    if info.status == StandardStatus.SUPERSEDED:
        return True, info.superseded_by
    return False, None


def is_standard_withdrawn(std_number: str) -> bool:
    """Determine if standard has been formally withdrawn without replacement."""
    info = get_standard_revision_info(std_number)
    return info is not None and info.status == StandardStatus.WITHDRAWN


def is_standard_verified_in_catalog(std_number: str) -> bool:
    """Check if standard exists in the authoritative verified registry."""
    return get_standard_revision_info(std_number) is not None


def get_active_replacement(std_number: str) -> Optional[str]:
    """Return active replacement standard for a superseded standard."""
    is_sup, rep = is_standard_superseded(std_number)
    return rep if is_sup else None
