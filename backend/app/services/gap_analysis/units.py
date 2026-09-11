"""Deterministic physical engineering unit normalization utility."""

from typing import Optional, Tuple


def normalize_unit(val: float, from_unit: Optional[str], to_unit: Optional[str]) -> Tuple[float, str]:
    """Normalize physical engineering units deterministically."""
    if not from_unit or not to_unit:
        return val, to_unit or from_unit or ""

    u_from = from_unit.strip().lower().replace("°", "").replace("deg ", "").replace("deg", "")
    u_to = to_unit.strip().lower().replace("°", "").replace("deg ", "").replace("deg", "")

    if u_from == u_to:
        return val, to_unit

    # Temperature: Fahrenheit -> Celsius
    if u_from in ("f", "fahrenheit") and u_to in ("c", "celsius"):
        return round((val - 32.0) * (5.0 / 9.0), 2), to_unit

    # Volume: Liters -> Milliliters
    if u_from in ("l", "liter", "litres", "litre") and u_to in ("ml", "milliliter", "milliliters"):
        return round(val * 1000.0, 2), to_unit

    # Volume: Milliliters -> Liters
    if u_from in ("ml", "milliliter", "milliliters") and u_to in ("l", "liter", "litres"):
        return round(val / 1000.0, 3), to_unit

    # Length: Centimeters -> Millimeters
    if u_from in ("cm", "centimeter") and u_to in ("mm", "millimeter"):
        return round(val * 10.0, 2), to_unit

    # Length: Meters -> Millimeters
    if u_from in ("m", "meter") and u_to in ("mm", "millimeter"):
        return round(val * 1000.0, 2), to_unit

    # Current: Amperes -> Milliamperes
    if u_from in ("a", "amp", "ampere") and u_to in ("ma", "milliampere", "milliamps"):
        return round(val * 1000.0, 2), to_unit

    # Current: Milliamperes -> Amperes
    if u_from in ("ma", "milliampere", "milliamps") and u_to in ("a", "amp", "ampere"):
        return round(val / 1000.0, 4), to_unit

    # Time: Hours -> Minutes
    if u_from in ("h", "hr", "hrs", "hour", "hours") and u_to in ("min", "mins", "minute", "minutes"):
        return round(val * 60.0, 2), to_unit

    # Time: Seconds -> Minutes
    if u_from in ("s", "sec", "secs", "second") and u_to in ("min", "mins", "minute"):
        return round(val / 60.0, 2), to_unit

    return val, to_unit
