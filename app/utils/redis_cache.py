import json
from typing import Any, Dict, Optional, Union

from app.core.redis_client import redis_client
from app.utils.logging.redis_logger import RedisLogger

# Set up enhanced Redis logger
logger = RedisLogger("redis_cache")


async def get_cache(key: str) -> Optional[Union[Dict, list]]:
    """
    Get data from Redis cache by key

    Args:
        key: Redis cache key

    Returns:
        The cached data if found, otherwise None
    """
    logger.info("Attempting to get from cache", key=key)
    cached_data = redis_client.get(key)
    if cached_data:
        logger.info("Cache hit", key=key)
        return json.loads(cached_data)
    logger.info("Cache miss", key=key)
    return None


async def set_cache(key: str, data: Union[Dict, list], expiration: int = 300) -> bool:
    """
    Set data in Redis cache with expiration time

    Args:
        key: Redis cache key
        data: Data to be cached (will be JSON serialized)
        expiration: Cache TTL in seconds (default: 5 minutes)

    Returns:
        Boolean indicating success
    """
    try:
        logger.info("Setting cache", key=key, expiration=expiration)
        redis_client.setex(key, expiration, json.dumps(data))
        logger.info("Successfully set cache", key=key)
        return True
    except Exception as e:
        logger.error("Failed to set cache", exception=e, key=key)
        return False


async def clear_cache(pattern: str) -> None:
    """
    Clear all cache keys matching the given pattern

    Args:
        pattern: Redis key pattern to match (e.g., 'twitch:*')
    """
    logger.info("Clearing cache", pattern=pattern)
    keys = redis_client.keys(pattern)
    if keys:
        logger.info("Found keys to delete", count=len(keys))
        redis_client.delete(*keys)
        logger.info("Successfully deleted keys", count=len(keys))
    else:
        logger.info("No keys found matching pattern", pattern=pattern)
