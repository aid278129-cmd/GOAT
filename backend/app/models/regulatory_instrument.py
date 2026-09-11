from typing import Optional
from datetime import date
from sqlalchemy import String, Text, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class RegulatoryInstrument(Base):
    """Regulatory instrument (QCO, CRS notification, etc.) linked to a standard.

    Separates STANDARD INFORMATION from REGULATORY / MANDATORY STATUS.
    A standard's existence does not imply mandatory certification.
    Mandatory status requires a verified regulatory instrument.
    """

    __tablename__ = "regulatory_instruments"

    standard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("standards.id"), index=True, nullable=False
    )

    # QCO | CRS_NOTIFICATION | OTHER
    instrument_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    notification_number: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    gazette_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    scope_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)

    # UNVERIFIED | REQUIRES_REVIEW | VERIFIED
    verification_status: Mapped[str] = mapped_column(
        String(50), default="REQUIRES_REVIEW", index=True
    )

    source_document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
