"""Redis client, reserved for caching in Module 8.

Nothing uses it yet. It is kept here so the connection setup is ready
when caching is added.
"""

import redis.asyncio as redis

from app.core.config import REDIS_HOST, REDIS_PORT

redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    max_connections=10,
)

redis_client = redis.Redis(connection_pool=redis_pool)


async def connect_redis():
    """Return the shared Redis client, for use as a FastAPI dependency."""
    return redis_client