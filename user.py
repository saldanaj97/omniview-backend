import httpx
from fastapi import HTTPException

import config

TWITCH_SCOPES = "user:read:follows"


async def get_user_profile(access_token):
    """Retrieve user profile from Twitch API."""
    headers = {
        "Client-ID": config.TWITCH_CLIENT_ID,
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


async def get_user_follows(access_token, user_id):
    """Retrieve user follows from Twitch API."""
    headers = {
        "Client-ID": config.TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
    }

    # Adjust as needed
    params = {
        "user_id": user_id,
        "first": 10,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/channels/followed",
            headers=headers,
            params=params,
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user follows")

    data = response.json()
    return data.get("data", [])
