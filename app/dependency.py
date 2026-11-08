import redis.asyncio as redis
import os

redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
    max_connections=10
    )

redis_client = redis.Redis(connection_pool=redis_pool)



async def connect_redis():
    return redis_client