from arq.connections import ArqRedis, create_pool
from redis.asyncio import Redis, from_url

from app.core.config import get_settings

settings = get_settings()

_redis_client: Redis | None = None
_arq_pool: ArqRedis | None = None


async def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def get_arq_pool() -> ArqRedis:
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(settings.REDIS_URL)
    return _arq_pool


async def close_arq_pool() -> None:
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.close()
        _arq_pool = None
