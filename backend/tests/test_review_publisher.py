from unittest.mock import AsyncMock

import pytest

from app.github.client import GitHubClient
from app.github.publisher import GitHubReviewPublisher
from app.review_engine.state import VerifiedFinding


def test_format_inline_comment_body():
    finding = VerifiedFinding(
        category="CODE_SECURITY",
        severity="CRITICAL",
        title="SQL Injection in auth",
        description="Direct f-string formatting in SQL query",
        file_path="app/auth.py",
        line_start=25,
        line_end=25,
        suggestion_markdown='cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
        verification_reason="Confirmed parameter concatenation",
    )

    body = GitHubReviewPublisher.format_inline_comment_body(finding)

    assert "🔴 Critical" in body
    assert "SQL Injection in auth" in body
    assert "Direct f-string formatting" in body
    assert "```suggestion" in body
    assert "cursor.execute" in body
    assert "Verified by PR-Sentinel" in body


def test_prepare_comments_separation():
    in_hunk = VerifiedFinding(
        category="CODE_SECURITY",
        severity="HIGH",
        title="Command Injection",
        description="os.system call",
        file_path="app/main.py",
        line_start=12,
        is_in_diff_hunk=True,
        is_verified=True,
    )
    out_of_hunk = VerifiedFinding(
        category="CODE_SECURITY",
        severity="MEDIUM",
        title="Exposed Secret in config",
        description="Hardcoded API key in settings",
        file_path="app/config.py",
        line_start=5,
        is_in_diff_hunk=False,  # outside hunk
        is_verified=True,
    )
    unverified = VerifiedFinding(
        category="CODE_SECURITY",
        severity="LOW",
        title="Theoretical Race Condition",
        description="False positive",
        file_path="app/main.py",
        line_start=14,
        is_in_diff_hunk=True,
        is_verified=False,  # rejected by verifier
    )

    inline_comments, non_hunk = GitHubReviewPublisher.prepare_comments(
        [in_hunk, out_of_hunk, unverified]
    )

    # Only verified in-hunk finding is placed inline
    assert len(inline_comments) == 1
    assert inline_comments[0]["path"] == "app/main.py"
    assert inline_comments[0]["line"] == 12
    assert inline_comments[0]["side"] == "RIGHT"

    # Out-of-hunk finding is routed to non_hunk list for summary appendix
    assert len(non_hunk) == 1
    assert non_hunk[0].title == "Exposed Secret in config"


@pytest.mark.asyncio
async def test_publish_review_request_changes():
    mock_gh_client = AsyncMock(spec=GitHubClient)
    mock_gh_client.create_pull_request_review = AsyncMock(
        return_value={"id": 1001, "state": "CHANGES_REQUESTED"}
    )

    publisher = GitHubReviewPublisher(mock_gh_client)

    finding = VerifiedFinding(
        category="CODE_SECURITY",
        severity="HIGH",
        title="Path Traversal",
        description="Unsanitized file path",
        file_path="app/files.py",
        line_start=30,
        is_in_diff_hunk=True,
        is_verified=True,
    )

    res = await publisher.publish_review(
        owner="acme",
        repo="webapp",
        pull_number=15,
        commit_sha="commit_sha_123",
        verdict="REQUEST_CHANGES",
        summary_markdown="## 🛡️ Audit Summary\nIssues found.",
        verified_findings=[finding],
    )

    assert res["state"] == "CHANGES_REQUESTED"
    mock_gh_client.create_pull_request_review.assert_called_once()
    kwargs = mock_gh_client.create_pull_request_review.call_args.kwargs
    assert kwargs["owner"] == "acme"
    assert kwargs["repo"] == "webapp"
    assert kwargs["pull_number"] == 15
    assert kwargs["event"] == "REQUEST_CHANGES"
    assert len(kwargs["comments"]) == 1
    assert kwargs["comments"][0]["path"] == "app/files.py"
    assert kwargs["comments"][0]["line"] == 30


@pytest.mark.asyncio
async def test_publish_review_approve_clean():
    mock_gh_client = AsyncMock(spec=GitHubClient)
    mock_gh_client.create_pull_request_review = AsyncMock(
        return_value={"id": 1002, "state": "APPROVED"}
    )

    publisher = GitHubReviewPublisher(mock_gh_client)

    res = await publisher.publish_review(
        owner="acme",
        repo="webapp",
        pull_number=16,
        commit_sha="clean_sha_456",
        verdict="APPROVE",
        summary_markdown="## 🛡️ Audit Summary\nClean PR.",
        verified_findings=[],
    )

    assert res["state"] == "APPROVED"
    mock_gh_client.create_pull_request_review.assert_called_once()
    kwargs = mock_gh_client.create_pull_request_review.call_args.kwargs
    assert kwargs["event"] == "APPROVE"
    assert kwargs["comments"] is None


@pytest.mark.asyncio
async def test_publish_review_fallback_on_inline_error():
    """If GitHub returns 422 on inline comments, publisher gracefully falls back to summary only."""
    mock_gh_client = AsyncMock(spec=GitHubClient)

    # First call with comments raises error; second call without comments succeeds
    mock_gh_client.create_pull_request_review = AsyncMock(
        side_effect=[
            Exception("HTTP 422 Unprocessable Entity: line not in diff"),
            {"id": 1003, "state": "COMMENTED"},
        ]
    )

    publisher = GitHubReviewPublisher(mock_gh_client)

    finding = VerifiedFinding(
        category="CODE_SECURITY",
        severity="MEDIUM",
        title="Deprecated API",
        description="Outdated method used",
        file_path="app/api.py",
        line_start=10,
        is_in_diff_hunk=True,
        is_verified=True,
    )

    res = await publisher.publish_review(
        owner="acme",
        repo="webapp",
        pull_number=17,
        commit_sha="sha_789",
        verdict="COMMENT",
        summary_markdown="## 🛡️ Audit Summary",
        verified_findings=[finding],
    )

    assert res["state"] == "COMMENTED"
    assert mock_gh_client.create_pull_request_review.call_count == 2
    # Second call had comments=None
    second_call_kwargs = mock_gh_client.create_pull_request_review.call_args_list[1].kwargs
    assert second_call_kwargs["comments"] is None
