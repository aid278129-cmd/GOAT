from typing import Optional
from sqlalchemy import String, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class RequirementEvidenceLink(Base):
    """Auditable first-class linkage between a Requirement and supporting Evidence.
    
    Answers deterministically: 'Why was this requirement marked SATISFIED?'
    Requirement -> Evidence -> Document -> Source -> Page/Excerpt -> Evaluation Rule -> Verdict.
    """

    __tablename__ = "requirement_evidence_links"

    assessment_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    requirement_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    # Linkage type: DIRECT_SUPPORT | CONTRADICTION | PARTIAL_SUPPORT | REFERENCE
    linkage_type: Mapped[str] = mapped_column(String(50), default="DIRECT_SUPPORT", nullable=False)
    # Relevance: PRIMARY | SECONDARY
    relevance: Mapped[str] = mapped_column(String(50), default="PRIMARY", nullable=False)
    linkage_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    supporting_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluation_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Rule result: PASS | FAIL | INCONCLUSIVE
    rule_result: Mapped[Optional[str]] = mapped_column(String(50), default="PASS", nullable=True)

    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
