import logging
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


async def code_specialist_node(state: ReviewState) -> dict[str, Any]:
    """LangGraph node: Analyzes modified code hunks for OWASP security vulnerabilities."""
    file_contexts = state.get("file_contexts", [])
    raw_findings: list[RawFinding] = list(state.get("raw_findings", []))

    if not file_contexts:
        logger.info("No file contexts to analyze in code_specialist_node.")
        return {"raw_findings": raw_findings}

    llm = LLMFactory.get_chat_model()
    try:
        structured_llm = llm.with_structured_output(CodeSecurityReport)
    except Exception as exc:
        logger.warning("Structured output not supported directly: %s. Using standard LLM.", exc)
        structured_llm = None

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

            try:
                if structured_llm:
                    response: CodeSecurityReport = await structured_llm.ainvoke(
                        [
                            SystemMessage(content=CODE_SECURITY_SYSTEM_PROMPT),
                            HumanMessage(content=user_prompt),
                        ]
                    )
                    for finding in response.findings:
                        # Ensure file path is accurate
                        finding.file_path = file_path
                        raw_findings.append(finding)
                else:
                    # Fallback invocation
                    res = await llm.ainvoke(
                        [
                            SystemMessage(content=CODE_SECURITY_SYSTEM_PROMPT),
                            HumanMessage(content=user_prompt),
                        ]
                    )
                    logger.debug("Raw LLM response: %s", res.content)
            except Exception as exc:
                logger.error("Error running code_specialist on %s: %s", file_path, exc)

    logger.info("Code specialist node finished. Total raw findings: %d", len(raw_findings))
    return {"raw_findings": raw_findings}
