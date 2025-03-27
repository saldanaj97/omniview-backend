import googleapiclient.discovery
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.youtube_auth import require_google_auth
from app.core.config import GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION
from app.services.google.subscriptions import (
    check_all_channels_live_status,
    enrich_and_filter_live_subscriptions,
    fetch_all_subscriptions,
)

router = APIRouter()


@router.get("/subscriptions/live")
async def get_subscriptions(credentials=Depends(require_google_auth)):
    """Get list of user's subscriptions that are currently live streaming"""
    try:
        youtube = googleapiclient.discovery.build(
            GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION, credentials=credentials
        )

        # Fetch all subscriptions and check their live status
        all_subscriptions = await fetch_all_subscriptions(youtube)
        live_statuses = await check_all_channels_live_status(all_subscriptions)

        # Enrich subscription data with live status information
        live_subscriptions = enrich_and_filter_live_subscriptions(
            all_subscriptions, live_statuses
        )

        return live_subscriptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch subscriptions",
                "message": str(e),
            },
        ) from e
