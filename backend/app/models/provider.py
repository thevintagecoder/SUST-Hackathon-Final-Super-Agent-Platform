"""SQLAlchemy model for a synthetic financial-service provider."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Provider(Base):
    """Represent one synthetic financial-service provider."""

    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )