from typing import Optional
from datetime import date
from sqlalchemy import String, Integer, BigInteger, Date, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class Document(Base):
    """Uploaded technical document, standard PDF, or test report.

    Trust model: ingestion_status tracks pipeline progress;
    verification_status tracks source authority trust — these are independent.
    A document may be INDEXED but UNVERIFIED.
    """

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # SHA-256 checksum

    # Document classification: standard | test_report | product_spec | bom | qco_order | amendment
    document_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    standard_number: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    edition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    revision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Source provenance link
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sources.id"), nullable=True)

    # Ingestion State: DISCOVERED | DOWNLOADED | EXTRACTED | SEGMENTED | VALIDATED | INDEXED | FAILED
    ingestion_status: Mapped[str] = mapped_column(String(50), default="DISCOVERED", index=True)

    # Trust / Verification State: UNVERIFIED | PROCESSING | VERIFIED | SUPERSEDED | REQUIRES_REVIEW
    # NOTE: INDEXED does NOT imply VERIFIED. These are independent axes.
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", index=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
