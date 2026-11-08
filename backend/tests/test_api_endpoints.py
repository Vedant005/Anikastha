import uuid

import pytest
from httpx import AsyncClient

from app.models.policy import Policy
from app.models.repository import Repository
from app.models.review_run import ReviewRun


@pytest.mark.asyncio
async def test_repositories_and_policy_endpoints(client: AsyncClient, db_session):
    # 1. Seed Repository
    repo = Repository(
        github_repo_id=123456,
        full_name="test-org/sentinel-demo",
        installation_id=98765,
        is_active=True,
    )
    db_session.add(repo)
    await db_session.flush()

    # Seed Policy
    policy = Policy(
        repository_id=repo.id,
        fail_on_severity="HIGH",
        block_prohibited_licenses=True,
        prohibited_licenses=["GPL-3.0"],
        auto_request_changes=True,
    )
    db_session.add(policy)
    await db_session.commit()

    # 2. List repositories
    res = await client.get("/api/v1/repositories")
    assert res.status_code == 200
    repos = res.json()
    assert len(repos) >= 1
    assert any(r["full_name"] == "test-org/sentinel-demo" for r in repos)

    # 3. Get repository policy
    res_pol = await client.get(f"/api/v1/repositories/{repo.id}/policy")
    assert res_pol.status_code == 200
    pol_data = res_pol.json()
    assert pol_data["fail_on_severity"] == "HIGH"
    assert "GPL-3.0" in pol_data["prohibited_licenses"]

    # 4. Update repository policy
    res_update = await client.put(
        f"/api/v1/repositories/{repo.id}/policy",
        json={"fail_on_severity": "CRITICAL", "auto_request_changes": False},
    )
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["fail_on_severity"] == "CRITICAL"
    assert updated_data["auto_request_changes"] is False

    # 5. Non-existent policy returns 404
    non_existent_id = uuid.uuid4()
    res_404 = await client.get(f"/api/v1/repositories/{non_existent_id}/policy")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_review_run_endpoints(client: AsyncClient, db_session, mock_arq_pool):
    # 1. Seed Repository & ReviewRun
    repo = Repository(
        github_repo_id=555111,
        full_name="acme/api-core",
        installation_id=111222,
        is_active=True,
    )
    db_session.add(repo)
    await db_session.flush()

    run = ReviewRun(
        repository_id=repo.id,
        pull_number=42,
        commit_sha="abcdef1234567890",
        title="Refactor auth",
        pr_author="alice",
        status="COMPLETED",
        verdict="APPROVE",
    )
    db_session.add(run)
    await db_session.commit()

    # 2. List reviews
    res = await client.get("/api/v1/reviews")
    assert res.status_code == 200
    reviews = res.json()
    assert len(reviews) >= 1
    assert any(r["pull_number"] == 42 for r in reviews)

    # Filter by repo_id
    res_filtered = await client.get(f"/api/v1/reviews?repo_id={repo.id}")
    assert res_filtered.status_code == 200
    assert len(res_filtered.json()) == 1

    # 3. Get specific review details
    res_detail = await client.get(f"/api/v1/reviews/{run.id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["commit_sha"] == "abcdef1234567890"

    # 4. Non-existent review returns 404
    res_not_found = await client.get(f"/api/v1/reviews/{uuid.uuid4()}")
    assert res_not_found.status_code == 404

    # 5. Rerun review
    res_rerun = await client.post(f"/api/v1/reviews/{run.id}/rerun")
    assert res_rerun.status_code == 202
    assert res_rerun.json()["status"] == "queued"
    mock_arq_pool.enqueue_job.assert_called_with("process_pull_request_review", run_id=str(run.id))
