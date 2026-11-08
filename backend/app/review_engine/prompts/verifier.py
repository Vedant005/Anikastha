import json
from typing import Any

from pydantic import BaseModel, Field

from app.review_engine.state import VerifiedFinding


class VerificationReport(BaseModel):
    verified_findings: list[VerifiedFinding] = Field(default_factory=list)


VERIFIER_SYSTEM_PROMPT = """You are PR-Sentinel's Adversarial Red-Team Verifier.
Your sole job is to ruthlessly critique candidate security findings and REJECT FALSE POSITIVES.

### Anti-Hallucination & Verification Checklist
For EVERY candidate finding, you must answer:
1. **Untouched Code Test**: Does the vulnerability exist in newly added or modified lines in this PR?
   - If the code existed prior to this PR and was not modified, REJECT IT (`is_verified = False`).
2. **Framework Mitigation Test**: Is this finding theoretical, but in reality safely mitigated by framework protections?
   - Example: SQL parameterization via SQLAlchemy or ORM query builders mitigates raw SQL injection.
   - Example: FastAPI Pydantic type validation guarantees that integers or enums cannot contain injection payloads.
   - If safely mitigated by existing architecture, REJECT IT (`is_verified = False`).
3. **Coordinate Accuracy**:
   - Check if the start and end lines fall within the valid diff lines of the modified file.
   - If valid, `is_in_diff_hunk = True`. If outside diff lines, mark `is_in_diff_hunk = False`.
4. **Remediation Validity**:
   - Verify that any proposed `suggestion_markdown` is syntactically correct and will not break the application.

Only approve genuine, actionable findings that will not waste the developer's time.
"""


def format_verifier_prompt(
    candidate_findings: list[dict[str, Any]],
    valid_diff_lines_by_file: dict[str, list[int]],
) -> str:
    return f"""Adversarially evaluate the following candidate security findings:

<valid_commentable_diff_lines>
{json.dumps(valid_diff_lines_by_file, indent=2)}
</valid_commentable_diff_lines>

<candidate_findings>
{json.dumps(candidate_findings, indent=2)}
</candidate_findings>

Scrutinize each finding. Reject false positives and pre-existing code alerts. Confirm diff line coordinates.
"""
