import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_optional, get_db
from app.models.policy import Policy
from app.models.repository import Repository
from app.models.user import User
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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    db: AsyncSession = Depends(get_db),
):
    """List connected GitHub repositories with multi-tenant scoping and ETag caching."""
    query = select(Repository).options(selectinload(Repository.policy))

    # Multi-tenant scoping: if user is authenticated, isolate by their installation IDs
    if current_user:
        user_inst_ids = [inst.installation_id for inst in current_user.installations]
        if not user_inst_ids:
            return []
        query = query.where(Repository.installation_id.in_(user_inst_ids))

    result = await db.execute(query.order_by(Repository.full_name))
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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    db: AsyncSession = Depends(get_db),
) -> Policy:
    """Retrieve security and licensing policy for a repository."""
    if current_user:
        repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = repo_result.scalar_one_or_none()
        user_inst_ids = [inst.installation_id for inst in current_user.installations]
        if not repo or repo.installation_id not in user_inst_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy for repository '{repo_id}' not found.",
            )

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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    db: AsyncSession = Depends(get_db),
) -> Policy:
    """Update security severity threshold and license rules for a repository."""
    if current_user:
        repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = repo_result.scalar_one_or_none()
        user_inst_ids = [inst.installation_id for inst in current_user.installations]
        if not repo or repo.installation_id not in user_inst_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository '{repo_id}' not found.",
            )

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
