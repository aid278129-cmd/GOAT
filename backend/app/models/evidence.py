from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class Evidence(Base):
    """First-class evidence model supporting rigorous regulatory verification and traceability.
    
    Invariants:
    - Product fact != Compliance evidence.
    - An evidence record represents verified or unverified documentary/laboratory data.
    - Satisfied verdicts require verified evidence from authorized sources.
    """

    __tablename__ = "evidence"

    # Unique domain identifier (e.g. "EV-LAB-001", "EV-MAT-002")
    evidence_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="")
    assessment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("assessments.id"), index=True, nullable=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("documents.id"), nullable=True)

    # Supported evidence types:
    # TEST_REPORT | LAB_REPORT | MATERIAL_CERTIFICATE | CALIBRATION_CERTIFICATE |
    # PRODUCT_SPECIFICATION | TECHNICAL_DRAWING | LABEL_PHOTO | PACKAGING_PHOTO |
    # MANUFACTURER_DECLARATION | BIS_DOCUMENT | QCO_DOCUMENT | PRODUCT_MANUAL | USER_PROVIDED_DOCUMENT
    evidence_type: Mapped[str] = mapped_column(String(50), default="TEST_REPORT", index=True, nullable=False)

    # Source provenance
    source_type: Mapped[str] = mapped_column(String(50), default="LABORATORY", nullable=False)  # LABORATORY | MANUFACTURER | REGULATOR | USER_UPLOAD
    source_authority: Mapped[str] = mapped_column(String(100), default="LAB_REPORT", index=True, nullable=False)  # NABL_ACCREDITED_LAB | BIS_OFFICIAL | MANUFACTURER_DECLARATION | USER_ASSERTED

    # Verification status: VERIFIED | UNVERIFIED | REJECTED | REQUIRES_REVIEW
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", index=True, nullable=False)

    # Extracted claim and normalization
    extracted_claim: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    normalized_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Document location & traceability
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Backwards compatibility with M1-M4
    source_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    extracted_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Extraction method & confidence
    extraction_method: Mapped[str] = mapped_column(String(50), default="STRUCTURED_PARSE", nullable=False)  # STRUCTURED_PARSE | OCR_TABLE | REGEX | MANUAL_ENTRY | LLM_ASSISTED
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Audit & Verification details
    verified_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash of content

    # Flexible metadata
    provenance_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.evidence_id:
            self.evidence_id = f"EV-{self.id[:8].upper()}" if self.id else f"EV-AUTO"
        if not self.source_text and self.source_excerpt:
            self.source_text = self.source_excerpt
        if not self.source_excerpt and self.source_text:
            self.source_excerpt = self.source_text
        if not self.extracted_value and self.normalized_value:
            self.extracted_value = str(self.normalized_value)
