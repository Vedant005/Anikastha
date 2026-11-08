import logging
from typing import Any

from app.github.client import GitHubClient
from app.review_engine.state import VerifiedFinding

logger = logging.getLogger("pr_sentinel.publisher")

SEVERITY_BADGES = {
    "CRITICAL": "🔴 Critical",
    "HIGH": "🟠 High",
    "MEDIUM": "🟡 Medium",
    "LOW": "🔵 Low",
    "INFO": "⚪ Info",
}


class GitHubReviewPublisher:
    """
    Formats and publishes verified PR security reviews and inline comments to GitHub.
    Guarantees coordinate safety to prevent HTTP 422 Unprocessable Entity errors.
    """

    def __init__(self, gh_client: GitHubClient):
        self.client = gh_client

    async def publish_review(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        commit_sha: str,
        verdict: str,
        summary_markdown: str,
        verified_findings: list[VerifiedFinding],
    ) -> dict[str, Any]:
        """
        Publish Pull Request Review with inline comments for in-hunk findings
        and executive summary markdown for top-level review.
        """
        inline_comments, non_hunk_findings = self.prepare_comments(verified_findings)

        # Append non-hunk findings to summary markdown if any exist
        full_summary = summary_markdown
        if non_hunk_findings:
            full_summary = self._append_non_hunk_findings(full_summary, non_hunk_findings)

        # GitHub review event mapping: APPROVE, REQUEST_CHANGES, COMMENT
        event = verdict
        if event not in ("APPROVE", "REQUEST_CHANGES", "COMMENT"):
            event = "COMMENT"

        # GitHub does not accept inline comments when event is APPROVE
        if event == "APPROVE" and inline_comments:
            event = "COMMENT"

        logger.info(
            "Publishing review for %s/%s #%d: event=%s, %d inline comments, %d non-hunk findings",
            owner,
            repo,
            pull_number,
            event,
            len(inline_comments),
            len(non_hunk_findings),
        )

        try:
            review_response = await self.client.create_pull_request_review(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
                commit_id=commit_sha,
                event=event,
                body=full_summary,
                comments=inline_comments if inline_comments else None,
            )
            return review_response

        except Exception as exc:
            logger.error(
                "Failed to post PR review with inline comments: %s. Retrying with summary comment only.",
                exc,
            )
            # Resilient fallback: If GitHub rejects inline comments (e.g. outdated diff),
            # publish review summary only without inline comments so the audit is never lost
            return await self.client.create_pull_request_review(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
                commit_id=commit_sha,
                event=event,
                body=full_summary,
                comments=None,
            )

    @classmethod
    def prepare_comments(
        cls, verified_findings: list[VerifiedFinding]
    ) -> tuple[list[dict[str, Any]], list[VerifiedFinding]]:
        """
        Separates findings into inline comments (inside diff hunks)
        and non-hunk findings (placed in summary).
        """
        inline_comments: list[dict[str, Any]] = []
        non_hunk_findings: list[VerifiedFinding] = []

        for f in verified_findings:
            if not f.is_verified:
                continue

            target_line = f.line_start or f.line_end
            if f.is_in_diff_hunk and target_line is not None and target_line > 0:
                comment_body = cls.format_inline_comment_body(f)
                inline_comments.append(
                    {
                        "path": f.file_path,
                        "line": target_line,
                        "side": "RIGHT",
                        "body": comment_body,
                    }
                )
            else:
                non_hunk_findings.append(f)

        return inline_comments, non_hunk_findings

    @classmethod
    def format_inline_comment_body(cls, finding: VerifiedFinding) -> str:
        """Format markdown body for an inline GitHub review comment."""
        badge = SEVERITY_BADGES.get(finding.severity, finding.severity)
        lines = [
            f"### {badge} — {finding.title}\n",
            f"**Category**: `{finding.category}`\n",
            f"{finding.description}\n",
        ]

        if finding.suggestion_markdown:
            sug = finding.suggestion_markdown.strip()
            # If already wrapped in ```suggestion, use as is, else wrap it
            if "```suggestion" in sug:
                lines.append(f"{sug}\n")
            else:
                lines.append(f"```suggestion\n{sug}\n```\n")

        lines.append(
            f"> 🛡️ *Verified by PR-Sentinel* — {finding.verification_reason or 'Validated security finding'}"
        )
        return "\n".join(lines)

    @classmethod
    def _append_non_hunk_findings(
        cls,
        summary: str,
        non_hunk_findings: list[VerifiedFinding],
    ) -> str:
        """Appends contextual findings that could not be commented inline."""
        appendix = [
            "\n---\n",
            "### 📌 Contextual / Non-Diff Findings",
            "The following verified findings exist in surrounding files or outside the direct PR diff lines:",
            "",
        ]

        for idx, f in enumerate(non_hunk_findings, start=1):
            badge = SEVERITY_BADGES.get(f.severity, f.severity)
            appendix.append(f"**{idx}. [{badge}] {f.title}**")
            appendix.append(f"- **File**: `{f.file_path}` (Line {f.line_start or 'N/A'})")
            appendix.append(f"- **Description**: {f.description}")
            if f.suggestion_markdown:
                appendix.append(f"```suggestion\n{f.suggestion_markdown.strip()}\n```")
            appendix.append("")

        return summary + "\n".join(appendix)
