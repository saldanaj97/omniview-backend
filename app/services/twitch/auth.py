import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request

import app.core.config as config


def get_authorization_url(state=None):
    """Generate the Twitch authorization URL."""
    scopes = config.TWITCH_SCOPES

    params = {
        "client_id": config.TWITCH_CLIENT_ID,
        "redirect_uri": config.TWITCH_CALLBACK_URL,
        "response_type": "code",
        "scope": scopes,
    }

    if state:
        params["state"] = state

    return f"https://id.twitch.tv/oauth2/authorize?{urlencode(params)}"


async def get_oauth_token(code):
    """Exchange authorization code for OAuth tokens."""

    params = {
        "client_id": config.TWITCH_CLIENT_ID,
        "client_secret": config.TWITCH_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": config.TWITCH_CALLBACK_URL,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://id.twitch.tv/oauth2/token", data=params)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")

    token_data = response.json()
    token_data["last_validated"] = time.time()
    return token_data


async def refresh_oauth_token(refresh_token):
    """Refresh an expired OAuth token using the refresh token."""
    params = {
        "client_id": config.TWITCH_CLIENT_ID,
        "client_secret": config.TWITCH_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://id.twitch.tv/oauth2/token", data=params)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to refresh access token")

    return response.json()


async def validate_access_token(access_token):
    """Check if the access token is still valid."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://id.twitch.tv/oauth2/validate",
            headers={"Authorization": f"OAuth {access_token}"},
        )
    return response.status_code == 200


async def ensure_valid_token(request):
    """
    Check if the current token is valid, refresh if needed, and update the session.
    Returns True if a valid token is available, False otherwise.
    Validates tokens on an hourly basis as required by Twitch API docs.
    """
    if "session" not in request.scope or "twitch_credentials" not in request.session:
        return False

    credentials = request.session["twitch_credentials"]
    access_token = credentials.get("access_token")
    refresh_token = credentials.get("refresh_token")
    last_validated = credentials.get("last_validated", 0)

    if not access_token:
        return False

    # Force validation if it's been more than an hour since last validation
    current_time = time.time()
    one_hour_in_seconds = 3600
    force_validation = (current_time - last_validated) >= one_hour_in_seconds

    # If refresh_token is missing or we need to force validation
    if force_validation or not refresh_token:
        is_valid = await validate_access_token(access_token)
        credentials["last_validated"] = current_time
        request.session["twitch_credentials"] = credentials

        # Token invalid and no refresh token, return False
        if is_valid:
            return True
        elif not refresh_token:
            return False
    elif last_validated > 0:
        # We have a last_validated time and don't need to force validation
        return True

    # Token is invalid or we need to refresh, try to refresh
    try:
        new_token_data = await refresh_oauth_token(refresh_token)
        new_token_data["last_validated"] = current_time
        request.session["twitch_credentials"] = new_token_data
        return True
    except HTTPException:
        # If refresh fails, clear credentials and return False
        request.session.pop("twitch_credentials", None)
        return False


async def verify_token(request: Request):
    """Dependency to verify token is valid and refresh if needed."""
    valid = await ensure_valid_token(request)
    if not valid:
        raise HTTPException(
            status_code=401, detail="Authentication required or token expired"
        )
    return request.session["twitch_credentials"]


async def get_client_credentials_oauth_token():
    """Client credentials grant flow."""
    params = {
        "client_id": config.TWITCH_CLIENT_ID,
        "client_secret": config.TWITCH_SECRET,
        "grant_type": "client_credentials",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://id.twitch.tv/oauth2/token", data=params)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")

    token_data = response.json()
    token_data["last_validated"] = time.time()
    return token_data
