import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.policy import PolicyRead


class RepositoryBase(BaseModel):
    github_repo_id: int
    full_name: str
    installation_id: int
    is_active: bool = True


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryRead(RepositoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    policy: Optional[PolicyRead] = None

