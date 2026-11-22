import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.review_engine.llm_factory import LLMFactory
from app.review_engine.prompts.code_security import (
    CODE_SECURITY_SYSTEM_PROMPT,
    CodeSecurityReport,
    format_code_security_prompt,
)
from app.review_engine.state import RawFinding, ReviewState

logger = logging.getLogger("pr_sentinel.code_specialist")


def _run_rule_based_heuristics(file_path: str, hunk_lines: list[dict[str, Any]]) -> list[RawFinding]:
    """
    High-precision heuristic scanner fallback when upstream LLM provider is unavailable or rate-limited.
    Detects unmistakable high-risk OWASP patterns on newly added diff lines.
    """
    findings: list[RawFinding] = []

    for item in hunk_lines:
        if item.get("type") != "add":
            continue

        content = item.get("content", "")
        line_no = item.get("new_line_no")

        # 1. SQL Injection pattern
        if re.search(r'SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\{', content, re.IGNORECASE) or re.search(
            r'\.execute\(text\(f["\']', content
        ):
            findings.append(
                RawFinding(
                    category="CODE_SECURITY",
                    severity="CRITICAL",
                    title="SQL Injection via unparameterized string formatting",
                    description=(
                        "Detected direct dynamic f-string formatting inside SQL query string. "
                        "Untrusted input can break out of string literals and alter SQL command structure (CWE-89)."
                    ),
                    file_path=file_path,
                    line_start=line_no,
                    line_end=line_no,
                    code_snippet=content.strip(),
                    suggestion_markdown="Use parameterized query with bound parameters (e.g. text('SELECT ... WHERE id = :id'), {'id': value})",
                    rule_id="CWE-89",
                )
            )

        # 2. Command Injection pattern
        if re.search(r'os\.system\(f?["\']', content) or re.search(
            r'subprocess\.(Popen|run|call)\(.*shell\s*=\s*True', content
        ):
            findings.append(
                RawFinding(
                    category="CODE_SECURITY",
                    severity="HIGH",
                    title="Command Injection via unquoted shell execution",
                    description=(
                        "Passing dynamically formatted string to shell execution function (os.system / shell=True). "
                        "Allows arbitrary command execution if input contains shell metacharacters (CWE-78)."
                    ),
                    file_path=file_path,
                    line_start=line_no,
                    line_end=line_no,
                    code_snippet=content.strip(),
                    suggestion_markdown="Use subprocess.run(['cmd', arg1, arg2], shell=False)",
                    rule_id="CWE-78",
                )
            )

        # 3. Insecure Deserialization pattern
        if "pickle.loads(" in content:
            findings.append(
                RawFinding(
                    category="CODE_SECURITY",
                    severity="CRITICAL",
                    title="Insecure Deserialization via pickle.loads",
                    description=(
                        "The pickle module is not secure against erroneous or maliciously constructed data. "
                        "Never unpickle untrusted user-controlled data (CWE-502)."
                    ),
                    file_path=file_path,
                    line_start=line_no,
                    line_end=line_no,
                    code_snippet=content.strip(),
                    suggestion_markdown="Use safe serialization formats like json or protocol buffers",
                    rule_id="CWE-502",
                )
            )

        # 4. Path Traversal pattern
        if re.search(r'open\(os\.path\.join\(.*,\s*[a-zA-Z0-9_]+\)', content) or re.search(
            r'open\(f["\'].*\{', content
        ):
            findings.append(
                RawFinding(
                    category="CODE_SECURITY",
                    severity="HIGH",
                    title="Path Traversal via unsanitized file path concatenation",
                    description=(
                        "Joining file paths directly with user input without verifying canonical path "
                        "allows directory traversal using '../' sequences (CWE-22)."
                    ),
                    file_path=file_path,
                    line_start=line_no,
                    line_end=line_no,
                    code_snippet=content.strip(),
                    suggestion_markdown="Validate path stays within allowed directory with os.path.realpath()",
                    rule_id="CWE-22",
                )
            )

    return findings


async def code_specialist_node(state: ReviewState) -> dict[str, Any]:
    """LangGraph node: Analyzes modified code hunks for OWASP security vulnerabilities."""
    file_contexts = state.get("file_contexts", [])
    raw_findings: list[RawFinding] = list(state.get("raw_findings", []))

    if not file_contexts:
        logger.info("No file contexts to analyze in code_specialist_node.")
        return {"raw_findings": raw_findings}

    llm = None
    structured_llm = None
    try:
        llm = LLMFactory.get_chat_model()
        structured_llm = llm.with_structured_output(CodeSecurityReport)
    except Exception as exc:
        logger.warning("Could not initialize structured LLM for code specialist: %s", exc)

    for f_ctx in file_contexts:
        file_path = f_ctx.get("file_path", "")
        language = f_ctx.get("language", "unknown")
        hunk_contexts = f_ctx.get("hunk_contexts", [])

        for h_ctx in hunk_contexts:
            hunk = h_ctx.get("hunk", {})
            hunk_lines = hunk.get("lines", [])
            hunk_text = "\n".join(
                f"{'+' if line_item.get('type') == 'add' else ('-' if line_item.get('type') == 'delete' else ' ')}{line_item.get('content', '')}"
                for line_item in hunk_lines
            )
            surrounding_code = h_ctx.get("surrounding_code", "")

            user_prompt = format_code_security_prompt(
                file_path=file_path,
                hunk_text=hunk_text,
                surrounding_code=surrounding_code,
                language=language,
            )

            hunk_analyzed_by_llm = False

            # 1. Attempt Primary Structured LLM invocation
            if structured_llm:
                try:
                    response: CodeSecurityReport = await structured_llm.ainvoke(
                        [
                            SystemMessage(content=CODE_SECURITY_SYSTEM_PROMPT),
                            HumanMessage(content=user_prompt),
                        ]
                    )
                    for finding in response.findings:
                        finding.file_path = file_path
                        raw_findings.append(finding)
                    hunk_analyzed_by_llm = True
                except Exception as exc:
                    logger.warning(
                        "Structured LLM failed on %s (%s). Attempting raw extraction.",
                        file_path,
                        exc,
                    )

            # 2. Attempt Unstructured Fallback if structured output parser threw ValidationError
            if not hunk_analyzed_by_llm and llm:
                try:
                    res = await llm.ainvoke(
                        [
                            SystemMessage(content=CODE_SECURITY_SYSTEM_PROMPT),
                            HumanMessage(
                                content=user_prompt
                                + "\n\nCRITICAL: Respond ONLY in valid JSON matching schema: {\"findings\": [...]}. No markdown wrap."
                            ),
                        ]
                    )
                    raw_text = getattr(res, "content", "")
                    # Extract JSON substring if wrapped in markdown
                    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        report = CodeSecurityReport.model_validate(parsed)
                        for finding in report.findings:
                            finding.file_path = file_path
                            raw_findings.append(finding)
                        hunk_analyzed_by_llm = True
                except Exception as raw_exc:
                    logger.warning("Unstructured LLM invocation also failed: %s", raw_exc)

            # 3. High-precision rule-based fallback if LLM was unavailable, 429'd, or failed
            if not hunk_analyzed_by_llm:
                heuristic_findings = _run_rule_based_heuristics(file_path, hunk_lines)
                if heuristic_findings:
                    logger.info(
                        "Heuristic fallback flagged %d issues in %s",
                        len(heuristic_findings),
                        file_path,
                    )
                    raw_findings.extend(heuristic_findings)

    logger.info("Code specialist node finished. Total raw findings: %d", len(raw_findings))
    return {"raw_findings": raw_findings}
