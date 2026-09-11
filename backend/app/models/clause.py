from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class Clause(Base):
    """Clause-level granularity representation within an Indian Standard.

    Trust model: verification_status defaults to REQUIRES_REVIEW.
    Segmentation confidence (segmentation_status) is separate from
    source verification (verification_status).
    """

    __tablename__ = "clauses"

    standard_id: Mapped[str] = mapped_column(String(36), ForeignKey("standards.id"), index=True, nullable=False)
    parent_clause_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=True)

    clause_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # e.g. "4.1", "5.2.3"
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)

    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Segmentation audit: CONFIDENT | REQUIRES_REVIEW
    segmentation_status: Mapped[str] = mapped_column(String(50), default="CONFIDENT")

    # Verification: UNVERIFIED | REQUIRES_REVIEW | VERIFIED | SUPERSEDED
    # NOTE: Defaults to REQUIRES_REVIEW. AI extraction ≠ regulatory verification.
    verification_status: Mapped[str] = mapped_column(String(50), default="REQUIRES_REVIEW", index=True)

    version: Mapped[str] = mapped_column(String(50), default="1.0")
    source_document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("documents.id"), nullable=True)

    # Vector embedding representation for pgvector / similarity search
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    standard: Mapped["Standard"] = relationship("Standard", back_populates="clauses")
    subclauses: Mapped[List["Clause"]] = relationship("Clause", backref="parent_clause", remote_side="Clause.id")
    requirements: Mapped[List["Requirement"]] = relationship(
        "Requirement", back_populates="clause", cascade="all, delete-orphan"
    )
