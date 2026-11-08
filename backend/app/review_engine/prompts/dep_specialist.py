import json
from typing import Any

from pydantic import BaseModel, Field

from app.review_engine.state import RawFinding


class DependencySecurityReport(BaseModel):
    findings: list[RawFinding] = Field(default_factory=list)


DEP_SPECIALIST_SYSTEM_PROMPT = """You are PR-Sentinel's Dependency Intelligence & License Compliance Specialist.
Your mission is to evaluate security advisories from OSV.dev and SPDX license check results against a Pull Request.

### Instructions
1. For each reported CVE/vulnerability:
   - Determine if the package is in production or dev dependencies.
   - Explain the attack vector, affected version, and safe fixed version.
   - Format actionable upgrade guidance or pinned version fix.
2. For each license violation:
   - Identify prohibited copyleft licenses (e.g. GPL-3.0, AGPL-3.0) that violate repository policy.
   - Explain commercial/distribution legal risk and recommend permissive alternatives (MIT, Apache-2.0, BSD).
"""


def format_dep_specialist_prompt(
    vulnerabilities: list[dict[str, Any]],
    license_alerts: list[dict[str, Any]],
    manifest_files: list[str],
) -> str:
    return f"""Evaluate the following dependency security and license scan results:

Manifest Files: {", ".join(manifest_files) if manifest_files else "None"}

<osv_vulnerabilities>
{json.dumps(vulnerabilities, indent=2) if vulnerabilities else "[]"}
</osv_vulnerabilities>

<license_alerts>
{json.dumps(license_alerts, indent=2) if license_alerts else "[]"}
</license_alerts>

Return structured security findings for confirmed package vulnerabilities and license policy violations.
"""
