import logging

import google.oauth2.credentials
import google_auth_oauthlib.flow
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleAuthRequest

from app.core.config import (
    FRONTEND_URL,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_FLOW_REDIRECT_URI,
    GOOGLE_SCOPES,
)
from app.services.google.auth import credentials_to_dict

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/authenticated")
async def index(request: Request):
    """Home page with an authentication link"""
    if request.session.get("google_credentials"):
        return request.session["google_credentials"]

    return {
        "message": "YouTube Live Broadcasts API",
        "authenticate": f"{request.url_for('authorize')}",
    }


@router.get("/authorize")
async def authorize(request: Request):
    """Initiate OAuth flow"""
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        GOOGLE_CLIENT_SECRET, scopes=GOOGLE_SCOPES
    )

    flow.redirect_uri = GOOGLE_FLOW_REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )

    request.session["state"] = state
    return {"url": authorization_url}


@router.get("/oauth2callback")
async def oauth2callback(request: Request):
    """Handle OAuth callback"""
    state = request.query_params.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="State not found in session")

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        GOOGLE_CLIENT_SECRET, scopes=GOOGLE_SCOPES, state=state
    )
    flow.redirect_uri = GOOGLE_FLOW_REDIRECT_URI

    # Fix: Force HTTPS for Railway deployment
    url = str(request.url)
    if url.startswith("http:"):
        url = "https:" + url[5:]

    # Get the authorization response URL
    authorization_response = str(url)
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in session
    credentials = flow.credentials
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found")

    # Store the credentials in the session
    if "session" in request.scope:
        # Preserve existing Twitch credentials if present
        twitch_credentials = request.session.get("twitch_credentials")
        twitch_user_profile = request.session.get("twitch_user_profile")

        # Update Google credentials
        request.session["google_credentials"] = credentials_to_dict(credentials)

        # Restore Twitch credentials if they existed
        if twitch_credentials:
            request.session["twitch_credentials"] = twitch_credentials
        if twitch_user_profile:
            request.session["twitch_user_profile"] = twitch_user_profile

    return RedirectResponse(url=f"{FRONTEND_URL}/auth/success", status_code=302)


@router.get("/oauth/refresh")
async def refresh_token(request: Request):
    """
    Refresh the user's Google access token if needed.

    Returns:
        JSON with refresh status
    """
    if "session" not in request.scope or "google_credentials" not in request.session:
        raise HTTPException(
            status_code=401,
            detail={"message": "Not authenticated with Google", "refreshed": False},
        )

    try:
        # Save existing Twitch credentials if present
        twitch_credentials = request.session.get("twitch_credentials")
        twitch_user_profile = request.session.get("twitch_user_profile")

        google_credentials = request.session["google_credentials"]

        # Check if the credential dictionary has minimum required fields
        required_fields = ["token", "refresh_token", "client_id", "client_secret"]
        for field in required_fields:
            if field not in google_credentials:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": f"Missing required credential field: {field}",
                        "refreshed": False,
                    },
                )

        # Create credentials object
        credentials = google.oauth2.credentials.Credentials(
            token=google_credentials["token"],
            refresh_token=google_credentials["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=google_credentials["client_id"],
            client_secret=google_credentials["client_secret"],
        )

        # Check if expired and refresh if needed
        if credentials.refresh_token:
            request_object = GoogleAuthRequest()
            credentials.refresh(request_object)

            # Update the session with the refreshed credentials
            request.session["google_credentials"] = credentials_to_dict(credentials)

            # Restore Twitch credentials if they existed
            if twitch_credentials:
                request.session["twitch_credentials"] = twitch_credentials
            if twitch_user_profile:
                request.session["twitch_user_profile"] = twitch_user_profile

            return {
                "message": "Token refreshed successfully",
                "refreshed": True,
                "platform": "youtube",
            }

        # No refresh token, can't refresh
        if "refresh_token" not in google_credentials:
            await logout(request)
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "No refresh token available, please login again. ",
                    "refreshed": False,
                    "platform": "youtube",
                },
            )

        return {
            "message": "Token is still valid",
            "refreshed": False,
            "platform": "youtube",
        }

    except Exception as e:
        logger.error("Error refreshing Google token: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error refreshing token: {str(e)}",
                "refreshed": False,
                "platform": "youtube",
            },
        ) from e


@router.get("/logout")
async def logout(request: Request):
    """Log the user out of the session"""
    if not request.session or "google_credentials" not in request.session:
        return {
            "message": "No active session found",
            "platform": "youtube",
        }

    request.session.pop("google_credentials", None)

    return {
        "message": "User has been logged out of Youtube successfully.",
        "platform": "youtube",
    }
