import uuid
from typing import List, Optional
from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_arq_pool, get_db
from app.models.review_run import ReviewRun
from app.schemas.review_run import ReviewRunRead

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get(
    "",
    response_model=List[ReviewRunRead],
    summary="List Review Runs",
)
async def list_reviews(
    repo_id: Optional[uuid.UUID] = Query(None, description="Filter by repository ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[ReviewRun]:
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
        select(ReviewRun)
        .options(selectinload(ReviewRun.findings))
        .where(ReviewRun.id == review_id)
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

