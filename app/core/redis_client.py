import json
import logging
from typing import Any, Dict, Optional

import redis

from app.core.config import REDIS_URL

# Set up logger
logger = logging.getLogger(__name__)

# Create a Redis client
redis_client = redis.from_url(REDIS_URL)
print(
    "Redis client initialized with URL: ", REDIS_URL.split("@")[-1]
)  # Logs Redis host without credentials


async def set_token_data(
    user_id: str, platform: str, token_data: Dict[str, Any], expiry_seconds: int = 3600
) -> bool:
    """
    Store token data in Redis with expiration

    Args:
        user_id: The user's unique identifier
        platform: The platform name (twitch, youtube, kick)
        token_data: The token data to store
        expiry_seconds: Time in seconds until the token expires

    Returns:
        bool: Success status
    """
    key = f"token:{platform}:{user_id}"
    try:
        # Store as JSON string
        print("Setting Redis token data for key: ", key)
        redis_client.setex(key, expiry_seconds, json.dumps(token_data))
        print(f"Successfully saved token data for {platform} user: {user_id}")
        return True
    except Exception as e:
        logger.error("Failed to save token data in Redis: %s", str(e))
        return False


async def get_token_data(user_id: str, platform: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve token data from Redis

    Args:
        user_id: The user's unique identifier
        platform: The platform name (twitch, youtube, kick)

    Returns:
        Dict or None: The token data if found, None otherwise
    """
    key = f"token:{platform}:{user_id}"
    try:
        print(
            f"Attempting to retrieve token data for key: {key}",
        )
        data = redis_client.get(key)
        if data:
            print(
                f"Cache HIT: Found token data for {platform} user: {user_id}",
            )
            return json.loads(data)
        print(f"Cache MISS: No token data found for {platform} user:  {user_id}")
        return None
    except Exception as e:
        logger.error("Error retrieving token data from Redis: %s", str(e))
        return None


async def delete_token_data(user_id: str, platform: str) -> bool:
    """Delete token data from Redis"""
    key = f"token:{platform}:{user_id}"
    try:
        print(f"Deleting token data for key: {key}")
        result = redis_client.delete(key)
        if result > 0:
            print(f"Successfully deleted token data for {platform} user: {user_id}")
        else:
            print(f"No token data found to delete for {platform} user: {user_id}")
        return True
    except Exception as e:
        logger.error("Failed to delete token data from Redis: %s", str(e))
        return False


# Add utility function to check Redis connection
def check_redis_connection() -> bool:
    """Check if Redis connection is working properly"""
    try:
        redis_client.ping()
        print("Redis connection test: SUCCESS")
        return True
    except redis.ConnectionError as e:
        logger.error("Redis connection test: FAILED - %s", str(e))
        return False
