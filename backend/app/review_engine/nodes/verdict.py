import logging
from typing import Any

from app.review_engine.state import ReviewState, VerifiedFinding

logger = logging.getLogger("pr_sentinel.verdict")


async def verdict_node(state: ReviewState) -> dict[str, Any]:
    """
    LangGraph node: Computes overall PR review verdict and generates executive summary.
    """
    verified = state.get("verified_findings", [])
    policy = state.get("policy", {})

    fail_on_severity = policy.get("fail_on_severity", "HIGH").upper()
    block_licenses = policy.get("block_prohibited_licenses", True)
    auto_request_changes = policy.get("auto_request_changes", True)

    severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    threshold_rank = severity_rank.get(fail_on_severity, 3)

    critical_count = sum(1 for f in verified if f.severity == "CRITICAL")
    high_count = sum(1 for f in verified if f.severity == "HIGH")
    medium_count = sum(1 for f in verified if f.severity == "MEDIUM")
    low_count = sum(1 for f in verified if f.severity == "LOW")

    has_policy_failing_severity = any(
        severity_rank.get(f.severity, 0) >= threshold_rank for f in verified
    )
    has_prohibited_license = any(f.category == "LICENSE" and block_licenses for f in verified)

    should_block = has_policy_failing_severity or has_prohibited_license

    if should_block:
        verdict = "REQUEST_CHANGES" if auto_request_changes else "COMMENT"
    elif verified:
        verdict = "COMMENT"
    else:
        verdict = "APPROVE"

    summary_markdown = _generate_summary_markdown(
        repo_name=state.get("repo_name", ""),
        pull_number=state.get("pull_number", 0),
        verdict=verdict,
        verified_findings=verified,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
    )

    logger.info("Verdict calculated: %s (total verified findings: %d)", verdict, len(verified))
    return {
        "verdict": verdict,
        "summary_markdown": summary_markdown,
    }


def _generate_summary_markdown(
    repo_name: str,
    pull_number: int,
    verdict: str,
    verified_findings: list[VerifiedFinding],
    critical_count: int,
    high_count: int,
    medium_count: int,
    low_count: int,
) -> str:
    verdict_emoji = {
        "APPROVE": "✅ Approved",
        "COMMENT": "💬 Advisory Comments",
        "REQUEST_CHANGES": "🚨 Changes Requested",
    }.get(verdict, "ℹ️ Review Complete")

    lines = [
        f"## 🛡️ PR-Sentinel Security Review — {verdict_emoji}\n",
        f"**Repository**: `{repo_name}` | **PR**: `#{pull_number}`\n",
        "### 📊 Security Findings Summary",
        "| Severity | Count | Status |",
        "| :--- | :---: | :--- |",
        f"| 🔴 Critical | {critical_count} | {'Blocker' if critical_count > 0 else 'Clean'} |",
        f"| 🟠 High | {high_count} | {'Action Required' if high_count > 0 else 'Clean'} |",
        f"| 🟡 Medium | {medium_count} | {'Review Suggested' if medium_count > 0 else 'Clean'} |",
        f"| 🔵 Low / Info | {low_count} | Advisory |",
        "",
    ]

    if not verified_findings:
        lines.append(
            "> ✨ **No security vulnerabilities or license compliance issues detected!** Great job!"
        )
        return "\n".join(lines)

    lines.append("### 🔍 Verified Findings")
    for idx, f in enumerate(verified_findings, start=1):
        lines.append(f"#### {idx}. [{f.severity}] {f.title}")
        lines.append(
            f"- **Category**: `{f.category}` | **File**: `{f.file_path}` (Lines {f.line_start or 'N/A'}-{f.line_end or 'N/A'})"
        )
        lines.append(f"- **Description**: {f.description}")
        if f.suggestion_markdown:
            lines.append(f"- **Suggested Fix**:\n{f.suggestion_markdown}")
        if not f.is_in_diff_hunk:
            lines.append(
                "  *(Note: Finding is located in surrounding context outside the immediate diff hunk)*"
            )
        lines.append("")

    return "\n".join(lines)
