from typing import Optional
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base


class ComplianceResult(Base):
    """Auditable compliance evaluation linking product, standard, clause, and evidence provenance."""

    __tablename__ = "compliance_results"

    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True, nullable=False)
    standard_id: Mapped[str] = mapped_column(String(36), ForeignKey("standards.id"), index=True, nullable=False)
    clause_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=True)
    requirement_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("requirements.id"), nullable=True)
    evidence_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("evidence.id"), nullable=True)

    # Compliance Status:
    # SATISFIED | POTENTIALLY_SATISFIED | MISSING_EVIDENCE | MORE_INFORMATION_REQUIRED |
    # POTENTIAL_GAP | NOT_APPLICABLE | CONFLICTING_EVIDENCE | REQUIRES_EXPERT_REVIEW
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    gap_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit provenance chain details
    provenance_chain: Mapped[dict] = mapped_column(JSON, default=dict)

    product: Mapped["Product"] = relationship("Product", back_populates="compliance_results")
