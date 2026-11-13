import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert data["environment"] == "test"


@pytest.mark.asyncio
async def test_cors_vercel_origin(client: AsyncClient):
    """Ensure Vercel origins are allowed by CORS."""
    response = await client.get("/healthz", headers={"Origin": "https://anikastha.vercel.app"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://anikastha.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"
