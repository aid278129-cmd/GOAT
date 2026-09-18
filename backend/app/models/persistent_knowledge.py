"""Zyntrix Phase 6: Authoritative BIS Knowledge Repository Models.

Implements the authoritative knowledge layer for SIH Problem Statement ID: 26107:
"AI-powered Intelligent Assistant for Indian Standards and BIS Services for Industries and Consumers"

Models:
 1. BISKnowledgeSource - Classified authoritative source provenance.
 2. BISDocument - Parent statutory document container.
 3. BISDocumentVersion - Immutable document versions with SHA-256 and publishing lifecycle.
 4. BISStandard - Indian Standards catalog (IS number, title, scope, CRO status).
 5. BISStandardRevision - Versioned standard revisions with effective dates.
 6. BISClause - Codified clauses with parameter keys, expected units, and limits.
 7. BISScheme - Official BIS certification schemes (ISI Mark, CRS, Scheme IV).
 8. BISService - Structured BIS services (Certification, Testing, Hallmarking, Consumer).
 9. BISTestingRequirement - Explicit laboratory testing requirements and apparatus.
10. BISLaboratory - Recognized testing laboratories with location and accreditations.
11. BISHallmarkingReference - Gold/silver grades, HUID guidelines, and consumer verification.
12. BISRelatedStandard - Normative references and IEC/ISO cross-walks.
13. KnowledgeChunk - Segmented knowledge units for lexical and semantic indexing.
14. KnowledgeEmbedding - Dense vector representations for semantic retrieval.
15. KnowledgeIngestionRun - Traceable ingestion runs with duration and chunk counts.
16. KnowledgeCitation - Validated provenance citations linking assistant answers to source clauses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Text, Integer, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class BISKnowledgeSource(Base):
    """Authoritative or approved regulatory knowledge source."""

    __tablename__ = "bis_knowledge_sources"

    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), default="AUTHORITATIVE_BIS", nullable=False, index=True
    )  # AUTHORITATIVE_BIS | AUTHORIZED_SOURCE | SECONDARY_REFERENCE | UNVERIFIED_EXTERNAL
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    publisher: Mapped[str] = mapped_column(String(255), default="Bureau of Indian Standards", nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    publication_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    documents: Mapped[List["BISDocument"]] = relationship("BISDocument", back_populates="source", cascade="all, delete-orphan")


class BISDocument(Base):
    """Parent document container for standards, guidelines, manuals, or lab directories."""

    __tablename__ = "bis_documents"

    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_knowledge_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_title: Mapped[str] = mapped_column(String(512), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(50), default="STANDARD", nullable=False, index=True
    )  # STANDARD | SCHEME_GUIDELINE | LABORATORY_DIRECTORY | HALLMARKING_GUIDE | CONSUMER_MANUAL
    document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="ELECTRICAL_ELECTRONICS", nullable=False, index=True)

    # Relationships
    source: Mapped["BISKnowledgeSource"] = relationship("BISKnowledgeSource", back_populates="documents")
    versions: Mapped[List["BISDocumentVersion"]] = relationship(
        "BISDocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="desc(BISDocumentVersion.created_at)"
    )


class BISDocumentVersion(Base):
    """Immutable version of a BIS document with SHA-256 integrity and publishing lifecycle."""

    __tablename__ = "bis_document_versions"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_identifier: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 2015, v1.2, 2021-A1
    status: Mapped[str] = mapped_column(
        String(50), default="PUBLISHED", nullable=False, index=True
    )  # DISCOVERED | INGESTING | PARSED | INDEXED | VALIDATION_REQUIRED | PUBLISHED | SUPERSEDED | FAILED
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    parsed_metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    publication_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    document: Mapped["BISDocument"] = relationship("BISDocument", back_populates="versions")
    standards: Mapped[List["BISStandard"]] = relationship("BISStandard", back_populates="document_version")
    chunks: Mapped[List["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="document_version", cascade="all, delete-orphan")


class BISStandard(Base):
    """Indian Standard specification container."""

    __tablename__ = "bis_standards"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bis_document_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    standard_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., IS 16221 (Part 2)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    scope_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_category: Mapped[str] = mapped_column(String(100), default="SOLAR_INVERTERS", nullable=False, index=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cro_order_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., MeitY CRO Phase IV
    equivalent_international_standard: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # IEC 62109-2
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)

    # Relationships
    document_version: Mapped[Optional["BISDocumentVersion"]] = relationship("BISDocumentVersion", back_populates="standards")
    revisions: Mapped[List["BISStandardRevision"]] = relationship(
        "BISStandardRevision", back_populates="standard", cascade="all, delete-orphan", order_by="desc(BISStandardRevision.revision_year)"
    )


class BISStandardRevision(Base):
    """Specific published revision of an Indian Standard."""

    __tablename__ = "bis_standard_revisions"

    standard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_standards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bis_document_versions.id", ondelete="SET NULL"), nullable=True
    )
    revision_year: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. 2015
    amendment_number: Mapped[Optional[str]] = mapped_column(String(50), default="", nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="PUBLISHED", nullable=False, index=True
    )  # PUBLISHED | SUPERSEDED | WITHDRAWN
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reaffirmation_year: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    standard: Mapped["BISStandard"] = relationship("BISStandard", back_populates="revisions")
    clauses: Mapped[List["BISClause"]] = relationship(
        "BISClause", back_populates="standard_revision", cascade="all, delete-orphan", order_by="BISClause.clause_number"
    )
    testing_requirements: Mapped[List["BISTestingRequirement"]] = relationship(
        "BISTestingRequirement", back_populates="standard_revision", cascade="all, delete-orphan"
    )


class BISClause(Base):
    """Codified technical or procedural clause in an Indian Standard."""

    __tablename__ = "bis_clauses"

    standard_revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_standard_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., 5.3, 4.2.1
    clause_title: Mapped[str] = mapped_column(String(255), nullable=False)
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_name: Mapped[str] = mapped_column(String(255), default="General Requirements", nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    requirement_type: Mapped[str] = mapped_column(String(50), default="QUANTITATIVE", nullable=False)
    parameter_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    expected_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    comparison_operator: Mapped[Optional[str]] = mapped_column(String(20), default=">=", nullable=True)
    threshold_min: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    threshold_max: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    standard_revision: Mapped["BISStandardRevision"] = relationship("BISStandardRevision", back_populates="clauses")
    chunks: Mapped[List["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="clause")


class BISScheme(Base):
    """Official BIS Conformity Assessment Scheme."""

    __tablename__ = "bis_schemes"

    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bis_knowledge_sources.id", ondelete="SET NULL"), nullable=True
    )
    scheme_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # SCHEME_I | SCHEME_II_CRS | SCHEME_IV
    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    governing_regulation: Mapped[str] = mapped_column(String(255), default="BIS (Conformity Assessment) Regulations, 2018", nullable=False)
    description: Mapped[Text] = mapped_column(Text, nullable=False)
    applicable_products_summary: Mapped[Text] = mapped_column(Text, nullable=False)
    process_overview: Mapped[Text] = mapped_column(Text, nullable=False)
    official_guideline_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)


class BISService(Base):
    """Authoritative BIS service guide for industries, startups, and consumers."""

    __tablename__ = "bis_services"

    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_type: Mapped[str] = mapped_column(
        String(50), default="PRODUCT_CERTIFICATION", nullable=False, index=True
    )  # PRODUCT_CERTIFICATION | HALLMARKING | LABORATORY_RECOGNITION | STANDARDS_FORMATION | CONSUMER_AFFAIRS | TRAINING
    description: Mapped[Text] = mapped_column(Text, nullable=False)
    eligibility_criteria: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    step_by_step_procedure: Mapped[Text] = mapped_column(Text, nullable=False)
    required_documents: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    portal_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    statutory_source_ref: Mapped[str] = mapped_column(String(255), default="BIS Official Rules & Regulations", nullable=False)
    last_verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)


class BISTestingRequirement(Base):
    """Codified testing procedure and apparatus requirement."""

    __tablename__ = "bis_testing_requirements"

    standard_revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_standard_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bis_clauses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_method: Mapped[Text] = mapped_column(Text, nullable=False)
    required_apparatus: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    sampling_criteria: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    acceptance_threshold: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    standard_revision: Mapped["BISStandardRevision"] = relationship("BISStandardRevision", back_populates="testing_requirements")


class BISLaboratory(Base):
    """BIS recognized or accredited testing laboratory."""

    __tablename__ = "bis_laboratories"

    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bis_knowledge_sources.id", ondelete="SET NULL"), nullable=True
    )
    lab_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    lab_type: Mapped[str] = mapped_column(
        String(50), default="CENTRAL_LAB", nullable=False
    )  # CENTRAL_LAB | REGIONAL_LAB | BRANCH_LAB | RECOGNIZED_PRIVATE_LAB
    location_city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location_state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[Text] = mapped_column(Text, nullable=False)
    accredited_standards: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)  # list of IS numbers
    testing_capabilities: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    validity_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)


class BISHallmarkingReference(Base):
    """Statutory hallmarking reference data for gold and silver articles."""

    __tablename__ = "bis_hallmarking_references"

    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bis_knowledge_sources.id", ondelete="SET NULL"), nullable=True
    )
    metal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # GOLD | SILVER
    standard_number: Mapped[str] = mapped_column(String(100), nullable=False)  # IS 1417 (Gold) | IS 2112 (Silver)
    purity_grades_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    mandatory_marks_json: Mapped[List[Dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    huid_structure_description: Mapped[Text] = mapped_column(Text, nullable=False)
    consumer_verification_steps: Mapped[Text] = mapped_column(Text, nullable=False)
    statutory_order_ref: Mapped[str] = mapped_column(String(255), default="Hallmarking Order, 2021", nullable=False)
    last_verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class BISRelatedStandard(Base):
    """Traceable cross-walk between related standards."""

    __tablename__ = "bis_related_standards"

    primary_standard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_standards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    related_standard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_standards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), default="NORMATIVE_REFERENCE", nullable=False
    )  # NORMATIVE_REFERENCE | PARENT_SERIES | TESTING_METHOD | SUBSIDIARY | EQUIVALENT_IEC_ISO
    notes: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)


class KnowledgeChunk(Base):
    """Fine-grained textual chunk for lexical and semantic retrieval."""

    __tablename__ = "knowledge_chunks"

    document_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_document_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("bis_clauses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_text: Mapped[Text] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    document_version: Mapped["BISDocumentVersion"] = relationship("BISDocumentVersion", back_populates="chunks")
    clause: Mapped[Optional["BISClause"]] = relationship("BISClause", back_populates="chunks")
    embedding: Mapped[Optional["KnowledgeEmbedding"]] = relationship(
        "KnowledgeEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan"
    )


class KnowledgeEmbedding(Base):
    """Dense vector embedding for semantic search."""

    __tablename__ = "knowledge_embeddings"

    chunk_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-004", nullable=False)
    vector_json: Mapped[List[float]] = mapped_column(JSON, nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, default=768, nullable=False)

    # Relationships
    chunk: Mapped["KnowledgeChunk"] = relationship("KnowledgeChunk", back_populates="embedding")


class KnowledgeIngestionRun(Base):
    """Audit log of knowledge ingestion runs."""

    __tablename__ = "knowledge_ingestion_runs"

    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bis_knowledge_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="STARTED", nullable=False)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clauses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)


class KnowledgeCitation(Base):
    """Authoritative citation provenance linking conversation claims to source clauses."""

    __tablename__ = "knowledge_citations"

    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    message_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    document_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    standard_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    clause_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    citation_label: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., [IS 16221:2015 - Clause 5.3]
    claim_text: Mapped[Text] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="AUTHORITATIVE_BIS", nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
