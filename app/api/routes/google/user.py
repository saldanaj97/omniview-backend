import googleapiclient.discovery
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies.youtube_auth import require_google_auth
from app.core.config import GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION
from app.services.google.user import (
    check_all_channels_live_status,
    enrich_and_filter_live_subscriptions,
    fetch_all_subscriptions,
)
from app.utils.redis_cache import get_cache, set_cache  # added import

router = APIRouter()


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
        if cached_data:
            return JSONResponse(content={"data": cached_data})

        # Fetch all subscriptions and check their live status
        all_subscriptions = await fetch_all_subscriptions(youtube)
        live_statuses = await check_all_channels_live_status(all_subscriptions)

        # Enrich subscription data with live status information
        live_subscriptions = enrich_and_filter_live_subscriptions(
            all_subscriptions, live_statuses
        )

        # Serialize FollowedStreamer models to dictionaries
        serialized_live_subs = [sub.model_dump() for sub in live_subscriptions]

        await set_cache(cache_key, serialized_live_subs, 120)  # cache result

        return JSONResponse(content={"data": serialized_live_subs})
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Failed to get subscriptions that are currently live.",
                "message": str(e),
            },
            status_code=500,
        )
