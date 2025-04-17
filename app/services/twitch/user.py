from typing import Dict, List

import httpx
from fastapi import HTTPException

from app.core.config import TWITCH_CLIENT_ID
from app.utils.http_utils import raise_for_status


async def get_user_profile(access_token, user_ids=[]):
    """Retrieve user profiles from Twitch API."""
    request_url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
    }
    params = [("login", user_id) for user_id in user_ids] if user_ids else []

    async with httpx.AsyncClient() as client:
        response = await client.get(request_url, headers=headers, params=params)

    raise_for_status(response, context="Failed to retrieve user profile")

    data = response.json()
    return data.get("data", [])


async def get_user_follows(access_token: str, user_id: str) -> List[Dict]:
    """
    Get the list of users that the specified user is following
    """
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
    }
    params = {"user_id": user_id, "first": 100}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.twitch.tv/helix/streams/followed",
            headers=headers,
            params=params,
        )

    raise_for_status(response)

    data = response.json()
    if "data" not in data:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected response format from Twitch API: {data}",
        )

    # Retrieve the rest of the data for each user
    user_logins = [user["user_login"] for user in data["data"]]
    user_info_list = await get_user_profile(access_token, user_logins)

    # Combine each original user dict with the corresponding user_info dict
    combined = []
    login_to_info = {info["login"]: info for info in user_info_list}
    for user_item in data["data"]:
        login = user_item["user_login"]
        extra_info = login_to_info.get(login, {})
        merged = {**extra_info, **user_item}
        combined.append(merged)
    return combined
