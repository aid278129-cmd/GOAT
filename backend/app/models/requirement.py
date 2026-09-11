from typing import Optional, List
from sqlalchemy import String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class Requirement(Base):
    """Specific measurable technical/safety requirement under a Clause.

    Trust model: verification_status defaults to REQUIRES_REVIEW.
    Machine-extracted interpretation_status (CONFIDENT/REQUIRES_REVIEW)
    is separate from source verification_status.
    """

    __tablename__ = "requirements"

    clause_id: Mapped[str] = mapped_column(String(36), ForeignKey("clauses.id"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # e.g. "REQ-IS17526-001"

    # Requirement type: MATERIAL | DIMENSION | PERFORMANCE | SAFETY | CONSTRUCTION | MARKING | PACKAGING | TESTING | DOCUMENTATION | OTHER
    requirement_type: Mapped[str] = mapped_column(String(50), default="PERFORMANCE", index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    measurable_condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # lab_test | material_certificate | visual_inspection
    test_method_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Machine extraction confidence: CONFIDENT | REQUIRES_REVIEW
    interpretation_status: Mapped[str] = mapped_column(String(50), default="CONFIDENT")

    # Source verification: UNVERIFIED | REQUIRES_REVIEW | VERIFIED
    # NOTE: Separate from interpretation_status. AI extraction ≠ regulatory verification.
    verification_status: Mapped[str] = mapped_column(String(50), default="REQUIRES_REVIEW", index=True)

    # Vector embedding representation
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    clause: Mapped["Clause"] = relationship("Clause", back_populates="requirements")
    tests: Mapped[List["StandardTest"]] = relationship(
        "StandardTest", back_populates="requirement", cascade="all, delete-orphan"
    )
