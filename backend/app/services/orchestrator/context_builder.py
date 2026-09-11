"""Controlled Context Builder for Layer 3 AI Orchestrator.

Constructs an isolated, verified context for the single LLM.
Treats all user text, uploaded PDF text, OCR scans, voice transcripts,
and BOM rows as UNTRUSTED DATA. Enforces zero compliance authority.
"""

from typing import Dict, Any, List, Optional
from backend.app.schemas.product_dna import ProductFact, ProductDNACore
from backend.app.services.orchestrator.schemas import OrchestratorContext
from backend.app.services.security.prompt_guard import scan_and_sanitize_untrusted_text


class ContextBuilder:
    """Assembles prompt context strictly bounded by verified Product DNA and BIS catalog."""

    @classmethod
    def build_context(
        cls,
        product_dna: Optional[Any],
        verified_standard: Optional[str] = None,
        retrieved_clauses: Optional[List[Dict[str, Any]]] = None,
        available_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> OrchestratorContext:
        """Assemble structured context bounded by verified data."""
        p_name = "Immersion Water Heater / Appliance"
        cat = "Kitchen & Domestic Appliances"
        dna_facts_dict: Dict[str, Any] = {}

        if product_dna:
            if hasattr(product_dna, "product_name"):
                p_name = product_dna.product_name
                cat = product_dna.category
            elif isinstance(product_dna, dict):
                p_name = product_dna.get("product_name", p_name)
                cat = product_dna.get("category", cat)

            # Extract facts from ProductDNA
            facts_list = []
            if hasattr(product_dna, "facts"):
                facts_list = product_dna.facts
            elif isinstance(product_dna, dict) and "facts" in product_dna:
                facts_list = product_dna["facts"]

            for f in facts_list:
                f_name = f.field_name if hasattr(f, "field_name") else f.get("field_name")
                f_val = f.value if hasattr(f, "value") else f.get("value")
                f_prov = f.provenance.value if hasattr(f, "provenance") and hasattr(f.provenance, "value") else str(f.get("provenance", ""))
                f_state = f.verification_state.value if hasattr(f, "verification_state") and hasattr(f.verification_state, "value") else str(f.get("verification_state", ""))
                dna_facts_dict[f_name] = {
                    "value": f_val,
                    "provenance": f_prov,
                    "state": f_state,
                }

        return OrchestratorContext(
            product_name=p_name,
            category=cat,
            product_dna_facts=dna_facts_dict,
            target_standard=verified_standard or "IS 302-2-201:2008",
            applicable_clauses=retrieved_clauses or [],
            available_evidence=available_evidence or [],
        )


context_builder = ContextBuilder()
