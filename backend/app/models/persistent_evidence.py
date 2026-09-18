from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, BigInteger, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.compliance_job import ComplianceJob
    from backend.app.models.persistent_dna import PersistentDNA


class PersistentEvidence(Base):
    """Authoritative persistent evidence artifact stored durably with server SHA-256."""

    __tablename__ = "persistent_evidence"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, audio, image, engineering
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), default="Engineering Upload", nullable=False)
    
    # Lifecycle: UPLOADED -> QUEUED -> PROCESSING -> EXTRACTION_COMPLETE -> REQUIRES_REVIEW
    processing_status: Mapped[str] = mapped_column(String(50), default="UPLOADED", nullable=False)
    
    # Acceptance Gating: REQUIRES_REVIEW -> ACCEPTED | REJECTED
    acceptance_status: Mapped[str] = mapped_column(String(50), default="REQUIRES_REVIEW", nullable=False)
    acceptance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob", back_populates="evidence_items")
    lifecycle_events: Mapped[List["EvidenceLifecycleEvent"]] = relationship(
        "EvidenceLifecycleEvent", back_populates="evidence", cascade="all, delete-orphan", order_by="EvidenceLifecycleEvent.created_at"
    )
    dna_parameters: Mapped[List["PersistentDNA"]] = relationship(
        "PersistentDNA", back_populates="source_evidence"
    )


class EvidenceLifecycleEvent(Base):
    """Append-only lifecycle event tracking transitions of evidence state."""

    __tablename__ = "evidence_lifecycle_events"

    evidence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("persistent_evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    evidence: Mapped["PersistentEvidence"] = relationship("PersistentEvidence", back_populates="lifecycle_events")
