from typing import Dict, Any, Optional
from backend.app.services.cad.cad_errors import UnsupportedCADFormatError


class CADCapabilityStatus:
    SUPPORTED = "SUPPORTED"
    FUTURE = "FUTURE"
    VISUALIZATION_ONLY = "VISUALIZATION ONLY"
    UNSUPPORTED = "UNSUPPORTED"


CAD_CAPABILITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "STEP": {
        "status": CADCapabilityStatus.SUPPORTED,
        "extensions": [".step", ".stp"],
        "description": "Standard for the Exchange of Product Model Data (ISO 10303-21). Authoritative boundary representation (B-Rep), topology, and dimensional extraction.",
    },
    "STP": {
        "status": CADCapabilityStatus.SUPPORTED,
        "extensions": [".step", ".stp"],
        "description": "Standard for the Exchange of Product Model Data (ISO 10303-21). Authoritative boundary representation (B-Rep), topology, and dimensional extraction.",
    },
    "IGES": {
        "status": CADCapabilityStatus.FUTURE,
        "extensions": [".iges", ".igs"],
        "description": "Initial Graphics Exchange Specification. Slated for future multi-surface CAD parsing release.",
    },
    "IGS": {
        "status": CADCapabilityStatus.FUTURE,
        "extensions": [".iges", ".igs"],
        "description": "Initial Graphics Exchange Specification. Slated for future multi-surface CAD parsing release.",
    },
    "STL": {
        "status": CADCapabilityStatus.FUTURE,
        "extensions": [".stl"],
        "description": "Standard Tessellation Language. Slated for future polygonal mesh creepage analysis release.",
    },
    "OBJ": {
        "status": CADCapabilityStatus.FUTURE,
        "extensions": [".obj"],
        "description": "Wavefront 3D Object. Slated for future spatial mesh verification release.",
    },
    "GLTF": {
        "status": CADCapabilityStatus.VISUALIZATION_ONLY,
        "extensions": [".gltf", ".glb"],
        "description": "GL Transmission Format. Supported for browser client 3D rendering only. Not authoritative for dimensional compliance assessments.",
    },
    "GERBER": {
        "status": CADCapabilityStatus.FUTURE,
        "extensions": [".gbr", ".gerber"],
        "description": "PCB artwork and trace vector specification. Slated for future electronic creepage & clearance release.",
    },
    "DXF": {
        "status": CADCapabilityStatus.FUTURE,
        "extensions": [".dxf"],
        "description": "Drawing Exchange Format. Slated for future 2D cross-section compliance verification.",
    },
}


def validate_cad_format(filename: str) -> str:
    """
    Validate CAD filename extension against the explicit capability registry.
    Returns format code if SUPPORTED, otherwise raises UnsupportedCADFormatError.
    """
    ext = filename.lower()
    for fmt_key, spec in CAD_CAPABILITY_REGISTRY.items():
        for candidate_ext in spec["extensions"]:
            if ext.endswith(candidate_ext):
                status = spec["status"]
                if status == CADCapabilityStatus.SUPPORTED:
                    return "STEP"
                elif status == CADCapabilityStatus.VISUALIZATION_ONLY:
                    raise UnsupportedCADFormatError(
                        candidate_ext,
                        f"CAD format '{fmt_key}' is VISUALIZATION ONLY. Authoritative engineering compliance assessment requires STEP (.stp, .step) files.",
                    )
                else:
                    raise UnsupportedCADFormatError(
                        candidate_ext,
                        f"CAD format '{fmt_key}' is marked as FUTURE ({spec['description']}). Current authoritative compliance assessment only supports STEP (.stp, .step) geometry.",
                    )

    # Unknown extension
    dot_idx = filename.rfind(".")
    unsupported_ext = filename[dot_idx:] if dot_idx != -1 else "UNKNOWN"
    raise UnsupportedCADFormatError(
        unsupported_ext,
        f"Unsupported CAD format '{unsupported_ext}'. Only standard STEP files (.stp, .step) are supported for authoritative engineering assessment.",
    )
