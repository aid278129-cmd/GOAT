from typing import Optional, List
from sqlalchemy import String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class DecisionRecord(Base):
    """Immutable audit record establishing the deterministic provenance of a compliance decision."""

    __tablename__ = "decision_records"

    product_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    standard_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    standard_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    clause_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    clause_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    requirement_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    rule_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decision_engine: Mapped[str] = mapped_column(String(100), default="DETERMINISTIC_RULE_ENGINE")
    llm_decision: Mapped[bool] = mapped_column(Boolean, default=False)

    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    inputs_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
