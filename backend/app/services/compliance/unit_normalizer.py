import re
from typing import Optional, Tuple, Dict, Any


class IncompatibleUnitsError(ValueError):
    """Raised when attempting to convert between non-compatible dimensional units."""
    pass


# Unit normalization definitions and conversion factors to standard SI base units
DIMENSION_MAP = {
    # Length (base: m)
    "m": ("LENGTH", 1.0, "m"),
    "meter": ("LENGTH", 1.0, "m"),
    "meters": ("LENGTH", 1.0, "m"),
    "mm": ("LENGTH", 0.001, "m"),
    "millimeter": ("LENGTH", 0.001, "m"),
    "cm": ("LENGTH", 0.01, "m"),
    "centimeter": ("LENGTH", 0.01, "m"),
    "km": ("LENGTH", 1000.0, "m"),
    "in": ("LENGTH", 0.0254, "m"),
    "inch": ("LENGTH", 0.0254, "m"),
    "ft": ("LENGTH", 0.3048, "m"),
    "foot": ("LENGTH", 0.3048, "m"),

    # Power (base: W)
    "w": ("POWER", 1.0, "W"),
    "watt": ("POWER", 1.0, "W"),
    "watts": ("POWER", 1.0, "W"),
    "mw": ("POWER", 0.001, "W"),
    "milliwatt": ("POWER", 0.001, "W"),
    "kw": ("POWER", 1000.0, "W"),
    "kilowatt": ("POWER", 1000.0, "W"),
    "megaw": ("POWER", 1000000.0, "W"),
    "hp": ("POWER", 745.7, "W"),

    # Voltage (base: V)
    "v": ("VOLTAGE", 1.0, "V"),
    "volt": ("VOLTAGE", 1.0, "V"),
    "volts": ("VOLTAGE", 1.0, "V"),
    "mv": ("VOLTAGE", 0.001, "V"),
    "millivolt": ("VOLTAGE", 0.001, "V"),
    "uv": ("VOLTAGE", 0.000001, "V"),
    "kv": ("VOLTAGE", 1000.0, "V"),
    "kilovolt": ("VOLTAGE", 1000.0, "V"),

    # Current (base: A)
    "a": ("CURRENT", 1.0, "A"),
    "amp": ("CURRENT", 1.0, "A"),
    "amps": ("CURRENT", 1.0, "A"),
    "ampere": ("CURRENT", 1.0, "A"),
    "ma": ("CURRENT", 0.001, "A"),
    "milliamp": ("CURRENT", 0.001, "A"),
    "ua": ("CURRENT", 0.000001, "A"),
    "ka": ("CURRENT", 1000.0, "A"),

    # Resistance (base: ohm)
    "ω": ("RESISTANCE", 1.0, "ohm"),
    "ohm": ("RESISTANCE", 1.0, "ohm"),
    "ohms": ("RESISTANCE", 1.0, "ohm"),
    "kω": ("RESISTANCE", 1000.0, "ohm"),
    "kohm": ("RESISTANCE", 1000.0, "ohm"),
    "kohms": ("RESISTANCE", 1000.0, "ohm"),
    "mω": ("RESISTANCE", 1000000.0, "ohm"),
    "mohm": ("RESISTANCE", 1000000.0, "ohm"),
    "mohms": ("RESISTANCE", 1000000.0, "ohm"),
    "megohm": ("RESISTANCE", 1000000.0, "ohm"),
    "gω": ("RESISTANCE", 1000000000.0, "ohm"),

    # Frequency (base: Hz)
    "hz": ("FREQUENCY", 1.0, "Hz"),
    "hertz": ("FREQUENCY", 1.0, "Hz"),
    "khz": ("FREQUENCY", 1000.0, "Hz"),
    "mhz": ("FREQUENCY", 1000000.0, "Hz"),
    "ghz": ("FREQUENCY", 1000000000.0, "Hz"),

    # Time (base: s)
    "s": ("TIME", 1.0, "s"),
    "sec": ("TIME", 1.0, "s"),
    "second": ("TIME", 1.0, "s"),
    "seconds": ("TIME", 1.0, "s"),
    "ms": ("TIME", 0.001, "s"),
    "min": ("TIME", 60.0, "s"),
    "minute": ("TIME", 60.0, "s"),
    "minutes": ("TIME", 60.0, "s"),
    "h": ("TIME", 3600.0, "s"),
    "hr": ("TIME", 3600.0, "s"),
    "hour": ("TIME", 3600.0, "s"),
    "hours": ("TIME", 3600.0, "s"),

    # Temperature (base: K - handled via dedicated affine conversion)
    "k": ("TEMPERATURE", 1.0, "K"),
    "kelvin": ("TEMPERATURE", 1.0, "K"),
    "°c": ("TEMPERATURE", 1.0, "K"),
    "c": ("TEMPERATURE", 1.0, "K"),
    "degc": ("TEMPERATURE", 1.0, "K"),
    "°f": ("TEMPERATURE", 1.0, "K"),
    "f": ("TEMPERATURE", 1.0, "K"),
    "degf": ("TEMPERATURE", 1.0, "K"),

    # Mass (base: kg)
    "kg": ("MASS", 1.0, "kg"),
    "kilogram": ("MASS", 1.0, "kg"),
    "g": ("MASS", 0.001, "kg"),
    "gram": ("MASS", 0.001, "kg"),
    "mg": ("MASS", 0.000001, "kg"),

    # Pressure (base: Pa)
    "pa": ("PRESSURE", 1.0, "Pa"),
    "kpa": ("PRESSURE", 1000.0, "Pa"),
    "mpa": ("PRESSURE", 1000000.0, "Pa"),
    "bar": ("PRESSURE", 100000.0, "Pa"),
}


def _clean_unit(raw_unit: Optional[str]) -> str:
    """Normalize unit string representation for lookup."""
    if not raw_unit:
        return ""
    u = raw_unit.strip().lower()
    # Normalize omega representations
    u = u.replace("ohm", "ω").replace("ohms", "ω")
    return u


def parse_numeric_value(raw: Any) -> Optional[float]:
    """Parse float from string or numeric input, extracting leading numeric content."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    raw_str = str(raw).strip()
    match = re.match(r"^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?", raw_str)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def parse_value_and_unit(raw_value: Any, fallback_unit: Optional[str] = None) -> Tuple[Optional[float], str]:
    """Extract numeric value and unit from combined string (e.g., '230 V' or '1.8 MΩ')."""
    if raw_value is None:
        return None, (fallback_unit or "")
    if isinstance(raw_value, (int, float)):
        return float(raw_value), (fallback_unit or "")
    
    raw_str = str(raw_value).strip()
    # Match number followed by optional unit
    match = re.match(r"^([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*(.*)$", raw_str)
    if match:
        val = float(match.group(1))
        unit = match.group(2).strip() or fallback_unit or ""
        return val, unit
    return None, (fallback_unit or "")


def get_dimension(unit: str) -> Optional[str]:
    """Lookup dimensional physical quantity for unit."""
    clean = _clean_unit(unit)
    entry = DIMENSION_MAP.get(clean)
    return entry[0] if entry else None


def are_units_compatible(unit1: str, unit2: str) -> bool:
    """Determine if two units belong to the same physical dimension."""
    if not unit1 and not unit2:
        return True
    d1 = get_dimension(unit1)
    d2 = get_dimension(unit2)
    if d1 and d2:
        return d1 == d2
    # If same raw string (e.g. custom or dimensionless)
    return _clean_unit(unit1) == _clean_unit(unit2)


def normalize_to_base(value: float, unit: str) -> Tuple[float, str, str]:
    """Normalize numeric value and unit into standard SI base representation.
    
    Returns:
        (normalized_value, base_unit, conversion_rule)
    """
    clean = _clean_unit(unit)
    entry = DIMENSION_MAP.get(clean)

    if not entry:
        # Dimensionless or unknown unit -> identity conversion
        return value, unit, "Identity (1:1)"

    dimension, factor, base_unit = entry

    # Handle Temperature Affine conversions
    if dimension == "TEMPERATURE":
        if clean in {"°c", "c", "degc"}:
            norm = value + 273.15
            rule = f"T(K) = {value}°C + 273.15 = {norm:.4f} K"
            return norm, "K", rule
        elif clean in {"°f", "f", "degf"}:
            norm = (value - 32.0) * (5.0 / 9.0) + 273.15
            rule = f"T(K) = ({value}°F - 32) * 5/9 + 273.15 = {norm:.4f} K"
            return norm, "K", rule
        else:
            return value, "K", "T(K) = 1.0 * K"

    norm_val = value * factor
    rule = f"1 {unit} = {factor} {base_unit} (normalized: {value} {unit} -> {norm_val:.6g} {base_unit})"
    return norm_val, base_unit, rule


def normalize_pair(
    observed_value: float,
    observed_unit: str,
    expected_value: float,
    expected_unit: str,
) -> Dict[str, Any]:
    """Normalize both observed and expected values into common base unit for deterministic evaluation.
    
    Returns structured dict with compatibility flag, normalized values, base units, and rules.
    """
    if not are_units_compatible(observed_unit, expected_unit):
        return {
            "compatible": False,
            "dimension": None,
            "observed_normalized": None,
            "expected_normalized": None,
            "base_unit": None,
            "conversion_rule": f"Incompatible dimensions: observed '{observed_unit}' vs expected '{expected_unit}'",
        }

    norm_obs, base_u, rule_obs = normalize_to_base(observed_value, observed_unit)
    norm_exp, _, rule_exp = normalize_to_base(expected_value, expected_unit)

    return {
        "compatible": True,
        "dimension": get_dimension(observed_unit) or "CUSTOM",
        "observed_normalized": norm_obs,
        "expected_normalized": norm_exp,
        "base_unit": base_u,
        "observed_rule": rule_obs,
        "expected_rule": rule_exp,
        "conversion_rule": f"Normalized to base unit [{base_u}]: Observed -> {norm_obs:.6g} {base_u}; Expected -> {norm_exp:.6g} {base_u}",
    }


class UnitNormalizer:
    """Statutory Unit Normalizer utility class."""

    @staticmethod
    def normalize(value: float, unit: str) -> Tuple[float, str]:
        val, u, _ = normalize_to_base(value, unit)
        return val, u

    @staticmethod
    def convert(value: float, from_unit: str, to_unit: str) -> float:
        norm_val, base_u, _ = normalize_to_base(value, from_unit)
        clean_to = _clean_unit(to_unit)
        entry = DIMENSION_MAP.get(clean_to)
        if entry:
            dimension, factor, _ = entry
            if dimension == "TEMPERATURE":
                if clean_to in {"°c", "c", "degc"}:
                    return norm_val - 273.15
                elif clean_to in {"°f", "f", "degf"}:
                    return (norm_val - 273.15) * 1.8 + 32.0
                return norm_val
            return norm_val / factor
        return norm_val

    @staticmethod
    def are_compatible(unit1: str, unit2: str) -> bool:
        return are_units_compatible(unit1, unit2)

    @staticmethod
    def normalize_pair(obs_val: float, obs_u: str, exp_val: float, exp_u: str) -> Dict[str, Any]:
        return normalize_pair(obs_val, obs_u, exp_val, exp_u)
