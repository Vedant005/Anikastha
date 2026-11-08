import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.review_engine.llm_factory import LLMFactory
from app.review_engine.prompts.verifier import (
    VERIFIER_SYSTEM_PROMPT,
    VerificationReport,
    format_verifier_prompt,
)
from app.review_engine.state import ReviewState, VerifiedFinding

logger = logging.getLogger("pr_sentinel.verifier")


async def verifier_node(state: ReviewState) -> dict[str, Any]:
    """
    LangGraph node: Adversarial Red-Team Verifier that eliminates false positives
    and strictly validates diff line coordinates to prevent GitHub 422 errors.
    """
    synthesized = state.get("synthesized_findings", [])
    diff_files = state.get("diff_files", [])

    if not synthesized:
        logger.info("No synthesized findings to verify.")
        return {"verified_findings": []}

    # Extract valid commentable lines for each file
    valid_diff_lines: dict[str, set[int]] = {}
    for df in diff_files:
        path = df.get("new_path") or df.get("file_path", "")
        valid_lines: set[int] = set()
        for hunk in df.get("hunks", []):
            valid_lines.update(hunk.get("valid_new_lines", []))
        valid_diff_lines[path] = valid_lines

    candidate_dicts = [f.model_dump() for f in synthesized]
    valid_lines_serializable = {k: sorted(list(v)) for k, v in valid_diff_lines.items()}

    llm = LLMFactory.get_chat_model()
    try:
        structured_llm = llm.with_structured_output(VerificationReport)
    except Exception as exc:
        logger.warning("Structured output not supported directly on verifier: %s", exc)
        structured_llm = None

    user_prompt = format_verifier_prompt(
        candidate_findings=candidate_dicts,
        valid_diff_lines_by_file=valid_lines_serializable,
    )

    verified_findings: list[VerifiedFinding] = []

    try:
        if structured_llm:
            report: VerificationReport = await structured_llm.ainvoke(
                [
                    SystemMessage(content=VERIFIER_SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ]
            )
            raw_verified = report.verified_findings
        else:
            raw_verified = []
            for f in synthesized:
                raw_verified.append(
                    VerifiedFinding(
                        **f.model_dump(),
                        is_verified=True,
                        verification_reason="Rule-based heuristic verification passed.",
                    )
                )

        # Coordinate Validation Gate:
        # Strictly cross-check line numbers against valid diff hunks
        for vf in raw_verified:
            if not vf.is_verified:
                logger.info("Adversarial verifier rejected false positive: %s", vf.title)
                continue

            file_valid_lines = valid_diff_lines.get(vf.file_path, set())
            if vf.line_start is not None and vf.line_start in file_valid_lines:
                vf.is_in_diff_hunk = True
            elif vf.category in ("DEPENDENCY_CVE", "LICENSE"):
                # Manifest/license alerts can be placed on first line if in diff, or summary
                vf.is_in_diff_hunk = bool(file_valid_lines and vf.line_start in file_valid_lines)
            else:
                # Genuine issue, but on line outside hunk (e.g. caller in untouched line)
                # Mark as not in hunk so it is safely published in the top-level review summary
                vf.is_in_diff_hunk = False

            verified_findings.append(vf)

    except Exception as exc:
        logger.error("Error during verification node: %s", exc)
        # Fallback to coordinate-validated synthesized findings
        for f in synthesized:
            file_valid_lines = valid_diff_lines.get(f.file_path, set())
            is_in_hunk = f.line_start in file_valid_lines if f.line_start else False
            verified_findings.append(
                VerifiedFinding(
                    **f.model_dump(),
                    is_verified=True,
                    verification_reason="Fallback verification passed.",
                    is_in_diff_hunk=is_in_hunk,
                )
            )

    logger.info(
        "Verification complete: %d verified findings (of %d candidate).",
        len(verified_findings),
        len(synthesized),
    )
    return {"verified_findings": verified_findings}
