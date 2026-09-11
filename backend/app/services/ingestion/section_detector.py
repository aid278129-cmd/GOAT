import re
from typing import List, Optional
from pydantic import BaseModel


class DetectedSection(BaseModel):
    section_number: str
    section_title: str
    full_heading: str
    page_number: int


SECTION_HEADING_REGEX = re.compile(
    r"^(?:SECTION\s+)?(\d+|ANNEX\s+[A-Z])[\.\s]+([A-Z\s,–\-\(\)\/]{3,80})$",
    re.MULTILINE,
)

COMMON_BIS_SECTIONS = {
    "1": "SCOPE",
    "2": "REFERENCES / NORMATIVE REFERENCES",
    "3": "TERMINOLOGY / DEFINITIONS",
    "4": "REQUIREMENTS / MATERIAL REQUIREMENTS",
    "5": "SAMPLING / METHODS OF TEST",
    "6": "PACKAGING AND MARKING",
    "7": "CRITERIA FOR CONFORMITY",
}


def detect_sections_in_text(pages: list) -> List[DetectedSection]:
    """Identify major BIS standard structural sections across extracted pages."""
    sections: List[DetectedSection] = []

    for page in pages:
        lines = page.text.split("\n")
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            match = SECTION_HEADING_REGEX.match(line_clean)
            if match:
                sec_num = match.group(1).strip()
                sec_title = match.group(2).strip()
                if len(sec_title) > 2 and not sec_title.isdigit():
                    sections.append(
                        DetectedSection(
                            section_number=sec_num,
                            section_title=sec_title,
                            full_heading=line_clean,
                            page_number=page.page_number,
                        )
                    )

    return sections
