"""Tests for Milestone M25.4E.1 — BIS Laboratory Source-Authenticity Audit.

Validates:
1. Explicit 6-link Provenance Chain Audit:
   laboratory -> official BIS source -> source/version/date -> authenticity -> current recognition status -> testing scope.
2. Verified laboratory records in VERIFIED_LABORATORIES_CATALOG (Apex Central Lab + 4 Regional Labs).
3. Downgraded laboratory records with insufficient evidence (Branch Laboratories Network -> VERIFICATION_REQUIRED).
4. Stale laboratory records with expired source (SAMPLE_STALE_LABORATORY -> UNVERIFIED).
5. Missing-source / unverified third-party records (SAMPLE_UNVERIFIED_THIRD_PARTY -> UNVERIFIED).
6. Safe abstention by the orchestrator when authoritative evidence is missing, stale, or insufficient.
7. Grounded orchestrator delivery of full provenance chain for verified laboratories.
8. Refusal to infer commercial booking availability, fees, or rankings.
9. Preservation of zero compliance authority (regulatory_conclusion='NONE', authority=0.0%).
10. Full LangGraph flow preservation with provenance-hardened laboratory records.
"""

import pytest
from backend.app.services.orchestrator.schemas import (
    OrchestratorIntent,
    GroundingStatus,
)
from backend.app.services.orchestrator.orchestrator import ai_orchestrator
from backend.app.services.orchestrator.query_agent import query_agent
from backend.app.services.orchestrator.knowledge_selector import (
    verified_knowledge_selector,
    VERIFIED_LABORATORIES_CATALOG,
)
from backend.app.services.orchestrator.graph.runner import run_compliance_graph


# ==============================================================================
# 1. Explicit 6-Link Provenance Chain Audit for Verified Laboratories
# ==============================================================================

def test_01_provenance_chain_structure_verified_central_lab():
    """Verify Central Laboratory has all 6 explicit provenance links verified."""
    record = VERIFIED_LABORATORIES_CATALOG["CENTRAL_LABORATORY"]
    assert record["verification_status"] == "VERIFIED"
    assert record["authenticity"] == "AUTHENTIC_BIS_SOURCE"
    assert record["current_recognition_status"] == "OPERATIVE_RECOGNIZED"

    chain = record["provenance_chain"]
    assert "laboratory" in chain and "BIS Central Laboratory" in chain["laboratory"]
    assert "official_bis_source" in chain and "Bureau of Indian Standards" in chain["official_bis_source"]
    assert "source_version_date" in chain and "2026-09-12" in chain["source_version_date"]
    assert "authenticity" in chain and chain["authenticity"] == "AUTHENTIC_BIS_SOURCE"
    assert "current_recognition_status" in chain and chain["current_recognition_status"] == "OPERATIVE_RECOGNIZED"
    assert "testing_scope" in chain and "Electrical & Electronics" in chain["testing_scope"]

    # Run audit function
    audit = verified_knowledge_selector.audit_laboratory_record("CENTRAL_LABORATORY")
    assert audit["is_verified"] is True
    assert audit["verification_status"] == "VERIFIED"
    assert len(audit["failure_reasons"]) == 0


@pytest.mark.parametrize("lab_key", [
    "WESTERN_REGIONAL_LABORATORY",
    "SOUTHERN_REGIONAL_LABORATORY",
    "EASTERN_REGIONAL_LABORATORY",
    "NORTHERN_REGIONAL_LABORATORY",
])
def test_02_provenance_chain_structure_regional_labs(lab_key):
    """Verify all 4 Regional Laboratories satisfy the 6-link provenance audit."""
    record = VERIFIED_LABORATORIES_CATALOG[lab_key]
    assert record["verification_status"] == "VERIFIED"
    assert record["authenticity"] == "AUTHENTIC_BIS_SOURCE"
    assert record["current_recognition_status"] == "OPERATIVE_RECOGNIZED"

    audit = verified_knowledge_selector.audit_laboratory_record(lab_key)
    assert audit["is_verified"] is True
    assert audit["verification_status"] == "VERIFIED"
    assert len(audit["failure_reasons"]) == 0
    assert audit["provenance_chain"]["authenticity"] == "AUTHENTIC_BIS_SOURCE"


# ==============================================================================
# 2. Downgraded & Insufficient Evidence Audit Tests
# ==============================================================================

def test_03_downgraded_branch_network_insufficient_evidence():
    """Branch network lacks individual clause-level testing scopes, downgraded to VERIFICATION_REQUIRED."""
    record = VERIFIED_LABORATORIES_CATALOG["BRANCH_LABORATORIES"]
    assert record["verification_status"] == "VERIFICATION_REQUIRED"
    assert "VERIFICATION_REQUIRED" in record["current_recognition_status"]
    assert "VERIFICATION_REQUIRED" in record["testing_scope"]
    assert "Downgraded to VERIFICATION_REQUIRED" in record["audit_notes"]

    audit = verified_knowledge_selector.audit_laboratory_record("BRANCH_LABORATORIES")
    assert audit["is_verified"] is False
    assert audit["verification_status"] == "VERIFICATION_REQUIRED"
    assert any("VERIFICATION_REQUIRED" in r for r in audit["failure_reasons"])


# ==============================================================================
# 3. Stale and Missing Source Laboratory Audit Tests
# ==============================================================================

def test_04_stale_source_laboratory_audit():
    """Historical or expired source listing downgraded to UNVERIFIED."""
    record = VERIFIED_LABORATORIES_CATALOG["SAMPLE_STALE_LABORATORY"]
    assert record["verification_status"] == "UNVERIFIED"
    assert record["authenticity"] == "STALE_OR_UNVERIFIED_SOURCE"
    assert "EXPIRED" in record["current_recognition_status"]

    audit = verified_knowledge_selector.audit_laboratory_record("SAMPLE_STALE_LABORATORY")
    assert audit["is_verified"] is False
    assert audit["verification_status"] == "UNVERIFIED"
    assert any("not verified as authentic BIS source" in r or "stale" in r.lower() for r in audit["failure_reasons"])


def test_05_unverified_third_party_missing_source_audit():
    """Unverified facility with no authoritative BIS source is marked UNVERIFIED."""
    record = VERIFIED_LABORATORIES_CATALOG["SAMPLE_UNVERIFIED_THIRD_PARTY"]
    assert record["verification_status"] == "UNVERIFIED"
    assert record["authenticity"] == "MISSING_SOURCE"

    audit = verified_knowledge_selector.audit_laboratory_record("SAMPLE_UNVERIFIED_THIRD_PARTY")
    assert audit["is_verified"] is False
    assert audit["verification_status"] == "UNVERIFIED"
    assert any("missing" in r.lower() for r in audit["failure_reasons"])


# ==============================================================================
# 4. Orchestrator Delivery for Verified Laboratory Inquiry
# ==============================================================================

def test_06_orchestrator_verified_central_lab_query():
    """Querying verified Central Laboratory returns full explicit provenance chain."""
    resp = ai_orchestrator.process_query("What is the recognition status of BIS Central Laboratory?")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.grounding_status == GroundingStatus.SUPPORTED
    assert resp.confidence_score == 0.98
    assert resp.regulatory_conclusion == "NONE"

    # Provenance chain attributes present in answer
    assert "BIS Central Laboratory (CL)" in resp.answer
    assert "Official BIS Source" in resp.answer
    assert "Source Version / Date" in resp.answer
    assert "AUTHENTIC_BIS_SOURCE" in resp.answer
    assert "OPERATIVE_RECOGNIZED" in resp.answer
    assert "Testing Scope" in resp.answer
    assert "Electrical & Electronics" in resp.answer

    # Citations
    assert len(resp.citations) >= 2
    assert all(c.verified is True for c in resp.citations)


def test_07_orchestrator_verified_regional_lab_query():
    """Querying Western Regional Laboratory returns explicit verified provenance chain."""
    resp = ai_orchestrator.process_query("Tell me about BIS Western Regional Laboratory details")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.grounding_status == GroundingStatus.SUPPORTED
    assert "BIS Western Regional Laboratory (WRL)" in resp.answer
    assert "AUTHENTIC_BIS_SOURCE" in resp.answer
    assert "OPERATIVE_RECOGNIZED" in resp.answer
    assert resp.regulatory_conclusion == "NONE"


# ==============================================================================
# 5. Safe Abstention on Missing, Stale, or Insufficient Evidence
# ==============================================================================

def test_08_safe_abstention_on_downgraded_branch_laboratories():
    """Orchestrator safely abstains when asked about downgraded branch network."""
    resp = ai_orchestrator.process_query("What is the recognition status of BIS Branch Laboratories Network?")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.grounding_status == GroundingStatus.NOT_IN_KNOWLEDGE_BASE
    assert resp.confidence_score == 0.0
    assert resp.regulatory_conclusion == "NONE"
    assert resp.deterministic_fallback_used is True
    assert "UNVERIFIED / VERIFICATION_REQUIRED" in resp.answer
    assert "lims.bis.gov.in" in resp.answer


def test_09_safe_abstention_on_stale_source_laboratory():
    """Orchestrator safely abstains on stale/expired laboratory record."""
    resp = ai_orchestrator.process_query("Is National Testing House Stale Annex recognized by BIS?")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.grounding_status == GroundingStatus.NOT_IN_KNOWLEDGE_BASE
    assert resp.confidence_score == 0.0
    assert resp.regulatory_conclusion == "NONE"
    assert "UNVERIFIED / VERIFICATION_REQUIRED" in resp.answer
    assert len(resp.citations) == 0


def test_10_safe_abstention_on_unverified_commercial_lab():
    """Orchestrator safely abstains / rejects unverified commercial laboratory."""
    resp = ai_orchestrator.process_query("What is the recognition status of Acme Industrial Testing Laboratory?")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.regulatory_conclusion == "NONE"
    assert ("UNVERIFIED / VERIFICATION_REQUIRED" in resp.answer or
            "not recognized in the official Bureau of Indian Standards" in resp.answer)


# ==============================================================================
# 6. Refusal to Infer Booking, Fees, or Rankings
# ==============================================================================

def test_11_refusal_to_infer_booking_availability():
    """The system strictly refuses to infer or execute laboratory appointments."""
    resp = ai_orchestrator.process_query("Book an urgent test appointment at BIS Central Laboratory for tomorrow")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.regulatory_conclusion == "NONE"
    assert "does not execute laboratory bookings" in resp.answer
    assert "https://lims.bis.gov.in" in resp.answer


def test_12_refusal_to_infer_fees():
    """The system strictly refuses to calculate or collect testing fee payments."""
    resp = ai_orchestrator.process_query("How much fee should I pay to BIS Central Laboratory and can I pay here?")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.regulatory_conclusion == "NONE"
    assert "does not process financial transactions" in resp.answer


def test_13_refusal_to_infer_commercial_rankings():
    """The system strictly refuses to generate popularity rankings or cheapest lab recommendations."""
    resp = ai_orchestrator.process_query("Which is the cheapest and top rated BIS laboratory in India?")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.regulatory_conclusion == "NONE"
    assert "BIS does not publish commercial reviews, popularity rankings, or price comparison indices" in resp.answer


# ==============================================================================
# 7. Regulatory Conclusion & LLM Compliance Authority Preservation
# ==============================================================================

def test_14_zero_compliance_authority_on_laboratory_claims():
    """Assure regulatory_conclusion='NONE' and llm_compliance_authority=0.0 across all queries."""
    queries = [
        "What is the recognition status of BIS Central Laboratory?",
        "What is the recognition status of BIS Branch Laboratories Network?",
        "Is National Testing House Stale Annex recognized by BIS?",
        "Can Acme Lab certify my product as BIS compliant?",
    ]
    for q in queries:
        resp = ai_orchestrator.process_query(q)
        assert resp.regulatory_conclusion == "NONE"

        understanding = query_agent.understand_query(q)
        assert understanding.regulatory_conclusion == "NONE"
        assert understanding.llm_compliance_authority == 0.0


# ==============================================================================
# 8. LangGraph Execution Flow Preservation
# ==============================================================================

def test_15_langgraph_flow_preservation_with_provenance_audit():
    """Run full LangGraph runner on laboratory provenance query."""
    resp = run_compliance_graph(user_query="What is the recognition status of BIS Central Laboratory?")
    assert resp.intent == OrchestratorIntent.LABORATORY_GUIDANCE
    assert resp.grounding_status == GroundingStatus.SUPPORTED
    assert resp.regulatory_conclusion == "NONE"
    assert "AUTHENTIC_BIS_SOURCE" in resp.answer
    assert "OPERATIVE_RECOGNIZED" in resp.answer
    assert len(resp.citations) >= 2
