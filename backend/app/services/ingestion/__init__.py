from backend.app.services.ingestion.document_loader import (
    calculate_file_sha256,
    register_document,
    save_uploaded_file,
    find_document_by_hash,
)
from backend.app.services.ingestion.pdf_extractor import (
    extract_pdf_content,
    extract_pdf_with_opendataloader,
    ExtractedPage,
    PDFExtractionResult,
)
from backend.app.services.ingestion.opendataloader_extractor import (
    extract_with_opendataloader,
    is_opendataloader_ready,
    OpenDataLoaderResult,
    OpenDataLoaderPage,
)
from backend.app.services.ingestion.pdf_parser import (
    parse_pdf_document,
    extract_clauses_and_tables,
)
from backend.app.services.ingestion.ocr import extract_text_from_image_bytes, is_scanned_page
from backend.app.services.ingestion.section_detector import detect_sections_in_text, DetectedSection
from backend.app.services.ingestion.clause_segmenter import segment_clauses_from_pages, SegmentedClause
from backend.app.services.ingestion.metadata_extractor import (
    extract_standard_metadata_from_text,
    ExtractedStandardMetadata,
)
from backend.app.services.ingestion.requirement_extractor import (
    extract_requirements_from_clause,
    ExtractedRequirement,
)
from backend.app.services.ingestion.embedder import (
    EmbeddingProvider,
    DeterministicLocalEmbeddingProvider,
    default_embedding_provider,
    cosine_similarity,
)
from backend.app.services.ingestion.pipeline import ingest_standard_document, IngestionSummary

__all__ = [
    "calculate_file_sha256",
    "register_document",
    "save_uploaded_file",
    "find_document_by_hash",
    "extract_pdf_content",
    "extract_pdf_with_opendataloader",
    "extract_with_opendataloader",
    "is_opendataloader_ready",
    "parse_pdf_document",
    "extract_clauses_and_tables",
    "ExtractedPage",
    "PDFExtractionResult",
    "OpenDataLoaderResult",
    "OpenDataLoaderPage",
    "extract_text_from_image_bytes",
    "is_scanned_page",
    "detect_sections_in_text",
    "DetectedSection",
    "segment_clauses_from_pages",
    "SegmentedClause",
    "extract_standard_metadata_from_text",
    "ExtractedStandardMetadata",
    "extract_requirements_from_clause",
    "ExtractedRequirement",
    "EmbeddingProvider",
    "DeterministicLocalEmbeddingProvider",
    "default_embedding_provider",
    "cosine_similarity",
    "ingest_standard_document",
    "IngestionSummary",
]
