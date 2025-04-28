import httpx

from app.utils.http_utils import check_kick_response_status


async def fetch_top_streams(credentials) -> dict:
    """
    Fetch top streams from Kick API.
    """
    access_token = credentials.get("access_token")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.kick.com/public/v1/livestreams",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Bearer {access_token}",
            },
        )
        check_kick_response_status(response, "Kick API error")
        raw_data = response.json()

        # Standardize and enrich streams with user profiles
        standardized = standardize_livestream_data(raw_data)
        unified = standardized.get("data", [])

        # Fetch profile images and display names for each streamer
        user_ids = list(
            {stream["user_id"] for stream in unified if stream.get("user_id")}
        )
        if user_ids:
            profiles = await fetch_profile_pictures(user_ids, client, access_token)
            for stream in unified:
                uid = stream.get("user_id")
                profile = profiles.get(uid, {})
                stream["profile_image_url"] = profile.get(
                    "profile_picture", stream.get("profile_image_url")
                )
                stream["user_name"] = profile.get("name", stream.get("user_name"))

        return {"data": unified}


async def fetch_profile_pictures(
    user_ids: list, client: httpx.AsyncClient, access_token: str
) -> dict:
    """
    Fetch profile pictures and names for a list of user IDs.
    """
    if not user_ids:
        return {}

    params = [("id", uid) for uid in user_ids]
    response = await client.get(
        "https://api.kick.com/public/v1/users",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "*/*"},
        params=params,
    )
    check_kick_response_status(
        response, context="Failed to retrieve Kick user profiles"
    )

    # Build a mapping from user id to a dict with profile_picture and name
    profile_list = response.json().get("data", [])
    profiles = {
        str(u["user_id"]): {
            "profile_picture": u.get("profile_picture"),
            "name": u.get("name"),
        }
        for u in profile_list
    }
    return profiles


def standardize_kick_stream_data(item: dict) -> dict:
    """
    Convert raw Kick stream item into unified Stream schema.
    """
    return {
        "id": str(item.get("broadcaster_user_id", "")),
        "user_id": str(item.get("broadcaster_user_id", "")),
        "user_name": str(item.get("slug", "")),
        "title": item.get("stream_title", ""),
        "viewer_count": item.get("viewer_count", 0),
        "started_at": item.get("started_at", ""),
        "language": item.get("language", ""),
        "thumbnail_url": item.get("thumbnail", ""),
        "is_mature": item.get("has_mature_content", False),
        "platform": "kick",
        "game_name": item.get("category", {}).get("name", ""),
        "stream_type": "live",
        "profile_image_url": item.get("profile_image_url", ""),
    }


def standardize_livestream_data(raw_data: dict) -> dict:
    """
    Standardizes the raw Kick API response into the unified Stream type.
    """
    return {
        "data": [
            standardize_kick_stream_data(item) for item in raw_data.get("data", [])
        ]
    }
