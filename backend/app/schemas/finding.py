import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class FindingBase(BaseModel):
    category: Literal["CODE_SECURITY", "DEPENDENCY_CVE", "LICENSE"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    title: str
    description: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion_markdown: str | None = None
    cve_id: str | None = None
    package_name: str | None = None
    current_version: str | None = None
    fixed_version: str | None = None
    is_verified: bool = False
    verification_reason: str | None = None
    published_inline: bool = False


class FindingCreate(FindingBase):
    review_run_id: uuid.UUID


class FindingRead(FindingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_run_id: uuid.UUID
    created_at: datetime
