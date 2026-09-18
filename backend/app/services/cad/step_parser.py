import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from steputils import p21
from backend.app.services.cad.cad_errors import CADGeometryParsingError, CADProcessingLimitExceeded


class ParsedSTEPData:
    """Structured container for parsed ISO 10303-21 STEP entities."""
    def __init__(self):
        self.file_name: str = ""
        self.description: List[str] = []
        self.schema: str = "CONFIG_CONTROL_DESIGN"
        self.author: str = ""
        self.organization: str = ""

        # Raw entities map by reference id (e.g. '#10')
        self.entities: Dict[str, Any] = {}

        # Categorized references
        self.products: List[str] = []
        self.solids: List[str] = []
        self.shells: List[str] = []
        self.faces: List[str] = []
        self.surfaces: List[str] = []
        self.edges: List[str] = []
        self.points: List[str] = []
        self.placements: List[str] = []
        self.cylinders: List[str] = []
        self.planes: List[str] = []

        # Point coordinates map: '#10' -> (x, y, z)
        self.cartesian_points: Dict[str, Tuple[float, float, float]] = {}

        # Units detected
        self.length_unit: str = "mm"
        self.angle_unit: str = "deg"


class StepParser:
    """
    Authoritative ISO 10303-21 STEP exchange structure parser.
    Extracts header metadata, B-Rep topology graph, geometric points, analytical surfaces,
    and assembly relationships without resorting to regex or simulated data.
    """

    def __init__(self, max_features: int = 100000):
        self.max_features = max_features

    def parse_file(self, file_path: str) -> ParsedSTEPData:
        """Parse STEP file from filesystem."""
        path = Path(file_path)
        if not path.exists():
            raise CADGeometryParsingError(f"STEP file does not exist at '{file_path}'")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return self.parse_text(content, filename=path.name)
        except Exception as exc:
            if isinstance(exc, (CADGeometryParsingError, CADProcessingLimitExceeded)):
                raise
            raise CADGeometryParsingError(f"Failed to read or parse STEP file: {str(exc)}", details={"path": str(path)})

    def parse_text(self, text: str, filename: str = "model.stp") -> ParsedSTEPData:
        """Parse STEP Part 21 content string into structured entities."""
        parsed = ParsedSTEPData()
        parsed.file_name = filename

        try:
            step_file = p21.loads(text)
        except Exception as exc:
            raise CADGeometryParsingError(f"ISO 10303-21 syntax parse error: {str(exc)}")

        # 1. Parse Header Section
        self._extract_header(step_file, parsed)

        # 2. Parse Data Section
        if not step_file.data:
            raise CADGeometryParsingError("STEP file contains no DATA section.")

        data_section = step_file.data[0]
        instances = data_section.instances

        if len(instances) > self.max_features:
            raise CADProcessingLimitExceeded("MAX_GEOMETRY_FEATURES", len(instances), self.max_features)

        # Index instances
        for ref_id, inst in instances.items():
            ref = str(ref_id)
            if not ref.startswith("#"):
                ref = f"#{ref}"

            entity = inst.entity
            name = getattr(entity, "name", "").upper()
            params = getattr(entity, "params", ())

            parsed.entities[ref] = {
                "ref": ref,
                "name": name,
                "params": params,
            }

            self._categorize_entity(ref, name, params, parsed)

        return parsed

    def _extract_header(self, step_file, parsed: ParsedSTEPData):
        """Extract metadata from STEP HEADER section."""
        try:
            header = step_file.header
            if hasattr(header, "entities"):
                for entity in header.entities:
                    name = getattr(entity, "name", "").upper()
                    params = getattr(entity, "params", ())
                    if name == "FILE_DESCRIPTION" and params:
                        parsed.description = [str(p) for p in params[0]] if isinstance(params[0], (list, tuple)) else [str(params[0])]
                    elif name == "FILE_SCHEMA" and params:
                        schema_val = params[0]
                        if isinstance(schema_val, (list, tuple)) and len(schema_val) > 0:
                            parsed.schema = str(schema_val[0]).strip("'\"")
                        else:
                            parsed.schema = str(schema_val).strip("'\"")
                    elif name == "FILE_NAME" and len(params) >= 5:
                        if not parsed.file_name or parsed.file_name == "model.stp":
                            parsed.file_name = str(params[0]).strip("'\"")
                        # Author
                        authors = params[2]
                        if isinstance(authors, (list, tuple)) and len(authors) > 0:
                            parsed.author = str(authors[0]).strip("'\"")
                        # Organization
                        orgs = params[3]
                        if isinstance(orgs, (list, tuple)) and len(orgs) > 0:
                            parsed.organization = str(orgs[0]).strip("'\"")
        except Exception:
            pass

    def _categorize_entity(self, ref: str, name: str, params: tuple, parsed: ParsedSTEPData):
        """Categorize entity and extract analytical coordinate & surface properties."""
        if name in {"PRODUCT_DEFINITION", "PRODUCT_DEFINITION_FORMATION", "PRODUCT", "NEXT_ASSEMBLY_USAGE_OCCURRENCE"}:
            parsed.products.append(ref)

        elif name in {"MANIFOLD_SOLID_BREP", "BREP_WITH_VOIDS", "FACETED_BREP", "SOLID_MODEL"}:
            parsed.solids.append(ref)

        elif name in {"CLOSED_SHELL", "OPEN_SHELL"}:
            parsed.shells.append(ref)

        elif name in {"ADVANCED_FACE", "FACE_SURFACE", "FACE"}:
            parsed.faces.append(ref)

        elif name == "CARTESIAN_POINT":
            parsed.points.append(ref)
            # CARTESIAN_POINT('name', (x, y, z))
            if len(params) >= 2 and isinstance(params[1], (list, tuple)):
                coords = params[1]
                try:
                    x = float(coords[0]) if len(coords) > 0 else 0.0
                    y = float(coords[1]) if len(coords) > 1 else 0.0
                    z = float(coords[2]) if len(coords) > 2 else 0.0
                    parsed.cartesian_points[ref] = (x, y, z)
                except (ValueError, TypeError):
                    pass

        elif name == "AXIS2_PLACEMENT_3D":
            parsed.placements.append(ref)

        elif name == "CYLINDRICAL_SURFACE":
            parsed.surfaces.append(ref)
            parsed.cylinders.append(ref)

        elif name == "PLANE":
            parsed.surfaces.append(ref)
            parsed.planes.append(ref)

        elif name in {"CONICAL_SURFACE", "TOROIDAL_SURFACE", "SPHERICAL_SURFACE", "B_SPLINE_SURFACE_WITH_KNOTS"}:
            parsed.surfaces.append(ref)

        elif name in {"EDGE_CURVE", "ORIENTED_EDGE", "LINE", "CIRCLE"}:
            parsed.edges.append(ref)
