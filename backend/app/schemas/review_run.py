import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.finding import FindingRead


class ReviewRunBase(BaseModel):
    pull_number: int
    commit_sha: str
    title: str = ""
    pr_author: str = ""
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"] = "PENDING"
    verdict: Literal["APPROVE", "COMMENT", "REQUEST_CHANGES"] | None = None
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary_markdown: str | None = None
    error_message: str | None = None
    execution_time_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ReviewRunCreate(ReviewRunBase):
    repository_id: uuid.UUID


class ReviewRunRead(ReviewRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    created_at: datetime
    findings: list[FindingRead] = []
