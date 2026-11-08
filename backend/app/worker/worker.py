import logging
from typing import Any

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.worker.tasks import process_pull_request_review

settings = get_settings()
logger = logging.getLogger("pr_sentinel.worker")


async def startup(ctx: dict[str, Any]) -> None:
    logger.info("PR-Sentinel ARQ worker started up.")


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("PR-Sentinel ARQ worker shutting down.")


class WorkerSettings:
    """ARQ Worker configuration."""

    functions = [process_pull_request_review]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    max_tries = 3
