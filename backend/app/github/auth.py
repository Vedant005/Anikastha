import base64
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
import httpx
import jwt

from app.core.config import get_settings

settings = get_settings()

# In-memory cache for installation tokens: {installation_id: (token, expire_timestamp)}
_token_cache: Dict[int, tuple[str, float]] = {}


def get_private_key_bytes() -> bytes:
    """
    Retrieve the GitHub App RSA private key bytes from either:
    1. Base64-encoded environment variable (GITHUB_APP_PRIVATE_KEY_BASE64)
    2. File path (GITHUB_APP_PRIVATE_KEY_PATH)
    """
    if settings.GITHUB_APP_PRIVATE_KEY_BASE64:
        return base64.b64decode(settings.GITHUB_APP_PRIVATE_KEY_BASE64)

    key_path = Path(settings.GITHUB_APP_PRIVATE_KEY_PATH)
    if key_path.exists():
        return key_path.read_bytes()

    raise ValueError(
        f"GitHub App private key not found at '{settings.GITHUB_APP_PRIVATE_KEY_PATH}' "
        "and GITHUB_APP_PRIVATE_KEY_BASE64 is not set."
    )


def generate_app_jwt(
    app_id: Optional[str] = None,
    private_key_bytes: Optional[bytes] = None,
) -> str:
    """
    Generate an RS256 signed JWT for authenticating as the GitHub App.
    Token is valid for 10 minutes (with 60-second clock drift allowance).
    """
    app_id = app_id or settings.GITHUB_APP_ID
    if not app_id:
        raise ValueError("GITHUB_APP_ID must be configured to generate GitHub App JWT.")

    if private_key_bytes is None:
        private_key_bytes = get_private_key_bytes()

    now = int(time.time())
    payload = {
        "iat": now - 60,       # 1 minute in the past for clock drift
        "exp": now + (9 * 60), # 9 minutes in future (GitHub max 10 min)
        "iss": str(app_id),
    }

    token = jwt.encode(payload, private_key_bytes, algorithm="RS256")
    return token


async def get_installation_access_token(
    installation_id: int,
    client: Optional[httpx.AsyncClient] = None,
) -> str:
    """
    Get or refresh an installation access token for a specific installation ID.
    Caches tokens until 5 minutes before expiration.
    """
    now = time.time()
    if installation_id in _token_cache:
        token, expires_at = _token_cache[installation_id]
        if expires_at - now > 300:  # Valid for more than 5 minutes
            return token

    app_jwt = generate_app_jwt()
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    owns_client = client is None
    http_client = client or httpx.AsyncClient()
    try:
        response = await http_client.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        token = data["token"]
        expires_at_str = data["expires_at"]  # ISO-8601 string
        dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        expires_timestamp = dt.timestamp()

        _token_cache[installation_id] = (token, expires_timestamp)
        return token
    finally:
        if owns_client:
            await http_client.aclose()


def clear_token_cache() -> None:
    """Clear cached installation tokens."""
    _token_cache.clear()

