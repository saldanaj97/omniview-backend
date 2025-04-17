import httpx

from app.utils.http_utils import check_kick_response_status


async def fetch_top_streams(credentials) -> dict:
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
        return standardize_livestream_data(raw_data)


def standardize_livestream_data(raw_data: dict) -> dict:
    """
    Standardizes the raw Kick API response into the unified Stream type.
    """
    return {
        "data": [
            {
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
            }
            for item in raw_data.get("data", [])
        ]
    }
