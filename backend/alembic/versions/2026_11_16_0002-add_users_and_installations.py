"""Add users and user_installations tables for multi-tenancy

Revision ID: 0002_add_users_and_installations
Revises: 0001_initial_schema
Create Date: 2026-11-16 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_add_users_and_installations"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("github_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_github_user_id", "users", ["github_user_id"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    # 2. User Installations table
    op.create_table(
        "user_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("installation_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "installation_id", name="uq_user_installation"),
    )
    op.create_index(
        "ix_user_installations_user_id", "user_installations", ["user_id"], unique=False
    )
    op.create_index(
        "ix_user_installations_installation_id",
        "user_installations",
        ["installation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("user_installations")
    op.drop_table("users")
