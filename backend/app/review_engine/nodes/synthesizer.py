import logging
from typing import Any

from app.review_engine.state import RawFinding, ReviewState

logger = logging.getLogger("pr_sentinel.synthesizer")


async def synthesizer_node(state: ReviewState) -> dict[str, Any]:
    """
    LangGraph node: Groups, deduplicates, and synthesizes findings across files and specialists.
    """
    raw_findings = state.get("raw_findings", [])
    if not raw_findings:
        return {"synthesized_findings": []}

    deduped: dict[str, RawFinding] = {}

    for finding in raw_findings:
        # Create unique key based on file, line or cve, and title
        key = f"{finding.category}:{finding.file_path}:{finding.line_start or 0}:{finding.cve_id or finding.title.lower().strip()}"
        if key not in deduped:
            deduped[key] = finding
        else:
            # If finding already exists, retain highest severity
            existing = deduped[key]
            severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
            if severity_order.get(finding.severity, 0) > severity_order.get(existing.severity, 0):
                deduped[key] = finding

    synthesized_list = list(deduped.values())
    logger.info(
        "Synthesizer completed: reduced %d raw findings to %d synthesized findings.",
        len(raw_findings),
        len(synthesized_list),
    )
    return {"synthesized_findings": synthesized_list}
