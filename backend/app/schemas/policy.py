import uuid
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class PolicyBase(BaseModel):
    fail_on_severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"
    block_prohibited_licenses: bool = True
    prohibited_licenses: List[str] = Field(
        default_factory=lambda: ["GPL-3.0", "AGPL-3.0", "SSPL-1.0"]
    )
    auto_request_changes: bool = True


class PolicyCreate(PolicyBase):
    repository_id: uuid.UUID


class PolicyUpdate(BaseModel):
    fail_on_severity: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = None
    block_prohibited_licenses: Optional[bool] = None
    prohibited_licenses: Optional[List[str]] = None
    auto_request_changes: Optional[bool] = None


class PolicyRead(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    updated_at: datetime

