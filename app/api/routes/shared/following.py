import asyncio
import logging
from typing import List

from fastapi import APIRouter, Request

from app.schemas.followed_streamer import FollowedStreamer
from app.services.shared.following import (
    _fetch_and_cache_streams,
    get_twitch_streams,
    get_user_id_from_session,
    get_youtube_streams,
)
from app.utils.redis_cache import get_cache

# Constants for cache expiry. We use different expiry times for Twitch and YouTube
# to optimize due to quota limits for Youtube.
TWITCH_CACHE_EXPIRY_SECONDS = 60
YOUTUBE_CACHE_EXPIRY_SECONDS = 300

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/following", response_model=List[FollowedStreamer])
async def get_followed_streams(request: Request) -> List[FollowedStreamer]:
    """
    Unified endpoint to get followed streams from all connected platforms.
    Returns a combined list of streams that the user follows across all platforms.
    """
    twitch_user_id = await get_user_id_from_session(request, "twitch")
    twitch_cache_key = f"twitch:following:{twitch_user_id}"
    twitch_cached_data = await get_cache(twitch_cache_key)
    youtube_user_id = await get_user_id_from_session(request, "youtube")
    youtube_cache_key = f"youtube:following:{youtube_user_id}"
    youtube_cached_data = await get_cache(youtube_cache_key)

    has_twitch_session = (
        "session" in request.scope and "twitch_credentials" in request.session
    )
    has_youtube_session = (
        "session" in request.scope and "google_credentials" in request.session
    )

    twitch_streams, youtube_streams = await asyncio.gather(
        _fetch_and_cache_streams(
            has_session=has_twitch_session,
            cached_data=twitch_cached_data,
            user_id=twitch_user_id,
            cache_key=twitch_cache_key,
            fetch_func=get_twitch_streams,
            cache_expiry=TWITCH_CACHE_EXPIRY_SECONDS,
            logger_prefix="Twitch",
            request=request,
        ),
        _fetch_and_cache_streams(
            has_session=has_youtube_session,
            cached_data=youtube_cached_data,
            user_id=youtube_user_id,
            cache_key=youtube_cache_key,
            fetch_func=get_youtube_streams,
            cache_expiry=YOUTUBE_CACHE_EXPIRY_SECONDS,
            logger_prefix="YouTube",
            request=request,
        ),
    )

    results = twitch_streams + youtube_streams
    results.sort(key=lambda x: x.viewer_count, reverse=True)
    return results
