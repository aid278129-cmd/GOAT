import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.models.persistent_cad import CADSnapshot, CADModel


def build_cad_snapshot_dict(
    cad_model: CADModel,
    geometry_stats: Dict[str, Any],
    component_tree: List[Dict[str, Any]],
    measurements: List[Dict[str, Any]],
    units: Dict[str, str],
) -> Dict[str, Any]:
    """
    Construct a deterministic, immutable dictionary representing the CAD snapshot.
    """
    return {
        "cad_model_id": cad_model.id,
        "source_evidence_id": cad_model.evidence_id,
        "source_sha256": cad_model.model_hash,
        "kernel_name": cad_model.kernel_name,
        "kernel_version": cad_model.kernel_version,
        "geometry_statistics": {
            "solid_count": cad_model.solid_count,
            "shell_count": cad_model.shell_count,
            "face_count": cad_model.face_count,
            "edge_count": cad_model.edge_count,
            "vertex_count": cad_model.vertex_count,
            "bounding_box": {
                "min": [cad_model.bbox_min_x, cad_model.bbox_min_y, cad_model.bbox_min_z],
                "max": [cad_model.bbox_max_x, cad_model.bbox_max_y, cad_model.bbox_max_z],
                "dimensions": [cad_model.dim_x, cad_model.dim_y, cad_model.dim_z],
            },
            "volume_mm3": cad_model.volume,
            "surface_area_mm2": cad_model.surface_area,
            **geometry_stats,
        },
        "component_tree": component_tree,
        "measurements": measurements,
        "units": units,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
