from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.compliance_job import ComplianceJob


class Organization(Base):
    """Multi-tenant organization boundary enforcing tenant isolation."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    compliance_jobs: Mapped[List["ComplianceJob"]] = relationship(
        "ComplianceJob", back_populates="organization", cascade="all, delete-orphan"
    )
