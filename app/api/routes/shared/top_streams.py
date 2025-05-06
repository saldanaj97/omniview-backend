import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas.top_streams import Stream
from app.services.google.public import fetch_top_streams as youtube_fetch_top_streams
from app.services.kick.public import fetch_top_streams as kick_fetch_top_streams
from app.services.twitch import public as twitch_public
from app.utils.http_utils import ensure_session_credentials
from app.utils.redis_cache import get_cache, set_cache

logger = logging.getLogger(__name__)

router = APIRouter()

TWITCH_CACHE_EXPIRY_SECONDS = 60
KICK_CACHE_EXPIRY_SECONDS = 120
YOUTUBE_CACHE_EXPIRY_SECONDS = 1200


@router.get("/top_streams")
async def top_streams(request: Request):
    """
    Unified endpoint to get top streams from Twitch, Kick, and YouTube in parallel.
    Returns a dict with each platform's top streams.
    """
    try:
        # Prepare cache keys
        twitch_cache_key = "twitch:public:top_streams"
        kick_cache_key = "kick:public:top_streams"
        youtube_cache_key = "google:public:top_streams"

        # Prepare credential fetches
        twitch_credentials = ensure_session_credentials(
            request, "twitch_public_credentials", "Twitch"
        )
        kick_credentials = ensure_session_credentials(
            request, "kick_public_credentials", "Kick"
        )
        youtube_credentials = ensure_session_credentials(request, "", "Youtube")

        # Prepare fetch functions
        async def get_twitch():
            cached = await get_cache(twitch_cache_key)
            if isinstance(cached, dict) and "data" in cached:
                return [Stream.model_validate(item) for item in cached["data"]]
            response = await twitch_public.get_top_streams(twitch_credentials)
            standardized = [
                Stream.model_validate(item) for item in response.get("data", [])
            ]
            await set_cache(
                twitch_cache_key, {"data": standardized}, TWITCH_CACHE_EXPIRY_SECONDS
            )
            return standardized

        async def get_kick():
            cached = await get_cache(kick_cache_key)
            if isinstance(cached, dict) and "data" in cached:
                return [Stream.model_validate(item) for item in cached["data"]]
            response = await kick_fetch_top_streams(kick_credentials)
            standardized = [
                Stream.model_validate(item) for item in response.get("data", [])
            ]
            await set_cache(
                kick_cache_key, {"data": standardized}, KICK_CACHE_EXPIRY_SECONDS
            )
            return standardized

        async def get_youtube():
            cached = await get_cache(youtube_cache_key)
            if isinstance(cached, dict) and "data" in cached:
                return [Stream.model_validate(item) for item in cached["data"]]
            response = await youtube_fetch_top_streams(youtube_credentials)
            standardized = [
                Stream.model_validate(item) for item in response.get("data", [])
            ]
            await set_cache(
                youtube_cache_key, {"data": standardized}, YOUTUBE_CACHE_EXPIRY_SECONDS
            )
            return standardized

        # Fetch top streams in parallel
        twitch_streams, kick_streams, youtube_streams = await asyncio.gather(
            get_twitch(), get_kick(), get_youtube()
        )

        return {
            "twitch": twitch_streams,
            "kick": kick_streams,
            "youtube": youtube_streams,
        }
    except Exception as e:
        logger.exception("Error fetching top streams: %s", str(e))
        raise HTTPException(status_code=500, detail="Error fetching top streams") from e
