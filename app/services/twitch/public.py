import logging
from typing import Dict

import httpx
from fastapi import HTTPException, Request

from app.core.config import TWITCH_CLIENT_ID
from app.utils.http_utils import (
    check_twitch_response_status,
    ensure_session_credentials,
)

# Set up logging
logger = logging.getLogger(__name__)


async def check_public_login_status(request: Request) -> Dict:
    """
    Public endpoint to check which platforms have access tokens available.
    This is used for public access without requiring a session.
    """
    try:
        ensure_session_credentials(request, "twitch_public_credentials", "Twitch")
        available = True
    except HTTPException:
        available = False

    return {
        "data": [
            {
                "platform": "Twitch",
                "accessTokenAvailable": available,
            }
        ],
        "error": None,
    }


def standardize_twitch_stream_data(item: dict) -> dict:
    """
    Convert raw Twitch stream data into unified Stream schema.
    """
    return {
        "id": item.get("id", ""),
        "user_id": item.get("user_id", ""),
        "user_name": item.get("user_name", item.get("user_login", "")),
        "title": item.get("title", ""),
        "viewer_count": item.get("viewer_count", 0),
        "started_at": item.get("started_at", ""),
        "language": item.get("language", ""),
        "thumbnail_url": item.get("thumbnail_url", ""),
        "is_mature": item.get("is_mature", False),
        "platform": "twitch",
        "game_name": item.get("game_name", None),
        "stream_type": item.get("type", None),
        "profile_image_url": None,
    }


async def get_top_streams(credentials) -> dict:
    """
    Get the list of top streams from Twitch

    Returns:
        A list of streams from Twitch.
    """

    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {credentials.get('access_token')}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/streams",
            headers=headers,
        )
        check_twitch_response_status(response, context="Failed to retrieve top streams")

        response_data = response.json()
        # Standardize each stream into unified schema
        streams = (
            response_data.get("data", [])
            if isinstance(response_data.get("data"), list)
            else []
        )
        unified = [standardize_twitch_stream_data(item) for item in streams]

        # Fetch profile images for each streamer
        if unified:
            await fetch_profile_images(client, headers, unified)

        return {"data": unified}


async def fetch_profile_images(
    client: httpx.AsyncClient, headers: dict, unified: list
) -> None:
    """
    Fetch profile images for each streamer in the unified list.
    This function modifies the unified list in place to add the profile_image_url.
    """
    # Fetch profile images for each streamer
    user_ids = list({stream["user_id"] for stream in unified if stream["user_id"]})
    if user_ids:
        params = [("id", uid) for uid in user_ids]
        profile_response = await client.get(
            "https://api.twitch.tv/helix/users",
            headers=headers,
            params=params,
        )
        check_twitch_response_status(
            profile_response,
            context="Failed to retrieve user profiles",
        )
        profile_data = profile_response.json().get("data", [])
        id_to_image = {
            user["id"]: user.get("profile_image_url") for user in profile_data
        }
        for stream in unified:
            stream["profile_image_url"] = id_to_image.get(stream["user_id"])
