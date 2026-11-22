import logging
from typing import Any

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.github.auth import generate_app_jwt, get_installation_access_token
from app.models.policy import Policy
from app.models.repository import Repository
from app.models.user import User, UserInstallation

logger = logging.getLogger("pr_sentinel.github.sync")
settings = get_settings()


async def _upsert_synced_repo(
    db: AsyncSession,
    repo_data: dict[str, Any],
    installation_id: int,
) -> Repository:
    """Helper to upsert a repository record and ensure default policy exists."""
    repo_id = repo_data["id"]
    full_name = repo_data["full_name"]
    is_private = repo_data.get("private", False)

    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.policy))
        .where(Repository.github_repo_id == repo_id)
    )
    repo = result.scalar_one_or_none()

    if not repo:
        repo = Repository(
            github_repo_id=repo_id,
            full_name=full_name,
            installation_id=installation_id,
            private=is_private,
            is_active=True,
        )
        db.add(repo)
        await db.flush()

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
        repo.installation_id = installation_id
        repo.full_name = full_name
        repo.private = is_private
        repo.is_active = True
        await db.flush()

    return repo


async def sync_user_installations_from_github(
    user: User,
    db: AsyncSession,
    client: httpx.AsyncClient | None = None,
) -> list[int]:
    """
    Query GitHub App installations (GET /app/installations) using GitHub App JWT.
    Match installations owned by the user (matching account.id or account.login)
    and record them in `user_installations` in the database.
    """
    if not settings.GITHUB_APP_ID:
        return [inst.installation_id for inst in user.installations]

    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=15.0)

    try:
        app_jwt = generate_app_jwt()
    except Exception as exc:
        logger.debug("Skipping GitHub App installations sync (JWT generation unavailable): %s", exc)
        if owns_client:
            await http_client.aclose()
        return [inst.installation_id for inst in user.installations]

    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PR-Sentinel-Security-Reviewer",
    }

    discovered_inst_ids: list[int] = []

    try:
        resp = await http_client.get("https://api.github.com/app/installations?per_page=100", headers=headers)
        if resp.status_code == 200:
            installations = resp.json()
            for inst in installations:
                inst_id = inst.get("id")
                acc = inst.get("account", {})
                acc_id = acc.get("id")
                acc_login = (acc.get("login") or "").lower()

                # Match if installation account matches user github_user_id or username
                matches_id = user.github_user_id and acc_id == user.github_user_id
                matches_login = user.username and acc_login == user.username.lower()

                if inst_id and (matches_id or matches_login):
                    discovered_inst_ids.append(inst_id)

            # Synchronize into user_installations
            existing_inst_ids = {inst.installation_id for inst in user.installations}
            for inst_id in discovered_inst_ids:
                if inst_id not in existing_inst_ids:
                    new_inst = UserInstallation(
                        user_id=user.id,
                        installation_id=inst_id,
                        role="admin",
                    )
                    db.add(new_inst)
                    user.installations.append(new_inst)

            if discovered_inst_ids:
                await db.commit()
                logger.info(
                    "Synced %d GitHub App installation(s) for user %s: %s",
                    len(discovered_inst_ids),
                    user.username,
                    discovered_inst_ids,
                )
    except Exception as exc:
        logger.warning("Failed to sync GitHub App installations for user %s: %s", user.username, exc)
    finally:
        if owns_client:
            await http_client.aclose()

    return [inst.installation_id for inst in user.installations]


async def sync_repositories_for_installation(
    installation_id: int,
    db: AsyncSession,
    client: httpx.AsyncClient | None = None,
) -> list[Repository]:
    """
    Fetch all repositories enrolled in a GitHub App installation directly
    from GitHub REST API (GET /installation/repositories) and upsert into DB.
    """
    if not settings.GITHUB_APP_ID:
        return []

    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=20.0)

    synced_repos: list[Repository] = []

    try:
        inst_token = await get_installation_access_token(installation_id, client=http_client)
        headers = {
            "Authorization": f"Bearer {inst_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PR-Sentinel-Security-Reviewer",
        }

        page = 1
        seen_repo_ids: set[int] = set()

        while True:
            url = f"https://api.github.com/installation/repositories?per_page=100&page={page}"
            resp = await http_client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.warning(
                    "GitHub API error fetching repositories for installation %d: HTTP %d %s",
                    installation_id,
                    resp.status_code,
                    resp.text,
                )
                break

            data = resp.json()
            repos_data = data.get("repositories", [])
            if not repos_data:
                break

            for r_data in repos_data:
                seen_repo_ids.add(r_data["id"])
                repo = await _upsert_synced_repo(
                    db=db,
                    repo_data=r_data,
                    installation_id=installation_id,
                )
                synced_repos.append(repo)

            # Check if all repositories fetched
            total_count = data.get("total_count", len(repos_data))
            if len(seen_repo_ids) >= total_count or len(repos_data) < 100:
                break
            page += 1

        # Mark removed repositories as inactive for this installation
        if seen_repo_ids:
            await db.execute(
                update(Repository)
                .where(
                    Repository.installation_id == installation_id,
                    Repository.github_repo_id.not_in(seen_repo_ids),
                )
                .values(is_active=False)
            )

        await db.commit()
        logger.info(
            "Successfully synced %d repository/repositories for installation %d",
            len(synced_repos),
            installation_id,
        )
    except Exception as exc:
        logger.warning(
            "Error syncing repositories from GitHub for installation %d: %s",
            installation_id,
            exc,
        )
    finally:
        if owns_client:
            await http_client.aclose()

    return synced_repos


async def sync_all_for_user(
    user: User,
    db: AsyncSession,
) -> list[Repository]:
    """
    Perform a complete discovery and sync:
    1. Query GitHub for any new or existing installations for this user.
    2. For each installation, fetch its repositories from GitHub and upsert to DB.
    3. Return all currently active repositories for the user.
    """
    async with httpx.AsyncClient(timeout=25.0) as client:
        inst_ids = await sync_user_installations_from_github(user, db, client=client)
        for inst_id in inst_ids:
            await sync_repositories_for_installation(inst_id, db, client=client)

    # Return refreshed active repositories from DB
    user_inst_ids = [inst.installation_id for inst in user.installations]
    if not user_inst_ids:
        return []

    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.policy))
        .where(Repository.installation_id.in_(user_inst_ids), Repository.is_active == True)  # noqa: E712
        .order_by(Repository.full_name)
    )
    return list(result.scalars().all())
