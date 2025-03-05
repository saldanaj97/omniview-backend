from typing import Dict, List

import fastapi
import httpx

from app.core.config import TWITCH_CLIENT_ID


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
        raise fastapi.HTTPException(
            status_code=400, detail="Failed to retrieve top streams"
        )