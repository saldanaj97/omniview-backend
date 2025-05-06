import logging
from typing import Any, Dict, List, Literal

import googleapiclient.discovery
from fastapi import HTTPException, Request

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
from app.utils.redis_cache import set_cache

logger = logging.getLogger(__name__)


def stream_data_to_unified_format(
    stream_data: Dict[str, Any], platform: Literal["twitch", "youtube"]
) -> FollowedStreamer:
    """Convert platform-specific stream data to unified FollowedStreamer format."""
    return FollowedStreamer(
        id=stream_data["id"],
        login=stream_data.get("login", stream_data.get("user_login", "")),
        display_name=stream_data["display_name"],
        type=stream_data.get("type", "live"),
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


async def get_user_id_from_session(
    request: Request, platform: Literal["youtube", "twitch"]
) -> str:
    """Extract user ID from session if available from any platform."""

    if "session" in request.scope:
        session = request.session

        # Check for Twitch user ID
        if (
            "twitch_user_profile" in session
            and session["twitch_user_profile"]
            and platform == "twitch"
        ):
            twitch_profile = (
                session["twitch_user_profile"][0]
                if session["twitch_user_profile"]
                else {}
            )
            if "id" in twitch_profile:
                return twitch_profile["id"]

        # Check for YouTube/Google user ID
        if platform == "youtube":
            try:
                credentials = await require_google_auth(request)
                youtube = googleapiclient.discovery.build(
                    GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION, credentials=credentials
                )
                channel_resp = youtube.channels().list(part="id", mine=True).execute()  # type: ignore[attr-defined]
                return channel_resp["items"][0]["id"]
            except HTTPException:
                logger.info(
                    "Google auth not available, skipping session YouTube user ID"
                )
                return ""
            except Exception as e:
                logger.error("Error fetching YouTube channel ID: %s", str(e))
    return ""


def _fetch_and_cache_streams(
    *,
    has_session: bool,
    cached_data,
    user_id,
    cache_key,
    fetch_func,
    cache_expiry,
    logger_prefix: str,
    request: Request,
):
    """
    Helper to fetch followed streams for a platform, using cache if available.
    Returns a coroutine.
    """

    async def _inner():
        if not has_session:
            return []
        if cached_data:
            logger.info(
                f"Returning cached {logger_prefix} followed streams for user %s",
                user_id,
            )
            return [FollowedStreamer.model_validate(item) for item in cached_data]
        streams = await fetch_func(request)
        await set_cache(
            cache_key,
            [stream.model_dump() for stream in streams],
            cache_expiry,
        )
        return streams

    return _inner()
