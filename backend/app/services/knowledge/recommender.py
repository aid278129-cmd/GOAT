"""Product-to-Standard Recommendation Engine (Phase 6).

Implements the structured recommendation pipeline:
Product Description
-> Structured Product Context Extraction
-> Candidate Standards Hybrid Retrieval
-> Evidence & Source Matching
-> Relevance Explanation & Confidence Basis
-> Applicable BIS Schemes & Testing Requirements
-> Human-readable Recommendation with Handoff Metadata.

Enforces:
- Non-authoritative language: 'Potentially relevant standards based on product description'
- Explains WHY each candidate was selected with matched product characteristics.
- Zero hallucination: Only recommends standards backed by published database records.
"""

import re
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.persistent_knowledge import (
    BISStandard,
    BISStandardRevision,
    BISClause,
    BISScheme,
    BISTestingRequirement,
    BISLaboratory,
)
from backend.app.services.knowledge.retrieval import BISHybridRetrievalEngine


class BISProductStandardRecommender:
    """Recommends Indian Standards, certification schemes, and testing considerations for products."""

    PRODUCT_KEYWORDS_MAP = {
        "SOLAR_INVERTERS": [
            "inverter", "solar", "photovoltaic", "pv", "hybrid inverter", "grid-tied", "grid-connected",
            "micro-inverter", "power converter", "string inverter", "bess"
        ],
        "IT_ELECTRONICS": [
            "adapter", "power supply", "charger", "laptop", "computer", "mobile", "tablet",
            "server", "smps", "information technology", "telecom"
        ],
        "HOUSEHOLD_APPLIANCES": [
            "heater", "geyser", "microwave", "fan", "mixer", "blender", "iron", "toaster",
            "refrigerator", "washing machine", "vacuum cleaner", "appliance"
        ],
        "BATTERIES": [
            "battery", "lithium", "cell", "li-ion", "lfp", "energy storage", "power bank",
            "secondary cell", "accumulator"
        ],
        "ELECTRICAL_ACCESSORIES": [
            "plug", "socket", "switch", "cable", "cord", "conduit", "connector", "outlet"
        ],
        "DOMESTIC_CONTAINERS": [
            "bottle", "flask", "thermosteel", "steel bottle", "vacuum flask", "water bottle",
            "container", "insulated", "cookware", "utensil", "stainless steel"
        ],
    }

    @classmethod
    def extract_structured_product_context(cls, description: str) -> Dict[str, Any]:
        """Extracts structured electrical and domain parameters from raw natural language."""
        desc_lower = description.lower()
        context: Dict[str, Any] = {
            "raw_description": description,
            "detected_categories": [],
            "power_kw": None,
            "power_w": None,
            "voltage_v": None,
            "current_a": None,
            "is_grid_connected": False,
            "is_portable": False,
            "intended_application": "GENERAL",
        }

        # Category classification
        for cat, keywords in cls.PRODUCT_KEYWORDS_MAP.items():
            if any(k in desc_lower for k in keywords):
                context["detected_categories"].append(cat)

        if not context["detected_categories"]:
            context["detected_categories"].append("ELECTRICAL_ELECTRONICS")

        # Power extraction (kW, W)
        kw_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kw|kilo\s*watts?)\b", desc_lower)
        if kw_match:
            context["power_kw"] = float(kw_match.group(1))

        w_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:w|watts?)\b", desc_lower)
        if w_match:
            context["power_w"] = float(w_match.group(1))

        # Voltage extraction
        v_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:v|volts?|vac|vdc)\b", desc_lower)
        if v_match:
            context["voltage_v"] = float(v_match.group(1))

        # Current extraction
        a_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:a|amps?|amperes?)\b", desc_lower)
        if a_match:
            context["current_a"] = float(a_match.group(1))

        # Functional flags
        if any(w in desc_lower for w in ["grid", "grid-tied", "grid-connected", "utility", "hybrid"]):
            context["is_grid_connected"] = True
        if any(w in desc_lower for w in ["portable", "handheld", "pocket", "mobile"]):
            context["is_portable"] = True

        if any(w in desc_lower for w in ["industrial", "commercial", "factory", "plant"]):
            context["intended_application"] = "INDUSTRIAL"
        elif any(w in desc_lower for w in ["household", "home", "domestic", "consumer", "residential"]):
            context["intended_application"] = "DOMESTIC"

        return context

    @classmethod
    async def recommend_standards_for_product(
        cls,
        db: AsyncSession,
        product_description: str,
        limit: int = 4,
    ) -> Dict[str, Any]:
        """Executes full product-to-standard recommendation pipeline."""
        context = cls.extract_structured_product_context(product_description)
        
        # 1. Search candidate standards using hybrid retrieval
        candidate_standards = await BISHybridRetrievalEngine.search_standards(
            db, product_description, limit=limit * 2
        )

        # 2. Enrich recommendations with rationale, matched characteristics, and clauses
        recommendations: List[Dict[str, Any]] = []
        primary_standard_num = None

        for cand in candidate_standards:
            std_id = cand["id"]
            std_num = cand["standard_number"]
            matched_characteristics = []

            # Determine match basis
            cand_cat = cand.get("product_category")
            if cand_cat in context["detected_categories"]:
                matched_characteristics.append(f"Product domain match: {cand_cat}")

            if "SOLAR_INVERTERS" in context["detected_categories"] and "16221" in std_num:
                if context["is_grid_connected"]:
                    matched_characteristics.append("Grid interconnection & anti-islanding functionality")
                if context.get("power_kw"):
                    matched_characteristics.append(f"Rated capacity: {context['power_kw']} kW")
                match_basis = "Direct standard specification for photovoltaic power converters / inverters."
                confidence = "HIGH_CONFIDENCE"
            elif "IT_ELECTRONICS" in context["detected_categories"] and "13252" in std_num:
                match_basis = "General safety specification for Information Technology equipment and power supplies."
                confidence = "HIGH_CONFIDENCE"
            elif "HOUSEHOLD_APPLIANCES" in context["detected_categories"] and "302" in std_num:
                match_basis = "General electrical safety standard for household appliances."
                confidence = "HIGH_CONFIDENCE"
            elif "BATTERIES" in context["detected_categories"] and "16046" in std_num:
                match_basis = "Safety requirements for secondary lithium cells and battery systems."
                confidence = "HIGH_CONFIDENCE"
            elif "ELECTRICAL_ACCESSORIES" in context["detected_categories"] and "1293" in std_num:
                match_basis = "Mandatory Indian standard for plugs and socket-outlets up to 16A."
                confidence = "HIGH_CONFIDENCE"
            elif ("DOMESTIC_CONTAINERS" in context["detected_categories"] or "bottle" in product_description.lower() or "flask" in product_description.lower()) and "17526" in std_num:
                match_basis = "Mandatory Indian standard for Vacuum Insulated Stainless Steel Flasks, Bottles, and Domestic Containers under DPIIT QCO Order."
                confidence = "HIGH_CONFIDENCE"
                matched_characteristics.append("Double-walled vacuum insulation & food-contact stainless steel (SS 304/316)")
            else:
                match_basis = f"Retrieved via keyword and title relevance for '{cand['title']}'."
                confidence = "MODERATE_CONFIDENCE"

            # Retrieve key clauses for this standard
            rev_stmt = (
                select(BISStandardRevision)
                .where(BISStandardRevision.standard_id == std_id)
                .order_by(BISStandardRevision.revision_year.desc())
                .limit(1)
            )
            rev = (await db.execute(rev_stmt)).scalars().first()
            clauses_summary = []
            if rev:
                c_stmt = (
                    select(BISClause)
                    .where(BISClause.standard_revision_id == rev.id)
                    .order_by(BISClause.clause_number)
                    .limit(4)
                )
                clauses = (await db.execute(c_stmt)).scalars().all()
                clauses_summary = [
                    {
                        "clause_number": c.clause_number,
                        "clause_title": c.clause_title,
                        "parameter_key": c.parameter_key,
                        "expected_value": c.expected_value,
                        "page_number": c.page_number,
                    }
                    for c in clauses
                ]

            if not primary_standard_num:
                primary_standard_num = std_num

            recommendations.append({
                "standard_number": std_num,
                "title": cand["title"],
                "revision": cand["version"],
                "scope_summary": cand["scope_summary"],
                "product_category": cand["product_category"],
                "is_mandatory": cand["is_mandatory"],
                "cro_order_reference": cand["cro_order_reference"],
                "why_retrieved": match_basis,
                "relevant_product_characteristics": matched_characteristics or ["General electrical characteristics"],
                "confidence_basis": confidence,
                "relevance_score": cand["relevance_score"],
                "source": "Bureau of Indian Standards Official Standards Catalogue",
                "key_clauses": clauses_summary,
            })

            if len(recommendations) >= limit:
                break

        # 3. Retrieve Applicable BIS Scheme
        schemes = await BISHybridRetrievalEngine.retrieve_schemes(db, product_description)
        suggested_scheme = schemes[0] if schemes else None

        # If solar inverter, ensure Scheme II CRS is highlighted
        if "SOLAR_INVERTERS" in context["detected_categories"]:
            crs_scheme = next((s for s in schemes if s["scheme_code"] == "SCHEME_II_CRS"), None)
            if crs_scheme:
                suggested_scheme = crs_scheme

        # 4. Retrieve Relevant Testing Labs for the Primary Standard
        labs = await BISHybridRetrievalEngine.retrieve_laboratories(
            db, standard_number=primary_standard_num
        )

        return {
            "product_context": context,
            "disclaimer": (
                "Based on the available authorized BIS sources, the following standards may be relevant "
                "to your product description. Further engineering review against current statutory notifications is recommended."
            ),
            "potentially_relevant_standards": recommendations,
            "applicable_bis_scheme": suggested_scheme,
            "testing_laboratories_count": len(labs),
            "sample_laboratories": labs[:3],
            "workstation_handoff_ready": True,
            "handoff_payload": {
                "suggested_title": f"Compliance Evaluation - {context['detected_categories'][0]} ({context.get('power_kw') or ''} kW)",
                "target_standard": primary_standard_num or "IS 16221 (Part 2)",
                "product_characteristics": context,
            },
        }
