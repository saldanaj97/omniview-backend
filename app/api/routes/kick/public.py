import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas.top_streams import Stream
from app.services.kick.public import fetch_top_streams  # <-- added import
from app.utils.http_utils import ensure_session_credentials
from app.utils.redis_cache import get_cache, set_cache

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/top_streams")
async def top_streams(request: Request):
    """
    Endpoint to get top streams from Kick.
    """
    try:
        # Check if we have the necessary credentials
        credentials = ensure_session_credentials(
            request, "kick_public_credentials", "Kick"
        )

        # Cache key for this endpoint
        cache_key = "kick:public:top_streams"

        # Try to get from cache first
        cached_data = await get_cache(cache_key)

        # Deserialize cached response into Stream models
        if isinstance(cached_data, dict) and "data" in cached_data:
            return {
                "data": [Stream.model_validate(item) for item in cached_data["data"]]
            }

        # If not in cache, fetch from Kick API
        response = await fetch_top_streams(credentials)

        # Convert to Stream models
        standardized = [
            Stream.model_validate(item) for item in response.get("data", [])
        ]
        # Cache for 2 minutes (120 seconds)
        await set_cache(cache_key, {"data": standardized}, 120)
        return {"data": standardized}
    except Exception as e:
        logger.exception("Error fetching top Kick streams: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
