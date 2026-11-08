import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.github.client import GitHubClient
from app.models.repository import Repository
from app.models.review_run import ReviewRun

logger = logging.getLogger("pr_sentinel.worker")


async def process_pull_request_review(ctx: dict[str, Any], run_id: str) -> dict[str, Any]:
    """
    ARQ Background Task: Process security review for a GitHub Pull Request.
    """
    logger.info("Starting PR review processing for run_id=%s", run_id)
    start_time = time.time()
    run_uuid = uuid.UUID(run_id)

    async with AsyncSessionLocal() as session:
        # Load ReviewRun with Repository and Policy
        result = await session.execute(
            select(ReviewRun)
            .options(selectinload(ReviewRun.repository).selectinload(Repository.policy))
            .where(ReviewRun.id == run_uuid)
        )
        review_run = result.scalar_one_or_none()

        if not review_run:
            logger.error("ReviewRun with id=%s not found.", run_id)
            return {"status": "error", "message": f"ReviewRun {run_id} not found"}

        # Update status to PROCESSING
        review_run.status = "PROCESSING"
        review_run.started_at = datetime.now(UTC)
        await session.commit()

        repo = review_run.repository
        if "/" in repo.full_name:
            owner, repo_name = repo.full_name.split("/", 1)
        else:
            owner, repo_name = "", repo.full_name

        try:
            # Initialize GitHub Client
            async with GitHubClient(installation_id=repo.installation_id) as gh_client:
                # Retrieve PR metadata
                pr_data = await gh_client.get_pull_request(
                    owner=owner, repo=repo_name, pull_number=review_run.pull_number
                )

                # Retrieve diff
                diff_text = await gh_client.get_pull_request_diff(
                    owner=owner, repo=repo_name, pull_number=review_run.pull_number
                )

                logger.info(
                    "Retrieved PR #%d diff for %s (length: %d chars)",
                    review_run.pull_number,
                    repo.full_name,
                    len(diff_text),
                )

                # Future phases (2-5) will plug in the full AST + LangGraph review here.
                # In Phase 1 foundation: complete baseline job lifecycle.
                execution_time = int((time.time() - start_time) * 1000)
                review_run.status = "COMPLETED"
                review_run.completed_at = datetime.now(UTC)
                review_run.execution_time_ms = execution_time
                review_run.summary_markdown = (
                    f"### 🛡️ PR-Sentinel Ingestion Complete\n\n"
                    f"- **Repository**: `{repo.full_name}`\n"
                    f"- **Pull Request**: `#{review_run.pull_number}`\n"
                    f"- **Base SHA**: `{pr_data.get('base', {}).get('sha', 'unknown')}`\n"
                    f"- **Head SHA**: `{review_run.commit_sha}`\n"
                    f"- **Diff Size**: {len(diff_text)} bytes\n\n"
                    f"Phase 1 pipeline validated successfully."
                )
                await session.commit()

                return {
                    "status": "success",
                    "run_id": run_id,
                    "execution_time_ms": execution_time,
                }

        except Exception as exc:
            logger.exception("Error processing PR review for run_id=%s: %s", run_id, exc)
            execution_time = int((time.time() - start_time) * 1000)
            review_run.status = "FAILED"
            review_run.error_message = str(exc)
            review_run.completed_at = datetime.now(UTC)
            review_run.execution_time_ms = execution_time
            await session.commit()
            return {"status": "failed", "run_id": run_id, "error": str(exc)}
