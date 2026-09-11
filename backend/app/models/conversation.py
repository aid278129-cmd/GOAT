from typing import Optional
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class Conversation(Base):
    """Audit log of intelligent assistant dialogues and provenance clarifications."""

    __tablename__ = "conversations"

    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    product_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("products.id"), nullable=True)
    session_title: Mapped[str] = mapped_column(String(255), default="Compliance Assessment Session")
    messages: Mapped[list] = mapped_column(JSON, default=list)  # list of {role, content, citations, timestamp}
