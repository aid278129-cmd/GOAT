import math
from typing import Dict, Any, List, Optional, Tuple
from backend.app.services.cad.step_parser import ParsedSTEPData
from backend.app.services.cad.cad_errors import CADGeometryParsingError


class ExtractedGeometry:
    """Structured geometry representation extracted from STEP entities."""
    def __init__(self):
        # Component hierarchy
        self.components: List[Dict[str, Any]] = []

        # Geometry features
        self.features: List[Dict[str, Any]] = []

        # Coordinate bounds (in mm)
        self.bbox_min: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.bbox_max: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.dim_x: float = 0.0
        self.dim_y: float = 0.0
        self.dim_z: float = 0.0

        # Statistics
        self.solid_count: int = 0
        self.shell_count: int = 0
        self.face_count: int = 0
        self.edge_count: int = 0
        self.vertex_count: int = 0

        # Physical quantities
        self.volume_mm3: float = 0.0
        self.surface_area_mm2: float = 0.0

        # Lightweight visual mesh representation for Babylon.js
        self.visual_mesh: Dict[str, Any] = {}


class GeometryExtractor:
    """
    Topological geometry extractor for ISO 10303-21 STEP models.
    Determines bounding extents, analytical cylindrical features (holes/bosses),
    planar boundaries (walls), and assembly components.
    """

    def extract(self, parsed: ParsedSTEPData) -> ExtractedGeometry:
        geo = ExtractedGeometry()

        # 1. Statistics
        geo.solid_count = len(parsed.solids)
        geo.shell_count = len(parsed.shells)
        geo.face_count = len(parsed.faces)
        geo.edge_count = len(parsed.edges)
        geo.vertex_count = len(parsed.cartesian_points)

        # 2. Extract Bounding Box
        self._compute_bounding_box(parsed, geo)

        # 3. Extract Assembly Components
        self._extract_components(parsed, geo)

        # 4. Extract Analytical Features (Cylinders/Holes, Planes/Walls)
        self._extract_features(parsed, geo)

        # 5. Compute Volume & Surface Area
        self._compute_physical_quantities(geo)

        # 6. Generate Visual Representation for Babylon.js
        self._generate_visual_mesh(geo)

        return geo

    def _compute_bounding_box(self, parsed: ParsedSTEPData, geo: ExtractedGeometry):
        """Compute exact axis-aligned bounding box from all CARTESIAN_POINT entities."""
        if not parsed.cartesian_points:
            geo.bbox_min = (0.0, 0.0, 0.0)
            geo.bbox_max = (0.0, 0.0, 0.0)
            geo.dim_x = 0.0
            geo.dim_y = 0.0
            geo.dim_z = 0.0
            return

        xs = [pt[0] for pt in parsed.cartesian_points.values()]
        ys = [pt[1] for pt in parsed.cartesian_points.values()]
        zs = [pt[2] for pt in parsed.cartesian_points.values()]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)

        geo.bbox_min = (round(min_x, 4), round(min_y, 4), round(min_z, 4))
        geo.bbox_max = (round(max_x, 4), round(max_y, 4), round(max_z, 4))
        geo.dim_x = round(abs(max_x - min_x), 4)
        geo.dim_y = round(abs(max_y - min_y), 4)
        geo.dim_z = round(abs(max_z - min_z), 4)

    def _extract_components(self, parsed: ParsedSTEPData, geo: ExtractedGeometry):
        """Extract components from PRODUCT_DEFINITION or MANIFOLD_SOLID_BREP entities."""
        if parsed.products:
            for prod_ref in parsed.products:
                ent = parsed.entities.get(prod_ref, {})
                params = ent.get("params", ())
                name = "Product_Component"
                part_num = None
                if params and len(params) > 0:
                    name = str(params[0]).strip("'\"")
                if len(params) > 2:
                    part_num = str(params[2]).strip("'\"")

                geo.components.append({
                    "id": f"comp_{prod_ref.replace('#', '')}",
                    "name": name or f"Component_{prod_ref}",
                    "part_number": part_num,
                    "instance_count": 1,
                    "source_reference": prod_ref,
                    "bounding_box": {
                        "min": geo.bbox_min,
                        "max": geo.bbox_max,
                        "dim": [geo.dim_x, geo.dim_y, geo.dim_z],
                    },
                })
        else:
            # If no product entity, solid models serve as components
            for idx, solid_ref in enumerate(parsed.solids or ["#1"]):
                ent = parsed.entities.get(solid_ref, {})
                params = ent.get("params", ())
                name = str(params[0]).strip("'\"") if params else f"Solid_{idx + 1}"
                geo.components.append({
                    "id": f"comp_solid_{idx + 1}",
                    "name": name or f"Enclosure_Body_{idx + 1}",
                    "part_number": f"PART-{idx + 1:03d}",
                    "instance_count": 1,
                    "source_reference": solid_ref,
                    "bounding_box": {
                        "min": geo.bbox_min,
                        "max": geo.bbox_max,
                        "dim": [geo.dim_x, geo.dim_y, geo.dim_z],
                    },
                })

    def _extract_features(self, parsed: ParsedSTEPData, geo: ExtractedGeometry):
        """Extract topological features (cylinders/holes, planes, solids)."""
        # 1. Cylindrical Features (Holes or Circular Bosses)
        for cyl_ref in parsed.cylinders:
            ent = parsed.entities.get(cyl_ref, {})
            params = ent.get("params", ())
            # CYLINDRICAL_SURFACE('name', placement_ref, radius)
            radius = None
            placement_ref = None
            if len(params) >= 3:
                try:
                    radius = float(params[2])
                    placement_ref = str(params[1])
                except (ValueError, TypeError):
                    pass
            elif len(params) >= 2:
                try:
                    radius = float(params[1])
                except (ValueError, TypeError):
                    pass

            if radius is not None and radius > 0:
                diameter = round(radius * 2.0, 4)
                geo.features.append({
                    "feature_type": "HOLE" if "hole" in str(params).lower() else "CYLINDER",
                    "feature_reference": cyl_ref,
                    "radius": round(radius, 4),
                    "diameter": diameter,
                    "placement_reference": placement_ref,
                    "metadata": {
                        "radius": radius,
                        "diameter": diameter,
                        "unit": "mm",
                        "description": f"Cylindrical feature with diameter {diameter} mm",
                    },
                })

        # 2. Planar Faces (Walls & Boundary Envelopes)
        for pln_ref in parsed.planes:
            ent = parsed.entities.get(pln_ref, {})
            params = ent.get("params", ())
            geo.features.append({
                "feature_type": "PLANE",
                "feature_reference": pln_ref,
                "metadata": {
                    "raw_params": [str(p) for p in params],
                    "unit": "mm",
                    "description": "Planar boundary face",
                },
            })

        # 3. If parallel planes exist with small delta, identify WALL feature
        # Or if vertices define a shell, extract wall thickness from geometry
        # Let's inspect planes or points for wall thickness
        self._detect_wall_thickness_feature(parsed, geo)

    def _detect_wall_thickness_feature(self, parsed: ParsedSTEPData, geo: ExtractedGeometry):
        """Analyze geometry points or planes to detect minimum structural wall thickness."""
        # Find distinct coordinates along each axis to check for thin wall profiles
        xs = sorted(list(set([round(pt[0], 4) for pt in parsed.cartesian_points.values()])))
        ys = sorted(list(set([round(pt[1], 4) for pt in parsed.cartesian_points.values()])))
        zs = sorted(list(set([round(pt[2], 4) for pt in parsed.cartesian_points.values()])))

        min_thickness = None
        source_ref = None

        for axis_coords, axis_name in [(xs, "X"), (ys, "Y"), (zs, "Z")]:
            if len(axis_coords) >= 2:
                for i in range(len(axis_coords) - 1):
                    diff = round(axis_coords[i+1] - axis_coords[i], 4)
                    if 0.5 <= diff <= 15.0:  # Typical engineering plastic/metal enclosure wall thickness
                        if min_thickness is None or diff < min_thickness:
                            min_thickness = diff
                            source_ref = f"Wall_Profile_{axis_name}_{axis_coords[i]}_{axis_coords[i+1]}"

        if min_thickness is not None:
            geo.features.append({
                "feature_type": "WALL",
                "feature_reference": source_ref or "#WALL_PROFILE",
                "thickness": min_thickness,
                "metadata": {
                    "wall_thickness": min_thickness,
                    "unit": "mm",
                    "description": f"Enclosure structural wall profile with thickness {min_thickness} mm",
                },
            })

    def _compute_physical_quantities(self, geo: ExtractedGeometry):
        """Compute volume and surface area based on established B-Rep dimensions."""
        if geo.dim_x > 0 and geo.dim_y > 0 and geo.dim_z > 0:
            # Envelope volume = dim_x * dim_y * dim_z
            geo.volume_mm3 = round(geo.dim_x * geo.dim_y * geo.dim_z, 2)
            # Envelope surface area = 2 * (xy + yz + zx)
            geo.surface_area_mm2 = round(
                2.0 * (geo.dim_x * geo.dim_y + geo.dim_y * geo.dim_z + geo.dim_z * geo.dim_x),
                2,
            )

    def _generate_visual_mesh(self, geo: ExtractedGeometry):
        """Generate lightweight Babylon.js compatible 3D representation."""
        min_x, min_y, min_z = geo.bbox_min
        max_x, max_y, max_z = geo.bbox_max

        # 8 corners of the bounding box
        corners = [
            [min_x, min_y, min_z],
            [max_x, min_y, min_z],
            [max_x, max_y, min_z],
            [min_x, max_y, min_z],
            [min_x, min_y, max_z],
            [max_x, min_y, max_z],
            [max_x, max_y, max_z],
            [min_x, max_y, max_z],
        ]

        # 12 edges of the bounding box
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Bottom loop
            [4, 5], [5, 6], [6, 7], [7, 4],  # Top loop
            [0, 4], [1, 5], [2, 6], [3, 7],  # Vertical pillars
        ]

        geo.visual_mesh = {
            "type": "BOUNDING_ENVELOPE",
            "center": [
                round((min_x + max_x) / 2.0, 4),
                round((min_y + max_y) / 2.0, 4),
                round((min_z + max_z) / 2.0, 4),
            ],
            "dimensions": [geo.dim_x, geo.dim_y, geo.dim_z],
            "corners": corners,
            "edges": edges,
            "components": geo.components,
            "cylinders": [f for f in geo.features if f.get("feature_type") in {"CYLINDER", "HOLE"}],
        }
