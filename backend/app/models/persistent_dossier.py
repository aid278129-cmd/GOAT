"""Authoritative persistent models for Regulatory Dossiers and Compliance Passports (Phase 5)."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    JSON,
    DateTime,
    Integer,
    Boolean,
    BigInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.compliance_job import ComplianceJob
    from backend.app.models.organization import Organization
    from backend.app.models.user import User
    from backend.app.models.persistent_assessment import AssessmentRun


class RegulatoryDossier(Base):
    """
    Authoritative, immutable snapshot of a compiled regulatory filing dossier.
    Represents an exact point-in-time state of standards, requirements, evidence,
    Product DNA, assessments, findings, human reviews, and human attestations.
    """

    __tablename__ = "regulatory_dossiers"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"dos_{uuid.uuid4().hex[:16]}"
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_run_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("assessment_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Immutable sequential version (1, 2, 3...) for the compliance job
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Status: GENERATING | GENERATED | FAILED
    status: Mapped[str] = mapped_column(String(32), default="GENERATED", nullable=False, index=True)

    # Cryptographic integrity digests (SHA-256)
    dossier_digest: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_dna_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_manifest_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    finding_digest: Mapped[str] = mapped_column(String(64), nullable=False)

    # Standard revisions & attestation UUID list
    standard_revisions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    attestation_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Metadata & system versions
    application_version: Mapped[str] = mapped_column(String(32), default="v5.0-production", nullable=False)
    assessment_engine_version: Mapped[str] = mapped_column(String(50), default="v2.0-deterministic", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    generated_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_by_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    job: Mapped["ComplianceJob"] = relationship("ComplianceJob")
    organization: Mapped["Organization"] = relationship("Organization")
    assessment_run: Mapped["AssessmentRun"] = relationship("AssessmentRun")

    sections: Mapped[List["DossierSection"]] = relationship(
        "DossierSection", back_populates="dossier", cascade="all, delete-orphan", order_by="DossierSection.section_number"
    )
    evidence_references: Mapped[List["DossierEvidenceReference"]] = relationship(
        "DossierEvidenceReference", back_populates="dossier", cascade="all, delete-orphan"
    )
    requirement_references: Mapped[List["DossierRequirementReference"]] = relationship(
        "DossierRequirementReference", back_populates="dossier", cascade="all, delete-orphan"
    )
    assessment_references: Mapped[List["DossierAssessmentReference"]] = relationship(
        "DossierAssessmentReference", back_populates="dossier", cascade="all, delete-orphan"
    )
    finding_references: Mapped[List["DossierFindingReference"]] = relationship(
        "DossierFindingReference", back_populates="dossier", cascade="all, delete-orphan"
    )
    attestation_references: Mapped[List["DossierAttestationReference"]] = relationship(
        "DossierAttestationReference", back_populates="dossier", cascade="all, delete-orphan"
    )
    generations: Mapped[List["DossierGeneration"]] = relationship(
        "DossierGeneration", back_populates="dossier", cascade="all, delete-orphan"
    )
    artifacts: Mapped[List["DossierArtifact"]] = relationship(
        "DossierArtifact", back_populates="dossier", cascade="all, delete-orphan"
    )


class DossierSection(Base):
    """Structured content section (1 to 20) belonging to a Regulatory Dossier."""

    __tablename__ = "dossier_sections"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"sec_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    section_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="sections")


class DossierEvidenceReference(Base):
    """Immutable evidence entry referenced within a dossier."""

    __tablename__ = "dossier_evidence_references"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"dev_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    acceptance_status: Mapped[str] = mapped_column(String(50), nullable=False)
    extracted_parameters_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="evidence_references")


class DossierRequirementReference(Base):
    """Requirement/clause covered within a dossier."""

    __tablename__ = "dossier_requirement_references"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"drq_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    clause_number: Mapped[str] = mapped_column(String(50), nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    parameter_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    applicability_state: Mapped[str] = mapped_column(String(50), default="APPLICABLE", nullable=False)

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="requirement_references")


class DossierAssessmentReference(Base):
    """Deterministic assessment result referenced within a dossier."""

    __tablename__ = "dossier_assessment_references"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"das_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    assessment_result_id: Mapped[str] = mapped_column(String(64), nullable=False)
    clause_number: Mapped[str] = mapped_column(String(50), nullable=False)
    assessment_state: Mapped[str] = mapped_column(String(50), nullable=False)
    observed_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comparison_operator: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="assessment_references")


class DossierFindingReference(Base):
    """Finding/gap snapshot referenced within a dossier."""

    __tablename__ = "dossier_finding_references"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"dfn_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finding_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    requirement_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    waiver_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="finding_references")


class DossierAttestationReference(Base):
    """Human attestation reference included in a dossier."""

    __tablename__ = "dossier_attestation_references"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"dat_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attestation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    attestor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    attestor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    attestation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    attested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="attestation_references")


class DossierGeneration(Base):
    """Execution lifecycle record of generating a dossier."""

    __tablename__ = "dossier_generations"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"dgen_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="STARTED", nullable=False)
    generation_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="generations")


class DossierArtifact(Base):
    """Tangible output artifact (e.g. PDF, JSON manifest) produced by dossier generation."""

    __tablename__ = "dossier_artifacts"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"dart_{uuid.uuid4().hex[:16]}"
    )
    dossier_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("regulatory_dossiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)  # PDF | JSON_MANIFEST
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    dossier: Mapped["RegulatoryDossier"] = relationship("RegulatoryDossier", back_populates="artifacts")
