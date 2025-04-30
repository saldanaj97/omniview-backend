import logging

import googleapiclient.discovery
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.youtube_auth import require_google_auth
from app.core.config import GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION
from app.schemas.followed_streamer import FollowedStreamer
from app.services.google.user import (
    check_all_channels_live_status,
    enrich_and_filter_live_subscriptions,
    fetch_all_subscriptions,
)
from app.utils.redis_cache import get_cache, set_cache

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/subscriptions")
async def get_subscriptions(credentials=Depends(require_google_auth)):
    """Get list of user's subscriptions that are currently live streaming"""
    try:
        # build the client so we can fetch the user's channel ID
        youtube = googleapiclient.discovery.build(
            GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION, credentials=credentials
        )

        # get the current user's channel id
        channel_resp = youtube.channels().list(part="id", mine=True).execute()
        channel_id = channel_resp["items"][0]["id"]

        # now namespace the cache key per‐user
        cache_key = f"google:subscriptions:{channel_id}"
        cached_data = await get_cache(cache_key)

        # Deserialize cached response into FollowedStreamer models
        if cached_data:
            return {
                "data": [FollowedStreamer.model_validate(item) for item in cached_data]
            }

        # Fetch all subscriptions and check their live status
        all_subscriptions = await fetch_all_subscriptions(youtube)
        live_statuses = await check_all_channels_live_status(all_subscriptions)

        # Enrich subscription data with live status information
        live_subscriptions = enrich_and_filter_live_subscriptions(
            all_subscriptions, live_statuses
        )

        # Cache the serializable data for 2 minutes
        await set_cache(
            cache_key, [sub.model_dump() for sub in live_subscriptions], 120
        )

        return {"data": live_subscriptions}
    except Exception as e:
        logger.exception("Error fetching YouTube subscriptions: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
