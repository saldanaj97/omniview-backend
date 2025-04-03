from typing import Dict, List

import httpx
from fastapi import HTTPException, Request

from app.core.config import TWITCH_CLIENT_ID


async def check_public_login_status(request: Request) -> Dict:
    """
    Public endpoint to check which platforms have access tokens available.
    This is used for public access without requiring a session.
    """
    if not request.session.get("twitch_public_credentials"):
        return {
            "data": [
                {
                    "platform": "Twitch",
                    "accessTokenAvailable": False,
                }
            ],
            "error": None,
        }

    return {
        "data": [
            {
                "platform": "Twitch",
                "accessTokenAvailable": True,
            }
        ],
        "error": None,
    }


async def get_top_streams(access_token) -> List[Dict]:
    """
    Get the list of users that the specified user is following

    Args:
        access_token: The user's access token for API authentication
        user_id: The ID of the user whose following list to retrieve

    Returns:
        A list of users that the specified user is following
    """
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers,
            )
        return response.json()
    except Exception as e:
        print(f"Error fetching top streams: {e}")
        raise HTTPException(status_code=400, detail="Failed to retrieve top streams")
