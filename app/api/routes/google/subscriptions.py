import google.oauth2.credentials
import googleapiclient.discovery
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.core.config import GOOGLE_API_SERVICE_NAME, GOOGLE_API_VERSION
from app.services.google.auth import credentials_to_dict
from app.services.google.subscriptions import (
    check_all_channels_live_status,
    enrich_and_filter_live_subscriptions,
    fetch_all_subscriptions,
)

router = APIRouter()


@router.get("/")
async def index(request: Request):
    """Home page with authentication link"""
    if "credentials" in request.session:
        return request.session["credentials"]
    return {
        "message": "You are not authenticated. Please log in using the link below.",
        "link": str(request.url_for("authorize")),
    }


@router.get("/subscriptions")
async def get_subscriptions(request: Request):
    """Get list of user's subscriptions that are currently live streaming"""
    if "credentials" not in request.session:
        return RedirectResponse(url=request.url_for("authorize"))

    credentials = google.oauth2.credentials.Credentials(
        **request.session["credentials"]
    )
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

    # Update credentials in session in case token was refreshed
    request.session["credentials"] = credentials_to_dict(credentials)

    return live_subscriptions
