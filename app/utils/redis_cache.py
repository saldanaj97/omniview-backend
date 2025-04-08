import json
import logging
from typing import Any, Dict, Optional, Union

from app.core.redis_client import redis_client

# Set up logging
logger = logging.getLogger(__name__)


async def get_cache(key: str) -> Optional[Union[Dict, list]]:
    """
    Get data from Redis cache by key

    Args:
        key: Redis cache key

    Returns:
        The cached data if found, otherwise None
    """
    logger.debug("Attempting to get from cache: %s", key)
    cached_data = redis_client.get(key)
    if cached_data:
        logger.debug("Cache hit for key: %s", key)
        return json.loads(cached_data)
    logger.debug("Cache miss for key: %s", key)
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
        logger.debug(
            "Setting cache for key: %s (expiration: %d seconds)", key, expiration
        )
        redis_client.setex(key, expiration, json.dumps(data))
        logger.debug("Successfully set cache for key: %s", key)
        return True
    except Exception as e:
        logger.error("Failed to set cache for key %s: %s", key, str(e))
        return False


async def clear_cache(pattern: str) -> None:
    """
    Clear all cache keys matching the given pattern

    Args:
        pattern: Redis key pattern to match (e.g., 'twitch:*')
    """
    logger.info("Clearing cache for pattern: %s", pattern)
    keys = redis_client.keys(pattern)
    if keys:
        logger.info("Found %d keys to delete", len(keys))
        redis_client.delete(*keys)
        logger.info("Successfully deleted %d keys", len(keys))
    else:
        logger.info("No keys found matching pattern: %s", pattern)
