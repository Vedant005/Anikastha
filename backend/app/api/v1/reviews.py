import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_arq_pool, get_db
from app.models.review_run import ReviewRun
from app.schemas.review_run import ReviewRunRead

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get(
    "",
    response_model=list[ReviewRunRead],
    summary="List Review Runs",
)
async def list_reviews(
    repo_id: uuid.UUID | None = Query(None, description="Filter by repository ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[ReviewRun]:
    """Retrieve paginated list of recent review runs."""
    query = (
        select(ReviewRun)
        .options(selectinload(ReviewRun.findings))
        .order_by(ReviewRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if repo_id:
        query = query.where(ReviewRun.repository_id == repo_id)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{review_id}",
    response_model=ReviewRunRead,
    summary="Get Review Details",
)
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReviewRun:
    """Retrieve detailed information and findings for a specific review run."""
    result = await db.execute(
        select(ReviewRun).options(selectinload(ReviewRun.findings)).where(ReviewRun.id == review_id)
    )
    review_run = result.scalar_one_or_none()
    if not review_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review run '{review_id}' not found.",
        )
    return review_run


@router.post(
    "/{review_id}/rerun",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Review Rerun",
)
async def rerun_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool),
):
    """Manually trigger a re-run of an existing PR review."""
    result = await db.execute(select(ReviewRun).where(ReviewRun.id == review_id))
    review_run = result.scalar_one_or_none()
    if not review_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review run '{review_id}' not found.",
        )

    review_run.status = "PENDING"
    review_run.error_message = None
    await db.commit()

    await arq_pool.enqueue_job("process_pull_request_review", run_id=str(review_id))
    return {"status": "queued", "run_id": str(review_id)}


@router.get(
    "/{review_id}/events",
    summary="Live Review Event Stream (SSE)",
)
async def stream_review_events(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream real-time status updates for a review run via Server-Sent Events."""

    async def event_generator() -> AsyncGenerator[str, None]:
        max_iterations = 60  # max 2 minutes of streaming
        for _ in range(max_iterations):
            result = await db.execute(
                select(ReviewRun)
                .options(selectinload(ReviewRun.findings))
                .where(ReviewRun.id == review_id)
            )
            run = result.scalar_one_or_none()
            if not run:
                yield f"data: {json.dumps({'error': 'not_found'})}\n\n"
                break

            payload = {
                "id": str(run.id),
                "status": run.status,
                "verdict": run.verdict,
                "total_findings": run.total_findings,
                "critical_count": run.critical_count,
                "high_count": run.high_count,
                "medium_count": run.medium_count,
                "low_count": run.low_count,
                "execution_time_ms": run.execution_time_ms,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if run.status in ("COMPLETED", "FAILED"):
                break

            await asyncio.sleep(1.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
