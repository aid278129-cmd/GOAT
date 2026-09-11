import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.core.logging import logger
from backend.app.services.ingestion.pdf_extractor import ExtractedPage

# Dotted decimal clauses e.g. "1.1", "4.2.1", "5.4.3.2"
DOTTED_CLAUSE_REGEX = re.compile(
    r"^(?:(?:CLAUSE|Clause)\s+)?(\d+\.\d+(?:\.\d+)*)(?:\s*[\.\:\-\s]\s*(.*))?$"
)
# Major numbered sections e.g. "4 REQUIREMENTS", "6 PACKAGING", "6. MARKING"
MAJOR_SECTION_REGEX = re.compile(
    r"^(?:(?:SECTION|Section)\s+)?(\d+)\s*[\.\:\-]\s*([A-Za-z0-9\s,\-\(\)\/\'\"]{2,80})$|^(?:(?:SECTION|Section)\s+)?(\d+)\s+([A-Z\s,\-\(\)\/\']{3,80})$"
)


class SegmentedClause(BaseModel):
    clause_number: str
    title: str
    section: Optional[str] = None
    text_content: str
    page_start: int
    page_end: int
    parent_clause_number: Optional[str] = None
    segmentation_status: str = "CONFIDENT"  # CONFIDENT | REQUIRES_REVIEW
    char_count: int = 0
    subclause_numbers: List[str] = Field(default_factory=list)


def get_parent_clause_number(clause_num: str) -> Optional[str]:
    """Calculate the parent clause identifier from dotted decimal hierarchy (e.g. '4.2.1' -> '4.2', '4.2' -> '4')."""
    parts = clause_num.split(".")
    if len(parts) > 1:
        return ".".join(parts[:-1])
    return None


def match_clause_header(line_str: str) -> Optional[tuple]:
    """Detect if a line represents a standard clause or major section heading."""
    line_clean = line_str.strip()
    if not line_clean:
        return None

    # Try dotted clause e.g. "4.2 Material Requirements", "1.1 This standard...", "5.4 Thermal Performance"
    m_dotted = DOTTED_CLAUSE_REGEX.match(line_clean)
    if m_dotted:
        cand_num = m_dotted.group(1).strip()
        rest = (m_dotted.group(2) or "").strip()

        # Filter out decimal measurements like "1.0 metre"
        if len(cand_num.split(".")) == 2 and rest.lower().startswith(("metre", "meter", "kg", "percent", "hours", "min", "sec")):
            return None

        # Determine if 'rest' is a title or start of sentence
        if rest and len(rest) <= 80 and not rest.endswith("."):
            cand_title = rest
        elif rest and "—" in rest:
            cand_title = rest.split("—")[0].strip()
        elif rest and "-" in rest:
            cand_title = rest.split("-")[0].strip()
        else:
            cand_title = f"Clause {cand_num}"

        return cand_num, cand_title

    # Try major section e.g. "4 REQUIREMENTS", "6 PACKAGING", "6. MARKING"
    m_major = MAJOR_SECTION_REGEX.match(line_clean)
    if m_major:
        num = (m_major.group(1) or m_major.group(3)).strip()
        title = (m_major.group(2) or m_major.group(4) or "").strip()
        if title and not title.lower().startswith(("hours", "minutes", "seconds", "times", "drops", "percent")):
            return num, title

    return None


def segment_clauses_from_pages(pages: List[ExtractedPage]) -> List[SegmentedClause]:
    """Segment extracted document pages into structured hierarchical clauses with page provenance."""
    if not pages:
        return []

    tagged_lines = []
    for p in pages:
        for line in p.text.split("\n"):
            tagged_lines.append({"text": line, "page": p.page_number})

    clauses: List[SegmentedClause] = []
    current_clause_num: Optional[str] = None
    current_title: str = ""
    current_text_lines: List[str] = []
    current_page_start: int = 1
    current_page_end: int = 1
    current_section: Optional[str] = None

    for item in tagged_lines:
        line_str = item["text"].strip()
        page_num = item["page"]

        if not line_str:
            if current_clause_num:
                current_text_lines.append("")
            continue

        header_match = match_clause_header(line_str)

        if header_match:
            cand_num, cand_title = header_match

            # Save previous clause if active
            if current_clause_num and current_text_lines:
                full_text = "\n".join(current_text_lines).strip()
                if len(full_text) > 0:
                    parent_num = get_parent_clause_number(current_clause_num)
                    status = "CONFIDENT" if len(full_text) >= 15 else "REQUIRES_REVIEW"
                    clauses.append(
                        SegmentedClause(
                            clause_number=current_clause_num,
                            title=current_title or f"Clause {current_clause_num}",
                            section=current_section,
                            text_content=full_text,
                            page_start=current_page_start,
                            page_end=current_page_end,
                            parent_clause_number=parent_num,
                            segmentation_status=status,
                            char_count=len(full_text),
                        )
                    )

            # Start new clause
            current_clause_num = cand_num
            current_title = cand_title or f"Clause {cand_num}"
            current_text_lines = [line_str]
            current_page_start = page_num
            current_page_end = page_num

            # Infer current major section number
            major_section_num = cand_num.split(".")[0]
            current_section = f"Section {major_section_num}"
        else:
            if current_clause_num:
                current_text_lines.append(line_str)
                current_page_end = page_num

    # Flush final clause
    if current_clause_num and current_text_lines:
        full_text = "\n".join(current_text_lines).strip()
        if len(full_text) > 0:
            parent_num = get_parent_clause_number(current_clause_num)
            status = "CONFIDENT" if len(full_text) >= 15 else "REQUIRES_REVIEW"
            clauses.append(
                SegmentedClause(
                    clause_number=current_clause_num,
                    title=current_title or f"Clause {current_clause_num}",
                    section=current_section,
                    text_content=full_text,
                    page_start=current_page_start,
                    page_end=current_page_end,
                    parent_clause_number=parent_num,
                    segmentation_status=status,
                    char_count=len(full_text),
                )
            )

    # Populate subclause_numbers on parent clauses
    clause_map = {c.clause_number: c for c in clauses}
    for c in clauses:
        if c.parent_clause_number and c.parent_clause_number in clause_map:
            clause_map[c.parent_clause_number].subclause_numbers.append(c.clause_number)

    logger.info(f"Segmented {len(clauses)} clauses across {len(pages)} pages.")
    return clauses
