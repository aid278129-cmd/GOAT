import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.database.session import get_db
from backend.app.models.compliance_job import ComplianceJob
from backend.app.models.persistent_evidence import PersistentEvidence, EvidenceLifecycleEvent
from backend.app.models.persistent_cad import (
    CADModel,
    CADComponent,
    CADGeometryFeature,
    CADMeasurement,
    CADSnapshot,
    CADProcessingStatus,
)
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, get_current_org, require_role
from backend.app.services.storage.service import storage_service
from backend.app.services.cad.cad_service import cad_service
from backend.app.services.cad.cad_registry import validate_cad_format, CAD_CAPABILITY_REGISTRY
from backend.app.services.cad.cad_errors import (
    UnsupportedCADFormatError,
    CADProcessingLimitExceeded,
    CADEvidenceGatingError,
    CADError,
)

router = APIRouter(prefix="/jobs/{job_id}/cad", tags=["Authoritative CAD & Digital Twin Intelligence"])


async def _verify_job_ownership(job_id: str, org_id: str, db: AsyncSession) -> ComplianceJob:
    result = await db.execute(
        select(ComplianceJob).where(
            ComplianceJob.id == job_id,
            ComplianceJob.organization_id == org_id,
        )
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance job '{job_id}' not found in organization.",
        )
    return job


def format_cad_model_dict(model: CADModel) -> Dict[str, Any]:
    return {
        "id": model.id,
        "job_id": model.job_id,
        "organization_id": model.organization_id,
        "evidence_id": model.evidence_id,
        "format": model.format,
        "kernel_name": model.kernel_name,
        "kernel_version": model.kernel_version,
        "model_hash": model.model_hash,
        "processing_status": model.processing_status,
        "processed_at": model.processed_at.isoformat() if model.processed_at else None,
        "error_code": model.error_code,
        "error_message": model.error_message,
        "statistics": {
            "solid_count": model.solid_count,
            "shell_count": model.shell_count,
            "face_count": model.face_count,
            "edge_count": model.edge_count,
            "vertex_count": model.vertex_count,
        },
        "bounding_box": {
            "min": [model.bbox_min_x, model.bbox_min_y, model.bbox_min_z],
            "max": [model.bbox_max_x, model.bbox_max_y, model.bbox_max_z],
            "dimensions": [model.dim_x, model.dim_y, model.dim_z],
        },
        "volume_mm3": model.volume,
        "surface_area_mm2": model.surface_area,
        "metadata": model.metadata_json or {},
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_cad_capabilities():
    """Retrieve the authoritative CAD format capability registry."""
    return {"capabilities": CAD_CAPABILITY_REGISTRY}


@router.get("", response_model=List[Dict[str, Any]])
async def list_cad_models(
    job_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all CAD models for a compliance job."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(CADModel)
        .where(CADModel.job_id == job_id, CADModel.organization_id == org.id)
        .order_by(desc(CADModel.created_at))
    )
    models = result.scalars().all()
    return [format_cad_model_dict(m) for m in models]


@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_cad_model(
    job_id: str,
    file: UploadFile = File(...),
    auto_process: bool = Form(True),
    current_user: User = Depends(require_role(["ENGINEER", "REVIEWER", "ADMIN"])),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a CAD file artifact (.stp, .step) into durable storage,
    verify server-side SHA-256 digest, create CADModel record, and trigger parsing.
    Rejects unsupported formats with UNSUPPORTED_CAD_FORMAT.
    """
    await _verify_job_ownership(job_id, org.id, db)

    # 1. Validate CAD format against registry
    try:
        validate_cad_format(file.filename or "")
    except UnsupportedCADFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": exc.error_code, "message": exc.message, "details": exc.details},
        )

    # 2. Ingest through authoritative storage service
    stored = await storage_service.save_evidence_file(
        file=file,
        organization_id=org.id,
        job_id=job_id,
    )

    # 3. Create PersistentEvidence record
    evidence = PersistentEvidence(
        id=f"evd_{uuid.uuid4().hex[:12]}",
        organization_id=org.id,
        job_id=job_id,
        file_name=stored["file_name"],
        file_type="engineering",
        mime_type=stored["mime_type"],
        file_size_bytes=stored["file_size_bytes"],
        storage_path=stored["storage_path"],
        sha256_hash=stored["sha256_hash"],
        source="CAD Ingestion",
        processing_status="PROCESSING",
        acceptance_status="REQUIRES_REVIEW",  # Initially requires review
    )
    db.add(evidence)
    await db.flush()

    # 4. Ingest CAD Model record
    try:
        cad_model = await cad_service.ingest_cad_model(
            organization_id=org.id,
            job_id=job_id,
            evidence=evidence,
            db=db,
            actor_id=current_user.id,
        )

        # 5. Process synchronously if requested
        if auto_process:
            cad_model = await cad_service.process_cad_model(
                cad_model_id=cad_model.id,
                db=db,
                actor_id=current_user.id,
            )

        return format_cad_model_dict(cad_model)

    except CADProcessingLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error_code": exc.error_code, "message": exc.message, "details": exc.details},
        )
    except CADError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": exc.error_code, "message": exc.message},
        )


@router.post("/{cad_model_id}/process", response_model=Dict[str, Any])
async def process_cad(
    job_id: str,
    cad_model_id: str,
    current_user: User = Depends(require_role(["ENGINEER", "REVIEWER", "ADMIN"])),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Execute / retry processing on an ingested CAD model."""
    await _verify_job_ownership(job_id, org.id, db)
    try:
        cad_model = await cad_service.process_cad_model(
            cad_model_id=cad_model_id,
            db=db,
            actor_id=current_user.id,
        )
        return format_cad_model_dict(cad_model)
    except CADProcessingLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error_code": exc.error_code, "message": exc.message, "details": exc.details},
        )
    except CADError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": exc.error_code, "message": exc.message},
        )


@router.get("/{cad_model_id}", response_model=Dict[str, Any])
async def get_cad_model(
    job_id: str,
    cad_model_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full CAD model details."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(CADModel).where(
            CADModel.id == cad_model_id,
            CADModel.job_id == job_id,
            CADModel.organization_id == org.id,
        )
    )
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CAD model not found.")
    return format_cad_model_dict(model)


@router.get("/{cad_model_id}/status", response_model=Dict[str, Any])
async def get_cad_status(
    job_id: str,
    cad_model_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Quick polling endpoint for CAD processing status."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(CADModel).where(
            CADModel.id == cad_model_id,
            CADModel.job_id == job_id,
            CADModel.organization_id == org.id,
        )
    )
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CAD model not found.")
    return {
        "id": model.id,
        "processing_status": model.processing_status,
        "error_code": model.error_code,
        "error_message": model.error_message,
        "processed_at": model.processed_at.isoformat() if model.processed_at else None,
    }


@router.get("/{cad_model_id}/components", response_model=List[Dict[str, Any]])
async def get_cad_components(
    job_id: str,
    cad_model_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve component hierarchy for a CAD model."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(CADComponent).where(CADComponent.cad_model_id == cad_model_id)
    )
    comps = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "part_number": c.part_number,
            "instance_count": c.instance_count,
            "parent_component_id": c.parent_component_id,
            "bounding_box": c.bounding_box_json,
            "metadata": c.metadata_json,
        }
        for c in comps
    ]


@router.get("/{cad_model_id}/measurements", response_model=List[Dict[str, Any]])
async def get_cad_measurements(
    job_id: str,
    cad_model_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve deterministic measurements established for a CAD model."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(CADMeasurement).where(CADMeasurement.cad_model_id == cad_model_id)
    )
    meas = result.scalars().all()
    return [
        {
            "id": m.id,
            "measurement_type": m.measurement_type,
            "value": m.value,
            "unit": m.unit,
            "axis": m.axis,
            "source_reference": m.source_reference,
            "confidence": m.confidence,
            "is_verified": m.is_verified,
            "metadata": m.metadata_json,
        }
        for m in meas
    ]


@router.get("/{cad_model_id}/snapshot", response_model=Dict[str, Any])
async def get_cad_snapshot(
    job_id: str,
    cad_model_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve immutable CAD snapshot."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(
        select(CADSnapshot)
        .where(CADSnapshot.cad_model_id == cad_model_id)
        .order_by(desc(CADSnapshot.created_at))
    )
    snap = result.scalars().first()
    if not snap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No snapshot found for this CAD model.")
    return {
        "id": snap.id,
        "cad_model_id": snap.cad_model_id,
        "source_evidence_id": snap.source_evidence_id,
        "source_sha256": snap.source_sha256,
        "kernel_name": snap.kernel_name,
        "kernel_version": snap.kernel_version,
        "geometry_statistics": snap.geometry_statistics,
        "component_tree": snap.component_tree,
        "measurements": snap.measurements,
        "units": snap.units,
        "created_at": snap.created_at.isoformat() if snap.created_at else None,
    }


@router.get("/{cad_model_id}/trace/{measurement_id}", response_model=Dict[str, Any])
async def get_cad_trace(
    job_id: str,
    cad_model_id: str,
    measurement_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve authoritative statutory trace for a specific measurement:
    Feature, Measured Value, Unit, Source CAD model, Backing Evidence, SHA-256,
    Snapshot, Kernel, Geometry Entity Reference, and Provenance.
    """
    await _verify_job_ownership(job_id, org.id, db)

    # 1. Load measurement
    meas_res = await db.execute(
        select(CADMeasurement).where(
            CADMeasurement.id == measurement_id,
            CADMeasurement.cad_model_id == cad_model_id,
        )
    )
    meas = meas_res.scalars().first()
    if not meas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement not found.")

    # 2. Load CAD model & evidence
    cad_res = await db.execute(select(CADModel).where(CADModel.id == cad_model_id))
    cad_model = cad_res.scalars().first()

    ev_res = await db.execute(select(PersistentEvidence).where(PersistentEvidence.id == cad_model.evidence_id))
    evidence = ev_res.scalars().first()

    # 3. Load snapshot
    snap_res = await db.execute(
        select(CADSnapshot).where(CADSnapshot.cad_model_id == cad_model_id).order_by(desc(CADSnapshot.created_at))
    )
    snapshot = snap_res.scalars().first()

    return {
        "measurement": {
            "id": meas.id,
            "feature": meas.measurement_type.replace("_", " ").title(),
            "measured_value": meas.value,
            "unit": meas.unit,
            "axis": meas.axis,
        },
        "source": {
            "cad_model_id": cad_model.id,
            "format": cad_model.format,
            "kernel_name": cad_model.kernel_name,
            "kernel_version": cad_model.kernel_version,
            "evidence_id": evidence.id if evidence else None,
            "sha256": evidence.sha256_hash if evidence else None,
            "file_name": evidence.file_name if evidence else None,
            "acceptance_status": evidence.acceptance_status if evidence else None,
            "snapshot_id": snapshot.id if snapshot else None,
        },
        "geometry_reference": meas.source_reference,
        "provenance_chain": "Product DNA -> CAD Measurement -> Geometry Feature -> CAD Snapshot -> Evidence -> SHA-256",
    }


@router.post("/{cad_model_id}/map-to-dna", response_model=Dict[str, Any])
async def map_cad_to_dna(
    job_id: str,
    cad_model_id: str,
    current_user: User = Depends(require_role(["ENGINEER", "REVIEWER", "ADMIN"])),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """
    Map authoritative CAD measurements to Product DNA.
    STRICT REGULATORY GATE: Requires backing evidence to have acceptance_status == 'ACCEPTED'.
    """
    await _verify_job_ownership(job_id, org.id, db)
    try:
        dna_items = await cad_service.map_cad_measurements_to_dna(
            job_id=job_id,
            cad_model_id=cad_model_id,
            organization_id=org.id,
            db=db,
            actor_id=current_user.id,
        )
        return {
            "status": "success",
            "mapped_count": len(dna_items),
            "parameters": [d.parameter for d in dna_items],
            "message": f"Successfully mapped {len(dna_items)} CAD parameters to authoritative Product DNA.",
        }
    except CADEvidenceGatingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": exc.error_code, "message": exc.message, "details": exc.details},
        )
    except CADError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": exc.error_code, "message": exc.message},
        )


@router.get("/{cad_model_id}/mesh", response_model=Dict[str, Any])
async def get_cad_mesh(
    job_id: str,
    cad_model_id: str,
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve visual mesh representation for Babylon.js viewport."""
    await _verify_job_ownership(job_id, org.id, db)
    result = await db.execute(select(CADModel).where(CADModel.id == cad_model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CAD model not found.")

    visual_mesh = (model.metadata_json or {}).get("visual_mesh")
    if not visual_mesh:
        visual_mesh = {
            "type": "BOUNDING_ENVELOPE",
            "center": [0, 0, 0],
            "dimensions": [model.dim_x or 0, model.dim_y or 0, model.dim_z or 0],
            "corners": [],
            "edges": [],
        }

    return {
        "cad_model_id": model.id,
        "processing_status": model.processing_status,
        "mesh": visual_mesh,
    }
