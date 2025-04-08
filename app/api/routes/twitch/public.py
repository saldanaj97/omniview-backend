import logging

from fastapi import APIRouter, HTTPException, Request

import app.services.twitch.public as public
from app.utils.redis_cache import get_cache, set_cache

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def public_check_login_status(request: Request):
    """
    Public endpoint to check which platforms have access tokens available.
    This is used for public access without requiring a session.
    """
    try:
        logger.info("Checking public login status")
        platform_status = await public.check_public_login_status(request=request)
        logger.info("Successfully retrieved platform status")
        return platform_status
    except Exception as e:
        logger.error("Failed to check public login status: %s", str(e))
        return {"data": [], "error": {"message": str(e)}}


@router.get("/top-streams")
async def top_streams(request: Request):
    # Cache key for this endpoint
    cache_key = "twitch:public:top-streams"

    # Try to get from cache first
    logger.info("Attempting to fetch top streams (cache key: %s)", cache_key)
    cached_data = await get_cache(cache_key)
    if cached_data:
        logger.info("Cache hit for top streams")
        return cached_data

    try:
        logger.info("Cache miss - fetching live top streams from Twitch")
        popular_streams = await public.get_top_streams(request=request)
        # Cache for 2 minutes (120 seconds) since stream data changes frequently
        await set_cache(cache_key, popular_streams, 120)
        logger.info("Successfully fetched and cached top streams")
        return popular_streams
    except Exception as e:
        logger.error("Failed to fetch top streams: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
