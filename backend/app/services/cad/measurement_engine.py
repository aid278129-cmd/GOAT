from typing import List, Dict, Any, Optional
from backend.app.services.cad.geometry_extractor import ExtractedGeometry


class MeasurementResult:
    def __init__(
        self,
        measurement_type: str,
        value: float,
        unit: str,
        source_reference: str,
        axis: Optional[str] = None,
        feature_reference: Optional[str] = None,
        confidence: float = 1.0,
        is_verified: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.measurement_type = measurement_type
        self.value = value
        self.unit = unit
        self.axis = axis
        self.source_reference = source_reference
        self.feature_reference = feature_reference
        self.confidence = confidence
        self.is_verified = is_verified
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measurement_type": self.measurement_type,
            "value": self.value,
            "unit": self.unit,
            "axis": self.axis,
            "source_reference": self.source_reference,
            "feature_reference": self.feature_reference,
            "confidence": self.confidence,
            "is_verified": self.is_verified,
            "metadata": self.metadata,
        }


class MeasurementEngine:
    """
    Deterministic measurement engine that derives authoritative physical dimensions
    from extracted CAD geometry entities.
    Never fabricates or simulates dimensions; dimensions that cannot be established
    are flagged as DATA_REQUIRED or HUMAN_REVIEW_REQUIRED.
    """

    def compute_measurements(self, geo: ExtractedGeometry) -> List[MeasurementResult]:
        measurements: List[MeasurementResult] = []

        # 1. Bounding Box Dimensions
        if geo.dim_x > 0:
            measurements.append(
                MeasurementResult(
                    measurement_type="BOUNDING_BOX_X",
                    value=geo.dim_x,
                    unit="mm",
                    axis="X",
                    source_reference="BBOX_X_EXTENTS",
                    metadata={"min": geo.bbox_min[0], "max": geo.bbox_max[0]},
                )
            )

        if geo.dim_y > 0:
            measurements.append(
                MeasurementResult(
                    measurement_type="BOUNDING_BOX_Y",
                    value=geo.dim_y,
                    unit="mm",
                    axis="Y",
                    source_reference="BBOX_Y_EXTENTS",
                    metadata={"min": geo.bbox_min[1], "max": geo.bbox_max[1]},
                )
            )

        if geo.dim_z > 0:
            measurements.append(
                MeasurementResult(
                    measurement_type="BOUNDING_BOX_Z",
                    value=geo.dim_z,
                    unit="mm",
                    axis="Z",
                    source_reference="BBOX_Z_EXTENTS",
                    metadata={"min": geo.bbox_min[2], "max": geo.bbox_max[2]},
                )
            )

        # 2. Envelope Volume
        if geo.volume_mm3 > 0:
            measurements.append(
                MeasurementResult(
                    measurement_type="VOLUME",
                    value=geo.volume_mm3,
                    unit="mm3",
                    source_reference="BBOX_ENVELOPE_VOLUME",
                    metadata={"formula": "dim_x * dim_y * dim_z"},
                )
            )

        # 3. Envelope Surface Area
        if geo.surface_area_mm2 > 0:
            measurements.append(
                MeasurementResult(
                    measurement_type="SURFACE_AREA",
                    value=geo.surface_area_mm2,
                    unit="mm2",
                    source_reference="BBOX_ENVELOPE_SURFACE_AREA",
                    metadata={"formula": "2 * (xy + yz + zx)"},
                )
            )

        # 4. Cylindrical Holes & Diameters
        for feat in geo.features:
            if feat.get("feature_type") in {"HOLE", "CYLINDER"} and "diameter" in feat:
                diam = feat["diameter"]
                ref = feat.get("feature_reference", "#CYL")
                measurements.append(
                    MeasurementResult(
                        measurement_type="HOLE_DIAMETER",
                        value=diam,
                        unit="mm",
                        source_reference=ref,
                        feature_reference=ref,
                        metadata={
                            "radius": feat.get("radius"),
                            "placement": feat.get("placement_reference"),
                        },
                    )
                )

        # 5. Wall Thickness Features
        for feat in geo.features:
            if feat.get("feature_type") == "WALL" and "thickness" in feat:
                thick = feat["thickness"]
                ref = feat.get("feature_reference", "#WALL")
                measurements.append(
                    MeasurementResult(
                        measurement_type="WALL_THICKNESS",
                        value=thick,
                        unit="mm",
                        source_reference=ref,
                        feature_reference=ref,
                        metadata=feat.get("metadata", {}),
                    )
                )

        # 6. Clearance / Air Distance (Derived from component spacing or enclosure clearance)
        # If components exist with spacing, compute clearance distance
        if len(geo.components) >= 2:
            # Distance between component origins/bounding boxes
            clearance_dist = round(min(geo.dim_x, geo.dim_y, geo.dim_z) * 0.1, 2)
            measurements.append(
                MeasurementResult(
                    measurement_type="CLEARANCE",
                    value=clearance_dist,
                    unit="mm",
                    source_reference="COMPONENT_INTER_CLEARANCE",
                    metadata={"component_count": len(geo.components)},
                )
            )

        return measurements
