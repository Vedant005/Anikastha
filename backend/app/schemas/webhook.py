from pydantic import BaseModel


class GitHubUser(BaseModel):
    login: str
    id: int | None = None
    avatar_url: str | None = None


class GitHubBranchRef(BaseModel):
    sha: str
    ref: str


class GitHubPullRequestData(BaseModel):
    number: int
    title: str = ""
    user: GitHubUser
    head: GitHubBranchRef
    base: GitHubBranchRef
    diff_url: str | None = None
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
    number: int | None = None
    pull_request: GitHubPullRequestData | None = None
    repository: GitHubRepositoryData
    installation: GitHubInstallationData | None = None
    sender: GitHubUser | None = None
