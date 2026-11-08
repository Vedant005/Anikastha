import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List
from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.repository import Repository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    fail_on_severity: Mapped[str] = mapped_column(
        String(20),
        default="HIGH",
        nullable=False,
    )
    block_prohibited_licenses: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    prohibited_licenses: Mapped[List[str]] = mapped_column(
        JSON,
        default=lambda: ["GPL-3.0", "AGPL-3.0", "SSPL-1.0"],
        nullable=False,
    )
    auto_request_changes: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(
        "Repository",
        back_populates="policy",
    )

