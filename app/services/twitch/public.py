from typing import Dict, List

import httpx
from fastapi import HTTPException, Request

from app.core.config import TWITCH_CLIENT_ID
from app.utils.http_utils import (
    check_twitch_response_status,
    ensure_session_credentials,
)


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


async def get_top_streams(request: Request) -> List[Dict]:
    """
    Get the list of top streams from Twitch

    Returns:
        A list of streams from Twitch.
    """
    credentials = ensure_session_credentials(
        request, "twitch_public_credentials", "Twitch"
    )

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

        return response.json()
