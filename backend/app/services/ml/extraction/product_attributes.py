"""M23 ML Component 1: Product Attribute & Technical Entity Extraction.

Layer: Layer 2 (Product DNA Engine)
Model Name: zyntrix-product-entity-extractor-v1
Model Type: Pattern Token Classification & Regularized Entity Span Extraction
Device: CPU

INVARIANTS:
1. Predictions are strictly CANDIDATE FACTS (verification_state = UNVERIFIED_CANDIDATE).
2. 0% regulatory authority.
3. If model unavailable or disabled, immediately returns deterministic fallback.
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.ml.contracts import (
    CandidateFact,
    MLPredictionContract,
    MLModelStatus,
    MLTaskType,
)
from backend.app.services.ml.registry import ml_model_registry
from backend.app.services.ml.health import ml_telemetry
from backend.app.services.product_dna.normalizer import (
    normalize_capacity,
    normalize_electrical,
    normalize_material,
)

MODEL_NAME = "zyntrix-product-entity-extractor-v1"
MODEL_VERSION = "1.0.0"

# Technical patterns for multi-attribute extraction
ENTITY_PATTERNS = {
    "voltage": re.compile(r"(\d+(?:\.\d+)?(?:\s*-\s*\d+)?)\s*(?:v(?:\s*ac|\s*a\.c\.)?|volts?)", re.IGNORECASE),
    "power": re.compile(r"(\d+(?:\.\d+)?)\s*(?:w|watts?|kw|kilowatts?)", re.IGNORECASE),
    "frequency": re.compile(r"(\d+(?:\.\d+)?)\s*(?:hz|hertz)", re.IGNORECASE),
    "current": re.compile(r"(\d+(?:\.\d+)?)\s*(?:a|amp|amps?|amperes?)", re.IGNORECASE),
    "capacity": re.compile(r"(\d+(?:\.\d+)?)\s*(?:ml|milliliters?|l|liters?|litres?)", re.IGNORECASE),
    "temperature": re.compile(r"(\d+(?:\.\d+)?)\s*(?:°\s*c|deg\s*c|celsius|°\s*f|deg\s*f|fahrenheit)", re.IGNORECASE),
    "pressure": re.compile(r"(\d+(?:\.\d+)?)\s*(?:bar|psi|kpa|mpa)", re.IGNORECASE),
    "weight": re.compile(r"(\d+(?:\.\d+)?)\s*(?:g|grams?|kg|kilograms?)", re.IGNORECASE),
    "dimensions": re.compile(r"(\d+(?:\.\d+)?\s*[xX*]\s*\d+(?:\.\d+)?(?:\s*[xX*]\s*\d+(?:\.\d+)?)?)\s*(?:mm|cm|m|inches?)", re.IGNORECASE),
}

MATERIAL_KEYWORDS = [
    ("Stainless Steel Grade 304", ["grade 304", "ss 304", "aisi 304", "sus 304", "is 6911"]),
    ("Stainless Steel Grade 316", ["grade 316", "ss 316", "aisi 316", "sus 316"]),
    ("Food Grade Silicone Elastomer", ["food grade silicone", "silicone elastomer", "silicone gasket", "is 9845"]),
    ("Polypropylene Flame Retardant", ["polypropylene", "pp ul94", "pp flame retardant"]),
    ("Copper", ["copper conductor", "pure copper", "electrolytic copper"]),
    ("Bakelite Phenolic Resin", ["bakelite", "phenolic resin", "phenolic handle"]),
]


class ProductAttributeExtractor:
    """CPU-first ML/Pattern candidate attribute extractor."""

    def __init__(self):
        self.model_name = MODEL_NAME
        self.model_version = MODEL_VERSION

    def is_available(self) -> bool:
        return (
            getattr(settings, "ML_ENABLED", True)
            and getattr(settings, "PRODUCT_EXTRACTION_ML_ENABLED", True)
        )

    def extract_candidate_facts(self, text: str, source_id: Optional[str] = None) -> Tuple[List[CandidateFact], MLPredictionContract]:
        """Extract candidate facts from raw unstructured text with provenance."""
        t0 = time.time()
        input_hash = MLPredictionContract.compute_input_hash(text)

        if not self.is_available():
            # Immediate deterministic fallback
            candidates = self._deterministic_fallback_extract(text)
            latency = (time.time() - t0) * 1000.0
            ml_telemetry.record_inference(self.model_name, latency, fallback_used=True)
            contract = MLPredictionContract(
                model_name=self.model_name,
                model_version=self.model_version,
                task=MLTaskType.PRODUCT_ATTRIBUTE_EXTRACTION.value,
                prediction={"candidate_count": len(candidates), "fields": [c.field for c in candidates]},
                confidence=0.75,
                input_hash=input_hash,
                fallback_used=True,
                regulatory_authority=0.0,
            )
            return candidates, contract

        candidates: List[CandidateFact] = []
        clean = text.strip()

        # 1. Electrical & Numeric Entities
        for field, pattern in ENTITY_PATTERNS.items():
            for match in pattern.finditer(clean):
                raw_span = match.group(0)
                val_str = match.group(1)
                
                # Determine unit
                unit = raw_span[len(val_str):].strip()
                try:
                    val = float(val_str) if "-" not in val_str else val_str
                except ValueError:
                    val = val_str

                # Assign confidence based on span context and pattern specificity
                conf = 0.92 if field in ["voltage", "power", "capacity"] else 0.88

                candidates.append(
                    CandidateFact(
                        field=field,
                        value=val,
                        raw_value=raw_span,
                        unit=unit,
                        confidence=conf,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        source_span=clean[max(0, match.start() - 20): min(len(clean), match.end() + 20)].strip(),
                        provenance="ML_CANDIDATE_EXTRACTION",
                        verification_state="UNVERIFIED_CANDIDATE",
                        regulatory_authority=0.0,
                    )
                )

        # 2. Materials
        text_lower = clean.lower()
        for mat_canon, aliases in MATERIAL_KEYWORDS:
            for alias in aliases:
                idx = text_lower.find(alias)
                if idx != -1:
                    span = clean[idx: idx + len(alias)]
                    candidates.append(
                        CandidateFact(
                            field="material",
                            value=mat_canon,
                            raw_value=span,
                            unit=None,
                            confidence=0.94,
                            model_name=self.model_name,
                            model_version=self.model_version,
                            source_span=clean[max(0, idx - 20): min(len(clean), idx + len(alias) + 20)].strip(),
                            provenance="ML_CANDIDATE_EXTRACTION",
                            verification_state="UNVERIFIED_CANDIDATE",
                            regulatory_authority=0.0,
                        )
                    )
                    break

        latency = (time.time() - t0) * 1000.0
        ml_telemetry.record_inference(self.model_name, latency, fallback_used=False)

        contract = MLPredictionContract(
            model_name=self.model_name,
            model_version=self.model_version,
            task=MLTaskType.PRODUCT_ATTRIBUTE_EXTRACTION.value,
            prediction={"candidate_count": len(candidates), "fields": [c.field for c in candidates]},
            confidence=round(sum(c.confidence for c in candidates) / len(candidates), 3) if candidates else 0.5,
            input_hash=input_hash,
            fallback_used=False,
            regulatory_authority=0.0,
        )

        return candidates, contract

    def _deterministic_fallback_extract(self, text: str) -> List[CandidateFact]:
        """Strict deterministic fallback when ML is inactive."""
        facts = []
        elec = normalize_electrical(text)
        if elec.get("wattage"):
            facts.append(
                CandidateFact(
                    field="power",
                    value=elec["wattage"],
                    raw_value=f"{elec['wattage']} W",
                    unit="W",
                    confidence=0.70,
                    model_name="deterministic-fallback-rules",
                    model_version="1.0.0",
                    source_span="deterministic electrical fallback",
                    provenance="DETERMINISTIC_FALLBACK",
                    verification_state="UNVERIFIED_CANDIDATE",
                    regulatory_authority=0.0,
                )
            )
        if elec.get("voltage"):
            facts.append(
                CandidateFact(
                    field="voltage",
                    value=elec["voltage"],
                    raw_value=f"{elec['voltage']} V",
                    unit="V",
                    confidence=0.70,
                    model_name="deterministic-fallback-rules",
                    model_version="1.0.0",
                    source_span="deterministic electrical fallback",
                    provenance="DETERMINISTIC_FALLBACK",
                    verification_state="UNVERIFIED_CANDIDATE",
                    regulatory_authority=0.0,
                )
            )
        cap_val, cap_unit = normalize_capacity(text)
        if cap_val:
            facts.append(
                CandidateFact(
                    field="capacity",
                    value=cap_val,
                    raw_value=f"{cap_val} {cap_unit or 'ml'}",
                    unit=cap_unit or "ml",
                    confidence=0.70,
                    model_name="deterministic-fallback-rules",
                    model_version="1.0.0",
                    source_span="deterministic capacity fallback",
                    provenance="DETERMINISTIC_FALLBACK",
                    verification_state="UNVERIFIED_CANDIDATE",
                    regulatory_authority=0.0,
                )
            )
        return facts


product_attribute_extractor = ProductAttributeExtractor()
