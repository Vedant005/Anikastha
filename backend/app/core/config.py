from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pr_sentinel"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # GitHub App Integration
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY_PATH: str = "./github_app_private_key.pem"
    GITHUB_APP_PRIVATE_KEY_BASE64: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""

    # LLM Settings
    LLM_PROVIDER: Literal["gemini", "openai", "anthropic"] = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Security & Policy Defaults
    DEFAULT_FAIL_ON_SEVERITY: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"
    AUTO_REQUEST_CHANGES: bool = True
    BLOCK_PROHIBITED_LICENSES: bool = True
    PROHIBITED_LICENSES: list[str] = Field(
        default_factory=lambda: ["GPL-3.0", "AGPL-3.0", "SSPL-1.0"]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
