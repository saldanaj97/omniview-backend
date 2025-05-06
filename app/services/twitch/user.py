from typing import Dict, List

import httpx
from fastapi import HTTPException

from app.core.config import TWITCH_CLIENT_ID
from app.schemas.followed_streamer import FollowedStreamer
from app.utils.http_utils import check_twitch_response_status


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

    check_twitch_response_status(response, context="Failed to retrieve user profile")

    data = response.json()
    return data.get("data", [])


async def get_user_follows(access_token: str, user_id: str) -> List[FollowedStreamer]:
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

    check_twitch_response_status(response)

    data = response.json()
    if "data" not in data:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected response format from Twitch API: {data}",
        )

    # Retrieve the rest of the data for each user
    user_logins = [user["user_login"] for user in data["data"]]
    user_info_list = await get_user_profile(access_token, user_logins)

    # Combine each original user dict with the corresponding user_info dict.
    # Standardize the merged data to the FollowedStreamer format.
    combined = []
    login_to_info = {info["login"]: info for info in user_info_list}
    for user_item in data["data"]:
        login = user_item["user_login"]
        extra_info = login_to_info.get(login, {})
        merged = {**extra_info, **user_item}
        combined.append(standardize_data(merged))
    return combined


def standardize_data(user_data: dict) -> FollowedStreamer:
    """Converts merged Twitch user data to the FollowedStreamer format."""
    return FollowedStreamer(
        id=user_data.get("id", ""),
        login=user_data.get("login", ""),
        display_name=user_data.get("display_name", user_data.get("login", "")),
        type=user_data.get("type", ""),
        broadcaster_type=user_data.get("broadcaster_type", ""),
        description=user_data.get("description", ""),
        profile_image_url=user_data.get("profile_image_url", ""),
        offline_image_url=user_data.get("offline_image_url", ""),
        view_count=user_data.get("view_count", 0),
        created_at=user_data.get("created_at", ""),
        user_id=user_data.get("id", ""),
        user_login=user_data.get("login", ""),
        user_name=user_data.get("display_name", user_data.get("login", "")),
        game_id=user_data.get("game_id", ""),
        game_name=user_data.get("game_name", ""),
        title=user_data.get("title", ""),
        viewer_count=user_data.get("viewer_count", 0),
        started_at=user_data.get("started_at", ""),
        language=user_data.get("language", ""),
        thumbnail_url=user_data.get("thumbnail_url", ""),
        tag_ids=user_data.get("tag_ids", []),
        tags=user_data.get("tags", []),
        is_mature=user_data.get("is_mature", False),
        platform="twitch",
    )
