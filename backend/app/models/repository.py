import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.policy import Policy
    from app.models.review_run import ReviewRun


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    github_repo_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    installation_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    policy: Mapped[Optional["Policy"]] = relationship(
        "Policy",
        back_populates="repository",
        uselist=False,
        cascade="all, delete-orphan",
    )
    review_runs: Mapped[List["ReviewRun"]] = relationship(
        "ReviewRun",
        back_populates="repository",
        cascade="all, delete-orphan",
        order_by="desc(ReviewRun.created_at)",
    )

