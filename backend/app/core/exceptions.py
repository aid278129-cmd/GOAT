from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.app.core.logging import logger


class ComplianceCompilerException(Exception):
    """Base exception for BIS Compliance Compiler system errors."""

    def __init__(
        self,
        message: str,
        code: str = "COMPLIANCE_ERROR",
        status_code: int = 400,
        remediation: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.remediation = remediation or "Verify request payload parameters against API specification."


class ProvenanceNotFoundError(ComplianceCompilerException):
    """Raised when a compliance claim cannot be substantiated by verified clause evidence."""

    def __init__(self, message: str = "Authoritative clause provenance not found"):
        super().__init__(
            message=message,
            code="PROVENANCE_NOT_FOUND",
            status_code=422,
            remediation="Provide an official BIS standard citation or NABL accredited laboratory report.",
        )


class MissingProductAttributeError(ComplianceCompilerException):
    """Raised when an applicability-critical product attribute is missing."""

    def __init__(self, attribute_name: str):
        super().__init__(
            message=f"Missing applicability-critical product attribute: {attribute_name}. Clarification required.",
            code="MISSING_ATTRIBUTE_CLARIFICATION_REQUIRED",
            status_code=422,
            remediation=f"Submit clarification response answering attribute '{attribute_name}'.",
        )


class DatabaseUnavailableError(ComplianceCompilerException):
    """Raised when database operations fail and standalone fallback is disabled."""

    def __init__(self, message: str = "Database service unavailable."):
        super().__init__(
            message=message,
            code="DATABASE_UNAVAILABLE",
            status_code=503,
            remediation="Start PostgreSQL container or configure DATABASE_URL in .env.",
        )


async def compliance_exception_handler(request: Request, exc: ComplianceCompilerException) -> JSONResponse:
    """Standardized error response handler for compliance exceptions."""
    req_id = getattr(request.state, "request_id", "REQ-COMPLIANCE")
    logger.warning(f"Compliance exception on {request.url.path} [{req_id}]: [{exc.code}] {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": req_id,
                "remediation": exc.remediation,
            },
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Sanitized global handler for unhandled exceptions (zero secret leakage)."""
    req_id = getattr(request.state, "request_id", "REQ-SYS-ERR")
    logger.error(f"Unhandled system exception on {request.url.path} [{req_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Internal connection strings and credentials have been secured.",
                "request_id": req_id,
                "remediation": "Inspect system health via GET /api/v1/system/health or review server logs.",
            },
        },
    )
