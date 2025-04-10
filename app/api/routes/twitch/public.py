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
        platform_status = await public.check_public_login_status(request=request)
        return platform_status
    except Exception as e:
        logger.error("Failed to check public login status: %s", str(e))
        return {"data": [], "error": {"message": str(e)}}


@router.get("/top-streams")
async def top_streams(request: Request):
    # Cache key for this endpoint
    cache_key = "twitch:public:top-streams"

    # Try to get from cache first
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        popular_streams = await public.get_top_streams(request=request)
        # Cache for 2 minutes (120 seconds) since stream data changes frequently
        await set_cache(cache_key, popular_streams, 120)
        return popular_streams
    except Exception as e:
        logger.error("Failed to fetch top streams: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
