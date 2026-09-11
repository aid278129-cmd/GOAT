from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class StandardTest(Base):
    """Laboratory testing parameter and pass/fail criteria from Indian Standards."""

    __tablename__ = "standard_tests"

    requirement_id: Mapped[str] = mapped_column(String(36), ForeignKey("requirements.id"), index=True, nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    parameter: Mapped[str] = mapped_column(String(200), nullable=False)
    specified_limit: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "Max 0.05% Pb", ">= 1000 hours"
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sampling_procedure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    requirement: Mapped["Requirement"] = relationship("Requirement", back_populates="tests")
