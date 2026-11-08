import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class FindingBase(BaseModel):
    category: Literal["CODE_SECURITY", "DEPENDENCY_CVE", "LICENSE"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    title: str
    description: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion_markdown: Optional[str] = None
    cve_id: Optional[str] = None
    package_name: Optional[str] = None
    current_version: Optional[str] = None
    fixed_version: Optional[str] = None
    is_verified: bool = False
    verification_reason: Optional[str] = None
    published_inline: bool = False


class FindingCreate(FindingBase):
    review_run_id: uuid.UUID


class FindingRead(FindingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_run_id: uuid.UUID
    created_at: datetime

