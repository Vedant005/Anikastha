import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.jwt import decode_access_token
from app.core.redis import get_arq_pool
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Extract authenticated User from Bearer token if present, otherwise return None."""
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        return None

    result = await db.execute(
        select(User).options(selectinload(User.installations)).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    return user


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """Enforce authentication; raise 401 if missing or invalid."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in with GitHub.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


__all__ = [
    "get_db",
    "get_arq_pool",
    "get_current_user",
    "get_current_user_optional",
]
