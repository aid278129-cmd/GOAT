import os
import json
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.core.logging import logger
from backend.app.models.document import Document
from backend.app.models.standard import Standard
from backend.app.models.clause import Clause
from backend.app.models.requirement import Requirement
from backend.app.models.source import Source
from backend.app.models.verification_record import VerificationRecord
from backend.app.models.regulatory_instrument import RegulatoryInstrument
from backend.app.models.amendment import Amendment
from backend.app.services.ingestion.document_loader import (
    calculate_file_sha256,
    register_document,
    save_uploaded_file,
)
from backend.app.services.ingestion.pdf_extractor import extract_pdf_content, PDFExtractionResult
from backend.app.services.ingestion.metadata_extractor import extract_standard_metadata_from_text
from backend.app.services.ingestion.clause_segmenter import segment_clauses_from_pages, SegmentedClause
from backend.app.services.ingestion.requirement_extractor import extract_requirements_from_clause
from backend.app.services.ingestion.embedder import default_embedding_provider


class IngestionSummary(BaseModel):
    document_id: str
    file_hash: str
    filename: str
    standard_id: str
    standard_number: str
    standard_title: str
    total_pages: int
    clauses_ingested: int
    requirements_ingested: int
    verification_status: str
    ingestion_status: str


async def _create_verification_record(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    verification_status: str,
    document_hash: Optional[str] = None,
    source_authority: Optional[str] = None,
    notes: Optional[str] = None,
    verification_method: str = "MACHINE_VALIDATION",
    verified_by: str = "SYSTEM_PIPELINE",
) -> None:
    """Create an immutable verification record for an ingested or audited entity."""
    record = VerificationRecord(
        entity_type=entity_type,
        entity_id=entity_id,
        verification_status=verification_status,
        verified_by=verified_by,
        verification_method=verification_method,
        source_authority=source_authority,
        document_hash=document_hash,
        notes=notes,
    )
    db.add(record)


async def register_source(
    db: AsyncSession,
    name: str,
    publisher: str,
    source_type: str = "USER_PROVIDED",
    authority_level: str = "UNVERIFIED",
    source_url: Optional[str] = None,
    access_method: str = "manual_upload",
    notes: Optional[str] = None,
) -> Source:
    """Register or find an existing source in the source registry."""
    stmt = select(Source).where(Source.name == name, Source.publisher == publisher)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    source = Source(
        name=name,
        publisher=publisher,
        source_type=source_type,
        authority_level=authority_level,
        source_url=source_url,
        access_method=access_method,
        notes=notes,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def ingest_standard_document(
    db: AsyncSession,
    file_path: str,
    original_filename: Optional[str] = None,
    document_type: str = "standard",
    standard_number_override: Optional[str] = None,
    standard_title_override: Optional[str] = None,
    is_verified: bool = False,
    is_synthetic_fixture: bool = False,
    source_type: str = "USER_PROVIDED",
    source_url: Optional[str] = None,
    publisher: Optional[str] = None,
) -> IngestionSummary:
    """End-to-end ingestion pipeline transforming a standard document into
    structured clauses and vector embeddings.

    Trust Governance Guard:
    If is_synthetic_fixture=True or file path contains 'fixtures/synthetic',
    the document CANNOT be marked VERIFIED. It must remain REQUIRES_REVIEW
    and USER_PROVIDED. INDEXED ≠ VERIFIED.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source file not found at {file_path}")

    # Check synthetic guard
    if "fixtures" in file_path or "synthetic" in file_path or is_synthetic_fixture:
        is_synthetic_fixture = True
        is_verified = False  # Synthetic fixture can NEVER be marked VERIFIED
        source_type = "USER_PROVIDED"

    filename = original_filename or os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_hash = calculate_file_sha256(file_path)

    verif_status = "VERIFIED" if is_verified else "REQUIRES_REVIEW"

    # Step 0: Register Source
    source_name = standard_number_override or filename
    source_publisher = publisher or ("Zyntrix Test Assets" if is_synthetic_fixture else "Unknown")
    authority_level = "AUTHORITATIVE" if (source_type == "BIS_OFFICIAL" and not is_synthetic_fixture) else "UNVERIFIED"

    source = await register_source(
        db=db,
        name=source_name,
        publisher=source_publisher,
        source_type=source_type,
        authority_level=authority_level,
        source_url=source_url,
        access_method="test_fixture" if is_synthetic_fixture else "cli_import",
        notes="Synthetic representative test fixture for unit testing." if is_synthetic_fixture else None,
    )

    # Step 1: Register Document
    doc = await register_document(
        db=db,
        original_filename=filename,
        file_path=file_path,
        stored_filename=os.path.basename(file_path),
        file_size=file_size,
        file_hash=file_hash,
        mime_type="application/pdf" if file_path.endswith(".pdf") else "text/plain",
        document_type=document_type,
        standard_number=standard_number_override,
        verification_status=verif_status,
    )
    doc.source_id = source.id
    doc.publisher = source_publisher
    doc.ingestion_status = "EXTRACTED"
    if is_synthetic_fixture:
        doc.verification_notes = "SYNTHETIC_TEST_FIXTURE: Not an authentic BIS publication. Excluded from authoritative compliance retrieval."
        doc.metadata_json = {
            "fixture_type": "SYNTHETIC_TEST_FIXTURE",
            "authoritative": False,
        }
    await db.commit()

    # Step 2: Extract text and page layout
    extraction: PDFExtractionResult = extract_pdf_content(file_path, enable_ocr=True)
    doc.page_count = extraction.total_pages

    full_text = "\n\n".join(p.text for p in extraction.pages)

    # Step 3: Extract standard metadata
    meta = extract_standard_metadata_from_text(
        full_text,
        default_standard_number=standard_number_override,
        default_title=standard_title_override,
    )

    doc.standard_number = meta.standard_number

    # Step 4: Register or Update Standard
    std_stmt = select(Standard).where(Standard.standard_number == meta.standard_number)
    std_res = await db.execute(std_stmt)
    std = std_res.scalar_one_or_none()

    if not std:
        std = Standard(
            standard_number=meta.standard_number,
            title=meta.title,
            category=meta.category,
            scope=meta.scope_summary,
            scheme=meta.scheme,
            is_mandatory_qco=meta.is_mandatory_qco,
            version="current",
            status="ACTIVE",
            verification_status=verif_status,
            source_document_id=doc.id,
        )
        db.add(std)
        await db.commit()
        await db.refresh(std)
    else:
        std.title = meta.title or std.title
        std.category = meta.category or std.category
        std.scope = meta.scope_summary or std.scope
        if is_verified:
            std.verification_status = verif_status
        std.source_document_id = doc.id
        await db.commit()
        await db.refresh(std)

    # Clean existing clauses for this standard to prevent duplicate ingestion
    await db.execute(delete(Clause).where(Clause.standard_id == std.id))
    await db.commit()

    # Step 5: Segment Clauses
    doc.ingestion_status = "SEGMENTED"
    await db.commit()

    segmented_clauses: List[SegmentedClause] = segment_clauses_from_pages(extraction.pages)

    # Step 6 & 7: Extract Requirements & Embeddings & Save to Database
    clause_orm_map: Dict[str, Clause] = {}
    created_clauses: List[Clause] = []
    total_reqs_count = 0

    # First pass: create all clause records
    for sc in segmented_clauses:
        embedding = default_embedding_provider.embed_text(f"{sc.clause_number} {sc.title}\n{sc.text_content}")

        clause_orm = Clause(
            standard_id=std.id,
            clause_number=sc.clause_number,
            title=sc.title,
            section=sc.section,
            text_content=sc.text_content,
            page_number=sc.page_start,
            page_start=sc.page_start,
            page_end=sc.page_end,
            segmentation_status=sc.segmentation_status,
            verification_status=verif_status,
            source_document_id=doc.id,
            embedding=embedding,
            metadata_json={
                "char_count": sc.char_count,
                "parent_clause_number": sc.parent_clause_number,
            },
        )
        db.add(clause_orm)
        clause_orm_map[sc.clause_number] = clause_orm
        created_clauses.append(clause_orm)

    await db.commit()

    # Refresh to obtain generated primary key IDs
    for c in created_clauses:
        await db.refresh(c)

    # Second pass: link parent_clause_id and add requirements
    for sc in segmented_clauses:
        current_clause = clause_orm_map.get(sc.clause_number)
        if not current_clause:
            continue

        if sc.parent_clause_number and sc.parent_clause_number in clause_orm_map:
            current_clause.parent_clause_id = clause_orm_map[sc.parent_clause_number].id

        reqs = extract_requirements_from_clause(sc, meta.standard_number)
        for r in reqs:
            req_embedding = default_embedding_provider.embed_text(f"{r.code} {r.description} {r.measurable_condition or ''}")
            req_orm = Requirement(
                clause_id=current_clause.id,
                code=r.code,
                requirement_type=r.requirement_type,
                description=r.description,
                measurable_condition=r.measurable_condition,
                evidence_type=r.evidence_type,
                test_method_reference=r.test_method_reference,
                interpretation_status=r.interpretation_status,
                verification_status=verif_status,
                embedding=req_embedding,
            )
            db.add(req_orm)
            total_reqs_count += 1

    doc.ingestion_status = "INDEXED"
    await db.commit()

    # Step 8: Create verification records (machine validation audit trail)
    await _create_verification_record(
        db, "document", doc.id, verif_status,
        document_hash=file_hash,
        source_authority=source.authority_level,
        notes=f"Machine validation: PDF readable, {extraction.total_pages} pages extracted, {len(segmented_clauses)} clauses segmented."
              + (" (SYNTHETIC_TEST_FIXTURE - Non-authoritative)" if is_synthetic_fixture else ""),
    )
    await _create_verification_record(
        db, "standard", std.id, verif_status,
        source_authority=source.authority_level,
        notes=f"Standard metadata extracted from document. Source type: {source_type}."
              + (" (SYNTHETIC_TEST_FIXTURE - Non-authoritative)" if is_synthetic_fixture else ""),
    )
    await db.commit()

    logger.info(
        f"Ingestion complete: {meta.standard_number} ({len(segmented_clauses)} clauses, {total_reqs_count} reqs) -> INDEXED / {verif_status}"
    )

    return IngestionSummary(
        document_id=doc.id,
        file_hash=file_hash,
        filename=filename,
        standard_id=std.id,
        standard_number=std.standard_number,
        standard_title=std.title,
        total_pages=extraction.total_pages,
        clauses_ingested=len(segmented_clauses),
        requirements_ingested=total_reqs_count,
        verification_status=verif_status,
        ingestion_status="INDEXED",
    )


async def register_official_knowledge_package(
    db: AsyncSession, package_dir: str
) -> Dict[str, Any]:
    """Register official BIS and government metadata from a verified knowledge package.

    Captures official standard metadata, QCO orders, product manuals, and
    audit records without fabricating standard text when full text is pending.
    """
    metadata_file = os.path.join(package_dir, "metadata.json")
    provenance_file = os.path.join(package_dir, "provenance.json")
    qco_file = os.path.join(package_dir, "regulatory", "qco_order_2023.json")
    pm_file = os.path.join(package_dir, "product_manual", "pm_is17526.json")
    verif_file = os.path.join(package_dir, "verification.json")

    results = {}

    # 1. Load metadata
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        std_num = meta["standard_number"]
        official_title = meta["official_title"]

        # Register official BIS source
        source = await register_source(
            db=db,
            name=f"BIS Official - {std_num}",
            publisher="Bureau of Indian Standards",
            source_type="BIS_OFFICIAL",
            authority_level="AUTHORITATIVE",
            source_url="https://www.manakonline.in",
            access_method="official_catalog",
            notes=f"Authoritative BIS Standards Catalog entry for {std_num}: {official_title}.",
        )

        # Register or update standard with official title
        stmt = select(Standard).where(Standard.standard_number == std_num)
        res = await db.execute(stmt)
        std = res.scalar_one_or_none()
        if not std:
            std = Standard(
                standard_number=std_num,
                title=official_title,
                category=meta.get("category", "General"),
                scope=meta.get("scope"),
                scheme=meta.get("certification_scheme", "Scheme I"),
                is_mandatory_qco=meta.get("is_mandatory", False),
                status=meta.get("status", "ACTIVE"),
                verification_status="REQUIRES_REVIEW",  # Full text pending
            )
            db.add(std)
            await db.commit()
            await db.refresh(std)
        else:
            std.title = official_title
            await db.commit()
            await db.refresh(std)

        results["standard_number"] = std_num
        results["official_title"] = official_title
        results["source_id"] = source.id

        # 2. Register QCO if available
        if os.path.exists(qco_file):
            with open(qco_file, "r", encoding="utf-8") as f:
                qco_data = json.load(f)

            qco_stmt = select(RegulatoryInstrument).where(
                RegulatoryInstrument.standard_id == std.id,
                RegulatoryInstrument.instrument_type == "QCO",
            )
            qco_res = await db.execute(qco_stmt)
            reg_inst = qco_res.scalar_one_or_none()
            if not reg_inst:
                reg_inst = RegulatoryInstrument(
                    standard_id=std.id,
                    instrument_type="QCO",
                    notification_number=qco_data.get("order_title"),
                    scope_description=qco_data.get("scope_description"),
                    is_mandatory=qco_data.get("is_mandatory", True),
                    verification_status="VERIFIED",
                    notes=f"Issued by {qco_data.get('issuing_department')}, {qco_data.get('issuing_ministry')}.",
                )
                db.add(reg_inst)
                await db.commit()
                results["qco_registered"] = True

        # 3. Log verification audit records
        if os.path.exists(verif_file):
            with open(verif_file, "r", encoding="utf-8") as f:
                v_data = json.load(f)
            for vr in v_data.get("verification_records", []):
                await _create_verification_record(
                    db=db,
                    entity_type="standard_package",
                    entity_id=std.id,
                    verification_status=vr["status"],
                    source_authority=vr.get("source_authority"),
                    verification_method=vr.get("method", "SOURCE_VERIFICATION"),
                    verified_by="SYSTEM_RESEARCH",
                    notes=vr.get("evidence"),
                )
            await db.commit()
            results["verification_logged"] = True

    return results
