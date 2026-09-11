import re
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ExtractedStandardMetadata(BaseModel):
    standard_number: str
    title: str
    edition: str = "First Edition"
    revision: Optional[str] = None
    publication_year: Optional[int] = None
    category: str = "General Engineering"
    scheme: str = "Scheme I"
    is_mandatory_qco: bool = False
    scope_summary: Optional[str] = None


# Regex for Indian Standard numbers: "IS 17526:2021", "IS 302-2-15:2009", "IS/ISO 9001"
IS_NUMBER_REGEX = re.compile(
    r"\b(IS\s*(?:[A-Z\/]+)?\s*\d+(?:[-\/]\d+)*(?::\d{4})?)\b",
    re.IGNORECASE,
)


def extract_standard_metadata_from_text(
    full_text: str, default_standard_number: Optional[str] = None, default_title: Optional[str] = None
) -> ExtractedStandardMetadata:
    """Extract standard number, title, and metadata from document text header or fallback defaults."""
    standard_number = default_standard_number
    title = default_title or "Indian Standard Specification"
    category = "General"
    scheme = "Scheme I"
    is_qco = False

    # Find IS number in first 2000 characters
    header_sample = full_text[:3000]
    match = IS_NUMBER_REGEX.search(header_sample)
    if match and not standard_number:
        standard_number = match.group(1).strip().upper()

    if not standard_number:
        standard_number = "IS UNKNOWN"

    # Infer publication year from IS number (e.g. "IS 17526:2021" -> 2021)
    year_match = re.search(r":(\d{4})", standard_number)
    pub_year = int(year_match.group(1)) if year_match else None

    # Detect mandatory QCO references
    if re.search(r"\b(Quality Control Order|QCO|Mandatory Certification)\b", header_sample, re.I):
        is_qco = True

    # Detect Scheme CRS vs ISI Mark
    if "COMPULSORY REGISTRATION SCHEME" in header_sample.upper() or "CRS" in header_sample:
        scheme = "Scheme II (CRS)"
    else:
        scheme = "Scheme I (ISI Mark)"

    # Detect common category keywords
    text_lower = full_text.lower()
    if any(k in text_lower for k in ["beverage", "flask", "bottle", "drinkware", "cooler"]):
        category = "Drinkware & Food Contact Containers"
    elif any(k in text_lower for k in ["electrical", "heater", "kettle", "toaster"]):
        category = "Electrical & Domestic Appliances"
    elif any(k in text_lower for k in ["footwear", "shoe", "boot"]):
        category = "Footwear & Leather"

    # Extract Scope section if available
    scope_match = re.search(
        r"(?:1\s+SCOPE|1\.\s+SCOPE|SCOPE)([\s\S]{50,600}?)(?:2\s+REFERENCES|2\.\s+NORMATIVE|2\s+NORMATIVE)",
        full_text,
        re.I,
    )
    scope_text = scope_match.group(1).strip() if scope_match else None

    return ExtractedStandardMetadata(
        standard_number=standard_number,
        title=title,
        edition="First Edition",
        publication_year=pub_year,
        category=category,
        scheme=scheme,
        is_mandatory_qco=is_qco,
        scope_summary=scope_text,
    )
