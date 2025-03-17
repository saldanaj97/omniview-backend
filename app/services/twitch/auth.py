from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

import app.core.config as config


def get_authorization_url(state=None):
    """Generate the Twitch authorization URL."""
    # Correctly format the scopes
    scopes = config.TWITCH_SCOPES

    params = {
        "client_id": config.TWITCH_CLIENT_ID,
        "redirect_uri": config.CALLBACK_URL,
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
        "redirect_uri": config.CALLBACK_URL,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://id.twitch.tv/oauth2/token", data=params)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")

    return response.json()


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

    return response.json()
