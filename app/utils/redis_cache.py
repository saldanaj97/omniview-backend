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
    print("Attempting to get from cache: ", key)
    cached_data = redis_client.get(key)
    if cached_data:
        print(f"Cache hit for key: {key}")
        return json.loads(cached_data)
    print(f"Cache miss for key: {key}")
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
        print(f"Setting cache for key: {key} (expiration: %d seconds) {expiration}")
        redis_client.setex(key, expiration, json.dumps(data))
        print(f"Successfully set cache for key: {key}")
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
    print(f"Clearing cache for pattern: {pattern}")
    keys = redis_client.keys(pattern)
    if keys:
        print(f"Found {len(keys)} keys to delete")
        redis_client.delete(*keys)
        print(f"Successfully deleted {len(keys)} keys")
    else:
        print(f"No keys found matching pattern: {pattern}")
