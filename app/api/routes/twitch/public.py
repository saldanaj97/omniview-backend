import logging

from fastapi import APIRouter, HTTPException, Request

from app.api.routes.twitch.auth import twitch_public_token
from app.schemas.top_streams import Stream
from app.services.twitch import public
from app.utils.http_utils import ensure_session_credentials
from app.utils.redis_cache import get_cache, set_cache

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/top_streams")
async def top_streams(request: Request):
    try:
        try:
            credentials = ensure_session_credentials(
                request, "twitch_public_credentials", "Twitch"
            )
        except HTTPException:
            # Generate public token if not present
            try:
                credentials = await twitch_public_token(request)
                request.session["twitch_public_credentials"] = credentials
            except Exception as e:
                logger.error("Failed to generate Twitch public token: %s", str(e))
                raise HTTPException(
                    status_code=500, detail="Failed to generate Twitch public token"
                ) from e

        # Cache key for this endpoint
        cache_key = "twitch:public:top_streams"

        # Try to get from cache first
        cached_data = await get_cache(cache_key)

        # Deserialize cached response into Stream models
        if isinstance(cached_data, dict) and "data" in cached_data:
            return {
                "data": [Stream.model_validate(item) for item in cached_data["data"]]
            }

        # If not in cache, fetch from Twitch API
        response = await public.get_top_streams(credentials)

        # Convert to Stream models
        standardized = [
            Stream.model_validate(item) for item in response.get("data", [])
        ]

        # Cache for 2 minutes (120 seconds) since stream data changes frequently
        await set_cache(cache_key, {"data": standardized}, 60)
        return {"data": standardized}
    except Exception as e:
        logger.exception("Error fetching top Twitch streams: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
