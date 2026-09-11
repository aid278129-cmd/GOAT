"""Multi-Modal Ingestion and Document Preparation API Endpoints.

Layer 1: Input Processing (OCR, Layout Parsing, Whisper STT, BOM Parser, Manual Spec).
Normalizes inputs into a strict UnifiedInputPayload before Layer 2 Product DNA handoff.
Preserves zero-hallucination and provenance:
USER TEXT != EVIDENCE != COMPLIANCE.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body, Response, Query
from backend.app.services.ingestion.voice_stt import voice_transcription_service
from backend.app.services.ingestion.bom_parser import bom_parser_service
from backend.app.services.ingestion.validator import document_validator
from backend.app.services.ingestion.template_generator import template_generator_service
from backend.app.services.ingestion.readiness_engine import document_readiness_engine
from backend.app.services.ingestion.pdf_extractor import extract_pdf_content
from backend.app.services.ingestion.ocr import extract_text_from_image_bytes
from backend.app.services.citation_guard.guard import citation_guard
from backend.app.schemas.evidence import (
    CitationGuardCheckRequest,
    CitationGuardCheckResponse,
)
from backend.app.schemas.unified_input import (
    InputMode,
    InputProvenanceType,
    UnifiedInputPayload,
    UnifiedAttributeItem,
    BOMComponentItem,
    DocumentMetadataItem,
    DocumentValidationResult,
    ReadinessChecklist,
    TechnicalRequirementItem,
)

router = APIRouter(tags=["Layer 1: Multi-Modal Input Processing & Preparation"])


@router.get("/ingest/requirements", response_model=List[TechnicalRequirementItem], summary="Get required information checklist for standard/category")
async def get_required_information(
    target_standard: Optional[str] = Query(None, description="BIS Standard number (e.g. IS 302-2-201:2008)"),
    category: Optional[str] = Query(None, description="Product Category (e.g. Kitchen & Domestic Appliances)"),
) -> List[TechnicalRequirementItem]:
    """Dynamically fetches required technical fields from verified BIS/QCO knowledge.
    
    If knowledge is insufficient, returns UNKNOWN / INFORMATION REQUIRED without hallucinating.
    """
    return template_generator_service.get_requirements_for_standard_or_category(
        target_standard=target_standard,
        category=category,
    )


@router.get("/ingest/template", summary="Generate fillable specification, BOM, or sample product PDF template")
async def generate_template(
    template_type: str = Query("spec_csv", description="spec_csv | bom_csv | spec_json | sample_pdf"),
    target_standard: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    """Generates clean, fillable/downloadable template containing verified required fields."""
    if template_type in ("sample_pdf", "spec_pdf"):
        pdf_bytes = template_generator_service.generate_sample_product_info_pdf(target_standard, category)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="sample_product_information_specification.pdf"'},
        )
    elif template_type == "bom_csv":
        content = template_generator_service.generate_bom_csv_template()
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="zyntrix_bom_template.csv"'},
        )
    elif template_type == "spec_json":
        data = template_generator_service.generate_json_template(target_standard, category)
        return data
    else:
        content = template_generator_service.generate_csv_template(target_standard, category)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="zyntrix_spec_template.csv"'},
        )


@router.get("/ingest/sample-product-pdf", summary="Download reference sample Product Information PDF")
async def get_sample_product_pdf(
    target_standard: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    """Download a publication-grade sample Product Information Specification PDF illustrating proper format."""
    pdf_bytes = template_generator_service.generate_sample_product_info_pdf(target_standard, category)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="sample_product_information_specification.pdf"'},
    )


@router.post("/ingest/validate", response_model=DocumentValidationResult, summary="Pre-flight validation for uploaded documents")
async def validate_document(
    file: Optional[UploadFile] = File(None),
    input_mode: InputMode = Form(InputMode.PDF),
    product_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
) -> DocumentValidationResult:
    """Validates file integrity, format magic bytes, empty/malformed data, and duplicate hashes."""
    if file:
        content = await file.read()
        return document_validator.validate_file(
            file_bytes=content,
            filename=file.filename or "uploaded_file",
            input_mode=input_mode,
        )
    elif input_mode == InputMode.MANUAL:
        return document_validator.validate_manual_spec(
            product_name=product_name or "",
            category=category or "",
            description=description or "",
        )
    else:
        raise HTTPException(status_code=400, detail="Either a file payload or manual spec form fields are required.")


@router.post("/ingest/process", response_model=UnifiedInputPayload, summary="Process and normalize multi-modal inputs into Unified Schema")
async def process_unified_input(
    input_mode: InputMode = Form(InputMode.PDF),
    file: Optional[UploadFile] = File(None),
    product_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    raw_content: Optional[str] = Form(None),
    target_standard: Optional[str] = Form(None),
    authoritative_mode: bool = Form(False),
) -> UnifiedInputPayload:
    """Executes full Layer 1 processing: Validation -> Extraction -> Normalization -> Readiness Evaluation."""
    extracted_text = ""
    source_filename = None
    file_bytes = b""
    sha256 = ""
    declared_attrs: List[UnifiedAttributeItem] = []
    bom_components: List[BOMComponentItem] = []
    attached_docs: List[DocumentMetadataItem] = []

    # 1. Handle File Uploads (PDF, Image/OCR, BOM File)
    if file:
        source_filename = document_validator.sanitize_filename(file.filename or "uploaded_file")
        file_bytes = await file.read()
        sha256 = document_validator.calculate_sha256(file_bytes)

        val_result = document_validator.validate_file(
            file_bytes=file_bytes,
            filename=source_filename,
            input_mode=input_mode,
        )

        if not val_result.is_valid:
            # Actionable error response
            err_msgs = [i.message for i in val_result.issues]
            remediations = [i.actionable_remediation for i in val_result.issues]
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Document Validation Failed",
                    "issues": err_msgs,
                    "remediations": remediations,
                },
            )

        attached_docs.append(
            DocumentMetadataItem(
                filename=source_filename,
                sha256_hash=sha256,
                file_size_bytes=len(file_bytes),
                mime_type=file.content_type or "application/octet-stream",
                is_verified_format=True,
                provenance_type=(
                    InputProvenanceType.DOCUMENT_EVIDENCE
                    if input_mode == InputMode.PDF
                    else (InputProvenanceType.OCR if input_mode == InputMode.IMAGE_OCR else InputProvenanceType.BOM)
                ),
            )
        )

        # Extraction by Mode
        if input_mode == InputMode.PDF:
            pdf_result = extract_pdf_content(file_bytes, filename=source_filename)
            extracted_text = "\n\n".join(p.text for p in pdf_result.pages if p.text.strip())
            provenance = InputProvenanceType.DOCUMENT_EVIDENCE

        elif input_mode == InputMode.IMAGE_OCR:
            ocr_res = extract_text_from_image_bytes(file_bytes)
            if ocr_res.success and ocr_res.text:
                extracted_text = ocr_res.text
            else:
                extracted_text = f"Product image attached. {ocr_res.details or ''}".strip()
            provenance = InputProvenanceType.OCR

        elif input_mode == InputMode.BOM:
            content_str = file_bytes.decode("utf-8", errors="ignore")
            bom_parsed = bom_parser_service.parse_bom_content(content_str, filename=source_filename)
            extracted_text = (
                f"Parsed BOM with {bom_parsed['total_parts']} components. "
                f"Materials: {', '.join(bom_parsed['materials']) if bom_parsed['materials'] else 'Standard'}"
            )
            for c in bom_parsed["components"]:
                bom_components.append(
                    BOMComponentItem(
                        part_number=c["part_number"],
                        name=c["name"],
                        material=c["material"],
                        specification=c["specification"],
                        quantity=str(c["quantity"]),
                    )
                )
            provenance = InputProvenanceType.BOM

        elif input_mode == InputMode.VOICE:
            voice_res = await voice_transcription_service.transcribe_audio(file_bytes, filename=source_filename)
            if voice_res.get("success"):
                extracted_text = voice_res.get("text", "")
            else:
                extracted_text = f"Voice audio query: {voice_res.get('error', 'Audio input recorded.')}"
            provenance = InputProvenanceType.VOICE_TRANSCRIPT

    # 2. Handle Direct Raw Content / Manual Spec
    elif raw_content:
        extracted_text = raw_content
        provenance = InputProvenanceType.BOM if input_mode == InputMode.BOM else InputProvenanceType.USER_CLAIM
        if input_mode == InputMode.BOM:
            bom_parsed = bom_parser_service.parse_bom_content(raw_content)
            for c in bom_parsed["components"]:
                bom_components.append(
                    BOMComponentItem(
                        part_number=c["part_number"],
                        name=c["name"],
                        material=c["material"],
                        specification=c["specification"],
                        quantity=str(c["quantity"]),
                    )
                )

    else:
        # Manual Mode
        provenance = InputProvenanceType.MANUAL_INPUT
        val_result = document_validator.validate_manual_spec(
            product_name=product_name or "",
            category=category or "",
            description=description or "",
        )
        if not val_result.is_valid:
            err_msgs = [i.message for i in val_result.issues]
            remediations = [i.actionable_remediation for i in val_result.issues]
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Specification Validation Failed",
                    "issues": err_msgs,
                    "remediations": remediations,
                },
            )

    # Combine description & auto-fill product details if not supplied
    final_name = (product_name or "").strip()
    final_cat = (category or "").strip()
    final_desc = (description or "").strip()

    if extracted_text:
        if final_desc:
            final_desc = f"{final_desc}\n\n[Extracted from {source_filename or 'Input'}]:\n{extracted_text}"
        else:
            final_desc = extracted_text

    if not final_name:
        final_name = "Sample Product (Layer 1 Ingested)"
    if not final_cat:
        final_cat = "Kitchen & Domestic Appliances"

    # Evaluate Document Readiness & Input Completeness
    checklist = document_readiness_engine.evaluate_readiness(
        product_name=final_name,
        category=final_cat,
        description=final_desc,
        target_standard=target_standard,
        provenance_type=provenance,
    )

    # Populate declared attributes with provenance
    for ev in checklist.evaluations:
        if ev.extracted_value:
            declared_attrs.append(
                UnifiedAttributeItem(
                    name=ev.field_name,
                    value=str(ev.extracted_value),
                    provenance_type=provenance,
                    source_filename=source_filename,
                    confidence=0.95 if provenance in (InputProvenanceType.DOCUMENT_EVIDENCE, InputProvenanceType.BOM) else 0.85,
                    raw_snippet=str(ev.extracted_value),
                )
            )

    return UnifiedInputPayload(
        input_mode=input_mode,
        product_name=final_name,
        category=final_cat,
        description=final_desc,
        declared_attributes=declared_attrs,
        components_bom=bom_components,
        attached_documents=attached_docs,
        readiness_checklist=checklist,
        authoritative_mode=authoritative_mode,
    )


# Keep existing endpoints for full backward compatibility
@router.post("/ingest/voice", summary="Transcribe voice query via Whisper STT")
async def ingest_voice_query(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(default="en"),
) -> Dict[str, Any]:
    try:
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

        result = await voice_transcription_service.transcribe_audio(
            audio_bytes=content,
            filename=audio.filename or "recording.wav",
            language=language,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")


@router.post("/ingest/bom", summary="Parse Bill of Materials (BOM) table")
async def ingest_bom_table(
    file: Optional[UploadFile] = File(None),
    raw_content: Optional[str] = Form(default=None),
) -> Dict[str, Any]:
    content_str = ""
    filename = "bom.csv"

    if file:
        file_bytes = await file.read()
        content_str = file_bytes.decode("utf-8", errors="ignore")
        filename = file.filename or "bom.csv"
    elif raw_content:
        content_str = raw_content
    else:
        raise HTTPException(status_code=400, detail="Either file upload or raw_content is required.")

    parsed = bom_parser_service.parse_bom_content(content_str, filename=filename)
    return parsed


@router.post("/citation-guard/verify", response_model=CitationGuardCheckResponse, summary="Verify claim through Citation Guard")
async def verify_citation_guard(
    request: CitationGuardCheckRequest = Body(...),
) -> CitationGuardCheckResponse:
    result = citation_guard.verify_claim(request)
    return result
