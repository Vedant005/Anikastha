from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    login: str
    id: Optional[int] = None
    avatar_url: Optional[str] = None


class GitHubBranchRef(BaseModel):
    sha: str
    ref: str


class GitHubPullRequestData(BaseModel):
    number: int
    title: str = ""
    user: GitHubUser
    head: GitHubBranchRef
    base: GitHubBranchRef
    diff_url: Optional[str] = None
    state: str = "open"


class GitHubRepositoryData(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool = False


class GitHubInstallationData(BaseModel):
    id: int


class GitHubWebhookPayload(BaseModel):
    action: str
    number: Optional[int] = None
    pull_request: Optional[GitHubPullRequestData] = None
    repository: GitHubRepositoryData
    installation: Optional[GitHubInstallationData] = None
    sender: Optional[GitHubUser] = None

