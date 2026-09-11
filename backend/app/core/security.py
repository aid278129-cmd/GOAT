import os
import uuid
import secrets
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from backend.app.core.config import settings


def generate_secure_storage_filename(original_filename: str) -> str:
    """Generate a randomized secure storage filename preserving safe extensions to prevent path traversal."""
    ext = Path(original_filename).suffix.lower()
    random_token = secrets.token_hex(16)
    return f"{random_token}{ext}"


def validate_file_upload(file: UploadFile) -> None:
    """Validate uploaded document MIME type and file size constraint."""
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: {settings.ALLOWED_MIME_TYPES}",
        )


def sanitize_sensitive_data(data: dict) -> dict:
    """Mask confidential fields in payloads before debugging/logging."""
    sensitive_keys = {"password", "secret", "token", "api_key", "proprietary_bom"}
    sanitized = {}
    for k, v in data.items():
        if any(sk in k.lower() for sk in sensitive_keys):
            sanitized[k] = "********"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_sensitive_data(v)
        else:
            sanitized[k] = v
    return sanitized
