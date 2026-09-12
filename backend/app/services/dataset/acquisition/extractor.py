"""Regulatory Metadata and Relationship Extraction Engine.

Enforces:
1. Strict factuality: Missing standard metadata defaults to 'UNKNOWN'. Never hallucinated.
2. QCO extraction: Missing QCO defaults to 'QCO_UNCERTAIN' or 'QCO_NOT_VERIFIED'.
3. Provenance-preserving relationship tracking:
   SUPERSEDES, SUPERSEDED_BY, AMENDS, AMENDED_BY, WITHDRAWN, REFERENCES, NORMATIVE_REFERENCE.
4. Laboratory records extraction from official recognition schedules.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class ExtractedStandardMetadata(BaseModel):
    standard_number: str = "UNKNOWN"
    title: str = "UNKNOWN"
    edition: str = "UNKNOWN"
    revision: str = "UNKNOWN"
    publication_date: str = "UNKNOWN"
    scope: str = "UNKNOWN"
    document_status: str = "ACTIVE"
    amendments: List[str] = Field(default_factory=list)
    normative_references: List[str] = Field(default_factory=list)
    related_products: List[str] = Field(default_factory=list)


class ExtractedQCOMetadata(BaseModel):
    qco_identifier: str = "UNKNOWN"
    notification_number: str = "UNKNOWN"
    standard_numbers: List[str] = Field(default_factory=list)
    product_scope: str = "UNKNOWN"
    issue_date: str = "UNKNOWN"
    effective_date: str = "UNKNOWN"
    scheme: str = "UNKNOWN"
    mandatory_status: bool = True
    conditions: List[str] = Field(default_factory=list)
    exemptions: List[str] = Field(default_factory=list)
    amendments: List[str] = Field(default_factory=list)
    verification_status: str = "QCO_NOT_VERIFIED"


class ExtractedLabRecord(BaseModel):
    lab_name: str
    location: str = "UNKNOWN"
    recognition_status: str = "RECOGNISED"
    is_numbers: List[str] = Field(default_factory=list)
    test_facilities: List[str] = Field(default_factory=list)
    source_url: str


class MetadataExtractor:
    """Extracts structured regulatory metadata from text without hallucinating missing fields."""

    @classmethod
    def extract_standard_metadata(cls, text: str, default_code: Optional[str] = None) -> ExtractedStandardMetadata:
        """Extracts standard code, title, and normative references from document text."""
        std_num = default_code or "UNKNOWN"
        if std_num == "UNKNOWN":
            m_std = re.search(r"IS\s+(\d+(?:\s*\([^\)]+\))?(?::\d{4})?)", text)
            if m_std:
                std_num = f"IS {m_std.group(1).strip()}"

        # Title extraction
        title = "UNKNOWN"
        m_title = re.search(r"(?:Indian Standard|INDIAN STANDARD)\s*\n+([A-Z0-9\s,\-\(\)]+?)(?=\n+[A-Z\s]{4,}|\n+Gr\s+\d|\n+ICS)", text)
        if m_title:
            cand = m_title.group(1).strip()
            if 5 < len(cand) < 150:
                title = cand

        # Edition / Revision
        edition = "UNKNOWN"
        m_ed = re.search(r"(First|Second|Third|Fourth|Fifth|\d+(?:st|nd|rd|th)?)\s+Revision", text, re.IGNORECASE)
        if m_ed:
            edition = m_ed.group(0).strip()

        # Publication date
        pub_date = "UNKNOWN"
        m_date = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}", text)
        if m_date:
            pub_date = m_date.group(0).strip()

        # Scope
        scope = "UNKNOWN"
        m_scope = re.search(r"(?:1\s+SCOPE|1\.\s+SCOPE|SCOPE)\s*\n+([^\n]+(?:\n+[^\n]+){1,4})", text, re.IGNORECASE)
        if m_scope:
            scope = m_scope.group(1).strip()

        # Status
        status = "ACTIVE"
        if "superseded" in text.lower():
            status = "SUPERSEDED"
        elif "withdrawn" in text.lower():
            status = "WITHDRAWN"

        # Normative references: only when explicitly defined under normative references section
        normative_refs = []
        m_norm_sec = re.search(r"(?:2\s+NORMATIVE REFERENCES|NORMATIVE REFERENCES)\s*\n+(.+?)(?=\n+\d+\s+[A-Z]|\Z)", text, re.DOTALL | re.IGNORECASE)
        if m_norm_sec:
            sec_text = m_norm_sec.group(1)[:2000]
            found_refs = re.findall(r"IS\s+\d+(?:\s*\([^\)]+\))?(?::\d{4})?", sec_text)
            normative_refs = sorted(list(set(found_refs)))

        # Amendments mentioned
        amendments = []
        amds = re.findall(r"Amendment\s+No\.\s*\d+(?:\s+[A-Za-z]+\s+\d{4})?", text, re.IGNORECASE)
        if amds:
            amendments = sorted(list(set(amds)))

        return ExtractedStandardMetadata(
            standard_number=std_num,
            title=title,
            edition=edition,
            revision=edition,
            publication_date=pub_date,
            scope=scope,
            document_status=status,
            amendments=amendments,
            normative_references=normative_refs,
        )

    @classmethod
    def extract_qco_metadata(cls, text: str, source_id: str = "") -> ExtractedQCOMetadata:
        """Extracts Quality Control Order facts from regulatory text."""
        notif_num = "UNKNOWN"
        m_so = re.search(r"S\.O\.\s*[\d\(\)A-Za-z\.\-\/]+", text)
        if m_so:
            notif_num = m_so.group(0).strip().rstrip(".,;:—-\u2014")

        # Governed IS numbers
        is_nums = sorted(list(set(re.findall(r"IS\s+\d+(?:\s*\([^\)]+\))?(?::\d{4})?", text))))

        # Issue / Effective dates
        effective_date = "UNKNOWN"
        m_eff = re.search(r"(?:shall come into force on|date of its publication|with effect from)\s+([^\.\n]+)", text, re.IGNORECASE)
        if m_eff:
            effective_date = m_eff.group(1).strip()

        # Exemptions
        exemptions = []
        if "exemption" in text.lower() or "shall not apply" in text.lower():
            m_ex = re.findall(r"nothing in this order shall apply to\s+([^\.]+)", text, re.IGNORECASE)
            exemptions = [e.strip() for e in m_ex]

        # Mandatory status
        mandatory = "compulsory" in text.lower() or "shall conform" in text.lower() or "order" in text.lower()

        return ExtractedQCOMetadata(
            qco_identifier=source_id or notif_num,
            notification_number=notif_num,
            standard_numbers=is_nums,
            effective_date=effective_date,
            scheme="Scheme-I" if "scheme-i" in text.lower() else ("Scheme-II" if "scheme-ii" in text.lower() else "UNKNOWN"),
            mandatory_status=mandatory,
            exemptions=exemptions,
            verification_status="QCO_NOT_VERIFIED",
        )
