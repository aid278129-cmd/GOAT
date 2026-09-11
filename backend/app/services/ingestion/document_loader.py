import hashlib
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.security import generate_secure_storage_filename
from backend.app.core.logging import logger
from backend.app.models.document import Document


def calculate_file_sha256(file_path: str) -> str:
    """Calculate SHA-256 cryptographic hash of a file for integrity tracking and deduplication."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


async def find_document_by_hash(db: AsyncSession, file_hash: str) -> Optional[Document]:
    """Check if a document with the exact SHA-256 hash already exists in the registry."""
    stmt = select(Document).where(Document.file_hash == file_hash)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def save_uploaded_file(file_content: bytes, original_filename: str) -> Tuple[str, str, int, str]:
    """Save bytes to secure local storage and return (file_path, stored_filename, file_size, file_hash)."""
    os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
    stored_filename = generate_secure_storage_filename(original_filename)
    target_path = os.path.join(settings.STORAGE_LOCAL_PATH, stored_filename)

    with open(target_path, "wb") as f:
        f.write(file_content)

    file_size = len(file_content)
    file_hash = calculate_file_sha256(target_path)
    return target_path, stored_filename, file_size, file_hash


async def register_document(
    db: AsyncSession,
    original_filename: str,
    file_path: str,
    stored_filename: str,
    file_size: int,
    file_hash: str,
    mime_type: str,
    document_type: str = "standard",
    standard_number: Optional[str] = None,
    source_url: Optional[str] = None,
    verification_status: str = "UNVERIFIED",
) -> Document:
    """Register or return existing document in the PostgreSQL document registry."""
    existing = await find_document_by_hash(db, file_hash)
    if existing:
        logger.info(f"Duplicate document detected by SHA-256 ({file_hash}). Reusing existing ID {existing.id}.")
        return existing

    doc = Document(
        filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size_bytes=file_size,
        mime_type=mime_type,
        file_hash=file_hash,
        document_type=document_type,
        standard_number=standard_number,
        source_url=source_url,
        ingestion_status="DISCOVERED",
        verification_status=verification_status,
        metadata_json={
            "original_filename": original_filename,
            "registered_from": "ingestion_pipeline",
        },
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    logger.info(f"Registered new document {doc.id} (hash: {file_hash[:12]}...)")
    return doc
