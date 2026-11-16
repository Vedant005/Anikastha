import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    github_user_id: int
    username: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime
    installation_ids: list[int] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AuthExchangeRequest(BaseModel):
    code: str


class DevLoginRequest(BaseModel):
    username: str = "demo-developer"
    github_user_id: int = 999999
    installation_ids: list[int] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
