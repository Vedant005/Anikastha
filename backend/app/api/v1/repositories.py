import hashlib
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.github.sync import sync_all_for_user
from app.models.policy import Policy
from app.models.repository import Repository
from app.models.user import User
from app.schemas.policy import PolicyRead, PolicyUpdate
from app.schemas.repository import RepositoryRead

logger = logging.getLogger("pr_sentinel.repositories")
router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get(
    "",
    response_model=list[RepositoryRead],
    summary="List Repositories",
)
async def list_repositories(
    request: Request,
    response: Response,
    sync: bool = Query(False, description="Trigger on-demand sync from GitHub API"),
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    db: AsyncSession = Depends(get_db),
):
    """List connected GitHub repositories with multi-tenant scoping and ETag caching."""
    # Unauthenticated requests have no tenant access -> return empty list
    if not current_user:
        return []

    user_inst_ids = [inst.installation_id for inst in current_user.installations]

    # If user has no installations in DB, or DB has 0 repositories, or sync requested:
    # Attempt an active on-demand synchronization with GitHub REST API
    should_sync = sync or not user_inst_ids
    if not should_sync:
        check_query = select(Repository.id).where(
            Repository.installation_id.in_(user_inst_ids),
            Repository.is_active == True,  # noqa: E712
        ).limit(1)
        has_any = (await db.execute(check_query)).scalar_one_or_none()
        if not has_any:
            should_sync = True

    if should_sync:
        try:
            await sync_all_for_user(current_user, db)
            user_inst_ids = [inst.installation_id for inst in current_user.installations]
        except Exception as exc:
            logger.warning("Active repository sync encountered warning: %s", exc)

    if not user_inst_ids:
        return []

    query = (
        select(Repository)
        .options(selectinload(Repository.policy))
        .where(Repository.installation_id.in_(user_inst_ids), Repository.is_active == True)  # noqa: E712
        .order_by(Repository.full_name)
    )

    result = await db.execute(query)
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
    if if_none_match and if_none_match == etag and not sync:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=60, stale-while-revalidate=300",
            },
        )

    return repos


@router.post(
    "/sync",
    response_model=list[RepositoryRead],
    summary="Sync Repositories from GitHub API",
)
async def sync_repositories_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    On-demand API synchronization:
    1. Discovers newly enrolled installations for the authenticated user.
    2. Queries GitHub API (GET /installation/repositories) to sync all repositories.
    3. Returns the refreshed repository list.
    """
    repos = await sync_all_for_user(current_user, db)
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
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view repository policy.",
        )

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
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update repository policy.",
        )

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
