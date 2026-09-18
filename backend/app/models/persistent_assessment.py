from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, ForeignKey, JSON, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.compliance_job import ComplianceJob
    from backend.app.models.persistent_standards import JobStandard, JobRequirement
    from backend.app.models.persistent_evidence import PersistentEvidence
    from backend.app.models.persistent_dna import PersistentDNA
    from backend.app.models.user import User


class AssessmentRun(Base):
    """Authoritative persistent snapshot of an entire deterministic compliance assessment run."""

    __tablename__ = "assessment_runs"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    standard_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("job_standards.id", ondelete="CASCADE"), nullable=True, index=True
    )

    engine_version: Mapped[str] = mapped_column(String(50), default="v2.0-deterministic", nullable=False)
    standard_revision: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    dna_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Authoritative counts by state (never percentage unless calculated from these counts)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob")
    standard: Mapped[Optional["JobStandard"]] = relationship("JobStandard")
    results: Mapped[List["PersistentAssessmentResult"]] = relationship(
        "PersistentAssessmentResult", back_populates="assessment_run", cascade="all, delete-orphan", order_by="PersistentAssessmentResult.clause_number"
    )
    findings: Mapped[List["ComplianceFinding"]] = relationship(
        "ComplianceFinding", back_populates="assessment_run", cascade="all, delete-orphan"
    )


class PersistentAssessmentResult(Base):
    """Authoritative deterministic assessment result for an individual clause requirement."""

    __tablename__ = "persistent_assessment_results"

    assessment_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("job_requirements.id", ondelete="CASCADE"), nullable=True, index=True
    )

    clause_number: Mapped[str] = mapped_column(String(50), nullable=False)
    parameter_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Applicability State: APPLICABLE | NOT_APPLICABLE | DATA_REQUIRED | CONFLICT
    applicability_state: Mapped[str] = mapped_column(String(50), default="APPLICABLE", nullable=False)
    applicability_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Engineering State: NOT_ASSESSED | DATA_REQUIRED | CONFLICT | NOT_APPLICABLE | ENGINEERING_PASS | ENGINEERING_GAP | HUMAN_REVIEW_REQUIRED
    assessment_state: Mapped[str] = mapped_column(String(50), nullable=False)

    observed_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observed_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    normalized_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    normalized_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    threshold_min: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    threshold_max: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    comparison_operator: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    evaluation_expression: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("persistent_evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_dna_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("persistent_dna.id", ondelete="SET NULL"), nullable=True, index=True
    )

    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trace_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), default="v2.0-deterministic", nullable=False)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    evaluated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    assessment_run: Mapped["AssessmentRun"] = relationship("AssessmentRun", back_populates="results")
    requirement: Mapped[Optional["JobRequirement"]] = relationship("JobRequirement")


class ComplianceFinding(Base):
    """Persistent statutory non-conformance or engineering gap finding."""

    __tablename__ = "compliance_findings"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("job_requirements.id", ondelete="CASCADE"), nullable=True, index=True
    )

    severity: Mapped[str] = mapped_column(String(50), default="MAJOR", nullable=False)  # CRITICAL | MAJOR | MINOR | OBSERVATION
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    observed_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status: OPEN | UNDER_REVIEW | RESOLVED | WAIVED
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assessment_run: Mapped["AssessmentRun"] = relationship("AssessmentRun", back_populates="findings")
    requirement: Mapped[Optional["JobRequirement"]] = relationship("JobRequirement")
