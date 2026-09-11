from typing import Optional
from datetime import date
from sqlalchemy import String, Text, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class Amendment(Base):
    """Amendment relationship linked to a parent standard version.

    Preserves amendment identity, source provenance, and affected clause
    references without blindly merging text into the base standard.
    """

    __tablename__ = "amendments"

    standard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("standards.id"), index=True, nullable=False
    )

    amendment_number: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Amendment No. 1"
    publication_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    source_document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=True
    )

    # Comma-separated clause numbers or JSON; null = unknown / REQUIRES_REVIEW
    affected_clauses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # UNVERIFIED | REQUIRES_REVIEW | VERIFIED
    verification_status: Mapped[str] = mapped_column(
        String(50), default="REQUIRES_REVIEW", index=True
    )
