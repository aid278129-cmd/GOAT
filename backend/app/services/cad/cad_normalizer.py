from typing import Tuple, Dict, Any


CAD_UNIT_CONVERSIONS: Dict[str, float] = {
    # Length conversions to mm
    "mm": 1.0,
    "millimeter": 1.0,
    "millimeters": 1.0,
    "m": 1000.0,
    "meter": 1000.0,
    "meters": 1000.0,
    "cm": 10.0,
    "centimeter": 10.0,
    "centimeters": 10.0,
    "in": 25.4,
    "inch": 25.4,
    "inches": 25.4,
    "ft": 304.8,
    "foot": 304.8,
    "feet": 304.8,

    # Area conversions to mm2
    "mm2": 1.0,
    "cm2": 100.0,
    "m2": 1000000.0,
    "in2": 645.16,

    # Volume conversions to mm3
    "mm3": 1.0,
    "cm3": 1000.0,
    "m3": 1000000000.0,
    "in3": 16387.064,
    "l": 1000000.0,
    "liter": 1000000.0,
    "liters": 1000000.0,

    # Angles to degrees
    "deg": 1.0,
    "degree": 1.0,
    "degrees": 1.0,
    "rad": 57.2957795,
    "radian": 57.2957795,
    "radians": 57.2957795,
}


class CADNormalizer:
    """Normalizes CAD quantities to canonical engineering units."""

    @staticmethod
    def normalize_length(value: float, from_unit: str = "mm") -> Tuple[float, str]:
        unit_key = from_unit.lower().strip()
        factor = CAD_UNIT_CONVERSIONS.get(unit_key, 1.0)
        return round(value * factor, 4), "mm"

    @staticmethod
    def normalize_volume(value: float, from_unit: str = "mm3") -> Tuple[float, str]:
        unit_key = from_unit.lower().strip()
        factor = CAD_UNIT_CONVERSIONS.get(unit_key, 1.0)
        return round(value * factor, 2), "mm3"

    @staticmethod
    def normalize_area(value: float, from_unit: str = "mm2") -> Tuple[float, str]:
        unit_key = from_unit.lower().strip()
        factor = CAD_UNIT_CONVERSIONS.get(unit_key, 1.0)
        return round(value * factor, 2), "mm2"
