import uuid
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.persistent_cad import (
    CADModel,
    CADComponent,
    CADGeometryFeature,
    CADMeasurement,
    CADSnapshot,
    CADProcessingStatus,
)
from backend.app.models.persistent_evidence import PersistentEvidence
from backend.app.models.persistent_dna import PersistentDNA
from backend.app.models.persistent_audit import AuditEvent
from backend.app.services.cad.cad_registry import validate_cad_format
from backend.app.services.cad.cad_errors import (
    CADError,
    UnsupportedCADFormatError,
    CADProcessingLimitExceeded,
    CADGeometryParsingError,
    CADEvidenceGatingError,
)
from backend.app.services.cad.step_parser import StepParser
from backend.app.services.cad.geometry_extractor import GeometryExtractor
from backend.app.services.cad.measurement_engine import MeasurementEngine
from backend.app.services.cad.cad_snapshot import build_cad_snapshot_dict
from backend.app.services.storage.service import storage_service
from backend.app.core.logging import logger

MAX_CAD_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_COMPONENT_COUNT = 1000
MAX_GEOMETRY_FEATURES = 100000
MAX_PROCESSING_TIME = 60.0  # seconds


class CADService:
    """
    Authoritative CAD intelligence orchestration service.
    Directs STEP parsing, topological inspection, measurement derivation,
    PostgreSQL persistence, and accepted-evidence gated Product DNA integration.
    """

    def __init__(self):
        self.parser = StepParser(max_features=MAX_GEOMETRY_FEATURES)
        self.extractor = GeometryExtractor()
        self.measurement_engine = MeasurementEngine()

    async def ingest_cad_model(
        self,
        organization_id: str,
        job_id: str,
        evidence: PersistentEvidence,
        db: AsyncSession,
        actor_id: str = "system",
    ) -> CADModel:
        """
        Create CADModel record from an ingested CAD evidence file.
        Validates format against capability registry and checks file size limits.
        """
        # Validate format
        fmt = validate_cad_format(evidence.file_name)

        # Validate resource size limits
        if evidence.file_size_bytes and evidence.file_size_bytes > MAX_CAD_FILE_SIZE:
            raise CADProcessingLimitExceeded("MAX_CAD_FILE_SIZE", evidence.file_size_bytes, MAX_CAD_FILE_SIZE)

        cad_model = CADModel(
            id=f"cad_{uuid.uuid4().hex[:16]}",
            organization_id=organization_id,
            job_id=job_id,
            evidence_id=evidence.id,
            format=fmt,
            kernel_name="ISO-10303-21-StepUtils",
            kernel_version="1.0.0",
            model_hash=evidence.sha256_hash,
            processing_status=CADProcessingStatus.QUEUED,
            metadata_json={
                "file_name": evidence.file_name,
                "file_size_bytes": evidence.file_size_bytes,
                "storage_path": evidence.storage_path,
            },
        )
        db.add(cad_model)
        await db.flush()

        audit = AuditEvent(
            organization_id=organization_id,
            job_id=job_id,
            action="CAD_PROCESSING_STARTED",
            target_type="CAD_MODEL",
            target_id=cad_model.id,
            actor_id=actor_id,
            details={
                "cad_model_id": cad_model.id,
                "evidence_id": evidence.id,
                "sha256": evidence.sha256_hash,
                "format": fmt,
            },
        )
        db.add(audit)
        await db.flush()

        return cad_model

    async def process_cad_model(
        self,
        cad_model_id: str,
        db: AsyncSession,
        actor_id: str = "system",
    ) -> CADModel:
        """
        Execute full CAD geometry extraction and measurement pipeline under timeout protection.
        """
        res = await db.execute(select(CADModel).where(CADModel.id == cad_model_id))
        cad_model = res.scalars().first()
        if not cad_model:
            raise CADError(f"CAD model '{cad_model_id}' not found")

        # Load evidence record to get storage path
        ev_res = await db.execute(select(PersistentEvidence).where(PersistentEvidence.id == cad_model.evidence_id))
        evidence = ev_res.scalars().first()
        if not evidence:
            raise CADError(f"Backing evidence '{cad_model.evidence_id}' not found")

        cad_model.processing_status = CADProcessingStatus.PROCESSING
        await db.flush()

        try:
            storage_path = storage_service.resolve_storage_path(evidence.storage_path)
        except Exception:
            storage_path = Path(evidence.storage_path)

        if not storage_path.exists():
            cad_model.processing_status = CADProcessingStatus.FAILED
            cad_model.error_code = "FILE_NOT_FOUND"
            cad_model.error_message = f"CAD file missing from storage path '{evidence.storage_path}'"
            await db.flush()
            raise CADError(cad_model.error_message, error_code="FILE_NOT_FOUND")

        try:
            # Execute parsing and extraction under timeout guard
            parsed, geo, measurements = await asyncio.wait_for(
                asyncio.to_thread(self._parse_and_extract_sync, str(storage_path)),
                timeout=MAX_PROCESSING_TIME,
            )

            # Check component count limit
            if len(geo.components) > MAX_COMPONENT_COUNT:
                raise CADProcessingLimitExceeded("MAX_COMPONENT_COUNT", len(geo.components), MAX_COMPONENT_COUNT)

            # 1. Update CADModel statistics & bounding box
            cad_model.solid_count = geo.solid_count
            cad_model.shell_count = geo.shell_count
            cad_model.face_count = geo.face_count
            cad_model.edge_count = geo.edge_count
            cad_model.vertex_count = geo.vertex_count

            cad_model.bbox_min_x = geo.bbox_min[0]
            cad_model.bbox_min_y = geo.bbox_min[1]
            cad_model.bbox_min_z = geo.bbox_min[2]
            cad_model.bbox_max_x = geo.bbox_max[0]
            cad_model.bbox_max_y = geo.bbox_max[1]
            cad_model.bbox_max_z = geo.bbox_max[2]
            cad_model.dim_x = geo.dim_x
            cad_model.dim_y = geo.dim_y
            cad_model.dim_z = geo.dim_z

            cad_model.volume = geo.volume_mm3
            cad_model.surface_area = geo.surface_area_mm2

            cad_model.processing_status = CADProcessingStatus.MEASUREMENTS_AVAILABLE
            cad_model.processed_at = datetime.now(timezone.utc)
            cad_model.metadata_json = {
                **cad_model.metadata_json,
                "visual_mesh": geo.visual_mesh,
                "schema": parsed.schema,
                "author": parsed.author,
                "organization": parsed.organization,
            }

            # 2. Persist CADComponents
            component_records: Dict[str, CADComponent] = {}
            for comp_dict in geo.components:
                comp = CADComponent(
                    cad_model_id=cad_model.id,
                    name=comp_dict.get("name", "Component"),
                    part_number=comp_dict.get("part_number"),
                    instance_count=comp_dict.get("instance_count", 1),
                    bounding_box_json=comp_dict.get("bounding_box"),
                    metadata_json=comp_dict,
                )
                db.add(comp)
                await db.flush()
                component_records[comp_dict.get("source_reference", comp.id)] = comp

            # 3. Persist CADGeometryFeatures
            feature_records: Dict[str, CADGeometryFeature] = {}
            for feat_dict in geo.features:
                feat = CADGeometryFeature(
                    cad_model_id=cad_model.id,
                    feature_type=feat_dict.get("feature_type", "FEATURE"),
                    feature_reference=feat_dict.get("feature_reference", "#FEAT"),
                    metadata_json=feat_dict.get("metadata", {}),
                )
                db.add(feat)
                await db.flush()
                feature_records[feat.feature_reference] = feat

            # 4. Persist CADMeasurements
            measurement_dicts: List[Dict[str, Any]] = []
            for m in measurements:
                feat_rec = feature_records.get(m.feature_reference) if m.feature_reference else None
                meas = CADMeasurement(
                    cad_model_id=cad_model.id,
                    feature_id=feat_rec.id if feat_rec else None,
                    measurement_type=m.measurement_type,
                    value=m.value,
                    unit=m.unit,
                    axis=m.axis,
                    source_reference=m.source_reference,
                    confidence=m.confidence,
                    is_verified=m.is_verified,
                    metadata_json=m.metadata,
                )
                db.add(meas)
                measurement_dicts.append(m.to_dict())

            # 5. Create immutable CADSnapshot
            snap_dict = build_cad_snapshot_dict(
                cad_model=cad_model,
                geometry_stats={
                    "solid_count": geo.solid_count,
                    "shell_count": geo.shell_count,
                    "face_count": geo.face_count,
                    "edge_count": geo.edge_count,
                    "vertex_count": geo.vertex_count,
                },
                component_tree=[c.get("name") for c in geo.components],
                measurements=measurement_dicts,
                units={"length": parsed.length_unit, "angle": parsed.angle_unit},
            )

            snapshot = CADSnapshot(
                cad_model_id=cad_model.id,
                source_evidence_id=evidence.id,
                source_sha256=evidence.sha256_hash,
                kernel_name=cad_model.kernel_name,
                kernel_version=cad_model.kernel_version,
                geometry_statistics=snap_dict["geometry_statistics"],
                component_tree=geo.components,
                measurements=measurement_dicts,
                units=snap_dict["units"],
            )
            db.add(snapshot)

            # Audit events
            db.add(
                AuditEvent(
                    organization_id=cad_model.organization_id,
                    job_id=cad_model.job_id,
                    action="CAD_PROCESSING_COMPLETED",
                    target_type="CAD_MODEL",
                    target_id=cad_model.id,
                    actor_id=actor_id,
                    details={
                        "cad_model_id": cad_model.id,
                        "status": cad_model.processing_status,
                        "measurements_count": len(measurements),
                    },
                )
            )
            db.add(
                AuditEvent(
                    organization_id=cad_model.organization_id,
                    job_id=cad_model.job_id,
                    action="CAD_SNAPSHOT_CREATED",
                    target_type="CAD_SNAPSHOT",
                    target_id=snapshot.id,
                    actor_id=actor_id,
                    details={
                        "cad_model_id": cad_model.id,
                        "snapshot_id": snapshot.id,
                        "sha256": evidence.sha256_hash,
                    },
                )
            )

            await db.flush()
            return cad_model

        except asyncio.TimeoutError:
            cad_model.processing_status = CADProcessingStatus.FAILED
            cad_model.error_code = "CAD_PROCESSING_LIMIT_EXCEEDED"
            cad_model.error_message = f"CAD processing exceeded timeout limit of {MAX_PROCESSING_TIME} seconds."
            db.add(
                AuditEvent(
                    organization_id=cad_model.organization_id,
                    job_id=cad_model.job_id,
                    action="CAD_PROCESSING_FAILED",
                    target_type="CAD_MODEL",
                    target_id=cad_model.id,
                    actor_id=actor_id,
                    details={"cad_model_id": cad_model.id, "error": cad_model.error_message},
                )
            )
            await db.flush()
            raise CADProcessingLimitExceeded("MAX_PROCESSING_TIME", f">{MAX_PROCESSING_TIME}s", f"{MAX_PROCESSING_TIME}s")

        except Exception as exc:
            cad_model.processing_status = CADProcessingStatus.FAILED
            cad_model.error_code = getattr(exc, "error_code", "CAD_PROCESSING_ERROR")
            cad_model.error_message = str(exc)
            db.add(
                AuditEvent(
                    organization_id=cad_model.organization_id,
                    job_id=cad_model.job_id,
                    action="CAD_PROCESSING_FAILED",
                    target_type="CAD_MODEL",
                    target_id=cad_model.id,
                    actor_id=actor_id,
                    details={"cad_model_id": cad_model.id, "error": str(exc)},
                )
            )
            await db.flush()
            raise

    def _parse_and_extract_sync(self, file_path: str):
        """Synchronous helper invoked via thread pool."""
        parsed = self.parser.parse_file(file_path)
        geo = self.extractor.extract(parsed)
        measurements = self.measurement_engine.compute_measurements(geo)
        return parsed, geo, measurements

    async def map_cad_measurements_to_dna(
        self,
        job_id: str,
        cad_model_id: str,
        organization_id: str,
        db: AsyncSession,
        actor_id: str = "system",
    ) -> List[PersistentDNA]:
        """
        Map authoritative CAD measurements to Product DNA.
        STRICT REGULATORY GATE: Backing evidence MUST have acceptance_status == 'ACCEPTED'.
        """
        res = await db.execute(
            select(CADModel).where(
                CADModel.id == cad_model_id,
                CADModel.job_id == job_id,
                CADModel.organization_id == organization_id,
            )
        )
        cad_model = res.scalars().first()
        if not cad_model:
            raise CADError(f"CAD model '{cad_model_id}' not found in job.")

        # Check evidence gating
        ev_res = await db.execute(select(PersistentEvidence).where(PersistentEvidence.id == cad_model.evidence_id))
        evidence = ev_res.scalars().first()
        if not evidence or evidence.acceptance_status != "ACCEPTED":
            status = evidence.acceptance_status if evidence else "UNKNOWN"
            raise CADEvidenceGatingError(cad_model.evidence_id, status)

        # Load snapshot
        snap_res = await db.execute(
            select(CADSnapshot).where(CADSnapshot.cad_model_id == cad_model.id).order_by(desc(CADSnapshot.created_at))
        )
        snapshot = snap_res.scalars().first()
        snapshot_id = snapshot.id if snapshot else None

        # Load measurements
        meas_res = await db.execute(select(CADMeasurement).where(CADMeasurement.cad_model_id == cad_model.id))
        measurements = meas_res.scalars().all()

        dna_records: List[PersistentDNA] = []

        # Mapping rules from measurement_type to Product DNA parameter key
        type_to_param = {
            "BOUNDING_BOX_X": ("enclosure_length", "Mechanical Characteristics"),
            "BOUNDING_BOX_Y": ("enclosure_width", "Mechanical Characteristics"),
            "BOUNDING_BOX_Z": ("enclosure_height", "Mechanical Characteristics"),
            "WALL_THICKNESS": ("wall_thickness", "Safety Characteristics"),
            "HOLE_DIAMETER": ("hole_diameter", "Mechanical Characteristics"),
            "CLEARANCE": ("clearance", "Safety Characteristics"),
            "VOLUME": ("enclosure_volume", "Mechanical Characteristics"),
            "SURFACE_AREA": ("surface_area", "Mechanical Characteristics"),
        }

        for m in measurements:
            if m.measurement_type in type_to_param:
                param_key, category = type_to_param[m.measurement_type]

                # Check if already present in Product DNA
                existing = await db.execute(
                    select(PersistentDNA).where(
                        PersistentDNA.job_id == job_id,
                        PersistentDNA.organization_id == organization_id,
                        PersistentDNA.parameter == param_key,
                    )
                )
                dna = existing.scalars().first()

                meta = {
                    "source_chain": "Product DNA -> CAD Measurement -> Geometry Feature -> CAD Snapshot -> Evidence -> SHA-256",
                    "source_evidence_id": evidence.id,
                    "evidence_sha256": evidence.sha256_hash,
                    "cad_model_id": cad_model.id,
                    "cad_measurement_id": m.id,
                    "source_geometry_reference": m.source_reference,
                    "kernel_name": cad_model.kernel_name,
                    "kernel_version": cad_model.kernel_version,
                    "snapshot_id": snapshot_id,
                    "verification_timestamp": datetime.now(timezone.utc).isoformat(),
                }

                if dna:
                    dna.value = str(m.value)
                    dna.unit = m.unit
                    dna.source_evidence_id = evidence.id
                    dna.confidence = m.confidence
                    dna.status = "VERIFIED"
                    dna.metadata_json = meta
                else:
                    dna = PersistentDNA(
                        organization_id=organization_id,
                        job_id=job_id,
                        parameter=param_key,
                        value=str(m.value),
                        unit=m.unit,
                        category=category,
                        source_evidence_id=evidence.id,
                        confidence=m.confidence,
                        status="VERIFIED",
                        metadata_json=meta,
                    )
                    db.add(dna)

                dna_records.append(dna)

                db.add(
                    AuditEvent(
                        organization_id=organization_id,
                        job_id=job_id,
                        action="CAD_DNA_PARAMETER_CREATED",
                        target_type="PRODUCT_DNA",
                        target_id=dna.id,
                        actor_id=actor_id,
                        details={
                            "parameter": param_key,
                            "value": m.value,
                            "unit": m.unit,
                            "cad_model_id": cad_model.id,
                            "cad_measurement_id": m.id,
                            "evidence_id": evidence.id,
                        },
                    )
                )

        await db.flush()
        return dna_records


cad_service = CADService()
