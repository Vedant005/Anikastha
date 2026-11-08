import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.repository import Repository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReviewRun(Base):
    __tablename__ = "review_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    pull_number: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )
    commit_sha: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False,
    )
    pr_author: Mapped[str] = mapped_column(
        String(100),
        default="",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        index=True,
        nullable=False,
    )  # PENDING, PROCESSING, COMPLETED, FAILED
    verdict: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )  # APPROVE, COMMENT, REQUEST_CHANGES
    total_findings: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    critical_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    high_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    medium_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    low_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    summary_markdown: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(
        "Repository",
        back_populates="review_runs",
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="review_run",
        cascade="all, delete-orphan",
        order_by="Finding.created_at",
    )

