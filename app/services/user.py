from typing import Dict, List

import httpx
from fastapi import HTTPException

from app.core.config import TWITCH_CLIENT_ID


async def get_user_profile(access_token):
    """Retrieve user profile from Twitch API."""
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/users", headers=headers
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user profile")

    data = response.json()
    return data.get("data", [{}])[0] if data.get("data") else {}


async def get_user_follows(access_token: str, user_id: str) -> List[Dict]:
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
    params = {"user_id": user_id, "first": 100}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.twitch.tv/helix/streams/followed",
                headers=headers,
                params=params,
            )
        return response.json()
    except Exception as e:
        print(f"Error fetching users followed streamers: {e}")
        raise HTTPException(status_code=400, detail="Failed to retrieve top streams")