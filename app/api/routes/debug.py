import logging

from fastapi import APIRouter, HTTPException

from app.core.redis_client import redis_client

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/cache/keys")
async def get_cache_keys(pattern: str = "*"):
    """
    Debug endpoint to get all Redis cache keys matching a pattern
    """
    try:
        print("Finding cache keys matching pattern:", pattern)
        keys = redis_client.keys(pattern)
        print(f"Found {len(keys)}, keys matching pattern {pattern}")
        return {"keys": keys, "count": len(keys)}
    except Exception as e:
        logger.error("Error getting cache keys: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/cache/get")
async def get_cache_value(key: str):
    """
    Debug endpoint to get a specific Redis cache value
    """
    try:
        print("Attempting to get cache value for key: ", key)
        value = redis_client.get(key)
        if value:
            print("Cache hit for key: ", key)
            return {"key": key, "value": value}
        print("Cache miss for key: ", key)
        return {"key": key, "value": None}
    except Exception as e:
        logger.error("Error getting cache value: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/cache/flush")
async def flush_cache():
    """
    Debug endpoint to flush all Redis cache
    """
    try:
        print("Flushing Redis cache")
        redis_client.flushdb()
        print("Cache flushed successfully")
        return {"message": "Cache flushed successfully"}
    except Exception as e:
        logger.error("Error flushing cache: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
