"""SQLAlchemy model for a simulated financial-service agent."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Agent(Base):
    """Represent one simulated agent outlet."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    area: Mapped[str] = mapped_column(
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