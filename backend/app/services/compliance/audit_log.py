"""Authority Audit Logger (Milestone M24.4).

Maintains a dedicated, tamper-evident record of all authoritative compliance decisions
strictly segregated from non-authoritative AI reasoning logs.
"""

from typing import List, Dict, Any, Optional
from backend.app.services.compliance.authority_types import AuthoritativeRecord


class AuthorityAuditLogger:
    """In-memory audit trail for verified authoritative compliance decisions."""

    def __init__(self):
        self._records: List[AuthoritativeRecord] = []

    def record_decision(self, record: AuthoritativeRecord) -> None:
        """Append a validated authoritative decision to the audit trail."""
        self._records.append(record)

    def get_records_by_correlation(self, correlation_id: str) -> List[AuthoritativeRecord]:
        """Retrieve authoritative decisions for a specific interaction run."""
        return [r for r in self._records if r.correlation_id == correlation_id]

    def clear(self) -> None:
        """Clear the audit trail (test fixture utility)."""
        self._records.clear()

    @property
    def total_records(self) -> int:
        return len(self._records)


authority_audit_logger = AuthorityAuditLogger()
