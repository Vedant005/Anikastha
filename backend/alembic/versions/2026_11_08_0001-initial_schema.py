"""Initial database schema for repositories, policies, review_runs, findings

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Repositories table
    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("installation_id", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repositories_github_repo_id", "repositories", ["github_repo_id"], unique=True)
    op.create_index("ix_repositories_full_name", "repositories", ["full_name"], unique=False)
    op.create_index("ix_repositories_installation_id", "repositories", ["installation_id"], unique=False)

    # 2. Policies table
    op.create_table(
        "policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("fail_on_severity", sa.String(length=20), nullable=False, server_default="HIGH"),
        sa.Column("block_prohibited_licenses", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("prohibited_licenses", sa.JSON(), nullable=False),
        sa.Column("auto_request_changes", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Review Runs table
    op.create_table(
        "review_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pull_number", sa.Integer(), nullable=False),
        sa.Column("commit_sha", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("pr_author", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("verdict", sa.String(length=30), nullable=True),
        sa.Column("total_findings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_markdown", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_runs_repository_id", "review_runs", ["repository_id"], unique=False)
    op.create_index("ix_review_runs_pull_number", "review_runs", ["pull_number"], unique=False)
    op.create_index("ix_review_runs_status", "review_runs", ["status"], unique=False)

    # 4. Findings table
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("review_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("review_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("code_snippet", sa.Text(), nullable=True),
        sa.Column("suggestion_markdown", sa.Text(), nullable=True),
        sa.Column("cve_id", sa.String(length=100), nullable=True),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("current_version", sa.String(length=100), nullable=True),
        sa.Column("fixed_version", sa.String(length=100), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verification_reason", sa.Text(), nullable=True),
        sa.Column("published_inline", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_findings_review_run_id", "findings", ["review_run_id"], unique=False)
    op.create_index("ix_findings_category", "findings", ["category"], unique=False)
    op.create_index("ix_findings_severity", "findings", ["severity"], unique=False)


def downgrade() -> None:
    op.drop_table("findings")
    op.drop_table("review_runs")
    op.drop_table("policies")
    op.drop_table("repositories")

