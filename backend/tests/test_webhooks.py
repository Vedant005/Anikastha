import hashlib
import hmac
import json
from unittest.mock import AsyncMock
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.policy import Policy
from app.models.repository import Repository
from app.models.review_run import ReviewRun


def sign_payload(payload_bytes: bytes, secret: str = "test_webhook_secret_key_123") -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_webhook_ping(client: AsyncClient):
    payload = json.dumps({"zen": "Keep it logically awesome."}).encode("utf-8")
    sig = sign_payload(payload)

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Delivery": "test-delivery-uuid-1",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pong"
    assert data["delivery"] == "test-delivery-uuid-1"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_rejected(client: AsyncClient):
    payload = json.dumps({"action": "opened"}).encode("utf-8")
    invalid_sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": invalid_sig,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401
    assert "Invalid X-Hub-Signature-256" in response.json()["detail"]


@pytest.mark.asyncio
async def test_webhook_pr_opened_enqueues_review(client: AsyncClient, db_session, mock_arq_pool):
    payload_data = {
        "action": "opened",
        "number": 101,
        "pull_request": {
            "number": 101,
            "title": "Add authentication router",
            "state": "open",
            "user": {"login": "octocat"},
            "head": {"sha": "headsha123456", "ref": "feature/auth"},
            "base": {"sha": "baseshaabcdef", "ref": "main"},
        },
        "repository": {
            "id": 999888,
            "name": "super-app",
            "full_name": "octocat/super-app",
            "private": False,
        },
        "installation": {
            "id": 54321,
        },
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = sign_payload(payload_bytes)

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload_bytes,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Delivery": "pr-delivery-101",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["repository"] == "octocat/super-app"
    assert data["pull_number"] == 101
    assert "run_id" in data

    # Verify database persistence
    res = await db_session.execute(
        select(Repository).where(Repository.github_repo_id == 999888)
    )
    repo = res.scalar_one_or_none()
    assert repo is not None
    assert repo.full_name == "octocat/super-app"
    assert repo.installation_id == 54321

    # Verify default policy was created
    res_policy = await db_session.execute(
        select(Policy).where(Policy.repository_id == repo.id)
    )
    policy = res_policy.scalar_one_or_none()
    assert policy is not None
    assert policy.fail_on_severity == "HIGH"
    assert policy.block_prohibited_licenses is True

    # Verify review_run record was created with status PENDING
    res_run = await db_session.execute(
        select(ReviewRun).where(ReviewRun.pull_number == 101)
    )
    run = res_run.scalar_one_or_none()
    assert run is not None
    assert run.status == "PENDING"
    assert run.commit_sha == "headsha123456"

    # Verify ARQ job enqueued
    mock_arq_pool.enqueue_job.assert_called_once_with(
        "process_pull_request_review",
        run_id=str(run.id),
    )


@pytest.mark.asyncio
async def test_webhook_pr_unhandled_action_ignored(client: AsyncClient):
    payload_data = {
        "action": "closed",
        "number": 102,
        "repository": {"id": 1, "name": "a", "full_name": "o/a", "private": False},
    }
    payload_bytes = json.dumps(payload_data).encode("utf-8")
    sig = sign_payload(payload_bytes)

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload_bytes,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "ignored"
    assert data["action"] == "closed"

