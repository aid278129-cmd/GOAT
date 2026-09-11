from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, Text, ForeignKey, JSON, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class AssessmentStatus(str, Enum):
    """Lifecycle states of an assessment."""
    DRAFT = "DRAFT"
    COLLECTING_INFORMATION = "COLLECTING_INFORMATION"
    ANALYZING = "ANALYZING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLIANCE_REVIEW = "COMPLIANCE_REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"


class Assessment(Base):
    """First-class Assessment entity representing an auditable compliance assessment lifecycle."""

    __tablename__ = "assessments"

    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True, nullable=False)
    assessment_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=AssessmentStatus.DRAFT.value, index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(50), default="DEVELOPMENT_MODE", nullable=False)  # AUTHORITATIVE_MODE | DEVELOPMENT_MODE

    # Audit metadata
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Dynamic assessment state snapshots
    product_dna_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    applicability_snapshot: Mapped[list] = mapped_column(JSON, default=list)
    compliance_summary_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    snapshots: Mapped[List["AssessmentSnapshot"]] = relationship(
        "AssessmentSnapshot", back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentSnapshot(Base):
    """Immutable point-in-time snapshot of an assessment for strict audit reproducibility."""

    __tablename__ = "assessment_snapshots"

    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessments.id"), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'EVIDENCE_ADDED', 'CLARIFICATION_ANSWERED', 'DECISION_RECALCULATED'

    product_dna_state: Mapped[dict] = mapped_column(JSON, default=dict)
    knowledge_version: Mapped[str] = mapped_column(String(50), default="M4.0-OFFICIAL-2023", nullable=False)
    rule_versions: Mapped[dict] = mapped_column(JSON, default=dict)
    decision_records_snapshot: Mapped[list] = mapped_column(JSON, default=list)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    summary_counts: Mapped[dict] = mapped_column(JSON, default=dict)

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="snapshots")
