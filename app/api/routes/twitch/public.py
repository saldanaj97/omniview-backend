import logging

from fastapi import APIRouter, HTTPException, Request

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
        credentials = ensure_session_credentials(
            request, "twitch_public_credentials", "Twitch"
        )

        cache_key = "twitch:public:top_streams"
        cached_data = await get_cache(cache_key)

        if isinstance(cached_data, dict) and "data" in cached_data:
            return {
                "data": [Stream.model_validate(item) for item in cached_data["data"]]
            }

        response = await public.get_top_streams(credentials)
        standardized = [
            Stream.model_validate(item) for item in response.get("data", [])
        ]

        await set_cache(cache_key, {"data": standardized}, 60)
        return {"data": standardized}
    except Exception as e:
        logger.exception("Error fetching top Twitch streams: %s", str(e))
        raise HTTPException(
            status_code=500, detail="Error fetching Twitch streams"
        ) from e
