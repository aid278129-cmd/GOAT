from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.user import User
    from backend.app.models.persistent_evidence import PersistentEvidence
    from backend.app.models.persistent_dna import PersistentDNA
    from backend.app.models.persistent_standards import JobStandard, JobRequirement
    from backend.app.models.persistent_audit import AuditEvent


class ComplianceJob(Base):
    """Authoritative Compliance Job lifecycle entity."""

    __tablename__ = "compliance_jobs"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    stage: Mapped[str] = mapped_column(String(50), default="01_EVIDENCE_INGESTION", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="IN_PROGRESS", nullable=False)
    compliance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="compliance_jobs")
    evidence_items: Mapped[List["PersistentEvidence"]] = relationship(
        "PersistentEvidence", back_populates="job", cascade="all, delete-orphan"
    )
    dna_parameters: Mapped[List["PersistentDNA"]] = relationship(
        "PersistentDNA", back_populates="job", cascade="all, delete-orphan"
    )
    standards: Mapped[List["JobStandard"]] = relationship(
        "JobStandard", back_populates="job", cascade="all, delete-orphan"
    )
    requirements: Mapped[List["JobRequirement"]] = relationship(
        "JobRequirement", back_populates="job", cascade="all, delete-orphan"
    )
    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="job", cascade="all, delete-orphan"
    )
