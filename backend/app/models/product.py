from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intended_use: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Core DNA attributes stored as JSON structure with provenance metadata
    dna_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    attributes: Mapped[List["ProductAttribute"]] = relationship(
        "ProductAttribute", back_populates="product", cascade="all, delete-orphan"
    )
    compliance_results: Mapped[List["ComplianceResult"]] = relationship(
        "ComplianceResult", back_populates="product", cascade="all, delete-orphan"
    )
