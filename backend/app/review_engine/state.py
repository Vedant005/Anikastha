import operator
from typing import Annotated, Any, Literal

from pydantic import BaseModel
from typing_extensions import TypedDict


class RawFinding(BaseModel):
    """Candidate security or compliance finding before adversarial verification."""

    category: Literal["CODE_SECURITY", "DEPENDENCY_CVE", "LICENSE"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    title: str
    description: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion_markdown: str | None = None
    cve_id: str | None = None
    package_name: str | None = None
    rule_id: str | None = None


class VerifiedFinding(BaseModel):
    """Finding that has passed the adversarial red-team verifier."""

    category: Literal["CODE_SECURITY", "DEPENDENCY_CVE", "LICENSE"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    title: str
    description: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion_markdown: str | None = None
    cve_id: str | None = None
    package_name: str | None = None
    is_verified: bool = True
    verification_reason: str = ""
    is_in_diff_hunk: bool = True
    confidence_score: float = 1.0


class ReviewState(TypedDict):
    """Typed LangGraph State shared across specialist, synthesizer, and verifier nodes."""

    repo_name: str
    pull_number: int
    commit_sha: str
    diff_files: list[dict[str, Any]]
    file_contexts: list[dict[str, Any]]
    dependencies: list[dict[str, Any]]
    vulnerabilities: list[dict[str, Any]]
    license_alerts: list[dict[str, Any]]
    policy: dict[str, Any]
    raw_findings: Annotated[list[RawFinding], operator.add]
    synthesized_findings: list[RawFinding]
    verified_findings: list[VerifiedFinding]
    verdict: str  # APPROVE, COMMENT, REQUEST_CHANGES
    summary_markdown: str
