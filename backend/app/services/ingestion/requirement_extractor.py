import re
from typing import List, Optional
from pydantic import BaseModel
from backend.app.services.ingestion.clause_segmenter import SegmentedClause


class ExtractedRequirement(BaseModel):
    code: str
    requirement_type: str  # MATERIAL | DIMENSION | PERFORMANCE | SAFETY | CONSTRUCTION | MARKING | PACKAGING | TESTING | DOCUMENTATION | OTHER
    description: str
    measurable_condition: Optional[str] = None
    evidence_type: Optional[str] = None
    test_method_reference: Optional[str] = None
    interpretation_status: str = "CONFIDENT"  # CONFIDENT | REQUIRES_REVIEW


# Regex patterns for requirement categorization
MATERIAL_KEYWORDS = re.compile(r"\b(material|stainless steel|grade|alloy|copper|brass|polymer|plastic|silicone|rubber|coating|chemical composition)\b", re.I)
PERFORMANCE_KEYWORDS = re.compile(r"\b(thermal|temperature|retention|efficiency|endurance|life cycle|leakage|pressure|capacity|flow rate|insulation)\b", re.I)
SAFETY_KEYWORDS = re.compile(r"\b(safety|electric shock|hazardous|toxicity|lead content|flammability|earthing|insulation resistance|contamination)\b", re.I)
MARKING_KEYWORDS = re.compile(r"\b(marking|marked|label|isi mark|standard mark|batch number|manufacturer name|symbol|packaging)\b", re.I)
DIMENSION_KEYWORDS = re.compile(r"\b(dimension|thickness|diameter|height|tolerance|volume|nominal size|weight|mass)\b", re.I)
TEST_METHOD_REGEX = re.compile(r"(?:tested in accordance with|as per clause|as described in|method of test|test method)\s+([A-Za-z0-9\.\:\-]+)", re.I)
MEASURABLE_REGEX = re.compile(r"(?:shall\s+(?:not\s+be\s+less\s+than|be\s+at\s+least|not\s+exceed|conform\s+to|be\s+within))\s+([^\.\;]{5,100})", re.I)


def extract_requirements_from_clause(
    clause: SegmentedClause, standard_number_clean: str = "IS"
) -> List[ExtractedRequirement]:
    """Extract structured, auditable requirements from a segmented clause without inventing interpretations."""
    text = clause.text_content
    clean_std = re.sub(r"[^A-Za-z0-9]", "", standard_number_clean)
    clean_cls = re.sub(r"[^A-Za-z0-9]", "_", clause.clause_number)

    # Determine requirement type by keyword frequency and clause context
    req_type = "PERFORMANCE"
    evidence_type = "lab_test"
    interp_status = "CONFIDENT"

    if MATERIAL_KEYWORDS.search(text) or "material" in clause.title.lower():
        req_type = "MATERIAL"
        evidence_type = "material_certificate"
    elif SAFETY_KEYWORDS.search(text) or "safety" in clause.title.lower():
        req_type = "SAFETY"
        evidence_type = "safety_audit"
    elif MARKING_KEYWORDS.search(text) or "marking" in clause.title.lower():
        req_type = "MARKING"
        evidence_type = "visual_inspection"
    elif DIMENSION_KEYWORDS.search(text) or "dimension" in clause.title.lower():
        req_type = "DIMENSION"
        evidence_type = "dimensional_inspection"
    elif PERFORMANCE_KEYWORDS.search(text) or "performance" in clause.title.lower():
        req_type = "PERFORMANCE"
        evidence_type = "lab_test"
    else:
        req_type = "CONSTRUCTION"
        evidence_type = "inspection"
        interp_status = "REQUIRES_REVIEW"

    # Extract measurable condition
    measurable_match = MEASURABLE_REGEX.search(text)
    measurable_condition = measurable_match.group(0).strip() if measurable_match else None

    # Extract test method reference
    test_match = TEST_METHOD_REGEX.search(text)
    test_ref = test_match.group(0).strip() if test_match else None

    req_code = f"REQ-{clean_std}-{clean_cls}"

    return [
        ExtractedRequirement(
            code=req_code,
            requirement_type=req_type,
            description=clause.title + ": " + text[:300].strip() + ("..." if len(text) > 300 else ""),
            measurable_condition=measurable_condition,
            evidence_type=evidence_type,
            test_method_reference=test_ref,
            interpretation_status=interp_status,
        )
    ]
