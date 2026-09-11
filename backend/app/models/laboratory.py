from typing import Optional
from sqlalchemy import String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base


class Laboratory(Base):
    """BIS Recognized testing laboratory."""

    __tablename__ = "laboratories"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    location_city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    location_state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    is_nabl_accredited: Mapped[bool] = mapped_column(Boolean, default=True)
    is_bis_recognized: Mapped[bool] = mapped_column(Boolean, default=True)
    scope_standards: Mapped[list] = mapped_column(JSON, default=list)  # List of IS numbers accredited
