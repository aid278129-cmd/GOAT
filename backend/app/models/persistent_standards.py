from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.compliance_job import ComplianceJob


class JobStandard(Base):
    """Authoritative assigned standard for a compliance job."""

    __tablename__ = "job_standards"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    standard_identifier: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., IS 13252 (Part 1): 2010
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    revision_year: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    applicability: Mapped[str] = mapped_column(String(100), default="MANDATORY", nullable=False)
    is_active_assessment_basis: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scope_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob", back_populates="standards")
    requirements: Mapped[List["JobRequirement"]] = relationship(
        "JobRequirement", back_populates="standard", cascade="all, delete-orphan", order_by="JobRequirement.clause_reference"
    )


class JobRequirement(Base):
    """Authoritative standard clause requirement assigned to a job."""

    __tablename__ = "job_requirements"

    standard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_standards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Statutory Schema
    requirement_id: Mapped[str] = mapped_column(String(100), default="", index=True, nullable=False)  # e.g. REQ-1.5.1
    clause_reference: Mapped[str] = mapped_column(String(50), default="", nullable=False)  # e.g., 1.5.1
    clause_number: Mapped[str] = mapped_column(String(50), default="", nullable=False)  # backward compat
    section: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)  # backward compat

    # Supported: NUMERIC, BOOLEAN, ENUMERATION, TEXT_REVIEW, RANGE, GEOMETRY, DOCUMENT, HUMAN_REVIEW, NOT_APPLICABLE
    requirement_type: Mapped[str] = mapped_column(String(100), default="NUMERIC", nullable=False)

    # Resolution target in Product DNA
    parameter_key: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    expected_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # backward compat

    # Supported operators: >, >=, <, <=, ==, RANGE, ENUMERATION, BOOLEAN, TEXT_REVIEW, NOT_APPLICABLE
    comparison_operator: Mapped[str] = mapped_column(String(50), default=">=", nullable=False)
    threshold_min: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    threshold_max: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    limit_min: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # backward compat
    limit_max: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # backward compat
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allowed_values: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)

    # Deterministic Applicability Expression
    applicability_condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Verification criteria
    evidence_requirement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_method: Mapped[Optional[str]] = mapped_column(String(100), default="TYPE_TEST", nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    test_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pass_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Execution State: PENDING, PASS, FAIL, NOT_APPLICABLE
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    standard: Mapped["JobStandard"] = relationship("JobStandard", back_populates="requirements")
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob", back_populates="requirements")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.clause_reference and self.clause_number:
            self.clause_reference = self.clause_number
        if not self.clause_number and self.clause_reference:
            self.clause_number = self.clause_reference
        if not self.requirement_id:
            self.requirement_id = f"REQ-{self.clause_reference or self.id[:8]}"
        if not self.requirement_text and self.description:
            self.requirement_text = self.description
        if not self.description and self.requirement_text:
            self.description = self.requirement_text
        if not self.expected_unit and self.unit:
            self.expected_unit = self.unit
        if not self.unit and self.expected_unit:
            self.unit = self.expected_unit
        if not self.threshold_min and self.limit_min:
            self.threshold_min = self.limit_min
        if not self.limit_min and self.threshold_min:
            self.limit_min = self.threshold_min
        if not self.threshold_max and self.limit_max:
            self.threshold_max = self.limit_max
        if not self.limit_max and self.threshold_max:
            self.limit_max = self.threshold_max
