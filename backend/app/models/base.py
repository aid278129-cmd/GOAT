import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative model with UUID primary keys and standard UTC audit timestamps."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __init__(self, **kwargs):
        """Initialize instance and populate column defaults in Python memory."""
        if hasattr(self, "__table__"):
            for col in self.__table__.columns:
                if col.key not in kwargs and col.default is not None:
                    try:
                        kwargs[col.key] = col.default.arg(None) if callable(col.default.arg) else col.default.arg
                    except Exception:
                        pass
        for k, v in kwargs.items():
            setattr(self, k, v)
