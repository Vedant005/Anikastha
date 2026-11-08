import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import jwt
import pytest

from app.github.auth import (
    clear_token_cache,
    generate_app_jwt,
    get_installation_access_token,
)


def test_generate_app_jwt(rsa_key_pair):
    pem_bytes, public_key = rsa_key_pair
    app_id = "98765"

    token = generate_app_jwt(app_id=app_id, private_key_bytes=pem_bytes)
    assert token is not None

    # Decode and verify token using public key
    decoded = jwt.decode(token, public_key, algorithms=["RS256"])
    assert decoded["iss"] == "98765"
    now = int(time.time())
    # iat is approx now - 60, exp is approx now + 540
    assert abs(decoded["iat"] - (now - 60)) < 10
    assert abs(decoded["exp"] - (now + 540)) < 10


@pytest.mark.asyncio
async def test_get_installation_access_token(rsa_key_pair):
    pem_bytes, _ = rsa_key_pair
    clear_token_cache()

    mock_response = {
        "token": "ghs_test_token_abcdef123456",
        "expires_at": "2030-01-01T00:00:00Z",
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    response_mock = AsyncMock()
    response_mock.json = (
        MagicMock(return_value=mock_response)
        if hasattr(MagicMock, "return_value")
        else lambda: mock_response
    )
    response_mock.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=response_mock)

    with patch("app.github.auth.generate_app_jwt", return_value="mock_jwt"):
        token = await get_installation_access_token(installation_id=1234, client=mock_client)
        assert token == "ghs_test_token_abcdef123456"

        # Verify caching: second call within validity period should NOT make another HTTP call
        token2 = await get_installation_access_token(installation_id=1234, client=mock_client)
        assert token2 == "ghs_test_token_abcdef123456"
        assert mock_client.post.call_count == 1
