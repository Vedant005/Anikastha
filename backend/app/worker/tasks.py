import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.analyzer.context_builder import RepositoryContextBuilder
from app.analyzer.dependency_parser import DependencyParser
from app.analyzer.license_checker import LicenseChecker
from app.analyzer.osv_client import OSVClient
from app.core.database import AsyncSessionLocal
from app.github.client import GitHubClient
from app.github.diff_parser import DiffParser
from app.models.finding import Finding
from app.models.repository import Repository
from app.models.review_run import ReviewRun
from app.review_engine.graph import review_engine_graph
from app.review_engine.state import ReviewState
from app.schemas.dependency import Dependency, LicenseCheckResult, Vulnerability

logger = logging.getLogger("pr_sentinel.worker")


async def process_pull_request_review(ctx: dict[str, Any], run_id: str) -> dict[str, Any]:
    """
    ARQ Background Task: Full multi-agent security review pipeline for a GitHub Pull Request.
    """
    logger.info("Starting PR review processing for run_id=%s", run_id)
    start_time = time.time()
    run_uuid = uuid.UUID(run_id)

    async with AsyncSessionLocal() as session:
        # Load ReviewRun with Repository and Policy
        result = await session.execute(
            select(ReviewRun)
            .options(selectinload(ReviewRun.repository).selectinload(Repository.policy))
            .where(ReviewRun.id == run_uuid)
        )
        review_run = result.scalar_one_or_none()

        if not review_run:
            logger.error("ReviewRun with id=%s not found.", run_id)
            return {"status": "error", "message": f"ReviewRun {run_id} not found"}

        # Update status to PROCESSING
        review_run.status = "PROCESSING"
        review_run.started_at = datetime.now(UTC)
        await session.commit()

        repo = review_run.repository
        policy = repo.policy
        policy_dict = {
            "fail_on_severity": policy.fail_on_severity if policy else "HIGH",
            "block_prohibited_licenses": policy.block_prohibited_licenses if policy else True,
            "prohibited_licenses": policy.prohibited_licenses
            if policy
            else ["GPL-3.0", "AGPL-3.0"],
            "auto_request_changes": policy.auto_request_changes if policy else True,
        }

        owner, repo_name = (
            repo.full_name.split("/", 1) if "/" in repo.full_name else ("", repo.full_name)
        )

        try:
            # 1. Initialize GitHub Client
            async with GitHubClient(installation_id=repo.installation_id) as gh_client:
                # Retrieve PR metadata & diff
                await gh_client.get_pull_request(
                    owner=owner, repo=repo_name, pull_number=review_run.pull_number
                )
                diff_text = await gh_client.get_pull_request_diff(
                    owner=owner, repo=repo_name, pull_number=review_run.pull_number
                )

                # 2. Parse diff hunks
                diff_files = DiffParser.parse_diff(diff_text)
                logger.info("Parsed %d modified files from git diff.", len(diff_files))

                # 3. Security intelligence & context extraction
                file_contexts: list[dict[str, Any]] = []
                all_dependencies: list[Dependency] = []
                vulnerabilities: list[Vulnerability] = []
                license_alerts: list[LicenseCheckResult] = []

                osv_client = OSVClient()
                license_checker = LicenseChecker()

                for df in diff_files:
                    if df.status == "deleted" or df.is_binary:
                        continue

                    # Fetch full file content at head ref
                    content = await gh_client.get_file_content(
                        owner=owner,
                        repo=repo_name,
                        path=df.new_path,
                        ref=review_run.commit_sha,
                    )

                    # Check for package manifests
                    if DependencyParser.is_manifest_file(df.new_path):
                        deps = DependencyParser.parse_manifest(df.new_path, content or "")
                        all_dependencies.extend(deps)

                        # Check for vulnerabilities and licenses
                        if deps:
                            pkg_vulns = await osv_client.query_batch(deps, fetch_details=False)
                            vulnerabilities.extend(pkg_vulns)

                            pkg_licenses = await license_checker.check_dependencies(
                                deps,
                                prohibited_licenses=policy_dict.get("prohibited_licenses", []),
                            )
                            license_alerts.extend(pkg_licenses)

                    # Build Tree-sitter AST and context
                    f_ctx = RepositoryContextBuilder.build_file_context(df, content)
                    file_contexts.append(f_ctx.model_dump())

                # 4. Prepare LangGraph Review State
                initial_state: ReviewState = {
                    "repo_name": repo.full_name,
                    "pull_number": review_run.pull_number,
                    "commit_sha": review_run.commit_sha,
                    "diff_files": [df.model_dump() for df in diff_files],
                    "file_contexts": file_contexts,
                    "dependencies": [d.model_dump() for d in all_dependencies],
                    "vulnerabilities": [v.model_dump() for v in vulnerabilities],
                    "license_alerts": [la.model_dump() for la in license_alerts],
                    "policy": policy_dict,
                    "raw_findings": [],
                    "synthesized_findings": [],
                    "verified_findings": [],
                    "verdict": "APPROVE",
                    "summary_markdown": "",
                }

                # 5. Run LangGraph Review Pipeline
                final_state = await review_engine_graph.ainvoke(initial_state)

                verified_findings = final_state.get("verified_findings", [])
                verdict = final_state.get("verdict", "APPROVE")
                summary_markdown = final_state.get("summary_markdown", "")

                # 6. Persist Findings to Database
                for vf in verified_findings:
                    finding_record = Finding(
                        review_run_id=review_run.id,
                        category=vf.category,
                        severity=vf.severity,
                        title=vf.title,
                        description=vf.description,
                        file_path=vf.file_path,
                        line_start=vf.line_start,
                        line_end=vf.line_end,
                        code_snippet=vf.code_snippet,
                        suggestion_markdown=vf.suggestion_markdown,
                        cve_id=vf.cve_id,
                        package_name=vf.package_name,
                        is_verified=vf.is_verified,
                        verification_reason=vf.verification_reason,
                        published_inline=vf.is_in_diff_hunk,
                    )
                    session.add(finding_record)

                # 7. Update ReviewRun execution metrics & status
                execution_time = int((time.time() - start_time) * 1000)
                review_run.status = "COMPLETED"
                review_run.verdict = verdict
                review_run.total_findings = len(verified_findings)
                review_run.critical_count = sum(
                    1 for f in verified_findings if f.severity == "CRITICAL"
                )
                review_run.high_count = sum(1 for f in verified_findings if f.severity == "HIGH")
                review_run.medium_count = sum(
                    1 for f in verified_findings if f.severity == "MEDIUM"
                )
                review_run.low_count = sum(1 for f in verified_findings if f.severity == "LOW")
                review_run.summary_markdown = summary_markdown
                review_run.execution_time_ms = execution_time
                review_run.completed_at = datetime.now(UTC)
                await session.commit()

                logger.info(
                    "Review completed for run_id=%s with verdict=%s (%d findings, %dms)",
                    run_id,
                    verdict,
                    len(verified_findings),
                    execution_time,
                )

                return {
                    "status": "success",
                    "run_id": run_id,
                    "verdict": verdict,
                    "total_findings": len(verified_findings),
                    "execution_time_ms": execution_time,
                }

        except Exception as exc:
            logger.exception("Error processing PR review for run_id=%s: %s", run_id, exc)
            execution_time = int((time.time() - start_time) * 1000)
            review_run.status = "FAILED"
            review_run.error_message = str(exc)
            review_run.completed_at = datetime.now(UTC)
            review_run.execution_time_ms = execution_time
            await session.commit()
            return {"status": "failed", "run_id": run_id, "error": str(exc)}
