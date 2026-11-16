import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.policy import Policy
from app.models.repository import Repository
from app.schemas.policy import PolicyRead, PolicyUpdate
from app.schemas.repository import RepositoryRead

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get(
    "",
    response_model=list[RepositoryRead],
    summary="List Repositories",
)
async def list_repositories(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """List all connected GitHub repositories with ETag caching support."""
    result = await db.execute(
        select(Repository).options(selectinload(Repository.policy)).order_by(Repository.full_name)
    )
    repos = list(result.scalars().all())

    # Generate deterministic ETag based on IDs, update timestamps, and active flags
    etag_tokens = [
        f"{r.id}:{r.updated_at.isoformat()}:{r.is_active}:{r.policy.updated_at.isoformat() if r.policy else ''}"
        for r in repos
    ]
    raw_hash = hashlib.sha256(";".join(etag_tokens).encode("utf-8")).hexdigest()[:16]
    etag = f'"{raw_hash}"'

    # Set cache headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=60, stale-while-revalidate=300"

    # Evaluate conditional GET
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=60, stale-while-revalidate=300",
            },
        )

    return repos


@router.get(
    "/{repo_id}/policy",
    response_model=PolicyRead,
    summary="Get Repository Policy",
)
async def get_repository_policy(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Policy:
    """Retrieve security and licensing policy for a repository."""
    result = await db.execute(select(Policy).where(Policy.repository_id == repo_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy for repository '{repo_id}' not found.",
        )
    return policy


@router.put(
    "/{repo_id}/policy",
    response_model=PolicyRead,
    summary="Update Repository Policy",
)
async def update_repository_policy(
    repo_id: uuid.UUID,
    policy_update: PolicyUpdate,
    db: AsyncSession = Depends(get_db),
) -> Policy:
    """Update security severity threshold and license rules for a repository."""
    result = await db.execute(select(Policy).where(Policy.repository_id == repo_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy for repository '{repo_id}' not found.",
        )

    update_data = policy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    await db.commit()
    await db.refresh(policy)
    return policy
