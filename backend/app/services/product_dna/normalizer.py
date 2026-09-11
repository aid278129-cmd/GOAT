"""Deterministic Fact Normalization & Unit Standardization for Layer 2 Product DNA.

Standardizes technical attributes, electrical ratings, capacity volumes, and material
classifications into canonical units without altering their physical meaning.
Enforces physical plausibility bounds checks.
"""

import re
from typing import Tuple, Optional, Any, Dict, List


def normalize_capacity(raw_val: str) -> Tuple[Optional[int], Optional[str]]:
    """Normalize volume/capacity expressions to milliliters (ml).
    e.g. '750 ml', '750mL', '0.75 litre', '0.75L', '1 L' -> (750, 'ml')
    """
    raw = str(raw_val).strip().lower()
    
    # Match litres e.g. "0.75 litre", "0.75l", "1.5 litres", "1L"
    litre_match = re.search(r"([\d\.]+)\s*(?:litres?|liter|l)\b", raw)
    if litre_match:
        try:
            litres = float(litre_match.group(1))
            ml = int(round(litres * 1000))
            return ml, "ml"
        except ValueError:
            pass

    # Match ml e.g. "750 ml", "750ml", "1000 ml"
    ml_match = re.search(r"(\d+)\s*(?:ml|millilitres?|milliliter)\b", raw)
    if ml_match:
        try:
            return int(ml_match.group(1)), "ml"
        except ValueError:
            pass

    # Bare number check if context suggests capacity
    bare_num = re.search(r"^(\d+)$", raw)
    if bare_num:
        return int(bare_num.group(1)), "ml"

    return None, None


def normalize_electrical(raw_val: str) -> Dict[str, Any]:
    """Normalize electrical voltage, frequency, and wattage expressions.
    e.g. '230 volts AC', '230V a.c.', '1.5 kW', '1500W', '50 Hz'
    """
    res: Dict[str, Any] = {}
    raw = str(raw_val).strip()

    # Voltage: "230V", "230 volts", "220-240 V"
    volt_match = re.search(r"(\d+(?:-\d+)?)\s*(?:v|volts|v\.a\.c\.)", raw, re.I)
    if volt_match:
        res["voltage"] = volt_match.group(1)
        res["voltage_unit"] = "V"

    # Current type AC / DC
    if re.search(r"(?:a\.c\.|a\.c|ac|\balternating current\b)", raw, re.I):
        res["current_type"] = "AC"
    elif re.search(r"(?:d\.c\.|d\.c|dc|\bdirect current\b)", raw, re.I):
        res["current_type"] = "DC"

    # Frequency: "50 Hz", "50Hz", "60 Hz", "50 c/s"
    freq_match = re.search(r"(\d+)\s*(?:hz|hertz|c/s)", raw, re.I)
    if freq_match:
        res["frequency"] = int(freq_match.group(1))
        res["frequency_unit"] = "Hz"

    # Power/Wattage: Support both Watts (W) and Kilowatts (kW)
    # e.g. "1.5 kW", "2 kW", "1500 W", "1500 watts"
    kw_match = re.search(r"([\d\.]+)\s*(?:kw|kilowatts?)\b", raw, re.I)
    if kw_match:
        try:
            kw_val = float(kw_match.group(1))
            res["wattage"] = int(round(kw_val * 1000))
            res["wattage_unit"] = "W"
            res["wattage_normalized_from"] = f"{kw_val} kW"
        except ValueError:
            pass
    else:
        watt_match = re.search(r"(\d+)\s*(?:w|watts?)\b", raw, re.I)
        if watt_match:
            res["wattage"] = int(watt_match.group(1))
            res["wattage_unit"] = "W"

    return res


def normalize_material(raw_material: str) -> str:
    """Normalize common raw material strings to canonical technical tokens."""
    mat = str(raw_material).strip().lower()
    
    # Stainless steel variants
    if "304" in mat and any(k in mat for k in ["steel", "ss", "stainless", "aisi"]):
        return "stainless_steel_grade_304"
    if "316" in mat and any(k in mat for k in ["steel", "ss", "stainless", "aisi"]):
        return "stainless_steel_grade_316"
    if "stainless" in mat or "ss" in mat:
        return "stainless_steel"

    # Polymers & Plastics
    if "polypropylene" in mat or re.search(r"\bpp\b", mat):
        return "polypropylene_fr" if "flame" in mat or "v-0" in mat else "polypropylene"
    if "silicone" in mat:
        return "silicone_food_grade"
    if "copper" in mat:
        return "copper"
    if "aluminum" in mat or "aluminium" in mat:
        return "aluminum"
    if "brass" in mat:
        return "brass"
    if "polycarbonate" in mat:
        return "polycarbonate"

    # Return clean snake_case representation
    clean = re.sub(r"[^a-z0-9]+", "_", mat).strip("_")
    return clean or mat


def check_physical_plausibility(
    field_name: str,
    value: Any,
    unit: Optional[str] = None,
    category: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Validate that numeric product values conform to real-world physical bounds."""
    try:
        if field_name in ("rated_voltage", "voltage"):
            val_str = str(value).strip()
            m = re.match(r"^(\-?\d+(?:\.\d+)?)", val_str)
            val_num = float(m.group(1)) if m else float(val_str)
            if val_num <= 0:
                return False, f"Supply voltage cannot be zero or negative ({val_num} V)."
            if val_num > 1000:
                return False, f"Domestic/Commercial appliance voltage ({val_num} V) exceeds 1000V limit."


        elif field_name in ("rated_power_input", "wattage", "power"):
            val_num = float(value)
            if val_num <= 0:
                return False, f"Rated power input cannot be zero or negative ({val_num} W)."
            if val_num > 25000:
                return False, f"Rated power ({val_num} W) is physically implausible for domestic/commercial equipment (exceeds 25kW limit)."

        elif field_name in ("nominal_capacity", "capacity"):
            val_num = float(value)
            if val_num <= 0:
                return False, f"Product capacity cannot be zero or negative ({val_num} ml)."
            if val_num > 500000:  # 500 Litres
                return False, f"Capacity ({val_num} ml) exceeds plausible limits for personal/domestic containers."

        elif field_name in ("rated_frequency", "frequency"):
            val_num = float(value)
            if val_num not in (50, 60):
                return False, f"Rated mains frequency must be standard 50 Hz or 60 Hz, not {val_num} Hz."

    except (ValueError, TypeError):
        pass

    return True, None
