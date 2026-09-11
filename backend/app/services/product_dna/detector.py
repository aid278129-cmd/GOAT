"""Anomaly, Contradiction, Plausibility, and Prompt-Injection Detector for Layer 2.

Enforces zero-hallucination and security boundaries:
- Detects cross-source contradictory facts (e.g. BOM rating != Description rating).
- Rejects impossible physical values (e.g. negative voltage, 50,000 W kettle).
- Flags low-confidence extractions (< 0.70).
- Neutralizes prompt-injection attempts.
- Flags missing required product discriminators to block premature downstream progression.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from backend.app.schemas.product_dna import (
    ProductFact,
    FactVerificationState,
    ClarificationRequirement,
)
from backend.app.services.product_dna.normalizer import check_physical_plausibility
from backend.app.core.logging import logger

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"(?:system\s+prompt|system\s+instruction)\s*[:=]", re.IGNORECASE),
    re.compile(r"mark\s+(?:as\s+)?(?:compliant|satisfied|certified|passed)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:an?\s+)?(?:evaluator|auditor|bis\s+officer)", re.IGNORECASE),
    re.compile(r"override\s+(?:compliance|safety|rules|gate)", re.IGNORECASE),
    re.compile(r"llm\s+authority\s*=\s*100%", re.IGNORECASE),
]

REQUIRED_DISCRIMINATORS: Dict[str, List[Dict[str, Any]]] = {
    "electric_kettle": [
        {"field": "rated_voltage", "question": "What is the rated operating voltage (V AC)?", "options": ["230 V AC", "220-240 V AC", "110 V AC"]},
        {"field": "rated_power_input", "question": "What is the rated power input (Watts)?", "options": ["1000 W", "1500 W", "1800 W", "2000 W"]},
        {"field": "nominal_capacity", "question": "What is the liquid capacity (ml or Liters)?", "options": ["1000 ml (1.0 L)", "1500 ml (1.5 L)", "1800 ml (1.8 L)"]},
        {"field": "heating_method", "question": "What heating element construction is used?", "options": ["Concealed stainless steel element", "Immersion tubular element"]},
    ],
    "water_heater": [
        {"field": "rated_voltage", "question": "What is the rated supply voltage?", "options": ["230 V AC", "240 V AC"]},
        {"field": "rated_power_input", "question": "What is the rated power input (Wattage)?", "options": ["1000 W", "1500 W", "2000 W"]},
        {"field": "sheath_material", "question": "What alloy is used for the tubular heating sheath?", "options": ["Stainless Steel Grade 304", "Copper Sheath", "Incoloy 800"]},
        {"field": "handle_material", "question": "What material is used for the insulating handle?", "options": ["Flame-retardant Polypropylene (UL94 V-0)", "Bakelite / Phenolic Resin"]},
    ],
    "vacuum_flask": [
        {"field": "nominal_capacity", "question": "What is the nominal volume holding capacity?", "options": ["500 ml", "750 ml", "1000 ml", "1500 ml"]},
        {"field": "inner_lining_material", "question": "What food-contact grade of stainless steel is used?", "options": ["Stainless Steel Grade 304 (IS 6911)", "Stainless Steel Grade 316"]},
        {"field": "thermal_retention_target", "question": "What is the certified thermal retention temperature after 6 hours?", "options": [">= 65 C (Standard)", ">= 70 C (High Insulation)"]},
        {"field": "lid_gasket_material", "question": "What polymer is used for the lid sealing gasket?", "options": ["Food Grade Silicone Elastomer (IS 9845)", "BPA-free EPDM Rubber"]},
    ],
}


class FactAnomalyDetector:
    """Detects contradictions, physical impossibilities, and missing facts."""

    @classmethod
    def sanitize_adversarial_input(cls, text: str) -> Tuple[str, List[str]]:
        """Detect and neutralize prompt injection attempts in raw input."""
        detected_attacks: List[str] = []
        clean_text = text

        for pat in PROMPT_INJECTION_PATTERNS:
            matches = pat.findall(clean_text)
            if matches:
                for m in matches:
                    detected_attacks.append(f"Prompt injection pattern intercepted: '{m}'")
                clean_text = pat.sub("[SECURITY_SUPPRESSED_INJECTION_ATTEMPT]", clean_text)

        return clean_text, detected_attacks

    @classmethod
    def detect_conflicts_between_facts(cls, facts: List[ProductFact]) -> List[ProductFact]:
        """Detect contradictions between facts from different multi-modal sources."""
        # Group facts by canonical field_name
        grouped: Dict[str, List[ProductFact]] = {}
        for f in facts:
            grouped.setdefault(f.field_name, []).append(f)

        for field_name, fact_list in grouped.items():
            if len(fact_list) > 1:
                # Compare normalized values
                values = {str(f.value).lower().strip() for f in fact_list}
                if len(values) > 1:
                    # Conflict found!
                    conflict_desc = f"Contradictory values detected across sources: {', '.join([f'{f.source or f.provenance.value}: {f.value}' for f in fact_list])}"
                    logger.warning(f"Layer 2 Conflict on {field_name}: {conflict_desc}")
                    for f in fact_list:
                        f.verification_state = FactVerificationState.CONFLICTING
                        f.conflict_notes = conflict_desc

        return facts

    @classmethod
    def validate_facts_plausibility(cls, facts: List[ProductFact], category: Optional[str] = None) -> List[ProductFact]:
        """Validate physical plausibility bounds for each fact."""
        for f in facts:
            is_plausible, reason = check_physical_plausibility(
                field_name=f.field_name,
                value=f.value,
                unit=f.unit,
                category=category,
            )
            if not is_plausible:
                f.verification_state = FactVerificationState.CONFLICTING
                f.conflict_notes = f"Physically impossible or out-of-bounds value: {reason}"

            # Flag low confidence extractions
            if f.confidence < 0.70 and f.verification_state != FactVerificationState.CONFLICTING:
                f.verification_state = FactVerificationState.NEEDS_CONFIRMATION

        return facts

    @classmethod
    def identify_missing_discriminators(
        cls,
        product_name: str,
        category: str,
        facts: List[ProductFact],
    ) -> List[ClarificationRequirement]:
        """Identify missing mandatory discriminators that block downstream progression."""
        name_lower = (product_name or "").lower()
        cat_lower = (category or "").lower()

        target_domain = None
        if "kettle" in name_lower:
            target_domain = "electric_kettle"
        elif any(k in name_lower or k in cat_lower for k in ["water heater", "immersion"]):
            target_domain = "water_heater"
        elif any(k in name_lower or k in cat_lower for k in ["flask", "bottle", "drinkware"]):
            target_domain = "vacuum_flask"

        if not target_domain or target_domain not in REQUIRED_DISCRIMINATORS:
            return []

        required_list = REQUIRED_DISCRIMINATORS[target_domain]
        existing_fields = {f.field_name for f in facts if f.value is not None}

        missing_clarifications: List[ClarificationRequirement] = []
        for req in required_list:
            field = req["field"]
            if field not in existing_fields:
                missing_clarifications.append(
                    ClarificationRequirement(
                        attribute_name=field,
                        display_question=req["question"],
                        reason=f"Mandatory product discriminator for {product_name}. Cannot be guessed under zero-hallucination policy.",
                        options=req.get("options"),
                        criticality="HIGH",
                        suggested_field_id=field,
                    )
                )

        return missing_clarifications


fact_anomaly_detector = FactAnomalyDetector()
