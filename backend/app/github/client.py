import base64
from typing import Any

import httpx

from app.github.auth import get_installation_access_token


class GitHubClient:
    """
    Async client for GitHub REST API powered by GitHub App Installation Tokens.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, installation_id: int, client: httpx.AsyncClient | None = None):
        self.installation_id = installation_id
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._external_client:
            await self._client.aclose()

    async def _get_headers(self, accept: str = "application/vnd.github+json") -> dict[str, str]:
        token = await get_installation_access_token(self.installation_id, client=self._client)
        return {
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PR-Sentinel-Security-Reviewer",
        }

    async def get_pull_request(self, owner: str, repo: str, pull_number: int) -> dict[str, Any]:
        """Fetch PR metadata."""
        headers = await self._get_headers()
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def get_pull_request_diff(self, owner: str, repo: str, pull_number: int) -> str:
        """Fetch raw unified diff string of the PR."""
        headers = await self._get_headers(accept="application/vnd.github.v3.diff")
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}"
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    async def get_pull_request_files(
        self, owner: str, repo: str, pull_number: int
    ) -> list[dict[str, Any]]:
        """Fetch list of changed files and their patch hunks in the PR."""
        headers = await self._get_headers()
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}/files"
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> str | None:
        """Fetch and base64 decode a file's content at a specific ref/commit SHA."""
        headers = await self._get_headers()
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        response = await self._client.get(url, headers=headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        if data.get("encoding") == "base64" and "content" in data:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return None

    async def create_pull_request_review(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        commit_id: str,
        event: str,  # APPROVE, REQUEST_CHANGES, COMMENT
        body: str,
        comments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Create a GitHub PR review with a summary body and inline comments.
        Each comment: {"path": str, "line": int, "side": "RIGHT", "body": str}
        """
        headers = await self._get_headers()
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        payload: dict[str, Any] = {
            "commit_id": commit_id,
            "body": body,
            "event": event,
        }
        if comments:
            payload["comments"] = comments

        response = await self._client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
