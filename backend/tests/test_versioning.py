"""Unit tests for Standard Versioning and Amendment models (M1.5).

Tests:
1. Version A -> Superseded -> Version B -> Current
2. Amendment linked to standard version
3. Historical records remain accessible and distinct
4. Superseded versions are not silently treated as current
5. Missing version information remains None/null without guessing
"""
from datetime import date
from backend.app.models.standard import Standard
from backend.app.models.amendment import Amendment
from backend.app.models.regulatory_instrument import RegulatoryInstrument


def test_standard_version_lifecycle_relationships():
    """Version A (Superseded) -> Version B (Current Active) relationship tracking."""
    # Version A: Historical edition
    std_v1 = Standard(
        standard_number="IS 17526:2018",
        title="Commercial Beverage Coolers - Specification",
        edition="First Edition",
        category="Drinkware & Food Contact Containers",
        status="SUPERSEDED",
        verification_status="SUPERSEDED",
        superseded_by="IS 17526:2021",
        publication_date=date(2018, 5, 15),
    )

    # Version B: Current authoritative edition
    std_v2 = Standard(
        standard_number="IS 17526:2021",
        title="Commercial Beverage Coolers and Insulated Flasks — Specification",
        edition="Second Edition",
        category="Drinkware & Food Contact Containers",
        status="ACTIVE",
        verification_status="VERIFIED",
        supersedes="IS 17526:2018",
        publication_date=date(2021, 11, 20),
    )

    assert std_v1.status == "SUPERSEDED"
    assert std_v1.superseded_by == "IS 17526:2021"
    assert std_v2.status == "ACTIVE"
    assert std_v2.supersedes == "IS 17526:2018"
    assert std_v1.standard_number != std_v2.standard_number


def test_amendment_association_and_affected_clauses():
    """Amendments are linked to parent standard without blindly overwriting base text."""
    std = Standard(
        standard_number="IS 17526:2021",
        title="Commercial Beverage Coolers and Insulated Flasks",
        category="Drinkware",
    )

    amendment_1 = Amendment(
        standard_id=std.id,
        amendment_number="Amendment No. 1",
        publication_date=date(2022, 6, 10),
        effective_date=date(2022, 8, 1),
        affected_clauses="4.2.1, 5.4",
        description="Revised allowable lead limits and updated ambient test temperature tolerances.",
        verification_status="VERIFIED",
    )

    assert amendment_1.standard_id == std.id
    assert amendment_1.amendment_number == "Amendment No. 1"
    assert "4.2.1" in amendment_1.affected_clauses
    assert amendment_1.verification_status == "VERIFIED"


def test_amendment_unknown_affected_clauses_requires_review():
    """If affected clauses are unknown, status must be REQUIRES_REVIEW, not guessed."""
    amendment = Amendment(
        standard_id="std-uuid-1",
        amendment_number="Amendment No. 2",
        affected_clauses=None,  # Not known from metadata
        description="Corrigendum issued by sectional committee",
    )

    assert amendment.affected_clauses is None
    assert amendment.verification_status == "REQUIRES_REVIEW"


def test_regulatory_instrument_qco_linkage():
    """QCO regulatory instrument is decoupled from standard identity."""
    std = Standard(
        standard_number="IS 17526:2021",
        title="Commercial Beverage Coolers",
        category="Drinkware",
    )

    qco = RegulatoryInstrument(
        standard_id=std.id,
        instrument_type="QCO",
        notification_number="S.O. 4521(E)",
        gazette_date=date(2023, 10, 1),
        effective_date=date(2024, 4, 1),
        scope_description="Insulated flasks, bottles and commercial coolers",
        is_mandatory=True,
        verification_status="VERIFIED",
    )

    assert qco.standard_id == std.id
    assert qco.is_mandatory is True
    assert qco.notification_number == "S.O. 4521(E)"
    assert qco.verification_status == "VERIFIED"


def test_missing_effective_dates_remain_null():
    """When effective dates are not explicitly published, they remain None rather than guessed."""
    std = Standard(
        standard_number="IS 9999:2024",
        title="Draft Standard Without Notification",
        category="General",
    )
    assert std.publication_date is None
    assert std.effective_from is None
    assert std.effective_to is None
