import logging

from fastapi import APIRouter, HTTPException, Request

from app.services.google.public import fetch_top_streams
from app.utils.http_utils import ensure_session_credentials
from app.utils.redis_cache import get_cache, set_cache

# Set up logging
logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/top_streams")
async def top_streams(request: Request):
    """
    Get a list of current top live streams on YouTube.
    """
    # Ensure public credentials are available in the session
    credentials = ensure_session_credentials(request, "", "Youtube")

    # Try to get from cache first
    cache_key = "google:public:top_streams"
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        response = await fetch_top_streams(credentials)

        # Cache for 20 minutes (1200 seconds) since stream data changes frequently
        await set_cache(cache_key, response, 1200)

        return response
    except Exception as e:
        logger.exception("Error fetching top YouTube streams: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
