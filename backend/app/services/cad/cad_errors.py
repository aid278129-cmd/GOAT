from typing import Optional


class CADError(Exception):
    """Base exception for CAD intelligence pipeline."""
    def __init__(self, message: str, error_code: str = "CAD_ERROR", details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class UnsupportedCADFormatError(CADError):
    """Raised when an uploaded CAD file format is unsupported or slated for future support."""
    def __init__(self, extension: str, message: Optional[str] = None):
        ext = extension.upper().lstrip(".")
        msg = message or f"Unsupported CAD format '{ext}'. Only STEP (.stp, .step) is currently supported for geometric intelligence."
        super().__init__(msg, error_code="UNSUPPORTED_CAD_FORMAT", details={"extension": ext})


class CADProcessingLimitExceeded(CADError):
    """Raised when file size, component count, geometry features, or timeout limits are breached."""
    def __init__(self, limit_type: str, actual_value: any, max_limit: any):
        msg = f"CAD processing resource limit breached: {limit_type} = {actual_value} (Max allowed: {max_limit})."
        super().__init__(msg, error_code="CAD_PROCESSING_LIMIT_EXCEEDED", details={"limit_type": limit_type, "actual": actual_value, "limit": max_limit})


class CADEngineUnavailableError(CADError):
    """Raised when the requested CAD kernel/provider is unavailable in the execution environment."""
    def __init__(self, kernel_name: str, message: Optional[str] = None):
        msg = message or f"CAD engine '{kernel_name}' is unavailable in the current runtime environment."
        super().__init__(msg, error_code="CAD_ENGINE_UNAVAILABLE", details={"kernel": kernel_name})


class CADGeometryParsingError(CADError):
    """Raised when CAD geometry or ISO 10303-21 entity tokens cannot be parsed."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, error_code="CAD_GEOMETRY_PARSING_ERROR", details=details)


class CADEvidenceGatingError(CADError):
    """Raised when unaccepted CAD evidence attempts to populate authoritative Product DNA."""
    def __init__(self, evidence_id: str, status: str):
        msg = f"Evidence gating violation: CAD evidence artifact '{evidence_id}' has acceptance status '{status}'. Only ACCEPTED evidence may contribute to authoritative Product DNA."
        super().__init__(msg, error_code="CAD_EVIDENCE_GATING_VIOLATION", details={"evidence_id": evidence_id, "status": status})
