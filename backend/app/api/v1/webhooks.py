import json
import logging
from typing import Any, Dict
from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_arq_pool, get_db
from app.core.config import get_settings
from app.core.security import verify_github_signature
from app.models.policy import Policy
from app.models.repository import Repository
from app.models.review_run import ReviewRun
from app.schemas.webhook import GitHubWebhookPayload

logger = logging.getLogger("pr_sentinel.webhook")
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


@router.post(
    "/github",
    status_code=status.HTTP_202_ACCEPTED,
    summary="GitHub App Webhook Ingestion",
)
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: str | None = Header(None, alias="X-GitHub-Delivery"),
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool),
) -> Dict[str, Any]:
    """
    Ingests GitHub App Webhooks:
    1. Validates HMAC SHA-256 signature against raw body.
    2. Enqueues pull_request events to ARQ worker queue.
    3. Responds with HTTP 202 Accepted.
    """
    body_bytes = await request.body()

    # 1. HMAC Signature Verification
    if settings.GITHUB_WEBHOOK_SECRET:
        is_valid = verify_github_signature(
            payload_body=body_bytes,
            signature_header=x_hub_signature_256,
            secret=settings.GITHUB_WEBHOOK_SECRET,
        )
        if not is_valid:
            logger.warning("Invalid webhook signature received for delivery=%s", x_github_delivery)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-Hub-Signature-256 signature.",
            )

    # 2. Ping / Health check from GitHub
    if x_github_event == "ping":
        logger.info("GitHub ping event received for delivery=%s", x_github_delivery)
        return {"status": "pong", "delivery": x_github_delivery}

    # 3. Pull Request Events
    if x_github_event == "pull_request":
        try:
            payload_data = json.loads(body_bytes.decode("utf-8"))
            payload = GitHubWebhookPayload.model_validate(payload_data)
        except Exception as exc:
            logger.error("Failed to parse GitHub webhook payload: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid webhook JSON payload: {exc}",
            )

        action = payload.action
        if action not in ("opened", "synchronize", "reopened"):
            logger.info("Ignoring pull_request action: %s", action)
            return {"status": "ignored", "action": action}

        if not payload.pull_request or not payload.installation:
            logger.warning("Missing pull_request or installation object in webhook.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing pull_request or installation in payload.",
            )

        repo_data = payload.repository
        pr_data = payload.pull_request
        installation_id = payload.installation.id

        # Upsert Repository record
        result = await db.execute(
            select(Repository).where(Repository.github_repo_id == repo_data.id)
        )
        repo = result.scalar_one_or_none()

        if not repo:
            repo = Repository(
                github_repo_id=repo_data.id,
                full_name=repo_data.full_name,
                installation_id=installation_id,
                is_active=True,
            )
            db.add(repo)
            await db.flush()

            # Create default policy for new repository
            default_policy = Policy(
                repository_id=repo.id,
                fail_on_severity=settings.DEFAULT_FAIL_ON_SEVERITY,
                block_prohibited_licenses=settings.BLOCK_PROHIBITED_LICENSES,
                prohibited_licenses=settings.PROHIBITED_LICENSES,
                auto_request_changes=settings.AUTO_REQUEST_CHANGES,
            )
            db.add(default_policy)
            await db.flush()
        else:
            # Update installation_id or name in case it changed
            repo.installation_id = installation_id
            repo.full_name = repo_data.full_name

        # Create ReviewRun entry with status PENDING
        review_run = ReviewRun(
            repository_id=repo.id,
            pull_number=pr_data.number,
            commit_sha=pr_data.head.sha,
            title=pr_data.title,
            pr_author=pr_data.user.login,
            status="PENDING",
        )
        db.add(review_run)
        await db.commit()
        await db.refresh(review_run)

        # Enqueue ARQ job
        run_id_str = str(review_run.id)
        try:
            await arq_pool.enqueue_job("process_pull_request_review", run_id=run_id_str)
            logger.info(
                "Enqueued PR review job for %s #%d (run_id=%s)",
                repo.full_name,
                review_run.pull_number,
                run_id_str,
            )
        except Exception as queue_exc:
            logger.error("Failed to enqueue ARQ job: %s", queue_exc)
            # ReviewRun is stored in DB so it can be retried or picked up
            return {
                "status": "stored_queue_failed",
                "run_id": run_id_str,
                "warning": str(queue_exc),
            }

        return {
            "status": "queued",
            "run_id": run_id_str,
            "repository": repo.full_name,
            "pull_number": review_run.pull_number,
        }

    return {"status": "unhandled_event", "event": x_github_event}

