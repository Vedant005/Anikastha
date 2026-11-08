import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.review_run import ReviewRun


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    review_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("review_runs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )  # CODE_SECURITY, DEPENDENCY_CVE, LICENSE
    severity: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False,
    )  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    line_start: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    line_end: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    code_snippet: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    suggestion_markdown: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    cve_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    package_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    current_version: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    fixed_version: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    verification_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    published_inline: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    review_run: Mapped["ReviewRun"] = relationship(
        "ReviewRun",
        back_populates="findings",
    )

