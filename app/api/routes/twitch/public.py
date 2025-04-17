import logging

from fastapi import APIRouter, HTTPException, Request

from app.services.twitch import public
from app.utils.http_utils import ensure_session_credentials
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
    return await public.check_public_login_status(request=request)


@router.get("/top-streams")
async def top_streams(request: Request):
    # Ensure Twitch public credentials exist in the session
    ensure_session_credentials(request, "twitch_public_credentials")

    # Cache key for this endpoint
    cache_key = "twitch:public:top-streams"

    # Try to get from cache first
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    popular_streams = await public.get_top_streams(request=request)

    # Cache for 2 minutes (120 seconds) since stream data changes frequently
    await set_cache(cache_key, popular_streams, 120)

    return popular_streams
