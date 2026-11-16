import uuid
import pytest
from httpx import AsyncClient

from app.models.policy import Policy
from app.models.repository import Repository
from app.models.review_run import ReviewRun


@pytest.mark.asyncio
async def test_auth_config(client: AsyncClient):
    """Test public auth config endpoint."""
    res = await client.get("/api/v1/auth/config")
    assert res.status_code == 200
    data = res.json()
    assert "oauth_configured" in data
    assert "is_dev_mode" in data
    assert data["is_dev_mode"] is True


@pytest.mark.asyncio
async def test_dev_login_and_me_endpoint(client: AsyncClient):
    """Test development login and token validation via /me."""
    # 1. Dev login
    login_payload = {
        "username": "sarah-engineer",
        "github_user_id": 888123,
        "installation_ids": [45678, 98765],
    }
    res_login = await client.post("/api/v1/auth/dev-login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["username"] == "sarah-engineer"
    assert login_data["user"]["github_user_id"] == 888123
    assert set(login_data["user"]["installation_ids"]) == {45678, 98765}

    token = login_data["access_token"]

    # 2. Call /me with valid token
    res_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["username"] == "sarah-engineer"
    assert set(me_data["installation_ids"]) == {45678, 98765}

    # 3. Call /me without token -> 401
    res_no_auth = await client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401

    # 4. Call /me with invalid token -> 401
    res_bad_auth = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res_bad_auth.status_code == 401


@pytest.mark.asyncio
async def test_multi_tenant_repository_and_review_isolation(client: AsyncClient, db_session):
    """Verify that User A cannot see or access User B's repositories or reviews."""
    # 1. Create two repositories with different GitHub App installation IDs
    repo_alice = Repository(
        github_repo_id=101010,
        full_name="alice-org/secure-service",
        installation_id=11111,
        is_active=True,
    )
    repo_bob = Repository(
        github_repo_id=202020,
        full_name="bob-org/payments-api",
        installation_id=22222,
        is_active=True,
    )
    db_session.add_all([repo_alice, repo_bob])
    await db_session.flush()

    # Add policies
    policy_alice = Policy(repository_id=repo_alice.id, fail_on_severity="HIGH", prohibited_licenses=[])
    policy_bob = Policy(repository_id=repo_bob.id, fail_on_severity="CRITICAL", prohibited_licenses=[])
    db_session.add_all([policy_alice, policy_bob])

    # Add reviews
    review_alice = ReviewRun(
        repository_id=repo_alice.id,
        pull_number=1,
        commit_sha="alice111",
        title="Alice PR",
        pr_author="alice",
        status="COMPLETED",
        verdict="APPROVE",
    )
    review_bob = ReviewRun(
        repository_id=repo_bob.id,
        pull_number=2,
        commit_sha="bob222",
        title="Bob PR",
        pr_author="bob",
        status="COMPLETED",
        verdict="REQUEST_CHANGES",
    )
    db_session.add_all([review_alice, review_bob])
    await db_session.commit()

    # 2. Login Alice (access to installation 11111)
    res_alice_login = await client.post(
        "/api/v1/auth/dev-login",
        json={"username": "alice", "github_user_id": 111, "installation_ids": [11111]},
    )
    token_alice = res_alice_login.json()["access_token"]
    headers_alice = {"Authorization": f"Bearer {token_alice}"}

    # 3. Login Bob (access to installation 22222)
    res_bob_login = await client.post(
        "/api/v1/auth/dev-login",
        json={"username": "bob", "github_user_id": 222, "installation_ids": [22222]},
    )
    token_bob = res_bob_login.json()["access_token"]
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    # 4. Verify Alice only sees Alice's repository
    res_repos_alice = await client.get("/api/v1/repositories", headers=headers_alice)
    assert res_repos_alice.status_code == 200
    alice_repos = res_repos_alice.json()
    assert len(alice_repos) == 1
    assert alice_repos[0]["full_name"] == "alice-org/secure-service"

    # 5. Verify Bob only sees Bob's repository
    res_repos_bob = await client.get("/api/v1/repositories", headers=headers_bob)
    assert res_repos_bob.status_code == 200
    bob_repos = res_repos_bob.json()
    assert len(bob_repos) == 1
    assert bob_repos[0]["full_name"] == "bob-org/payments-api"

    # 6. Verify Alice only sees Alice's reviews
    res_reviews_alice = await client.get("/api/v1/reviews", headers=headers_alice)
    assert res_reviews_alice.status_code == 200
    alice_reviews = res_reviews_alice.json()
    assert len(alice_reviews) == 1
    assert alice_reviews[0]["commit_sha"] == "alice111"

    # 7. Verify Alice CANNOT view Bob's review details -> 404
    res_forbidden_review = await client.get(f"/api/v1/reviews/{review_bob.id}", headers=headers_alice)
    assert res_forbidden_review.status_code == 404

    # 8. Verify Alice CANNOT view Bob's policy -> 404
    res_forbidden_policy = await client.get(
        f"/api/v1/repositories/{repo_bob.id}/policy", headers=headers_alice
    )
    assert res_forbidden_policy.status_code == 404

    # 9. Verify anonymous request without auth returns empty list (zero cross-tenant leakage)
    res_anon = await client.get("/api/v1/repositories")
    assert res_anon.status_code == 200
    assert res_anon.json() == []

    res_anon_reviews = await client.get("/api/v1/reviews")
    assert res_anon_reviews.status_code == 200
    assert res_anon_reviews.json() == []
