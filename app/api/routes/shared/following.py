import logging
from typing import Any, Dict, List, Literal

import googleapiclient.discovery
from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies.twitch_auth import require_twitch_auth
from app.api.dependencies.youtube_auth import require_google_auth
from app.core.config import GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION
from app.schemas.followed_streamer import FollowedStreamer
from app.services.google.user import (
    check_all_channels_live_status,
    enrich_and_filter_live_subscriptions,
    fetch_all_subscriptions,
)
from app.services.twitch import user as twitch_user
from app.utils.redis_cache import get_cache, set_cache

router = APIRouter()
logger = logging.getLogger(__name__)


CACHE_EXPIRY_SECONDS = 120


def stream_data_to_unified_format(
    stream_data: Dict[str, Any], platform: Literal["twitch", "youtube"]
) -> FollowedStreamer:
    """Convert platform-specific stream data to unified FollowedStreamer format."""
    return FollowedStreamer(
        id=stream_data["id"],
        login=stream_data.get("login", stream_data.get("user_login", "")),
        display_name=stream_data["display_name"],
        type=stream_data.get("type", ""),
        broadcaster_type=stream_data.get("broadcaster_type", ""),
        description=stream_data.get("description", ""),
        profile_image_url=stream_data.get("profile_image_url", ""),
        offline_image_url=stream_data.get("offline_image_url", ""),
        view_count=stream_data.get("view_count", 0),
        created_at=stream_data.get("created_at", ""),
        user_id=stream_data["user_id"],
        user_login=stream_data.get("user_login", stream_data.get("login", "")),
        user_name=stream_data["display_name"],
        game_id=stream_data.get("game_id", ""),
        game_name=stream_data.get("game_name", ""),
        title=stream_data["title"],
        viewer_count=stream_data["viewer_count"],
        started_at=stream_data["started_at"],
        language=stream_data["language"],
        thumbnail_url=stream_data["thumbnail_url"],
        tag_ids=stream_data.get("tag_ids", []),
        tags=stream_data.get("tags", []),
        is_mature=stream_data["is_mature"],
        livechat_id=stream_data.get("livechat_id", None),
        video_id=stream_data.get("video_id", None),
        platform=platform,
    )


async def get_twitch_streams(request: Request) -> List[FollowedStreamer]:
    """Fetch followed streams from Twitch if authenticated."""
    twitch_streams: List[FollowedStreamer] = []

    try:
        creds, user = None, None
        try:
            creds, user = await require_twitch_auth(request)
        except HTTPException:
            logger.info("Twitch auth not available, skipping Twitch streams")
            return []

        if creds and user and "id" in user and "access_token" in creds:
            raw_streams = await twitch_user.get_user_follows(
                access_token=creds["access_token"], user_id=user["id"]
            )

            twitch_streams = [
                stream_data_to_unified_format(stream.model_dump(), "twitch")
                for stream in raw_streams
            ]

            logger.info("Fetched %d Twitch streams", len(twitch_streams))
    except Exception as e:
        logger.error("Error fetching Twitch streams: %s", str(e))

    return twitch_streams


async def get_youtube_streams(request: Request) -> List[FollowedStreamer]:
    """Fetch followed streams from YouTube if authenticated."""
    youtube_streams: List[FollowedStreamer] = []

    try:
        credentials = None
        try:
            credentials = await require_google_auth(request)
        except HTTPException:
            logger.info("Google auth not available, skipping YouTube streams")
            return []

        if credentials:
            youtube = googleapiclient.discovery.build(
                GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION, credentials=credentials
            )

            all_subscriptions = await fetch_all_subscriptions(youtube)
            live_statuses = await check_all_channels_live_status(all_subscriptions)
            raw_streams = enrich_and_filter_live_subscriptions(
                all_subscriptions, live_statuses
            )

            youtube_streams = [
                stream_data_to_unified_format(stream.model_dump(), "youtube")
                for stream in raw_streams
            ]

            logger.info("Fetched %d YouTube streams", len(youtube_streams))
    except Exception as e:
        logger.error("Error fetching YouTube streams: %s", str(e))

    return youtube_streams


async def get_user_id_from_session(request: Request) -> str:
    """Extract user ID from session if available from any platform."""
    user_ids = []

    if "session" in request.scope:
        session = request.session

        # Check for Twitch user ID
        if "twitch_user_profile" in session and session["twitch_user_profile"]:
            twitch_profile = (
                session["twitch_user_profile"][0]
                if session["twitch_user_profile"]
                else {}
            )
            if "id" in twitch_profile:
                user_ids.append(f"{twitch_profile['id']}")

        # Check for YouTube/Google user ID
        if "google_credentials" in session:
            try:
                credentials = session["google_credentials"]
                youtube = googleapiclient.discovery.build(
                    GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION, credentials=credentials
                )
                channel_resp = youtube.channels().list(part="id", mine=True).execute()
                channel_id = channel_resp["items"][0]["id"]
                user_ids.append(f"{channel_id}")
            except Exception as e:
                logger.error("Error fetching YouTube channel ID: %s", str(e))

    # Generate a composite ID from all available platform IDs, or use "anonymous" if none
    return "_".join(user_ids) if user_ids else "anonymous"


@router.get("/following", response_model=List[FollowedStreamer])
async def get_followed_streams(request: Request) -> List[FollowedStreamer]:
    """
    Unified endpoint to get followed streams from all connected platforms.
    Returns a combined list of streams that the user follows across all platforms.
    """
    # Check for cached results first
    user_id = await get_user_id_from_session(request)
    cache_key = f"unified:following:{user_id}"
    cached_data = await get_cache(cache_key)

    if cached_data:
        logger.info("Returning cached followed streams for user %s", user_id)
        return [FollowedStreamer.model_validate(item) for item in cached_data]

    # Fetch streams from authenticated platforms
    has_twitch_session = (
        "session" in request.scope and "twitch_credentials" in request.session
    )
    has_youtube_session = (
        "session" in request.scope and "google_credentials" in request.session
    )

    twitch_streams = await get_twitch_streams(request) if has_twitch_session else []
    youtube_streams = await get_youtube_streams(request) if has_youtube_session else []

    # Combine results from all platforms
    results = twitch_streams + youtube_streams

    # Sort by viewer count (descending)
    results.sort(key=lambda x: x.viewer_count, reverse=True)

    # Cache the results
    await set_cache(
        cache_key, [stream.model_dump() for stream in results], CACHE_EXPIRY_SECONDS
    )

    return results
