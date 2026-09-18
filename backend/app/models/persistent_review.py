from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.compliance_job import ComplianceJob
    from backend.app.models.persistent_assessment import AssessmentRun, PersistentAssessmentResult, ComplianceFinding
    from backend.app.models.persistent_standards import JobRequirement
    from backend.app.models.user import User


class ReviewItem(Base):
    """Authoritative persistent record of a human engineering/regulatory review."""

    __tablename__ = "review_items"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("assessment_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    requirement_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("job_requirements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assessment_result_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("persistent_assessment_results.id", ondelete="SET NULL"), nullable=True, index=True
    )
    finding_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("compliance_findings.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Review Types:
    # EVIDENCE_REVIEW | DNA_CONFLICT_REVIEW | DOCUMENT_REVIEW | TEXT_REVIEW | GEOMETRY_REVIEW | ENGINEERING_JUDGEMENT | FINDING_REVIEW
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Status:
    # PENDING | ASSIGNED | IN_REVIEW | APPROVED | REJECTED | RETURNED | CANCELLED
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)

    # Priority:
    # CRITICAL | HIGH | MEDIUM | LOW
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    assigned_reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_reviewer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Reviewer decision: APPROVE | REJECT | RETURN
    decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Immutable snapshot captured at review initiation
    review_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob")
    assessment_run: Mapped[Optional["AssessmentRun"]] = relationship("AssessmentRun")
    requirement: Mapped[Optional["JobRequirement"]] = relationship("JobRequirement")
    assessment_result: Mapped[Optional["PersistentAssessmentResult"]] = relationship("PersistentAssessmentResult")
    finding: Mapped[Optional["ComplianceFinding"]] = relationship("ComplianceFinding")
    assigned_reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_reviewer_id])
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])


class HumanAttestation(Base):
    """Authoritative persistent record of a formal regulatory human compliance attestation."""

    __tablename__ = "human_attestations"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("review_items.id", ondelete="SET NULL"), nullable=True, index=True
    )

    attestor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    attestor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    attestor_role: Mapped[str] = mapped_column(String(50), nullable=False)

    # Attestation Types:
    # STANDARDS_CONFORMANCE | CLAUSE_COMPLIANCE | JOB_COMPLIANCE | EVIDENCE_SUFFICIENCY | DEVIATION_APPROVAL
    attestation_type: Mapped[str] = mapped_column(String(100), default="STANDARDS_CONFORMANCE", nullable=False)

    # Formal statutory legal declaration statement
    attestation_statement: Mapped[str] = mapped_column(Text, nullable=False)

    # Bounded scope definition:
    # {
    #   "job_id": "...",
    #   "standard_id": "...",
    #   "standard_identifier": "...",
    #   "standard_revision": "...",
    #   "assessment_run_id": "...",
    #   "clauses_covered": ["4.1", "4.2", ...],
    #   "evidence_hashes": ["sha256...", ...],
    #   "timestamp": "..."
    # }
    scope: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Decision: CONFORMANT | NON_CONFORMANT | CONDITIONAL_CONFORMANCE | WAIVER_GRANTED
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    conditions_or_stipulations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    attested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Lifecycle status: DRAFT | ACTIVE | SUPERSEDED | REVOKED
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False, index=True)

    supersedes_attestation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("human_attestations.id", ondelete="SET NULL"), nullable=True
    )

    # Revocation metadata
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    revocation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob")
    assessment_run: Mapped["AssessmentRun"] = relationship("AssessmentRun")
    review_item: Mapped[Optional["ReviewItem"]] = relationship("ReviewItem")
    attestor: Mapped["User"] = relationship("User", foreign_keys=[attestor_id])
