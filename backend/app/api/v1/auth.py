import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.jwt import create_access_token
from app.models.user import User, UserInstallation
from app.schemas.user import AuthExchangeRequest, DevLoginRequest, TokenResponse, UserRead

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/config", summary="Get Public Auth Configuration")
async def get_auth_config():
    """Returns whether GitHub OAuth is configured and the client ID."""
    return {
        "oauth_configured": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
        "client_id": settings.GITHUB_CLIENT_ID if settings.GITHUB_CLIENT_ID else None,
        "is_dev_mode": settings.ENVIRONMENT in ("development", "test"),
    }


@router.get("/github/login-url", summary="Get GitHub OAuth Login URL")
async def get_github_login_url():
    """Generates the GitHub OAuth authorization URL."""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth client ID is not configured on the server.",
        )
    url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&scope=read:user,user:email"
    )
    return {"url": url}


@router.post("/exchange", response_model=TokenResponse, summary="Exchange GitHub OAuth Code")
async def exchange_github_code(
    payload: AuthExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a GitHub OAuth temporary code for a PR-Sentinel JWT session token."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth client credentials are not configured.",
        )

    async with httpx.AsyncClient() as client:
        # 1. Exchange code for access token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": payload.code,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to communicate with GitHub OAuth service.",
            )

        token_data = token_resp.json()
        gh_access_token = token_data.get("access_token")
        if not gh_access_token:
            error_desc = token_data.get("error_description", "Invalid OAuth authorization code.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_desc,
            )

        # 2. Fetch authenticated GitHub user details
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {gh_access_token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "PR-Sentinel",
            },
        )
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve GitHub user profile.",
            )

        gh_user = user_resp.json()
        github_user_id = gh_user.get("id")
        username = gh_user.get("login")
        name = gh_user.get("name")
        email = gh_user.get("email")
        avatar_url = gh_user.get("avatar_url")

        # 3. Fetch user installations
        installations_resp = await client.get(
            "https://api.github.com/user/installations",
            headers={
                "Authorization": f"Bearer {gh_access_token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "PR-Sentinel",
            },
        )
        installation_ids: list[int] = []
        if installations_resp.status_code == 200:
            inst_data = installations_resp.json()
            installation_ids = [inst["id"] for inst in inst_data.get("installations", [])]

    # 4. Upsert User in database
    result = await db.execute(
        select(User).options(selectinload(User.installations)).where(User.github_user_id == github_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            github_user_id=github_user_id,
            username=username,
            name=name,
            email=email,
            avatar_url=avatar_url,
        )
        db.add(user)
        await db.flush()
        existing_inst_ids = set()
    else:
        user.username = username
        user.name = name
        user.email = email
        user.avatar_url = avatar_url
        existing_inst_ids = {inst.installation_id for inst in user.installations}

    # 5. Synchronize User Installations
    for inst_id in installation_ids:
        if inst_id not in existing_inst_ids:
            new_inst = UserInstallation(
                user_id=user.id,
                installation_id=inst_id,
                role="member",
            )
            db.add(new_inst)

    await db.commit()

    # 5b. Sync installations and repositories on-demand from GitHub API
    try:
        from app.github.sync import sync_all_for_user
        await sync_all_for_user(user, db)
    except Exception as sync_exc:
        logger.warning("Automatic post-login repository sync encountered warning: %s", sync_exc)

    # Re-fetch user with installations eagerly loaded
    refreshed_result = await db.execute(
        select(User).options(selectinload(User.installations)).where(User.id == user.id)
    )
    user = refreshed_result.scalar_one()

    # 6. Issue JWT session token
    token = create_access_token({
        "sub": str(user.id),
        "github_user_id": user.github_user_id,
        "username": user.username,
    })

    user_read = UserRead(
        id=user.id,
        github_user_id=user.github_user_id,
        username=user.username,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        installation_ids=[inst.installation_id for inst in user.installations],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_read,
    )


@router.post("/dev-login", response_model=TokenResponse, summary="Development & Test Login")
async def dev_login(
    payload: DevLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Convenience endpoint to authenticate in development or test mode without live GitHub OAuth."""
    if settings.ENVIRONMENT not in ("development", "test"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development login is disabled in production.",
        )

    # Upsert test user
    result = await db.execute(
        select(User)
        .options(selectinload(User.installations))
        .where(User.github_user_id == payload.github_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            github_user_id=payload.github_user_id,
            username=payload.username,
            name=payload.username.replace("-", " ").title(),
            email=f"{payload.username}@example.com",
            avatar_url=f"https://github.com/{payload.username}.png",
        )
        db.add(user)
        await db.flush()
        existing_inst_ids = set()
    else:
        user.username = payload.username
        existing_inst_ids = {inst.installation_id for inst in user.installations}

    # Upsert requested installations
    for inst_id in payload.installation_ids:
        if inst_id not in existing_inst_ids:
            db.add(
                UserInstallation(
                    user_id=user.id,
                    installation_id=inst_id,
                    role="admin",
                )
            )

    await db.commit()

    # 5b. Sync installations and repositories on-demand from GitHub API
    try:
        from app.github.sync import sync_all_for_user
        await sync_all_for_user(user, db)
    except Exception as sync_exc:
        logger.warning("Automatic post-login repository sync encountered warning: %s", sync_exc)

    # Re-fetch user with installations eagerly loaded
    refreshed_result = await db.execute(
        select(User).options(selectinload(User.installations)).where(User.id == user.id)
    )
    user = refreshed_result.scalar_one()

    token = create_access_token({
        "sub": str(user.id),
        "github_user_id": user.github_user_id,
        "username": user.username,
    })

    user_read = UserRead(
        id=user.id,
        github_user_id=user.github_user_id,
        username=user.username,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        installation_ids=[inst.installation_id for inst in user.installations],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_read,
    )


@router.get("/me", response_model=UserRead, summary="Get Current Authenticated User")
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Retrieve the currently authenticated user profile and authorized installation IDs."""
    return UserRead(
        id=current_user.id,
        github_user_id=current_user.github_user_id,
        username=current_user.username,
        name=current_user.name,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
        installation_ids=[inst.installation_id for inst in current_user.installations],
    )
