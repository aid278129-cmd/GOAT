from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class VerificationRecord(Base):
    """Audit trail for verification actions on knowledge entities.

    Distinguishes MACHINE_VALIDATION (pipeline checks: PDF readable, hash
    calculated, clauses parsed) from SOURCE_VERIFICATION (authoritative
    provenance confirmed) and HUMAN_REVIEW (manual expert confirmation).
    """

    __tablename__ = "verification_records"

    # document | standard | clause | requirement | amendment
    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    # UNVERIFIED | REQUIRES_REVIEW | VERIFIED | SUPERSEDED
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False)

    # SYSTEM_PIPELINE | PENDING_HUMAN_REVIEW | <human identifier>
    verified_by: Mapped[str] = mapped_column(String(200), default="SYSTEM_PIPELINE")

    # MACHINE_VALIDATION | SOURCE_VERIFICATION | HUMAN_REVIEW
    verification_method: Mapped[str] = mapped_column(String(50), default="MACHINE_VALIDATION")

    # BIS_OFFICIAL | GOVERNMENT_OFFICIAL | SECONDARY | USER_PROVIDED | None
    source_authority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
