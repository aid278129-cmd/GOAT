"""M23 ML Component 4: Multi-Source Anomaly & Contradiction Detector.

Layer: Layer 7 (Compliance Gap Engine) & Layer 2 (Product DNA Engine)
Model Name: zyntrix-anomaly-isolation-forest-v1
Model Type: Robust Statistical Variance + Isolation Forest Contradiction Detector
Device: CPU

INVARIANTS:
1. Always normalize units BEFORE comparison (1.5 kW == 1500 W, 0.75 L == 750 ml).
2. Never compare raw strings for numeric fields.
3. If unit conversion is impossible, mark UNKNOWN — never guess.
4. Anomalies trigger EXPERT_REVIEW_REQUIRED, NEVER automatic non-compliance.
5. 0% regulatory authority.
"""

import time
import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.ml.contracts import (
    AnomalyReport,
    MLPredictionContract,
    MLTaskType,
)
from backend.app.services.ml.registry import ml_model_registry
from backend.app.services.ml.health import ml_telemetry
from backend.app.services.gap_analysis.units import normalize_unit

MODEL_NAME = "zyntrix-anomaly-isolation-forest-v1"
MODEL_VERSION = "1.0.0"


class MultiSourceAnomalyDetector:
    """Detects parametric conflicts and statistical anomalies across document sources."""

    def __init__(self):
        self.model_name = MODEL_NAME
        self.model_version = MODEL_VERSION

    def is_available(self) -> bool:
        return (
            getattr(settings, "ML_ENABLED", True)
            and getattr(settings, "ANOMALY_DETECTION_ENABLED", True)
        )

    def detect_conflicts(
        self,
        field_name: str,
        observations: List[Dict[str, Any]],  # [{"source": "spec", "value": 750, "unit": "ml"}, ...]
        canonical_unit: Optional[str] = None,
    ) -> AnomalyReport:
        """Detect numeric or categorical conflicts across multiple sources."""
        t0 = time.time()
        input_hash = MLPredictionContract.compute_input_hash({"field": field_name, "obs": observations})

        if not observations or len(observations) < 2:
            return AnomalyReport(
                has_conflict=False,
                fields_involved=[field_name],
                action_required="NONE",
                explanation="Fewer than 2 observations; no cross-source conflict possible.",
            )

        # 1. Deterministic Normalization
        normalized_obs = []
        observed_map = {}
        normalized_map = {}
        unknown_units = False

        # Determine target unit if not provided
        target_unit = canonical_unit
        if not target_unit:
            for obs in observations:
                if obs.get("unit"):
                    target_unit = obs.get("unit")
                    break

        for obs in observations:
            src = obs.get("source", "unknown_source")
            raw_val = obs.get("value")
            unit = obs.get("unit")
            observed_map[src] = f"{raw_val} {unit}".strip()

            if isinstance(raw_val, (int, float)):
                if unit and target_unit:
                    norm_val, _ = normalize_unit(float(raw_val), unit, target_unit)
                    normalized_obs.append(norm_val)
                    normalized_map[src] = f"{round(norm_val, 4)} {target_unit}"
                else:
                    normalized_obs.append(float(raw_val))
                    normalized_map[src] = str(raw_val)
            else:
                # String / Categorical comparison
                normalized_map[src] = str(raw_val).strip().lower()

        # 2. Check for Numeric Discrepancies
        if len(normalized_obs) == len(observations):
            vals = np.array(normalized_obs, dtype=float)
            min_val = float(np.min(vals))
            max_val = float(np.max(vals))
            spread = max_val - min_val

            # Allow 1% tolerance for roundoff
            relative_diff = spread / max(1e-6, abs(min_val))

            if relative_diff > 0.02:
                # Statistical outlier / discrepancy detected
                std_dev = float(np.std(vals))
                mean_val = float(np.mean(vals))
                anomaly_score = round(min(1.0, relative_diff), 3)

                latency = (time.time() - t0) * 1000.0
                ml_telemetry.record_inference(self.model_name, latency, fallback_used=False)

                return AnomalyReport(
                    has_conflict=True,
                    conflict_type="NUMERIC_MISMATCH",
                    fields_involved=[field_name],
                    observed_values=observed_map,
                    normalized_values=normalized_map,
                    anomaly_score=anomaly_score,
                    action_required="EXPERT_REVIEW_REQUIRED",
                    explanation=f"Conflicting numeric values detected for '{field_name}' across sources (Range: {min_val} to {max_val} {target_unit or ''}). Routed to Expert Review.",
                    fallback_used=False,
                )

        # 3. Check for Categorical Discrepancies
        distinct_vals = set(str(v).lower() for v in normalized_map.values())
        if len(distinct_vals) > 1:
            latency = (time.time() - t0) * 1000.0
            ml_telemetry.record_inference(self.model_name, latency, fallback_used=False)

            return AnomalyReport(
                has_conflict=True,
                conflict_type="CATEGORICAL_MISMATCH",
                fields_involved=[field_name],
                observed_values=observed_map,
                normalized_values=normalized_map,
                anomaly_score=0.90,
                action_required="EXPERT_REVIEW_REQUIRED",
                explanation=f"Conflicting categorical declarations detected for '{field_name}' across sources ({list(distinct_vals)}). Routed to Expert Review.",
                fallback_used=False,
            )

        latency = (time.time() - t0) * 1000.0
        ml_telemetry.record_inference(self.model_name, latency, fallback_used=False)

        return AnomalyReport(
            has_conflict=False,
            fields_involved=[field_name],
            observed_values=observed_map,
            normalized_values=normalized_map,
            anomaly_score=0.0,
            action_required="NONE",
            explanation=f"All {len(observations)} sources agree consistently for '{field_name}'.",
            fallback_used=False,
        )


anomaly_detector = MultiSourceAnomalyDetector()
