from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.compliance_job import ComplianceJob
    from backend.app.models.persistent_evidence import PersistentEvidence


class PersistentDNA(Base):
    """Authoritative structured Product DNA parameter derived strictly from accepted evidence."""

    __tablename__ = "persistent_dna"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    category: Mapped[str] = mapped_column(String(100), nullable=False)  # Identity, Electrical, Mechanical, Safety, etc.
    parameter: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="VERIFIED", nullable=False)  # VERIFIED, CONFLICT, UNVERIFIED

    # Full Provenance
    source_evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("persistent_evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_or_sheet: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    verified_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verification_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob", back_populates="dna_parameters")
    source_evidence: Mapped[Optional["PersistentEvidence"]] = relationship(
        "PersistentEvidence", back_populates="dna_parameters"
    )
