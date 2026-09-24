import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    Float,
    Boolean,
    Index,
)
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import relationship
from backend.app.models.base import Base


class CADProcessingStatus:
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    PARSED = "PARSED"
    GEOMETRY_EXTRACTED = "GEOMETRY_EXTRACTED"
    MEASUREMENTS_AVAILABLE = "MEASUREMENTS_AVAILABLE"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    FAILED = "FAILED"


class CADModel(Base):
    """
    Authoritative CAD model artifact record stored in PostgreSQL.
    Tracks parsing lifecycle, geometry extraction, and dimensional measurements.
    """
    __tablename__ = "cad_models"

    id = Column(String(64), primary_key=True, default=lambda: f"cad_{uuid.uuid4().hex[:16]}")
    organization_id = Column(String(64), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(64), ForeignKey("compliance_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id = Column(String(64), ForeignKey("persistent_evidence.id", ondelete="CASCADE"), nullable=False, index=True)

    format = Column(String(32), nullable=False, default="STEP")  # STEP
    kernel_name = Column(String(64), nullable=False, default="ISO-10303-21-StepUtils")
    kernel_version = Column(String(32), nullable=False, default="1.0.0")
    model_hash = Column(String(64), nullable=False)  # Server-calculated SHA-256 of CAD artifact

    processing_status = Column(String(32), nullable=False, default=CADProcessingStatus.UPLOADED, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)

    # Geometry statistics & summary
    solid_count = Column(Integer, default=0)
    shell_count = Column(Integer, default=0)
    face_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    vertex_count = Column(Integer, default=0)

    # Overall bounding box dimensions (normalized in mm)
    bbox_min_x = Column(Float, nullable=True)
    bbox_min_y = Column(Float, nullable=True)
    bbox_min_z = Column(Float, nullable=True)
    bbox_max_x = Column(Float, nullable=True)
    bbox_max_y = Column(Float, nullable=True)
    bbox_max_z = Column(Float, nullable=True)
    dim_x = Column(Float, nullable=True)
    dim_y = Column(Float, nullable=True)
    dim_z = Column(Float, nullable=True)

    # Calculated physical quantities
    volume = Column(Float, nullable=True)  # in mm3
    surface_area = Column(Float, nullable=True)  # in mm2

    metadata_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    components = relationship("CADComponent", back_populates="cad_model", cascade="all, delete-orphan")
    features = relationship("CADGeometryFeature", back_populates="cad_model", cascade="all, delete-orphan")
    measurements = relationship("CADMeasurement", back_populates="cad_model", cascade="all, delete-orphan")
    snapshots = relationship("CADSnapshot", back_populates="cad_model", cascade="all, delete-orphan")


class CADComponent(Base):
    """
    Hierarchical component in a CAD assembly.
    """
    __tablename__ = "cad_components"

    id = Column(String(64), primary_key=True, default=lambda: f"comp_{uuid.uuid4().hex[:12]}")
    cad_model_id = Column(String(64), ForeignKey("cad_models.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_component_id = Column(String(64), ForeignKey("cad_components.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    part_number = Column(String(128), nullable=True)
    instance_count = Column(Integer, default=1, nullable=False)
    bounding_box_json = Column(JSONB, nullable=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)

    cad_model = relationship("CADModel", back_populates="components")
    features = relationship("CADGeometryFeature", back_populates="component")


class CADGeometryFeature(Base):
    """
    Topological geometry feature identified during CAD parsing.
    E.g. CYLINDER, HOLE, PLANE, WALL, FACE, SOLID, SHELL, VERTEX, EDGE.
    """
    __tablename__ = "cad_geometry_features"

    id = Column(String(64), primary_key=True, default=lambda: f"feat_{uuid.uuid4().hex[:12]}")
    cad_model_id = Column(String(64), ForeignKey("cad_models.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id = Column(String(64), ForeignKey("cad_components.id", ondelete="SET NULL"), nullable=True, index=True)

    feature_type = Column(String(64), nullable=False, index=True)  # CYLINDER, HOLE, PLANE, WALL, FACE, SOLID, SHELL
    feature_reference = Column(String(128), nullable=False)  # e.g. '#50', '#80'
    metadata_json = Column(JSONB, nullable=False, default=dict)

    cad_model = relationship("CADModel", back_populates="features")
    component = relationship("CADComponent", back_populates="features")
    measurements = relationship("CADMeasurement", back_populates="feature")


class CADMeasurement(Base):
    """
    Deterministic measurement established from CAD geometry entities.
    """
    __tablename__ = "cad_measurements"

    id = Column(String(64), primary_key=True, default=lambda: f"meas_{uuid.uuid4().hex[:12]}")
    cad_model_id = Column(String(64), ForeignKey("cad_models.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_id = Column(String(64), ForeignKey("cad_geometry_features.id", ondelete="SET NULL"), nullable=True, index=True)

    measurement_type = Column(String(64), nullable=False, index=True)  # BOUNDING_BOX_X, WALL_THICKNESS, HOLE_DIAMETER, CLEARANCE, etc.
    value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False, default="mm")
    axis = Column(String(8), nullable=True)  # X, Y, Z
    tolerance = Column(Float, nullable=True)
    source_reference = Column(String(255), nullable=False)  # STEP entity references e.g. '#50' or '#10,#20'
    confidence = Column(Float, default=1.0, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    metadata_json = Column(JSONB, nullable=False, default=dict)

    cad_model = relationship("CADModel", back_populates="measurements")
    feature = relationship("CADGeometryFeature", back_populates="measurements")


class CADSnapshot(Base):
    """
    Immutable, reproducible snapshot of processed CAD geometry, statistics, and measurements.
    """
    __tablename__ = "cad_snapshots"

    id = Column(String(64), primary_key=True, default=lambda: f"cadsnap_{uuid.uuid4().hex[:12]}")
    cad_model_id = Column(String(64), ForeignKey("cad_models.id", ondelete="CASCADE"), nullable=False, index=True)
    source_evidence_id = Column(String(64), ForeignKey("persistent_evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    source_sha256 = Column(String(64), nullable=False)

    kernel_name = Column(String(64), nullable=False)
    kernel_version = Column(String(32), nullable=False)

    geometry_statistics = Column(JSONB, nullable=False, default=dict)
    component_tree = Column(JSONB, nullable=False, default=list)
    measurements = Column(JSONB, nullable=False, default=list)
    units = Column(JSONB, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    cad_model = relationship("CADModel", back_populates="snapshots")
