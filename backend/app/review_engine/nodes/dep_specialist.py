import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.review_engine.llm_factory import LLMFactory
from app.review_engine.prompts.dep_specialist import (
    DEP_SPECIALIST_SYSTEM_PROMPT,
    DependencySecurityReport,
    format_dep_specialist_prompt,
)
from app.review_engine.state import RawFinding, ReviewState

logger = logging.getLogger("pr_sentinel.dep_specialist")


async def dep_specialist_node(state: ReviewState) -> dict[str, Any]:
    """LangGraph node: Evaluates dependency CVEs and license policy alerts."""
    vulnerabilities = state.get("vulnerabilities", [])
    license_alerts = state.get("license_alerts", [])
    raw_findings: list[RawFinding] = list(state.get("raw_findings", []))

    if not vulnerabilities and not license_alerts:
        logger.info("No vulnerabilities or license alerts to review in dep_specialist_node.")
        return {"raw_findings": raw_findings}

    dependencies = state.get("dependencies", [])
    manifest_files = list({d.get("manifest_file") for d in dependencies if d.get("manifest_file")})

    llm = LLMFactory.get_chat_model()
    try:
        structured_llm = llm.with_structured_output(DependencySecurityReport)
    except Exception as exc:
        logger.warning("Structured output not supported directly: %s. Using standard LLM.", exc)
        structured_llm = None

    user_prompt = format_dep_specialist_prompt(
        vulnerabilities=vulnerabilities,
        license_alerts=license_alerts,
        manifest_files=manifest_files,
    )

    try:
        if structured_llm:
            response: DependencySecurityReport = await structured_llm.ainvoke(
                [
                    SystemMessage(content=DEP_SPECIALIST_SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ]
            )
            for finding in response.findings:
                raw_findings.append(finding)
        else:
            # Deterministic fallback without LLM if structured call unavailable
            for v in vulnerabilities:
                raw_findings.append(
                    RawFinding(
                        category="DEPENDENCY_CVE",
                        severity=v.get("severity", "HIGH"),
                        title=f"Vulnerable dependency {v.get('package_name')} ({v.get('cve_id') or v.get('id')})",
                        description=v.get("summary", ""),
                        file_path=manifest_files[0] if manifest_files else "requirements.txt",
                        cve_id=v.get("cve_id") or v.get("id"),
                        package_name=v.get("package_name"),
                        suggestion_markdown=f"Upgrade {v.get('package_name')} to {v.get('fixed_version')}"
                        if v.get("fixed_version")
                        else None,
                    )
                )

            for lic in license_alerts:
                if lic.get("is_prohibited"):
                    raw_findings.append(
                        RawFinding(
                            category="LICENSE",
                            severity="HIGH",
                            title=f"Prohibited license detected: {lic.get('package_name')} ({lic.get('license_spdx')})",
                            description=lic.get(
                                "policy_reason", "Prohibited license by organization policy."
                            ),
                            file_path=manifest_files[0] if manifest_files else "package.json",
                            package_name=lic.get("package_name"),
                        )
                    )
    except Exception as exc:
        logger.error("Error running dep_specialist: %s", exc)

    logger.info("Dep specialist node finished. Total raw findings: %d", len(raw_findings))
    return {"raw_findings": raw_findings}
