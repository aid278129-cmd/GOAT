from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class Source(Base):
    """Registry of knowledge sources with authority classification.

    Represents WHERE knowledge came from — distinct from WHAT was extracted.
    Source authority determines the maximum trust level that derived
    documents, standards, and clauses may inherit.
    """

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    publisher: Mapped[str] = mapped_column(String(300), nullable=False)

    # BIS_OFFICIAL | GOVERNMENT_OFFICIAL | SECONDARY | USER_PROVIDED | OTHER
    source_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # AUTHORITATIVE | SUPPORTING | SECONDARY | UNVERIFIED
    authority_level: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", index=True)

    # manual_upload | api_sync | web_download | cli_import
    access_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
