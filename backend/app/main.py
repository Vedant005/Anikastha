import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.repositories import router as repositories_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.webhooks import router as webhooks_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.redis import close_arq_pool, close_redis_client, get_redis_client

settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pr_sentinel.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: initialize connections on startup and cleanup on shutdown."""
    logger.info("Initializing PR-Sentinel backend (env=%s)...", settings.ENVIRONMENT)

    # Initialize tables automatically for SQLite/Dev mode if needed
    if settings.ENVIRONMENT in ("development", "test"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas verified.")

    # Validate Redis connection
    try:
        redis = await get_redis_client()
        await redis.ping()
        logger.info("Connected to Redis at %s", settings.REDIS_URL)
    except Exception as exc:
        logger.warning("Could not connect to Redis during startup: %s", exc)

    yield

    # Clean shutdown
    logger.info("Shutting down PR-Sentinel backend...")
    await close_redis_client()
    await close_arq_pool()
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="PR-Sentinel API",
    description="Autonomous AI-Powered GitHub Pull Request Security Reviewer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """System health check probe."""
    db_status = "healthy"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    return {
        "status": "ok" if "healthy" in db_status else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }


app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(repositories_router, prefix="/api/v1")
