from typing import Optional
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class ProductAttribute(Base):
    """Extensible Product DNA attribute with full provenance tracking."""

    __tablename__ = "product_attributes"

    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), default="string")
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Provenance details (document, page, source text, confidence score, extraction method)
    provenance_type: Mapped[str] = mapped_column(String(50), default="USER_CLAIM", nullable=False)  # USER_CLAIM | USER_CLARIFICATION | DOCUMENT_EVIDENCE | LAB_EVIDENCE | OFFICIAL_SOURCE | DERIVED_VALUE
    source_document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(nullable=True)
    source_text: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    extraction_method: Mapped[str] = mapped_column(String(50), default="manual")  # manual | parsed | llm_extracted

    product: Mapped["Product"] = relationship("Product", back_populates="attributes")
