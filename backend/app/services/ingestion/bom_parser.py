"""Bill of Materials (BOM) Tabular Parser.

Layer 1: Input Processing (BOM Tables & Parametric Attribute Extraction).
Handles real-world MSME engineering BOMs:
- Supports CSV, TSV, Semicolon-separated, and JSON BOM formats.
- Disambiguates duplicate component parts with unique keys.
- Tolerates missing columns with safe regulatory fallbacks.
- Normalizes diverse unit formats (kW -> W, V AC, Hz, Amperes).
"""

import csv
import io
import json
import re
from typing import Dict, Any, List, Optional, Set
from backend.app.core.logging import logger


def normalize_electrical_ratings(text: str) -> Dict[str, str]:
    """Extract and standardize electrical ratings with unit normalization."""
    ratings: Dict[str, str] = {}
    
    # 1. Power (Watts / kW)
    # Check for kW first (e.g. "1.5 kW", "2.2kw")
    kw_match = re.search(r"(\d+(?:\.\d+)?)\s*k(?:w|watt)s?\b", text, re.IGNORECASE)
    if kw_match:
        try:
            val_w = int(float(kw_match.group(1)) * 1000)
            ratings["power"] = f"{val_w} W"
        except ValueError:
            ratings["power"] = f"{kw_match.group(1)} kW"
    else:
        w_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:w|watt|watts)\b", text, re.IGNORECASE)
        if w_match:
            ratings["power"] = f"{w_match.group(1)} W"

    # 2. Voltage (Volts / V AC)
    v_range_match = re.search(r"(\d{2,3}(?:\s*-\s*\d{2,3})?)\s*(?:v\b|volt|volts|v\s*ac)", text, re.IGNORECASE)
    if v_range_match:
        val = v_range_match.group(1).replace(" ", "")
        ratings["voltage"] = f"{val} V AC"

    # 3. Frequency (Hz / Hertz)
    hz_match = re.search(r"(\d{2}(?:\s*-\s*\d{2})?)\s*(?:hz|hertz)", text, re.IGNORECASE)
    if hz_match:
        ratings["frequency"] = f"{hz_match.group(1).replace(' ', '')} Hz"

    # 4. Current (Amperes / A)
    a_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:a\b|amp|amps|amperes)", text, re.IGNORECASE)
    if a_match:
        ratings["current"] = f"{a_match.group(1)} A"

    return ratings


class BOMParserService:
    """Parses structured BOM tables into normalized Product DNA attributes."""

    def parse_bom_content(self, content_str: str, filename: str = "bom.csv") -> Dict[str, Any]:
        """Parse BOM content string into components and parametric attributes."""
        content_str = (content_str or "").strip()
        if not content_str:
            return {
                "components": [],
                "materials": [],
                "electrical_ratings": {},
                "total_parts": 0,
                "duplicates_found": 0,
                "summary": "Empty BOM file received.",
            }

        # 1. Try JSON First
        if content_str.startswith("{") or content_str.startswith("["):
            try:
                data = json.loads(content_str)
                if isinstance(data, list):
                    return self._process_component_list(data)
                elif isinstance(data, dict) and "components" in data and isinstance(data["components"], list):
                    return self._process_component_list(data["components"])
            except json.JSONDecodeError:
                pass  # Fall through to tabular parsing

        # 2. Delimiter Auto-Detection (CSV, TSV, Semicolon)
        first_line = content_str.split("\n", 1)[0]
        if "\t" in first_line:
            delimiter = "\t"
        elif ";" in first_line and "," not in first_line:
            delimiter = ";"
        else:
            delimiter = ","

        try:
            reader = csv.reader(io.StringIO(content_str), delimiter=delimiter)
            rows = [row for row in reader if row and any(cell.strip() for cell in row)]
        except Exception as exc:
            logger.warning(f"CSV read error: {exc}")
            return {
                "components": [],
                "materials": [],
                "electrical_ratings": {},
                "total_parts": 0,
                "duplicates_found": 0,
                "summary": f"Failed to parse tabular data: {str(exc)}",
            }

        if not rows:
            return {
                "components": [],
                "materials": [],
                "electrical_ratings": {},
                "total_parts": 0,
                "duplicates_found": 0,
                "summary": "No tabular data rows found in BOM.",
            }

        headers = [h.strip().lower() for h in rows[0]]
        data_rows = rows[1:]

        components: List[Dict[str, Any]] = []
        materials_set: Set[str] = set()
        seen_part_numbers: Dict[str, int] = {}
        duplicates_count = 0
        all_text_fragments: List[str] = []

        for idx, row in enumerate(data_rows):
            comp_dict = {}
            for col_idx, cell in enumerate(row):
                key = headers[col_idx] if col_idx < len(headers) else f"col_{col_idx}"
                comp_dict[key] = cell.strip()

            # Name resolution
            name = (
                comp_dict.get("part name")
                or comp_dict.get("part_name")
                or comp_dict.get("component")
                or comp_dict.get("name")
                or comp_dict.get("item")
                or comp_dict.get("description")
                or f"Part {idx + 1}"
            )

            # Material resolution
            material = (
                comp_dict.get("material")
                or comp_dict.get("raw material")
                or comp_dict.get("raw_material")
                or comp_dict.get("composition")
                or "Standard Grade"
            )
            if material and material != "Standard Grade":
                materials_set.add(material)

            # Specification resolution
            spec = (
                comp_dict.get("specification")
                or comp_dict.get("spec")
                or comp_dict.get("rating")
                or comp_dict.get("value")
                or ""
            )

            # Quantity resolution with fallback
            raw_qty = comp_dict.get("quantity") or comp_dict.get("qty") or "1"
            # Sanitize quantity (e.g. "1 nos", "2 pcs" -> "1", "2")
            qty_match = re.search(r"(\d+(?:\.\d+)?)", str(raw_qty))
            quantity = qty_match.group(1) if qty_match else "1"

            # Part Number with Duplicate Disambiguation
            base_part_no = (
                comp_dict.get("part number")
                or comp_dict.get("part_no")
                or comp_dict.get("part_number")
                or comp_dict.get("id")
                or f"P{idx + 1:03d}"
            )

            if base_part_no in seen_part_numbers:
                dup_idx = seen_part_numbers[base_part_no]
                seen_part_numbers[base_part_no] += 1
                duplicates_count += 1
                unique_part_no = f"{base_part_no}-dup{dup_idx}"
            else:
                seen_part_numbers[base_part_no] = 1
                unique_part_no = base_part_no

            all_text_fragments.append(f"{name} {material} {spec}")

            components.append({
                "part_number": unique_part_no,
                "name": name,
                "material": material,
                "specification": spec,
                "quantity": quantity,
            })

        # Extract unified electrical ratings across all component texts
        full_spec_text = " ".join(all_text_fragments)
        electrical_ratings = normalize_electrical_ratings(full_spec_text)

        return {
            "components": components,
            "materials": sorted(list(materials_set)),
            "electrical_ratings": electrical_ratings,
            "total_parts": len(components),
            "duplicates_found": duplicates_count,
            "summary": (
                f"Successfully parsed {len(components)} components with {len(materials_set)} verified materials. "
                + (f"Resolved {duplicates_count} duplicate part IDs." if duplicates_count > 0 else "")
            ),
        }

    def _process_component_list(self, raw_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process JSON array of component specifications."""
        components: List[Dict[str, Any]] = []
        materials_set: Set[str] = set()
        seen_part_numbers: Dict[str, int] = {}
        duplicates_count = 0
        all_text_fragments: List[str] = []

        for idx, item in enumerate(raw_list):
            name = item.get("name") or item.get("component") or item.get("part_name") or f"Part {idx + 1}"
            mat = item.get("material") or item.get("composition") or "Standard Grade"
            if mat and mat != "Standard Grade":
                materials_set.add(mat)

            spec = item.get("specification") or item.get("rating") or item.get("value") or ""
            base_part_no = str(item.get("part_number") or item.get("id") or f"P{idx + 1:03d}")

            if base_part_no in seen_part_numbers:
                dup_idx = seen_part_numbers[base_part_no]
                seen_part_numbers[base_part_no] += 1
                duplicates_count += 1
                unique_part_no = f"{base_part_no}-dup{dup_idx}"
            else:
                seen_part_numbers[base_part_no] = 1
                unique_part_no = base_part_no

            raw_qty = str(item.get("quantity", 1))
            qty_match = re.search(r"(\d+(?:\.\d+)?)", raw_qty)
            quantity = qty_match.group(1) if qty_match else "1"

            all_text_fragments.append(f"{name} {mat} {spec}")

            components.append({
                "part_number": unique_part_no,
                "name": name,
                "material": mat,
                "specification": spec,
                "quantity": quantity,
            })

        full_spec_text = " ".join(all_text_fragments)
        electrical_ratings = normalize_electrical_ratings(full_spec_text)

        return {
            "components": components,
            "materials": sorted(list(materials_set)),
            "electrical_ratings": electrical_ratings,
            "total_parts": len(components),
            "duplicates_found": duplicates_count,
            "summary": (
                f"Parsed {len(components)} components from JSON structure with {len(materials_set)} materials. "
                + (f"Resolved {duplicates_count} duplicate part IDs." if duplicates_count > 0 else "")
            ),
        }


bom_parser_service = BOMParserService()
